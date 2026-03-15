# split_controller.py
"""PDF Split Controller – splits PDFs with multiple custom options.
Updated 2025‑05‑31: now tracks newly‑created files and exposes
`get_split_files()` / `get_completed_files()` so the caller can refresh its
master list just like the merge controller does.
"""

from __future__ import annotations

import os
import re
import gc
import time
import tempfile
import shutil
import traceback
import datetime
from dataclasses import dataclass
from multiprocessing import Process, Queue, Event, cpu_count, freeze_support
from threading import Thread
from typing import List, Tuple

import fitz  # PyMuPDF
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from psutil import disk_usage

from PDFUtility.PDFLogger import Logger
from SettingsController import SettingsController
from Utility import Utility
from ProgressDialog import DualProgressDialog

# ---------------------------------------------------------------------------
# Worker helper
# ---------------------------------------------------------------------------

def pdf_split_worker(task_id: int,
                     input_file: str,
                     output_path: str,
                     page_ranges: List[Tuple[int, int]],
                     result_queue: Queue,
                     cancel_event: Event,
                     log_dir: str) -> None:
    """Extract *page_ranges* from *input_file* and save to *output_path*."""
    name = f"SplitWorker-{task_id}"
    log_file = os.path.join(log_dir, f"split_worker_{task_id}.log") if log_dir else None
    try:
        def _log(msg: str):
            if log_file:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(msg + "\n")

        _log(f"{name}: started ‣ {input_file} -> {output_path} ranges:{page_ranges}")
        src = fitz.open(input_file)
        dst = fitz.open()
        for (start, end) in page_ranges:
            end = min(end, len(src) - 1)
            if cancel_event.is_set():
                _log(f"{name}: cancelled before copying {start}-{end}")
                result_queue.put(("cancelled", task_id, output_path))
                return
            dst.insert_pdf(src, from_page=start, to_page=end)
            _log(f"{name}: copied {start}-{end}")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        dst.save(output_path)
        dst.close()
        src.close()
        _log(f"{name}: completed successfully → {output_path}")
        result_queue.put(("success", task_id, output_path))
    except Exception as exc:
        tb = traceback.format_exc()
        if log_file:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(tb)
        result_queue.put(("error", task_id, str(exc)))


# ---------------------------------------------------------------------------
# Helper dataclass
# ---------------------------------------------------------------------------

@dataclass
class SplitJob:
    id: int
    input_file: str
    output_path: str
    ranges: List[Tuple[int, int]]  # inclusive 0‑based ranges


# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------

class SplitController:
    """Mirror of MergeController but for *splitting* PDFs."""

    def __init__(self, root: tk.Tk, selection_indices: List[int]):
        self.root = root
        self.selection_indices = selection_indices
        self.selected_indices: List[int] = []
        self.pdf_files: List[str] = []  # caller's master list (mutated)

        self.logger = Logger()
        self.settings_controller = SettingsController(root)
        self.settings = self.settings_controller.load_settings()
        self.utility = Utility(root)

        self.logger.info("SplitController", "==========================================================")
        self.logger.info("SplitController", " EVENT: INIT")
        self.logger.info("SplitController", "==========================================================")

        # Runtime state
        self.status_label = None
        self.cancel_event: Event | None = None
        self.progress: DualProgressDialog | None = None
        self.workers: List[Process] = []
        self.result_queue: Queue | None = None
        self.temp_dir: str | None = None
        self._generated_files: List[str] = []  # new files produced this run

    # -------- External setters ------------------------------------------------

    def set_status_label(self, label):
        self.status_label = label

    def set_selection(self, selection):
        self.selection_indices = selection
        self.logger.info("SplitController", f"Selection indices updated: {self.selection_indices}")

    def set_selected_indices(self, indices):
        self.selected_indices = indices
        self.logger.info("SplitController", f"Selected indices updated: {self.selected_indices}")

    def set_pdf_files(self, files: List[str]):
        self.pdf_files = files
        self.logger.info("SplitController", f"PDF file list updated: {len(files)} files")

    # -------- Helper getters --------------------------------------------------

    def _get_selected_files(self) -> List[str]:
        if not self.selected_indices or not self.pdf_files:
            return []
        return [self.pdf_files[idx] for idx in self.selected_indices if 0 <= idx < len(self.pdf_files)]

    # -------------------------------------------------------------------------
    # Public UI entry
    # -------------------------------------------------------------------------

    def split_pdf_ui(self) -> bool:
        """Kick‑off UI flow – returns *True* if the job started."""
        self.logger.info("SplitController", "Starting PDF split operation")
        freeze_support()

        targets = self._get_selected_files()
        if not targets:
            messagebox.showinfo("Info", "Please select at least 1 PDF to split.")
            return False

        split_dir = self.settings_controller.get_setting("split_directory")
        if not split_dir:
            split_dir = filedialog.askdirectory(title="Select Output Folder for Split PDFs")
            if not split_dir:
                return False
            self.settings_controller.set_setting("split_directory", split_dir)
        os.makedirs(split_dir, exist_ok=True)

        mode, param = self._prompt_split_options()
        if mode is None:
            return False

        self.cancel_event = Event()
        self.progress = DualProgressDialog(self.root, title="Splitting PDFs", message="Analyzing PDFs…")
        orig_cancel = self.progress.cancel
        def _cancel():
            orig_cancel(); self.cancel_event.set()
        self.progress.cancel = _cancel

        Thread(target=self._run_split, args=(targets, split_dir, mode, param), daemon=True).start()
        return True

    # -------------------------------------------------------------------------
    # UI helpers
    # -------------------------------------------------------------------------

    def _prompt_split_options(self):
        dlg = tk.Toplevel(self.root); dlg.title("Split Options"); dlg.transient(self.root); dlg.grab_set()
        frm = ttk.Frame(dlg, padding=20); frm.pack(fill=tk.BOTH, expand=True)
        mode_var = tk.StringVar(value="page"); n_var = tk.StringVar(value="2"); range_var = tk.StringVar(value="1-3,5")
        ttk.Label(frm, text="Choose how to split each PDF:").pack(anchor="w")
        for txt, val in (("Page‑by‑page", "page"), ("Every N pages", "every_n"), ("Specific ranges", "range")):
            ttk.Radiobutton(frm, text=txt, variable=mode_var, value=val).pack(anchor="w")
        every_box = ttk.Frame(frm); ttk.Label(every_box, text="N =").pack(side=tk.LEFT); ttk.Entry(every_box, textvariable=n_var, width=5).pack(side=tk.LEFT)
        rng_box = ttk.Frame(frm); ttk.Label(rng_box, text="Ranges (1‑based)").pack(side=tk.LEFT); ttk.Entry(rng_box, textvariable=range_var, width=25).pack(side=tk.LEFT)
        every_box.pack(anchor="w", pady=4); rng_box.pack(anchor="w", pady=4)
        result = {"mode": None, "param": None}
        def _ok():
            m = mode_var.get()
            if m == "every_n":
                try:
                    n = int(n_var.get()); assert n > 0
                except Exception:
                    messagebox.showerror("Error", "Enter a positive integer for N"); return
                result.update(mode=m, param=n)
            elif m == "range":
                txt = range_var.get().strip();
                if not txt:
                    messagebox.showerror("Error", "Enter at least one range"); return
                result.update(mode=m, param=txt)
            else:
                result.update(mode=m, param=None)
            dlg.destroy()
        ttk.Button(frm, text="OK", command=_ok, width=10).pack(side=tk.RIGHT, pady=(10,0), padx=5)
        ttk.Button(frm, text="Cancel", command=dlg.destroy, width=10).pack(side=tk.RIGHT, pady=(10,0))
        dlg.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dlg.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")
        self.root.wait_window(dlg)
        return result["mode"], result["param"]

    # -------------------------------------------------------------------------
    # Core logic
    # -------------------------------------------------------------------------

    def _run_split(self, files: List[str], out_dir: str, mode: str, param):
        try:
            self.temp_dir = tempfile.mkdtemp(prefix="pdf_split_")
            jobs: List[SplitJob] = []
            jid = 0
            for f in files:
                pages = self._get_page_count(f)
                if pages is None:
                    continue
                for rng in self._generate_ranges(pages, mode, param):
                    basename = os.path.splitext(os.path.basename(f))[0]
                    stamp = datetime.datetime.now().strftime("%Y%m%d")
                    part_idx = len([j for j in jobs if j.input_file == f]) + 1
                    out_name = f"{basename}_part{part_idx}_{stamp}.pdf"
                    out_path = os.path.join(out_dir, out_name)
                    jobs.append(SplitJob(jid, f, out_path, [rng])); jid += 1
            if not jobs:
                self._clean_up(); self.progress.close(); return

            self.result_queue = Queue(); max_workers = max(1, min(cpu_count()-1, 4))
            active: set[int] = set(); idx = 0; total = len(jobs)
            self.progress.update_message("Splitting pages…")

            def _has_space():
                return disk_usage(out_dir).free / (1024**2) > 200

            while idx < total or active:
                if self.cancel_event.is_set():
                    break
                while len(active) < max_workers and idx < total and _has_space():
                    job = jobs[idx]
                    p = Process(target=pdf_split_worker,
                                args=(job.id, job.input_file, job.output_path, job.ranges,
                                      self.result_queue, self.cancel_event,
                                      self.settings_controller.get_setting("log_dir")))
                    p.daemon = True; p.start(); self.workers.append(p); active.add(job.id); idx += 1

                while not self.result_queue.empty():
                    status, jid2, payload = self.result_queue.get()
                    active.discard(jid2)
                    if status == "success":
                        self._generated_files.append(payload)
                        done = len(self._generated_files)
                        self.progress.update_overall_progress((done/total)*100)
                    elif status == "error":
                        self.logger.error("SplitController", f"Job {jid2} failed: {payload}")
                gc.collect(); time.sleep(0.1)

            # Integrate new files into master list if not cancelled
            if not self.cancel_event.is_set():
                self.pdf_files.extend(self._generated_files)
                # dedupe while preserving order
                seen = set(); self.pdf_files = [x for x in self.pdf_files if not (x in seen or seen.add(x))]
                self.logger.info("SplitController", f"Added {len(self._generated_files)} new PDFs to list")
                self.progress.close(); self.root.after(0, lambda: messagebox.showinfo("Success", "PDFs split successfully!"))
            else:
                self.logger.info("SplitController", "Operation cancelled by user"); self.progress.close()
        except Exception as exc:
            self.logger.error("SplitController", f"Unhandled error: {exc}\n{traceback.format_exc()}")
            self.root.after(0, lambda: messagebox.showerror("Error", str(exc)))
        finally:
            self._clean_up()

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _get_page_count(self, path: str) -> int | None:
        try:
            doc = fitz.open(path); n = len(doc); doc.close(); return n
        except Exception as exc:
            self.logger.error("SplitController", f"Failed to read {path}: {exc}"); return None

    def _generate_ranges(self, total: int, mode: str, param) -> List[Tuple[int, int]]:
        ranges: List[Tuple[int, int]]
        if mode == "page":
            ranges = [(i, i) for i in range(total)]
        elif mode == "every_n":
            n = int(param)
            ranges = [(s, min(s+n-1, total-1)) for s in range(0, total, n)]
        else:  # range string
            ranges = []
            pat = re.compile(r"(\d+)(?:-(\d+))?")
            for part in str(param).split(','):
                m = pat.fullmatch(part.strip())
                if not m:
                    continue
                a, b = int(m.group(1)), int(m.group(2) or m.group(1))
                if a > b:
                    a, b = b, a
                a -= 1; b -= 1
                if a < total:
                    ranges.append((a, min(b, total-1)))
            if not ranges:
                ranges = [(0, total-1)]
        return ranges

    # -------------------------------------------------------------------------
    # Public getters  – caller uses these to refresh UI
    # -------------------------------------------------------------------------

    def get_completed_files(self):
        """Return full PDF list after the split operation."""
        return self.pdf_files

    # Alias for clarity
    def get_split_files(self):
        return self.get_completed_files()

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    def _clean_up(self):
        for p in self.workers:
            if p.is_alive():
                p.terminate()
        self.workers.clear()
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as exc:
                self.logger.error("SplitController", f"Temp cleanup failed: {exc}")
        self.temp_dir = None
