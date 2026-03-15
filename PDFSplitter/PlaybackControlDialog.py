import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
from PDFUtility.PDFLogger import Logger
class PlaybackControlDialog:
    def __init__(self, parent, tts, pdf_utility):
        self.tts = tts
        self.pdf_utility = pdf_utility
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Playback Control")
        self.dialog.geometry("400x350")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.logger = Logger()

        self.logger.info("PlaybackControlDialog", "Playback control dialog opened")

        ttk.Label(self.dialog, text="Now Playing:", font=("Arial", 12, "bold")).pack(pady=5)

        selected_indices = self.pdf_utility.listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Info", "No PDF file selected.")
            self.dialog.destroy()
            return

        self.pdf_file = self.pdf_utility.pdf_files[selected_indices[0]]
        self.now_playing_label = ttk.Label(self.dialog, text=os.path.basename(self.pdf_file), wraplength=300, anchor="center")
        self.now_playing_label.pack(pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.dialog, variable=self.progress_var, length=300, mode="determinate")
        self.progress_bar.pack(pady=5)

        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=10)

        self.play_btn = ttk.Button(button_frame, text="▶ Play", command=self.play_selected, width=12)
        self.play_btn.grid(row=0, column=0, padx=5, pady=5)
        self.pause_btn = ttk.Button(button_frame, text="⏸ Pause", command=self.pause_playback, width=12, state=tk.DISABLED)
        self.pause_btn.grid(row=0, column=1, padx=5, pady=5)
        self.resume_btn = ttk.Button(button_frame, text="⏵ Resume", command=self.resume_playback, width=12, state=tk.DISABLED)
        self.resume_btn.grid(row=1, column=0, padx=5, pady=5)
        self.stop_btn = ttk.Button(button_frame, text="⏹ Stop", command=self.stop_playback, width=12, state=tk.DISABLED)
        self.stop_btn.grid(row=1, column=1, padx=5, pady=5)
        self.skip_btn = ttk.Button(button_frame, text="⏭ Skip", command=self.skip_page, width=12)
        self.skip_btn.grid(row=2, column=0, padx=5, pady=5)
        self.rewind_btn = ttk.Button(button_frame, text="⏮ Rewind", command=self.rewind_page, width=12)
        self.rewind_btn.grid(row=2, column=1, padx=5, pady=5)

        self.pages = self.pdf_utility.extract_text_from_pdf(self.pdf_file)
        self.state = "stopped"  # can be 'playing', 'paused', 'stopped'
        self.progress_var.set(0)
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)

    def play_selected(self):
        if not self.pages:
            self.logger.warning("PlaybackController", "No text found in PDF.")
            messagebox.showinfo("Info", "No readable text found in the selected PDF.")
            return
        self.state = "playing"
        self.play_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.resume_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.logger.info("PlaybackController", f"Playing PDF: {self.pdf_file}")
        self.now_playing_label.config(text=os.path.basename(self.pdf_file))
        self.tts.start(self.pages)
        self.update_progress()

    def update_progress(self):
        if self.state == "playing" and self.tts.is_playing():
            progress = self.tts.get_progress() * 100
            self.progress_var.set(progress)
            self.dialog.after(500, self.update_progress)
            self.logger.info("PlaybackControlDialog", f"Playback progress: {progress}%")
        elif self.state == "playing":
            self.progress_var.set(100)
            self.stop_playback()

    def pause_playback(self):
        if self.state == "playing":
            self.state = "paused"
            self.pause_btn.config(state=tk.DISABLED)
            self.resume_btn.config(state=tk.NORMAL)
            self.logger.info("PlaybackController", "Pausing playback")
            self.tts.pause()

    def resume_playback(self):
        if self.state == "paused":
            self.state = "playing"
            self.pause_btn.config(state=tk.NORMAL)
            self.resume_btn.config(state=tk.DISABLED)
            self.logger.info("PlaybackController", "Resuming playback")
            self.tts.resume()
            self.update_progress()

    def stop_playback(self):
        self.state = "stopped"
        self.play_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.resume_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        self.logger.info("PlaybackController", "Stopping playback")
        self.tts.stop()
        self.progress_var.set(0)
        self.now_playing_label.config(text=os.path.basename(self.pdf_file))

    def skip_page(self):
        self.logger.info("PlaybackController", "Skipping to next page")
        self.tts.skip()

    def rewind_page(self):
        self.logger.info("PlaybackController", "Rewinding to previous page")
        self.tts.rewind()

    def on_close(self):
        self.stop_playback()
        self.dialog.destroy()