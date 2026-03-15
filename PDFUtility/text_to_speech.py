#!/usr/bin/env python3
# text_to_speech.py - Text to Speech engine for PDF Utility

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
import tempfile
import random
import fitz  # PyMuPDF

# Import Windows TTS support
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

from settings_controller import SettingsController
from PDFLogger import Logger

class TextToSpeech:
    def __init__(self):
        """Initialize the Text to Speech engine"""
        self.logger = Logger()
        self.settings_controller = SettingsController()
        
        # Load settings
        self.settings = self.settings_controller.load_settings()
        self.output_directory = self.settings.get("pdf", {}).get("default_output_dir", os.path.expanduser("~/Documents"))
        self.lang = self.settings.get("tts", {}).get("language", "en")
        self.rate = self.settings.get("tts", {}).get("rate", 150)
        self.volume = self.settings.get("tts", {}).get("volume", 1.0)
        self.voice = self.settings.get("tts", {}).get("voice", "System Default")
        
        # Determine which TTS engine to use
        self.use_windows_tts = (self.voice != "System Default" and PYTTSX3_AVAILABLE)
        
        if self.use_windows_tts:
            self.logger.info("TextToSpeech", f"Initializing Windows TTS Engine with voice: {self.voice}")
            try:
                self.windows_engine = pyttsx3.init()
                self._configure_windows_engine()
            except Exception as e:
                self.logger.error("TextToSpeech", f"Failed to initialize Windows TTS: {e}")
                self.use_windows_tts = False
                self.logger.info("TextToSpeech", "Falling back to Google TTS Engine")
        
        if not self.use_windows_tts:
            self.logger.info("TextToSpeech", "Initializing Google TTS Engine")
            self.windows_engine = None

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
        self.current_audio_data = None
        self.current_sample_rate = 0
        self.current_audio_frames = 0
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
        
        # Signals
        self.progress_callback = None
        self.status_callback = None
        self.complete_callback = None

    def _configure_windows_engine(self):
        """Configure the Windows TTS engine with selected voice and settings"""
        if not self.windows_engine:
            return
            
        try:
            # Set voice
            voices = self.windows_engine.getProperty('voices')
            voice_set = False
            
            for voice in voices:
                # First try exact match by voice ID (for saved voice IDs)
                if voice.id == self.voice:
                    self.windows_engine.setProperty('voice', voice.id)
                    self.logger.info("TextToSpeech", f"Set Windows TTS voice to: {voice.name} (ID: {voice.id})")
                    voice_set = True
                    break
                # Fallback: check if voice name contains our setting (for display names)
                elif self.voice in voice.name:
                    self.windows_engine.setProperty('voice', voice.id)
                    self.logger.info("TextToSpeech", f"Set Windows TTS voice to: {voice.name} (matched by name)")
                    voice_set = True
                    break
            
            if not voice_set:
                self.logger.warning("TextToSpeech", f"Could not find voice: {self.voice}. Using default voice.")
            
            # Set rate (Windows uses words per minute, settings uses 50-300 range)
            windows_rate = max(100, min(400, self.rate))  # Convert to WPM range
            self.windows_engine.setProperty('rate', windows_rate)
            
            # Set volume (0.0 to 1.0)
            self.windows_engine.setProperty('volume', self.volume)
            
        except Exception as e:
            self.logger.error("TextToSpeech", f"Error configuring Windows TTS: {e}")

    def reload_settings(self):
        """Reload settings and reconfigure TTS engine if needed"""
        self.settings = self.settings_controller.load_settings()
        new_voice = self.settings.get("tts", {}).get("voice", "System Default")
        new_rate = self.settings.get("tts", {}).get("rate", 150)
        new_volume = self.settings.get("tts", {}).get("volume", 1.0)
        
        # Check if we need to switch engines
        should_use_windows = (new_voice != "System Default" and PYTTSX3_AVAILABLE)
        
        if should_use_windows != self.use_windows_tts or new_voice != self.voice:
            self.logger.info("TextToSpeech", f"Voice setting changed from '{self.voice}' to '{new_voice}'")
            
            # Update settings
            self.voice = new_voice
            self.rate = new_rate
            self.volume = new_volume
            self.use_windows_tts = should_use_windows
            
            if self.use_windows_tts:
                self.logger.info("TextToSpeech", f"Switching to Windows TTS with voice: {self.voice}")
                try:
                    if not self.windows_engine:
                        self.windows_engine = pyttsx3.init()
                    self._configure_windows_engine()
                except Exception as e:
                    self.logger.error("TextToSpeech", f"Failed to initialize Windows TTS: {e}")
                    self.use_windows_tts = False
                    self.logger.info("TextToSpeech", "Falling back to Google TTS")
            else:
                self.logger.info("TextToSpeech", "Using Google TTS Engine")
                if self.windows_engine:
                    try:
                        self.windows_engine.stop()
                    except:
                        pass
        else:
            # Just update the settings values
            self.rate = new_rate
            self.volume = new_volume
            
            # Reconfigure if using Windows TTS
            if self.use_windows_tts and self.windows_engine:
                self._configure_windows_engine()

    def set_progress_callback(self, callback):
        """Set callback for progress updates"""
        self.progress_callback = callback
        
    def set_status_callback(self, callback):
        """Set callback for status updates"""
        self.status_callback = callback
        
    def set_complete_callback(self, callback):
        """Set callback for completion notification"""
        self.complete_callback = callback

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
        with self.files_lock:
            self.generated_files = []
            self.played_files = []
            self.current_audio_index = 0
            
        # Reset audio data
        self.current_audio_data = None
        self.current_sample_rate = 0
        self.current_audio_frames = 0
        
        # Clear queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
                
        # Start threads
        self.generator_thread = threading.Thread(target=self._generate_audio, daemon=True)
        self.playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self.monitor_thread = threading.Thread(target=self._monitor_playback, daemon=True)
        
        self.generator_thread.start()
        self.playback_thread.start()
        self.monitor_thread.start()
        
        # Notify status change
        if self.status_callback:
            self.status_callback("Started TTS playback")

    def _generate_audio(self):
        """Thread to generate audio files from text pages."""
        self.logger.info("TextToSpeech", f"Starting audio generation for {len(self.pages)} pages")
        
        if self.status_callback:
            self.status_callback(f"Generating audio for {len(self.pages)} pages")
        
        for i, page_text in enumerate(self.pages):
            # Check if we've been stopped
            if self.is_stopped.is_set():
                self.logger.info("TextToSpeech", "Audio generation stopped")
                break
                
            # If page text is empty or too short, skip it
            if not page_text or len(page_text.strip()) < 3:
                self.logger.info("TextToSpeech", f"Skipping empty or short page {i+1}")
                continue
                
            # Apply rate limiting
            with self.rate_limit_lock:
                now = time.time()
                since_last = now - self.last_tts_request
                if since_last < self.min_request_interval:
                    time.sleep(self.min_request_interval - since_last)
                self.last_tts_request = time.time()
                
            try:
                # Generate audio file
                temp_file = os.path.join(self.temp_dir, f"page_{i+1}_{random.randint(1000, 9999)}.mp3")
                
                self.logger.info("TextToSpeech", f"Generating audio for page {i+1}")
                if self.status_callback:
                    self.status_callback(f"Generating audio for page {i+1} of {len(self.pages)}")
                
                # Generate audio using appropriate engine
                if self.use_windows_tts and self.windows_engine:
                    # Use Windows TTS
                    temp_file = os.path.join(self.temp_dir, f"page_{i+1}_{random.randint(1000, 9999)}.wav")
                    self.windows_engine.save_to_file(page_text, temp_file)
                    self.windows_engine.runAndWait()
                    
                    # Convert WAV to MP3 for consistency
                    mp3_file = temp_file.replace('.wav', '.mp3')
                    try:
                        audio = AudioSegment.from_wav(temp_file)
                        audio.export(mp3_file, format="mp3")
                        os.remove(temp_file)  # Remove WAV file
                        temp_file = mp3_file
                    except Exception as conv_error:
                        self.logger.warning("TextToSpeech", f"Could not convert to MP3, using WAV: {conv_error}")
                        # Keep the WAV file if conversion fails
                        
                else:
                    # Use Google TTS
                    temp_file = os.path.join(self.temp_dir, f"page_{i+1}_{random.randint(1000, 9999)}.mp3")
                    tts = gTTS(text=page_text, lang=self.lang, slow=False)
                    tts.save(temp_file)
                
                # Add to generated files list and queue
                with self.files_lock:
                    self.generated_files.append(temp_file)
                    
                self.audio_queue.put(temp_file)
                
                self.logger.info("TextToSpeech", f"Added page {i+1} to queue")
                
                # Update progress
                if self.progress_callback:
                    progress = (i + 1) / len(self.pages)
                    self.progress_callback(progress)
                    
            except gTTSError as e:
                self.logger.error("TextToSpeech", f"TTS Error: {str(e)}")
                if self.status_callback:
                    self.status_callback(f"Error: {str(e)}")
            except Exception as e:
                self.logger.error("TextToSpeech", f"Error generating audio: {str(e)}")
                if self.status_callback:
                    self.status_callback(f"Error: {str(e)}")
                
        # Signal that generation is complete
        self.generation_complete.set()
        self.logger.info("TextToSpeech", "Audio generation complete")

    def _playback_loop(self):
        """Thread to play audio files from the queue."""
        while not self.is_stopped.is_set():
            # If paused, wait until resumed
            if self.is_paused.is_set():
                time.sleep(0.1)
                continue
                
            try:
                # Get the next audio file path from the queue
                try:
                    audio_file = self.audio_queue.get(timeout=0.5)
                except queue.Empty:
                    if self.generation_complete.is_set() and len(self.played_files) == len(self.generated_files):
                        # All files have been generated and played
                        self.logger.info("TextToSpeech", "All audio files played")
                        if self.complete_callback:
                            # Use a timer to call the callback from a different thread context
                            # to avoid cleanup being called from the playback thread
                            timer = threading.Timer(0.1, lambda: self.complete_callback("Playback completed"))
                            timer.start()
                        break
                    continue
                
                # Update current playback info
                with self.position_lock:
                    self.current_audio_file = audio_file
                    self.current_audio_index = len(self.played_files)
                    self.current_position = 0
                    self.playback_start_time = time.time()
                    
                # Play the audio file
                self.logger.info("TextToSpeech", f"Playing audio file: {os.path.basename(audio_file)}")
                if self.status_callback:
                    self.status_callback(f"Playing page {self.current_audio_index + 1}")
                    
                # Get audio data and info
                data, sample_rate = sf.read(audio_file)
                
                # Store duration for progress tracking
                self.current_audio_duration = len(data) / sample_rate
                
                # Apply volume
                data = data * self.volume
                
                # Reset playback finished flag
                self.playback_finished.clear()
                self.audio_playing = True
                
                # Determine number of channels properly
                if len(data.shape) == 1:
                    # Mono audio
                    channels = 1
                    self.current_audio_data = data.reshape(-1, 1)  # Convert to column vector
                else:
                    # Stereo or multi-channel audio
                    channels = data.shape[1]
                    self.current_audio_data = data
                
                # Store audio info for callback
                self.current_sample_rate = sample_rate
                self.current_audio_frames = len(self.current_audio_data)
                
                # Start playback using sounddevice
                with sd.OutputStream(samplerate=sample_rate, channels=channels,
                                    callback=self._audio_callback, finished_callback=self._on_audio_finished):
                    while not self.playback_finished.is_set() and not self.is_stopped.is_set():
                        # Wait for playback to finish or be stopped
                        time.sleep(0.1)
                        
                # Add to played files
                with self.files_lock:
                    if audio_file not in self.played_files:
                        self.played_files.append(audio_file)
                        
                self.audio_queue.task_done()
                
            except Exception as e:
                self.logger.error("TextToSpeech", f"Playback error: {str(e)}")
                self.playback_finished.set()
                if self.status_callback:
                    self.status_callback(f"Playback error: {str(e)}")
                time.sleep(0.5)  # Add a short delay before continuing
                
        # Clean up
        self.logger.info("TextToSpeech", "Playback thread ending")

    def _audio_callback(self, outdata, frames, time_info, status):
        """Callback for streaming audio data to sound device."""
        if status:
            self.logger.warning("TextToSpeech", f"Audio callback status: {status}")
            
        if self.is_paused.is_set() or self.is_stopped.is_set() or not hasattr(self, 'current_audio_data'):
            outdata.fill(0)  # Output silence
            return
            
        try:
            with self.position_lock:
                start_frame = self.current_position
                end_frame = min(start_frame + frames, self.current_audio_frames)
                
                if start_frame >= self.current_audio_frames:
                    # End of audio data
                    outdata.fill(0)
                    self.playback_finished.set()
                    return
                
                # Get the audio chunk
                chunk = self.current_audio_data[start_frame:end_frame]
                self.current_position = end_frame
                
                # Ensure proper shape for output
                if len(chunk) < frames:
                    # Pad with silence if chunk is shorter than requested frames
                    if chunk.shape[1] == 1:  # Mono
                        outdata[:len(chunk), 0] = chunk[:, 0]
                        outdata[len(chunk):, 0] = 0
                    else:  # Stereo or multi-channel
                        outdata[:len(chunk)] = chunk
                        outdata[len(chunk):] = 0
                    self.playback_finished.set()  # Signal end of file
                else:
                    # Copy data to output buffer
                    if chunk.shape[1] == 1:  # Mono
                        outdata[:, 0] = chunk[:, 0]
                    else:  # Stereo or multi-channel
                        outdata[:] = chunk
                
        except Exception as e:
            self.logger.error("TextToSpeech", f"Error in audio callback: {str(e)}")
            outdata.fill(0)
            self.playback_finished.set()

    def _on_audio_finished(self):
        """Called when an audio file finishes playing."""
        self.logger.info("TextToSpeech", "Audio finished playing")
        self.audio_playing = False
        self.playback_finished.set()

    def _monitor_playback(self):
        """Thread to monitor playback progress."""
        while not self.is_stopped.is_set():
            if self.audio_playing and not self.is_paused.is_set() and self.current_audio_duration > 0:
                # Calculate progress as a value between 0 and 1
                with self.position_lock:
                    if self.current_position > 0:
                        elapsed = time.time() - self.playback_start_time
                        progress = min(1.0, elapsed / self.current_audio_duration)
                        
                        if self.progress_callback:
                            # Calculate overall progress based on pages
                            current_page_index = self.current_audio_index
                            total_pages = len(self.pages)
                            overall_progress = (current_page_index + progress) / total_pages
                            self.progress_callback(overall_progress)
                            
            time.sleep(0.1)

    def pause(self):
        """Pause playback."""
        self.logger.info("TextToSpeech", "Pausing playback")
        self.is_paused.set()
        if self.status_callback:
            self.status_callback("Playback paused")

    def resume(self):
        """Resume playback."""
        self.logger.info("TextToSpeech", "Resuming playback")
        self.is_paused.clear()
        with self.position_lock:
            self.playback_start_time = time.time() - (self.current_position / 22050)  # Adjust for elapsed time
        if self.status_callback:
            self.status_callback("Playback resumed")

    def stop(self):
        """Stop playback gracefully."""
        self.logger.info("TextToSpeech", "Stopping playback")
        self._force_stop()
        if self.status_callback:
            self.status_callback("Playback stopped")

    def _force_stop(self):
        """Forcibly stop all playback and generation threads."""
        self.is_stopped.set()
        self.is_paused.clear()  # Clear pause to allow threads to see the stop flag
        self.playback_finished.set()
        
        # Clear audio data to prevent callback issues
        self.current_audio_data = None
        self.current_sample_rate = 0
        self.current_audio_frames = 0
        
        # Get current thread to avoid joining self
        current_thread = threading.current_thread()
        
        if (self.playback_thread and self.playback_thread.is_alive() and 
            self.playback_thread != current_thread):
            self.playback_thread.join(timeout=1.0)
            
        if (self.generator_thread and self.generator_thread.is_alive() and 
            self.generator_thread != current_thread):
            self.generator_thread.join(timeout=1.0)
            
        if (self.monitor_thread and self.monitor_thread.is_alive() and 
            self.monitor_thread != current_thread):
            self.monitor_thread.join(timeout=1.0)

    def skip(self):
        """Skip to the next page."""
        self.logger.info("TextToSpeech", "Skipping to next page")
        # Force the current playback to end
        self.playback_finished.set()
        if self.status_callback:
            self.status_callback("Skipping to next page")

    def rewind(self):
        """Go back to the previous page."""
        self.logger.info("TextToSpeech", "Rewinding to previous page")
        
        # Check if we have a previous page
        with self.files_lock:
            if self.current_audio_index > 0:
                # Force the current playback to end
                self.playback_finished.set()
                
                # Get the previous file
                prev_file = self.played_files[self.current_audio_index - 1]
                
                # Remove the current file from played files
                if self.current_audio_index < len(self.played_files):
                    self.played_files.pop()
                    
                # Add the previous file back to the queue
                self.audio_queue.put(prev_file)
                
                # Add the current file back to the queue
                if self.current_audio_file:
                    self.audio_queue.put(self.current_audio_file)
                    
                if self.status_callback:
                    self.status_callback("Rewinding to previous page")

    def is_playing(self):
        """Return True if audio is currently playing."""
        return self.audio_playing and not self.is_paused.is_set() and not self.is_stopped.is_set()

    def get_progress(self):
        """Return the current playback progress (0-1)."""
        if not self.is_playing() or len(self.pages) == 0:
            return 0
            
        with self.files_lock:
            with self.position_lock:
                current_page_index = self.current_audio_index
                total_pages = len(self.pages)
                
                if self.current_audio_duration > 0:
                    elapsed = time.time() - self.playback_start_time
                    page_progress = min(1.0, elapsed / self.current_audio_duration)
                else:
                    page_progress = 0
                    
                overall_progress = (current_page_index + page_progress) / total_pages
                return overall_progress
                
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file, returning a list of page texts."""
        self.logger.info("TextToSpeech", f"Extracting text from PDF: {pdf_path}")
        
        try:
            # Open the PDF
            pdf_doc = fitz.open(pdf_path)
            
            # Extract text from each page
            pages = []
            for i in range(len(pdf_doc)):
                page = pdf_doc[i]
                text = page.get_text()
                
                # Clean up the text
                text = text.strip()
                if text:  # Only add non-empty pages
                    pages.append(text)
                    
            self.logger.info("TextToSpeech", f"Extracted {len(pages)} pages of text")
            return pages
            
        except Exception as e:
            self.logger.error("TextToSpeech", f"Error extracting text: {str(e)}")
            return []
            
    def cleanup_temp_files(self):
        """Clean up temporary audio files."""
        self.logger.info("TextToSpeech", "Cleaning up temporary files")
        
        # Don't forcibly stop if we're being called from a callback
        # Just mark as stopped and let threads finish naturally
        current_thread = threading.current_thread()
        if (current_thread == self.playback_thread or 
            current_thread == self.generator_thread or 
            current_thread == self.monitor_thread):
            # We're being called from one of our own threads
            # Just mark as stopped and clean files
            self.is_stopped.set()
            self._cleanup_files_only()
        else:
            # Safe to force stop from external thread
            self._force_stop()
            self._cleanup_files_only()
            
    def _cleanup_files_only(self):
        """Clean up just the files without stopping threads"""
        # Remove generated files
        with self.files_lock:
            for file_path in self.generated_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    self.logger.warning("TextToSpeech", f"Error removing temp file {file_path}: {str(e)}")
                    
            # Clear the lists
            self.generated_files = []
            self.played_files = []
            
        self.logger.info("TextToSpeech", "Temporary files cleaned up")
