import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PDFUtility.PDFLogger import Logger
import configparser
import tempfile
from pathlib import Path
import sys
import atexit
import os
from pathlib import Path

def is_frozen():
    return getattr(sys, 'frozen', False)

def get_settings_path():
    if is_frozen():
        # Use user Documents or AppData for settings
        config_dir = os.path.join(str(Path.home()), "Documents", "PDFUtility")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "settings.ini")
    else:
        # Use script directory for settings
        return os.path.join(os.path.dirname(__file__), "settings.ini")

# Default constants
DEFAULT_VERSION = "1.0.0"
DEFAULT_BUILD_DATE = "06/09/2025"
DEFAULT_BUILD_VERSION = "1000"
DEFAULT_BUILD_PLATFORM = "NT"  # Windows
DEFAULT_RATE = "150"
DEFAULT_VOLUME = "1"
DEFAULT_CLEANUP_RUN_COUNT = 3
DEFAULT_CURRENT_CLEANUP_RUN_COUNT = 0
DEFAULT_TEMPORARY_FILE_LOCATION = str(Path.home() / "Documents" / "PDFUtility" / "Temp")
DEFAULT_LOG_DIR = str(Path.home() / "Documents" / "PDFUtility" / "Logs")
DEFAULT_MERGE_DIR = str(Path.home() / "Documents" / "PDFUtility" / "Merged")
DEFAULT_SPLIT_DIR = str(Path.home() / "Documents" / "PDFUtility" / "Split")
DEFAULT_CONVERT_DIR = str(Path.home() / "Documents" / "PDFUtility" / "Converted")
DEFAULT_OUTPUT_DIR = str(Path.home() / "Documents" / "PDFUtility" / "Output")
DEFAULT_INPUT_DIR = str(Path.home() / "Documents" / "PDFUtility" / "AutoConvert")

class SettingsController:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SettingsController, cls).__new__(cls)
        return cls._instance
    def __init__(self, root):
        if getattr(self, '_initialized', False):
            return  # Prevent re-initialization
        self._initialized = True
        self.logger = Logger()
        self.logger.info("SettingsController", "--- INIT ---")
        self.root = root

        # Load and apply settings
        self.sections = {}
        self.settings = self.load_settings()
        self.theme_var = tk.StringVar(value=self.settings.get("theme", "Light"))
        self.apply_theme()

        # Build info defaults
        self.build_version = DEFAULT_BUILD_VERSION
        self.build_date = DEFAULT_BUILD_DATE
        self.system_version = DEFAULT_VERSION
        self.build_platform = DEFAULT_BUILD_PLATFORM

        # Runtime defaults
        self.text_to_speech_rate = DEFAULT_RATE
        self.text_to_speech_volume = DEFAULT_VOLUME
        self.cleanup_run_count = DEFAULT_CLEANUP_RUN_COUNT
        self.current_cleanup_run_count = DEFAULT_CURRENT_CLEANUP_RUN_COUNT
        self.default_settings = defaults = {
            "theme": "Light",
            "output_directory": DEFAULT_OUTPUT_DIR,
            "split_directory": DEFAULT_SPLIT_DIR,
            "merge_directory": DEFAULT_MERGE_DIR,
            "convert_directory": DEFAULT_CONVERT_DIR,
            "build_version": DEFAULT_VERSION,
            "build_date": DEFAULT_BUILD_DATE,
            "system_version": DEFAULT_VERSION,
            "build_platform": DEFAULT_BUILD_PLATFORM,
            "text_to_speech_rate": DEFAULT_RATE,
            "text_to_speech_volume": DEFAULT_VOLUME,
            "cleanup_run_count": DEFAULT_CLEANUP_RUN_COUNT,
            "current_cleanup_run_count": DEFAULT_CURRENT_CLEANUP_RUN_COUNT,
            "temporary_file_location": tempfile.gettempdir(),
            "log_dir": DEFAULT_LOG_DIR,
            "auto_convert_dir": DEFAULT_INPUT_DIR,
        }
        self.settings = self.sections.setdefault("Settings", {}).copy()
        for k, v in self.default_settings.items():
            self.settings.setdefault(k, v)
        # Bind UI variables
        self.theme_var = tk.StringVar(value=self.settings["theme"])
        self.apply_theme()

        # Save on exit
        atexit.register(self.save_all)
    def get_setting(self, name, default=None):
        return self.settings.get(name, default)

    def set_setting(self, name, value):
        self.settings[name] = value
        self.save_runtime_settings()

    def apply_theme(self):
        theme = self.get_setting("theme", "Light")
        theme_name = "flatly" if theme == "Light" else "darkly"
        try:
            self.root.style.theme_use(theme_name)
            self.logger.info("PDFUtility", f"Applied theme: {theme_name}")
        except Exception as e:
            self.logger.warning("PDFUtility", f"Failed to apply theme: {e}")

    def load_settings(self):
        defaults = {
            "theme": "Light",
            "output_directory": DEFAULT_OUTPUT_DIR,
            "split_directory": DEFAULT_SPLIT_DIR,
            "merge_directory": DEFAULT_MERGE_DIR,
            "convert_directory": DEFAULT_CONVERT_DIR,
            "build_version": DEFAULT_VERSION,
            "build_date": DEFAULT_BUILD_DATE,
            "system_version": DEFAULT_VERSION,
            "build_platform": DEFAULT_BUILD_PLATFORM,
            "text_to_speech_rate": DEFAULT_RATE,
            "text_to_speech_volume": DEFAULT_VOLUME,
            "cleanup_run_count": DEFAULT_CLEANUP_RUN_COUNT,
            "current_cleanup_run_count": DEFAULT_CURRENT_CLEANUP_RUN_COUNT,
            "temporary_file_location": tempfile.gettempdir(),
            "log_dir": DEFAULT_LOG_DIR,
            "auto_convert_dir": DEFAULT_INPUT_DIR,
        }
        cfg = configparser.ConfigParser(interpolation=None)
        path = get_settings_path()
        all_settings = {"Settings": defaults.copy()}

        if os.path.exists(path):
            cfg.read(path, encoding="utf-8")
            for sect in cfg.sections():
                # make a plain dict of its items
                self.sections[sect] = dict(cfg[sect])
            if "Settings" in cfg:
                for key, raw in cfg["Settings"].items():
                    if key in defaults:
                        default_val = defaults[key]
                        if isinstance(default_val, bool):
                            defaults[key] = raw.lower() in ("1", "true", "yes", "on")
                        elif isinstance(default_val, int):
                            try:
                                defaults[key] = int(raw)
                            except ValueError:
                                pass
                        else:
                            defaults[key] = raw
            #self.save_runtime_settings()
        self.logger.info("PDFUtility", f"Settings loaded: {defaults}")
        return defaults

    def get_section(self, name: str) -> dict:
        """
        Return a dict of key→value for the given INI section,
        or empty dict if that section was not present.
        """
        return self.sections.get(name, {})

    def save_settings(self, settings_window):
        cfg = configparser.ConfigParser(interpolation=None)
        cfg["Settings"] = {k: str(v) for k, v in {
            "theme": self.theme_var.get(),
            "output_directory": self.output_dir_entry.get(),
            "split_directory": self.split_dir_entry.get(),
            "merge_directory": self.merge_dir_entry.get(),
            "convert_directory": self.convert_dir_entry.get(),
            "build_version": self.build_version,
            "build_date": self.build_date,
            "system_version": self.system_version,
            "build_platform": self.build_platform,
            "text_to_speech_rate": self.text_to_speech_rate,
            "text_to_speech_volume": self.text_to_speech_volume,
            "cleanup_run_count": self.cleanup_run_count,
            "current_cleanup_run_count": self.current_cleanup_run_count,
            "temporary_file_location": self.temp_dir_entry.get(),
            "log_dir": self.log_dir_entry.get(),
            "auto_convert_dir": DEFAULT_INPUT_DIR,
        }.items()}
        self.settings.update(cfg["Settings"])
        for d in [
            self.output_dir_entry.get(),
            self.split_dir_entry.get(),
            self.merge_dir_entry.get(),
            self.convert_dir_entry.get(),
            self.temp_dir_entry.get(),
            self.log_dir_entry.get(),
        ]:
            os.makedirs(d, exist_ok=True)
        with open(get_settings_path(), "w", encoding="utf-8") as f:
            cfg.write(f)
        self.apply_theme()
        settings_window.destroy()

    def save_runtime_settings(self):
        cfg = configparser.ConfigParser(interpolation=None)
        cfg["Settings"] = {k: str(v) for k, v in self.settings.items()}
        with open(get_settings_path(), "w", encoding="utf-8") as f:
            cfg.write(f)
        self.logger.info("PDFUtility", "Runtime settings saved")

    def save_runtime_settings_with_args(self, settings_dict):
        cfg = configparser.ConfigParser(interpolation=None)
        cfg["Settings"] = {k: str(v) for k, v in settings_dict.items()}
        with open(get_settings_path(), "w", encoding="utf-8") as f:
            cfg.write(f)
        self.settings = settings_dict.copy()
        #self.current_cleanup_run_count =
        self.logger.info("PDFUtility", "Runtime settings saved via args")

    def restore_defaults(self, settings_window):
        self.settings = {
            "theme": "Light",
            "output_directory": DEFAULT_OUTPUT_DIR,
            "split_directory": DEFAULT_SPLIT_DIR,
            "merge_directory": DEFAULT_MERGE_DIR,
            "convert_directory": DEFAULT_CONVERT_DIR,
            "build_version": DEFAULT_BUILD_VERSION,
            "build_date": DEFAULT_BUILD_DATE,
            "system_version": DEFAULT_VERSION,
            "build_platform": DEFAULT_BUILD_PLATFORM,
            "text_to_speech_rate": DEFAULT_RATE,
            "text_to_speech_volume": DEFAULT_VOLUME,
            "cleanup_run_count": DEFAULT_CLEANUP_RUN_COUNT,
            "current_cleanup_run_count": DEFAULT_CURRENT_CLEANUP_RUN_COUNT,
            "temporary_file_location": DEFAULT_TEMPORARY_FILE_LOCATION,
            "log_dir": DEFAULT_LOG_DIR,
            "auto_convert_dir": DEFAULT_INPUT_DIR,
        }
        # Update UI
        self.theme_var.set(self.settings["theme"])
        entries = [
            (self.output_dir_entry, "output_directory"),
            (self.split_dir_entry, "split_directory"),
            (self.merge_dir_entry, "merge_directory"),
            (self.convert_dir_entry, "convert_directory"),
            (self.temp_dir_entry, "temporary_file_location"),
            (self.log_dir_entry, "log_dir"),
        ]
        for entry, key in entries:
            entry.delete(0, tk.END)
            entry.insert(0, self.settings[key])
        self.rate_var.set(int(DEFAULT_RATE))
        self.volume_var.set(float(DEFAULT_VOLUME))
        self.cleanup_run_count = DEFAULT_CLEANUP_RUN_COUNT
        self.current_cleanup_run_count = DEFAULT_CURRENT_CLEANUP_RUN_COUNT
        self.save_settings(settings_window)

    def add_section(self, section: str):
        """Ensure a section exists."""
        self.sections.setdefault(section, {})

    def set_section_option(self, section: str, key: str, value):
        """Set or override a single key in a named section."""
        self.add_section(section)
        self.sections[section][key] = str(value)

    def get_section_option(self, section: str, key: str, default=None):
        """Retrieve a single option from a section."""
        return self.sections.get(section, {}).get(key, default)

    def get_section(self, section: str):
        """Return the entire key→value dict for a section."""
        return self.sections.get(section, {})

    def save_all(self):
        """
        Write out every section in self.sections to the INI.
        Call this any time sections or flat settings change.
        """
        cfg = configparser.ConfigParser(interpolation=None)
        for sect, opts in self.sections.items():
            # ensure keys are strings
            cfg[sect] = {k: str(v) for k, v in opts.items()}
        # Overwrite on disk
        with open(get_settings_path(), "w", encoding="utf-8") as f:
            cfg.write(f)
        self.logger.info("Settings", "All settings saved")
        # --- Load from disk ---
    def _load_all_sections(self):
        cfg = configparser.ConfigParser(interpolation=None)
        path = get_settings_path()
        sections = {}
        if os.path.exists(path):
            cfg.read(path, encoding="utf-8")
            for sect in cfg.sections():
                sections[sect] = dict(cfg[sect])
        else:
            # no file yet: start with an empty dict
            pass
        return sections

    def open_settings(self):
        self.logger.info("PDFUtility", "Opening settings dialog")
        self.settings = self.load_settings()

        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("600x750")
        settings_window.transient(self.root)
        settings_window.grab_set()

        container = ttk.Frame(settings_window, padding=12)
        container.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Title
        ttk.Label(scrollable, text="Settings", font=(None, 16, "bold")).pack(anchor="w", pady=(0, 20))

        # Theme
        ttk.Label(scrollable, text="Theme", font=(None, 12, "bold")).pack(anchor="w")
        ttk.Radiobutton(scrollable, text="Light Mode", variable=self.theme_var, value="Light").pack(anchor="w")
        ttk.Radiobutton(scrollable, text="Dark Mode", variable=self.theme_var, value="Dark").pack(anchor="w")

        # Version Info
        ttk.Separator(scrollable, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        ttk.Label(scrollable, text="Version Information", font=(None, 12, "bold")).pack(anchor="w")
        for label in [
            f"PDF Utility Version: {self.build_version}",
            f"System Version: {self.system_version}",
            f"Build Platform: {self.build_platform}",
            f"Build Date: {self.build_date}" ]:
            ttk.Label(scrollable, text=label).pack(anchor="w", pady=2)

        # Directories helper
        def browse(entry):
            d = filedialog.askdirectory(initialdir=entry.get())
            if d: entry.delete(0, tk.END); entry.insert(0, d)

        def dir_entry(parent, text, val):
            frm = ttk.Frame(parent, padding=(0,5))
            frm.pack(fill=tk.X)
            ttk.Label(frm, text=text).pack(anchor="w")
            sub = ttk.Frame(frm)
            sub.pack(fill=tk.X)
            ent = ttk.Entry(sub)
            ent.insert(0, val)
            ent.pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Button(sub, text="…", width=3, command=lambda: browse(ent)).pack(side=tk.LEFT, padx=4)
            return ent

        ttk.Separator(scrollable, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        ttk.Label(scrollable, text="Directories", font=(None, 12, "bold")).pack(anchor="w")
        self.output_dir_entry = dir_entry(scrollable, "Output Directory:", self.settings["output_directory"])
        self.split_dir_entry  = dir_entry(scrollable, "Split Directory:", self.settings["split_directory"])
        self.merge_dir_entry  = dir_entry(scrollable, "Merge Directory:", self.settings["merge_directory"])
        self.convert_dir_entry= dir_entry(scrollable, "Convert Directory:", self.settings["convert_directory"])
        self.temp_dir_entry   = dir_entry(scrollable, "Temp Directory:", self.settings["temporary_file_location"])
        self.log_dir_entry    = dir_entry(scrollable, "Log Directory:", self.settings["log_dir"])

        # Cleanup & Audio
        ttk.Separator(scrollable, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        ttk.Label(scrollable, text="Cleanup & Audio", font=(None, 12, "bold")).pack(anchor="w")
        frm = ttk.Frame(scrollable, padding=(0,5)); frm.pack(fill=tk.X)
        ttk.Label(frm, text="Cleanup Count:").pack(side=tk.LEFT)
        self.cleanup_run_count_var = tk.IntVar(value=self.cleanup_run_count)
        ttk.Spinbox(frm, from_=1, to=100, textvariable=self.cleanup_run_count_var, width=5).pack(side=tk.LEFT, padx=5)
        ttk.Label(frm, text=f"(Current: {self.current_cleanup_run_count})").pack(side=tk.LEFT)
        ttk.Button(frm, text="Purge Logs", command=self.purge_logs_and_reset).pack(side=tk.RIGHT)

        frm2 = ttk.Frame(scrollable, padding=(0,5)); frm2.pack(fill=tk.X)
        ttk.Label(frm2, text="TTS Rate:").pack(side=tk.LEFT)
        self.rate_var = tk.IntVar(value=int(self.text_to_speech_rate))
        ttk.Spinbox(frm2, from_=50, to=300, textvariable=self.rate_var, width=5).pack(side=tk.LEFT, padx=5)
        ttk.Label(frm2, text="Rate").pack(side=tk.LEFT)

        frm3 = ttk.Frame(scrollable, padding=(0,5)); frm3.pack(fill=tk.X)
        ttk.Label(frm3, text="TTS Volume:").pack(side=tk.LEFT)
        self.volume_var = tk.DoubleVar(value=float(self.text_to_speech_volume))
        scale = ttk.Scale(frm3, from_=0, to=1, variable=self.volume_var, orient=tk.HORIZONTAL)
        scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        vol_lbl = ttk.Label(frm3, text=f"{int(self.volume_var.get()*100)}%", width=4)
        vol_lbl.pack(side=tk.LEFT)
        self.volume_var.trace_add("write", lambda *a: vol_lbl.config(text=f"{int(self.volume_var.get()*100)}%"))

        # Buttons
        ttk.Separator(scrollable, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        btn_frm = ttk.Frame(scrollable); btn_frm.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frm, text="Restore Defaults", command=lambda: self.restore_defaults(settings_window)).pack(side=tk.LEFT)
        ttk.Button(btn_frm, text="Cancel", command=settings_window.destroy).pack(side=tk.RIGHT)
        ttk.Button(btn_frm, text="Save", command=lambda: self.save_settings(settings_window)).pack(side=tk.RIGHT, padx=5)

    def purge_logs_and_reset(self):
        self.logger.delete_logs()
        self.logger.cleanup()
        self.logger = Logger()
        self.current_cleanup_run_count = 0
        self.save_runtime_settings()
