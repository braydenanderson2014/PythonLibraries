import threading
import queue
import io
import os
import time
import numpy as np
import sounddevice as sd
import soundfile as sf
from pydub import AudioSegment
from gtts import gTTS
from gtts.tts import gTTSError
from PDFUtility.PDFLogger import Logger
import sys
import tempfile
import random
from SettingsController import SettingsController
import tkinter as tk


class TextToSpeech:
    def __init__(self, lang="en", rate=1.0, volume=1.0):
        self.root = tk.Tk()
        self.root.withdraw()  # hide the window because we don't need it. it's only there for settings.

        self.settings = SettingsController(self.root)
        self.settings.load_settings()
        self.output_directory = self.settings.get_setting("output_directory")
        self.logger = Logger()
        self.logger.info("TextToSpeech", f"Output Directory Set to {self.output_directory}")
        self.logger.info("TextToSpeech", "Initializing Google TTS Engine")

        self.lang = lang
        self.rate = rate
        self.volume = volume

        # Thread control events
        self.is_paused = threading.Event()
        self.is_stopped = threading.Event()
        self.is_stopped.set()  # Ensure stopped initially
        
        # Queue for audio data - store actual file paths instead of binary data
        self.audio_queue = queue.Queue(maxsize=10)
        
        # Thread references
        self.playback_thread = None
        self.generator_thread = None
        self.monitor_thread = None
        
        # Create a dedicated temp directory for our app
        self.temp_dir = os.path.join(tempfile.gettempdir(), "pdf_tts_temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.logger.info("TextToSpeech", f"Using temp directory: {self.temp_dir}")
        
        # File access lock
        self.file_lock = threading.Lock()
        
        # Track all generated audio files
        self.generated_files = []  # All generated files in order
        self.played_files = []     # Files that have been played
        
        # Current playback tracking
        self.current_audio_file = None
        self.current_audio_index = 0
        self.current_position = 0
        self.audio_playing = False
        self.current_audio_duration = 0
        self.playback_start_time = 0
        
        # Synchronization
        self.position_lock = threading.Lock()
        self.playback_lock = threading.Lock()
        self.queue_lock = threading.Lock()
        self.files_lock = threading.Lock()
        
        # Events for signaling between threads
        self.playback_finished = threading.Event()
        self.playback_finished.set()  # Initially no playback happening
        
        # Completion tracking
        self.generation_complete = threading.Event()
        
        # Rate limiting controls
        self.last_tts_request = 0
        self.min_request_interval = 1.0  # Minimum seconds between API requests
        self.rate_limit_lock = threading.Lock()

    def start(self, pages):
        """Starts generating and playing pages."""
        self.logger.info("TextToSpeech", "Starting playback")
        
        # Stop any existing playback
        self._force_stop()
        
        # Set up for new playback
        self.is_stopped.clear()
        self.is_paused.clear()
        self.generation_complete.clear()
        
        # Reset state
        self.pages = pages
        self.current_page = 0
        
        with self.position_lock:
            self.current_position = 0
            self.current_audio_file = None
            self.current_audio_index = 0
            self.playback_start_time = 0
            self.current_audio_duration = 0
        
        with self.files_lock:
            self.generated_files = []
            self.played_files = []
            
        # Ensure playback finished flag is set (no active playback)
        self.playback_finished.set()
        
        # Start background threads
        self.generator_thread = threading.Thread(target=self._generate_audio_loop, daemon=True)
        self.generator_thread.start()

        self.playback_thread = threading.Thread(target=self._play_audio_loop, daemon=True)
        self.playback_thread.start()

    def stop(self):
        """Stops playback and clears the queue."""
        self.logger.info("TextToSpeech", "Stopping playback")
        
        # Force a complete stop with timeout
        self._force_stop()
        
        # Reset position tracking
        with self.position_lock:
            self.current_position = 0
            self.current_audio_file = None
            self.current_audio_index = 0
            self.playback_start_time = 0
            self.current_audio_duration = 0
            
        # Clean up temp files - do this last
        self._cleanup_temp_files()
        
        self.logger.info("TextToSpeech", "Playback stopped successfully")

    def _force_stop(self):
        """Force a complete stop of all audio operations with timeout protection."""
        # Set stop flags
        self.is_stopped.set()
        
        # Immediately stop audio
        try:
            sd.stop()
        except Exception as e:
            self.logger.error("TextToSpeech", f"Error stopping sounddevice: {e}")
        
        # Set flags
        with self.playback_lock:
            self.audio_playing = False
            self.playback_finished.set()
        
        # Clear queue with timeout protection
        try:
            # Clear the queue with a timeout
            clear_start = time.time()
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()  # Clear queue without blocking
                except Exception:
                    # If we get an exception, break the loop
                    break
                
                # Safety timeout of 0.5 seconds for queue clearing
                if time.time() - clear_start > 0.5:
                    self.logger.warning("TextToSpeech", "Queue clearing timed out")
                    break
        except Exception as e:
            self.logger.error("TextToSpeech", f"Error clearing queue: {e}")
        
        # Wait for threads to notice stop with timeout
        if self.playback_thread and self.playback_thread.is_alive():
            try:
                self.playback_thread.join(timeout=0.5)
            except Exception:
                self.logger.warning("TextToSpeech", "Playback thread failed to join")
                
        if self.generator_thread and self.generator_thread.is_alive():
            try:
                self.generator_thread.join(timeout=0.5)
            except Exception:
                self.logger.warning("TextToSpeech", "Generator thread failed to join")
                
        if self.monitor_thread and self.monitor_thread.is_alive():
            try:
                self.monitor_thread.join(timeout=0.5)
            except Exception:
                self.logger.warning("TextToSpeech", "Monitor thread failed to join")

    def pause(self):
        """Pauses playback."""
        if self.is_paused.is_set():
            return  # Already paused

        self.logger.info("TextToSpeech", "Pausing playback")
        self.is_paused.set()

        try:
            # Calculate position based on elapsed time
            with self.position_lock:
                if self.playback_start_time > 0:
                    self.current_position += time.time() - self.playback_start_time
            # Stop playback
            sd.stop()
            with self.playback_lock:
                pass
        except Exception as e:
            self.logger.error("TextToSpeech", f"Error in pause: {e}")


    def resume(self):
        if not self.is_paused.is_set() or self.is_stopped.is_set():
            return  # Not paused or stopped 

        self.logger.info("TextToSpeech", "Resuming playback")   

        with self.position_lock:
            audio_file = self.current_audio_file
            position = self.current_position  # seconds
            audio_index = self.current_audio_index  

        if audio_file and os.path.exists(audio_file):
            try:
                self.logger.info("TextToSpeech", f"Resuming from file: {audio_file} (index {audio_index})")
                data, samplerate = sf.read(audio_file, dtype='float32')
                # Convert position in seconds to frame index
                start_frame = int(position * samplerate)
                if start_frame < len(data):
                    remainder = data[start_frame:]
                    duration = len(remainder) / samplerate
                    self.logger.info("TextToSpeech", f"Resumed playback from position {start_frame} ({position:.2f}s), playing {len(remainder)} frames ({duration:.2f}s)")
                    with self.position_lock:
                        self.playback_start_time = time.time()
                        self.current_audio_duration = duration
                    def finished_callback():
                        with self.playback_lock:
                            self.audio_playing = False
                            self.playback_finished.set()
                    with self.playback_lock:
                        self.audio_playing = True
                        self.playback_finished.clear()
                    sd.play(remainder, samplerate, blocking=False)
                    self.monitor_thread = threading.Thread(
                        target=self._monitor_playback,
                        args=(finished_callback, duration),
                        daemon=True
                    )
                    self.monitor_thread.start()
                else:
                    self.logger.warning("TextToSpeech", "Resume position beyond end of audio - moving to next audio")
                    with self.files_lock:
                        if audio_index + 1 < len(self.generated_files):
                            # Move to next file logic here
                            pass
                    with self.playback_lock:
                        self.playback_finished.set()
            except Exception as e:
                self.logger.error("TextToSpeech", f"Error resuming playback: {e}")
                with self.playback_lock:
                    self.playback_finished.set()
        else:
            # Fallback logic for missing file
            pass    

        self.is_paused.clear()

    def _monitor_playback(self, finished_callback, duration_seconds):
        """Monitor audio playback and call the callback when done."""
        try:
            # Wait for the duration of the audio plus a small buffer
            sleep_time = max(0.5, duration_seconds + 0.5)  # At least 0.5 seconds
            
            start_time = time.time()
            
            # Keep checking if playback should continue
            while (time.time() - start_time < sleep_time and 
                   not self.is_stopped.is_set() and 
                   not self.is_paused.is_set()):
                time.sleep(0.1)
                
            # Only mark as finished if we weren't stopped or paused
            if not self.is_stopped.is_set() and not self.is_paused.is_set():
                # Add current file to played files list
                with self.files_lock:
                    if self.current_audio_file and self.current_audio_file not in self.played_files:
                        self.played_files.append(self.current_audio_file)
                
                finished_callback()
                
        except Exception as e:
            self.logger.error("TextToSpeech", f"Error in monitor thread: {e}")
            # Call the callback even on error to prevent hanging
            finished_callback()

    def skip(self):
        """Skips to the next page."""
        self.logger.info("TextToSpeech", "Skipping to next page")
        try:
            # Stop current playback
            sd.stop()
            
            with self.playback_lock:
                self.audio_playing = False
                self.playback_finished.set()
            
            # Move to next audio file if available
            with self.files_lock:
                current_index = self.current_audio_index
                if current_index + 1 < len(self.generated_files):
                    next_file = self.generated_files[current_index + 1]
                    with self.position_lock:
                        self.current_audio_file = next_file
                        self.current_audio_index = current_index + 1
                        self.current_position = 0
                        self.playback_start_time = 0
                        self.current_audio_duration = 0
                else:
                    # No next file available yet
                    self.logger.info("TextToSpeech", "No next file available for skip, waiting for generation")
            
        except Exception as e:
            self.logger.error("TextToSpeech", f"Error in skip: {e}")

    def rewind(self):
        """Rewinds to the previous page."""
        self.logger.info("TextToSpeech", "Rewinding to previous page")
        try:
            # Stop current playback
            sd.stop()
            
            with self.playback_lock:
                self.audio_playing = False
                self.playback_finished.set()
            
            # Move to previous audio file if available
            with self.files_lock:
                current_index = self.current_audio_index
                if current_index > 0:
                    prev_file = self.generated_files[current_index - 1]
                    with self.position_lock:
                        self.current_audio_file = prev_file
                        self.current_audio_index = current_index - 1
                        self.current_position = 0
                        self.playback_start_time = 0
                        self.current_audio_duration = 0
                else:
                    # Already at the first file
                    self.logger.info("TextToSpeech", "Already at the first file, cannot rewind further")
            
        except Exception as e:
            self.logger.error("TextToSpeech", f"Error in rewind: {e}")

    def set_language(self, lang):
        """Set speech language."""
        self.logger.info("TextToSpeech", f"Setting language: {lang}")
        self.lang = lang

    def _respect_rate_limit(self):
        """Respect the TTS API rate limit by waiting if needed."""
        with self.rate_limit_lock:
            now = time.time()
            time_since_last = now - self.last_tts_request
            
            if time_since_last < self.min_request_interval:
                # Wait to respect rate limit
                sleep_time = self.min_request_interval - time_since_last
                # Add some jitter to avoid all threads hitting at the same time
                sleep_time += random.uniform(0.1, 0.5)
                time.sleep(sleep_time)
                
            # Update the last request time
            self.last_tts_request = time.time()

    def _generate_audio_loop(self):
        """Continuously generates speech files and queues them."""
        self.logger.info("TextToSpeech", "Starting audio generation loop")

        while not self.is_stopped.is_set() and self.current_page < len(self.pages):
            # If we're paused, slow down generation to save API calls
            if self.is_paused.is_set():
                time.sleep(0.5)  # Longer sleep during pause
            
            # Check if queue is full before adding more
            if self.audio_queue.full():
                time.sleep(0.1)
                continue
                
            # Get current page text
            text = self.pages[self.current_page]

            self.logger.info("TextToSpeech", f"Generating audio for page {self.current_page + 1}")
            audio_file = self._text_to_audio_file(text, f"page_{self.current_page + 1}")

            # Only add to queue if we have valid audio
            if audio_file and os.path.exists(audio_file):
                try:
                    with self.queue_lock:
                        # Check again if we've been stopped before adding to queue
                        if self.is_stopped.is_set():
                            break
                        self.audio_queue.put(audio_file, timeout=1.0)
                    
                    # Add to generated files list
                    with self.files_lock:
                        if audio_file not in self.generated_files:
                            self.generated_files.append(audio_file)
                            
                    self.current_page += 1
                except Exception as e:
                    self.logger.error("TextToSpeech", f"Error adding to queue: {e}")
            else:
                # Skip this page if we couldn't generate audio, but don't increment immediately
                # to allow for a retry
                retry_count = getattr(self, '_retry_count', 0) + 1
                self._retry_count = retry_count
                
                if retry_count > 3:  # After 3 retries, skip this page
                    self.logger.warning("TextToSpeech", f"Failed to generate audio after {retry_count} retries, skipping page {self.current_page + 1}")
                    self.current_page += 1
                    self._retry_count = 0
                else:
                    # Wait longer between retries, with increasing backoff
                    wait_time = 2.0 * retry_count
                    self.logger.info("TextToSpeech", f"Retry {retry_count} for page {self.current_page + 1}, waiting {wait_time}s")
                    time.sleep(wait_time)
                
            # Small sleep to prevent CPU thrashing
            time.sleep(0.05)
        
        # Set generation complete flag
        self.logger.info("TextToSpeech", "Audio generation completed")
        self.generation_complete.set()

    def _play_audio_loop(self):
        """Continuously plays audio files from the queue."""
        while not self.is_stopped.is_set():
            try:
                # Check if we're paused
                if self.is_paused.is_set():
                    time.sleep(0.1)
                    continue
                
                # Check if we're already playing
                playback_active = False
                with self.playback_lock:
                    playback_active = self.audio_playing and not self.playback_finished.is_set()
                    
                if playback_active:
                    time.sleep(0.1)  # Wait for current playback to finish
                    continue
                
                # Get audio file from queue if available
                audio_file = None
                with self.queue_lock:
                    if not self.audio_queue.empty():
                        audio_file = self.audio_queue.get(block=False)
                
                if audio_file and os.path.exists(audio_file):
                    with self.files_lock:
                        try:
                            audio_index = self.generated_files.index(audio_file)
                            self.logger.info("TextToSpeech", f"Playing audio file {audio_file} (index {audio_index})")
                        except ValueError:
                            # File not in list - should never happen
                            audio_index = len(self.generated_files)
                            self.logger.warning("TextToSpeech", f"Playing file not in generated list: {audio_file}")
                    
                    # Update current file and index
                    with self.position_lock:
                        self.current_audio_file = audio_file
                        self.current_audio_index = audio_index
                        self.current_position = 0
                    
                    # Play the audio file
                    self._play_audio_file(audio_file)
                else:
                    # Check if generation is complete and we've played all files
                    if self.generation_complete.is_set():
                        with self.files_lock:
                            all_played = True
                            for file in self.generated_files:
                                if file not in self.played_files:
                                    all_played = False
                                    break
                            
                            if all_played:
                                self.logger.info("TextToSpeech", "All audio files played and generation complete")
                                break
                    
                    # No audio available yet, wait a bit
                    time.sleep(0.1)
            except queue.Empty:
                # Queue timeout, just continue
                time.sleep(0.1)
            except Exception as e:
                self.logger.error("TextToSpeech", f"Error in play loop: {e}")
                time.sleep(0.1)
                
        self.logger.info("TextToSpeech", "Playback loop completed")

    def _text_to_audio_file(self, text, prefix="audio"):
        """Converts text to speech and saves to a file with retry logic and rate limiting."""
        if not text or not text.strip():
            self.logger.warning("TextToSpeech", "Skipping empty text page.")
            return None

        # Respect rate limits
        self._respect_rate_limit()
        
        try:
            # Create unique filename
            audio_file = os.path.join(self.temp_dir, f"{prefix}_{time.time()}_{random.randint(1000, 9999)}.wav")
            
            # Generate speech
            tts = gTTS(text, lang=self.lang)
            
            # Create a temporary MP3 file
            temp_mp3 = audio_file.replace(".wav", ".mp3")
            tts.save(temp_mp3)
            
            # Convert to WAV
            audio = AudioSegment.from_mp3(temp_mp3)
            audio.export(audio_file, format="wav")
            
            # Delete temporary MP3
            if os.path.exists(temp_mp3):
                os.remove(temp_mp3)
                
            return audio_file
            
        except gTTSError as e:
            if "429" in str(e):  # Too Many Requests
                self.logger.error("TextToSpeech", f"Rate limit exceeded: {e}")
                # Increase the minimum interval to back off more
                with self.rate_limit_lock:
                    self.min_request_interval = min(self.min_request_interval * 1.5, 5.0)  # Cap at 5 seconds
            else:
                self.logger.error("TextToSpeech", f"Error generating speech: {e}")
            return None
        except Exception as e:
            self.logger.error("TextToSpeech", f"Error generating speech: {e}")
            return None

    def _play_audio_file(self, audio_file):
        """Plays a WAV audio file using sounddevice."""
        if not audio_file or not os.path.exists(audio_file):
            with self.playback_lock:
                self.playback_finished.set()
            return
            
        try:
            # Load the audio file with explicit data type as float32
            data, samplerate = sf.read(audio_file, dtype='float32')
            
            # Calculate duration
            duration = len(data) / samplerate
            
            # Log audio info for debugging
            self.logger.info("TextToSpeech", f"Audio: {audio_file}, shape={data.shape}, dtype={data.dtype}, sr={samplerate}, duration={duration:.2f}s")
            
            # Store the start time and duration for pause/resume tracking
            with self.position_lock:
                self.playback_start_time = time.time()
                self.current_audio_duration = duration
            
            # Set up a finished callback
            def finished_callback():
                with self.playback_lock:
                    if not self.is_paused.is_set():
                        self.audio_playing = False
                        self.playback_finished.set()
                        
                # Add to played files list
                with self.files_lock:
                    if audio_file not in self.played_files:
                        self.played_files.append(audio_file)
            
            # Mark as playing
            with self.playback_lock:
                self.audio_playing = True
                self.playback_finished.clear()
            
            # Play the audio in non-blocking mode
            sd.play(data, samplerate, blocking=False)
            
            # Start a thread to check when playback is done
            self.monitor_thread = threading.Thread(
                target=self._monitor_playback,
                args=(finished_callback, duration),
                daemon=True
            )
            self.monitor_thread.start()
                
        except Exception as e:
            self.logger.error("TextToSpeech", f"Audio playback error: {e}")
            
            with self.playback_lock:
                self.audio_playing = False
                self.playback_finished.set()

    def _cleanup_temp_files(self):
        """Clean up temporary files at the end of playback."""
        # Only clean up if we're stopping completely
        if not self.is_stopped.is_set():
            return
            
        with self.files_lock:
            for file_path in self.generated_files:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        self.logger.debug("TextToSpeech", f"Deleted temp file: {file_path}")
                    except Exception as e:
                        self.logger.warning("TextToSpeech", f"Error deleting temporary file {file_path}: {e}")
            
            # Clear the lists
            self.generated_files = []
            self.played_files = []

    def is_playing(self):
        """Check if TTS is playing."""
        return not self.is_stopped.is_set() and not self.is_paused.is_set()

    def get_progress(self):
        """Get playback progress."""
        with self.files_lock:
            if not self.generated_files:
                return 0.0
                
            with self.position_lock:
                current_index = self.current_audio_index
                current_position = getattr(self, 'current_position', 0)  # seconds already played

            # Calculate progress based on files played plus current position in current file
            if current_index >= len(self.generated_files):
                return 1.0
                
            # Basic progress based on index
            progress = current_index / len(self.pages) if self.pages else 0.0
            
            # Add fractional progress for current file
            if self.playback_start_time > 0 and self.current_audio_duration > 0:
                elapsed = time.time() - self.playback_start_time
                total_elapsed = current_position + elapsed  # Add already-played portion

                if total_elapsed > 0 and total_elapsed < self.current_audio_duration:
                    file_progress = total_elapsed / self.current_audio_duration
                    file_weight = 1.0 / len(self.pages) if self.pages else 0.0
                    progress += file_progress * file_weight
            
            return min(progress, 1.0)
        
    def __del__(self):
        """Destructor to ensure we clean up."""
        self._force_stop()
        self._cleanup_temp_files()


    def shutdown(self):
        """Shuts down all threads and cleans up resources."""
        self.logger.info("TextToSpeech", "Shutting down TextToSpeech module")

        # Stop playback and set the stop flag
        self.is_stopped.set()

        # Stop any ongoing playback
        try:
            sd.stop()
        except Exception as e:
            self.logger.error("TextToSpeech", f"Error stopping sounddevice: {e}")

        # Clear the audio queue
        try:
            while not self.audio_queue.empty():
                self.audio_queue.get_nowait()
        except Exception as e:
            self.logger.error("TextToSpeech", f"Error clearing audio queue: {e}")

        # Join all threads
        if self.playback_thread and self.playback_thread.is_alive():
            self.logger.info("TextToSpeech", "Waiting for playback thread to terminate")
            self.playback_thread.join(timeout=1.0)

        if self.generator_thread and self.generator_thread.is_alive():
            self.logger.info("TextToSpeech", "Waiting for generator thread to terminate")
            self.generator_thread.join(timeout=1.0)

        if self.monitor_thread and self.monitor_thread.is_alive():
            self.logger.info("TextToSpeech", "Waiting for monitor thread to terminate")
            self.monitor_thread.join(timeout=1.0)

        

        # Clean up temporary files
        self._cleanup_temp_files()

        self.logger.info("TextToSpeech", "TextToSpeech module shut down successfully")