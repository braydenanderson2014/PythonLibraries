from __future__ import annotations

import shutil
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class DistributionStrategy(Enum):
    """File distribution strategies."""
    ROUND_ROBIN = "round_robin"  # Cycle through outputs
    LEAST_USED = "least_used"  # Always use lowest usage output
    RANDOM = "random"  # Random output selection
    EQUAL_SIZE = "equal_size"  # Balance total size across outputs


@dataclass
class OutputFolder:
    """Output folder configuration and state."""
    path: Path
    max_size_gb: Optional[float] = None  # None = unlimited
    enabled: bool = True
    
    # State tracking
    current_size_bytes: float = 0.0
    total_files: int = 0
    last_used_time: float = field(default_factory=time.time)
    
    def get_available_space_bytes(self) -> float:
        """Get available space in bytes."""
        if self.max_size_gb is None:
            return float('inf')
        max_bytes = self.max_size_gb * 1024 * 1024 * 1024
        return max_bytes - self.current_size_bytes
    
    def can_fit_file(self, file_size_bytes: float) -> bool:
        """Check if file can fit in this output."""
        if not self.enabled:
            return False
        return file_size_bytes <= self.get_available_space_bytes()


@dataclass
class ScannedFile:
    """File scanned from input directory."""
    path: Path
    size_bytes: int
    extension: str
    scanned_time: float = field(default_factory=time.time)
    processed: bool = False
    assigned_output: Optional[Path] = None


class FileScanner:
    """Scans input directories for media files."""
    
    def __init__(
        self,
        input_paths: List[Path] | str,
        extensions: Optional[List[str]] = None,
        poll_interval: int = 5,
    ) -> None:
        """
        Initialize file scanner.
        
        :param input_paths: Single path or list of paths to scan
        :param extensions: File extensions to scan for (e.g., ['.mkv', '.mp4'])
        :param poll_interval: Seconds between scans
        """
        if isinstance(input_paths, (str, Path)):
            self.input_paths = [Path(input_paths)]
        else:
            self.input_paths = [Path(p) for p in input_paths]
        
        self.extensions = set(e.lower() if e.startswith('.') else f'.{e}' for e in (extensions or []))
        self.poll_interval = poll_interval
        self.scanning = False
        self.scanned_files: Dict[Path, ScannedFile] = {}
        self._lock = threading.RLock()
    
    def scan_once(self) -> List[ScannedFile]:
        """Perform single scan and return new files."""
        new_files = []
        
        for input_path in self.input_paths:
            if not input_path.exists():
                continue
            
            for file_path in input_path.rglob("*"):
                if not file_path.is_file():
                    continue
                
                # Skip if extension filter doesn't match
                if self.extensions and file_path.suffix.lower() not in self.extensions:
                    continue
                
                # Skip if already found
                if file_path in self.scanned_files:
                    continue
                
                try:
                    size = file_path.stat().st_size
                    scanned_file = ScannedFile(
                        path=file_path,
                        size_bytes=size,
                        extension=file_path.suffix.lower(),
                    )
                    
                    with self._lock:
                        self.scanned_files[file_path] = scanned_file
                    
                    new_files.append(scanned_file)
                except OSError:
                    # File might have been deleted or is inaccessible
                    continue
        
        return new_files
    
    def get_unprocessed_files(self) -> List[ScannedFile]:
        """Get all files that haven't been processed."""
        with self._lock:
            return [f for f in self.scanned_files.values() if not f.processed]
    
    def mark_processed(self, file_path: Path) -> None:
        """Mark file as processed."""
        with self._lock:
            if file_path in self.scanned_files:
                self.scanned_files[file_path].processed = True
    
    def start_monitoring(self, callback: Optional[Callable[[List[ScannedFile]], None]] = None) -> threading.Thread:
        """Start background monitoring thread."""
        def monitor_loop():
            while self.scanning:
                new_files = self.scan_once()
                if new_files and callback:
                    callback(new_files)
                time.sleep(self.poll_interval)
        
        self.scanning = True
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        return thread
    
    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        self.scanning = False


class FileDistributor:
    """Distributes files to multiple output folders with load balancing."""
    
    def __init__(
        self,
        output_folders: List[OutputFolder] | Dict[str, OutputFolder],
        strategy: DistributionStrategy = DistributionStrategy.LEAST_USED,
        copy_mode: bool = True,  # True = copy, False = move
    ) -> None:
        """
        Initialize file distributor.
        
        :param output_folders: List of OutputFolder configs or dict mapping names to configs
        :param strategy: Load balancing strategy
        :param copy_mode: If True, copy files; if False, move files
        """
        if isinstance(output_folders, dict):
            self.outputs = list(output_folders.values())
        else:
            self.outputs = list(output_folders)
        
        self.strategy = strategy
        self.copy_mode = copy_mode
        self._lock = threading.RLock()
        
        # Create output directories
        for output in self.outputs:
            output.path.mkdir(parents=True, exist_ok=True)
    
    def _get_next_output(self, file_size_bytes: int) -> Optional[OutputFolder]:
        """Select next output folder based on strategy."""
        # Filter to only enabled outputs that can fit the file
        suitable = [o for o in self.outputs if o.can_fit_file(file_size_bytes)]
        
        if not suitable:
            return None
        
        if self.strategy == DistributionStrategy.ROUND_ROBIN:
            # Simple rotation
            return min(suitable, key=lambda o: o.last_used_time)
        
        elif self.strategy == DistributionStrategy.LEAST_USED:
            # Least used by count
            return min(suitable, key=lambda o: o.total_files)
        
        elif self.strategy == DistributionStrategy.EQUAL_SIZE:
            # Lowest current size
            return min(suitable, key=lambda o: o.current_size_bytes)
        
        elif self.strategy == DistributionStrategy.RANDOM:
            import random
            return random.choice(suitable)
        
        return suitable[0]
    
    def distribute_file(self, file_path: Path, new_name: Optional[str] = None) -> Optional[Path]:
        """
        Distribute single file to appropriate output.
        
        :param file_path: Path to file to distribute
        :param new_name: Optional new filename (default: keep original)
        :return: Destination path or None if failed
        """
        if not file_path.exists():
            return None
        
        file_size = file_path.stat().st_size
        output = self._get_next_output(file_size)
        
        if not output:
            return None
        
        # Use original name or provided name
        dest_name = new_name or file_path.name
        dest_path = output.path / dest_name
        
        # Avoid overwriting
        if dest_path.exists():
            base_name = dest_path.stem
            ext = dest_path.suffix
            counter = 1
            while dest_path.exists():
                dest_path = output.path / f"{base_name}_{counter}{ext}"
                counter += 1
        
        try:
            if self.copy_mode:
                shutil.copy2(file_path, dest_path)
            else:
                shutil.move(str(file_path), str(dest_path))
            
            # Update output statistics
            with self._lock:
                output.current_size_bytes += file_size
                output.total_files += 1
                output.last_used_time = time.time()
            
            return dest_path
        except IOError:
            return None
    
    def distribute_batch(
        self,
        files: List[ScannedFile],
        callback: Optional[Callable[[ScannedFile, Optional[Path]], None]] = None,
    ) -> Dict[Path, Optional[Path]]:
        """
        Distribute multiple files.
        
        :param files: List of ScannedFile objects
        :param callback: Callback(file, destination) for each distributed file
        :return: Dict mapping source paths to destination paths
        """
        results = {}
        
        for scanned_file in files:
            dest = self.distribute_file(scanned_file.path)
            results[scanned_file.path] = dest
            
            if callback:
                callback(scanned_file, dest)
            
            if dest:
                scanned_file.assigned_output = dest
        
        return results
    
    def get_load_status(self) -> Dict[str, Any]:
        """Get current load status of all outputs."""
        status = {}
        
        for i, output in enumerate(self.outputs):
            status[f"output_{i}"] = {
                "path": str(output.path),
                "enabled": output.enabled,
                "current_size_gb": output.current_size_bytes / (1024 * 1024 * 1024),
                "max_size_gb": output.max_size_gb,
                "available_space_gb": output.get_available_space_bytes() / (1024 * 1024 * 1024),
                "total_files": output.total_files,
            }
        
        return status
    
    def rebalance_if_needed(self) -> bool:
        """
        Check if rebalancing is recommended.
        Returns True if any output is over capacity or severely imbalanced.
        """
        # Check if any output is over capacity
        for output in self.outputs:
            if output.max_size_gb and output.get_available_space_bytes() < 0:
                return True
        
        # Check for severe imbalance (one output has 2x the load)
        if len(self.outputs) > 1:
            min_size = min(o.current_size_bytes for o in self.outputs)
            max_size = max(o.current_size_bytes for o in self.outputs)
            if max_size > min_size * 2:
                return True
        
        return False


class FileDistributionPipeline:
    """Combined scanner and distributor pipeline."""
    
    def __init__(
        self,
        input_paths: List[Path] | str,
        output_folders: List[OutputFolder] | Dict[str, OutputFolder],
        extensions: Optional[List[str]] = None,
        scan_interval: int = 5,
        strategy: DistributionStrategy = DistributionStrategy.LEAST_USED,
        copy_mode: bool = True,
    ) -> None:
        """Initialize combined pipeline."""
        self.scanner = FileScanner(input_paths, extensions, scan_interval)
        self.distributor = FileDistributor(output_folders, strategy, copy_mode)
        self.running = False
        self._thread: Optional[threading.Thread] = None
    
    def start(self, callback: Optional[Callable[[ScannedFile, Optional[Path]], None]] = None) -> None:
        """Start pipeline."""
        self.running = True
        
        def process_loop():
            while self.running:
                new_files = self.scanner.scan_once()
                
                if new_files:
                    self.distributor.distribute_batch(new_files, callback)
                    
                    for new_file in new_files:
                        self.scanner.mark_processed(new_file.path)
                
                time.sleep(self.scanner.poll_interval)
        
        self._thread = threading.Thread(target=process_loop, daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        """Stop pipeline."""
        self.running = False
        self.scanner.stop_monitoring()
        if self._thread:
            self._thread.join(timeout=5)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        return {
            "scanned_files": len(self.scanner.scanned_files),
            "processed_files": sum(1 for f in self.scanner.scanned_files.values() if f.processed),
            "distribution_load": self.distributor.get_load_status(),
            "rebalance_needed": self.distributor.rebalance_if_needed(),
        }
