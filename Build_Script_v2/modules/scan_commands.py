"""
Scanning Commands Module
Provides commands for scanning and analyzing project files.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from build_system import Command, BuildContext

# Try to import PIL for image analysis
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class ScanFilesCommand(Command):
    """
    Scan project files and collect information about the project structure.
    """
    
    @classmethod
    def get_name(cls) -> str:
        return "scan"
    
    @classmethod
    def get_aliases(cls) -> List[str]:
        return ["s", "scan-files"]
    
    @classmethod
    def get_description(cls) -> str:
        return "Scan project files and analyze project structure"
    
    @classmethod
    def get_flags(cls) -> List[str]:
        return ["--target", "--include", "--exclude", "--recursive"]
    
    @classmethod
    def get_help(cls) -> str:
        return """
Scan Files Command
==================

Usage: scan [options]

Description:
  Scans the project directory and collects information about files,
  including Python files, resource files, and project structure.
  
  Results are stored in the build memory for use by other commands.

Options:
  --target <path>    Specify target directory to scan (default: current directory)
  --include <ext>    Include files with specific extensions (comma-separated)
  --exclude <pattern> Exclude files matching pattern
  --recursive        Scan subdirectories recursively (default: true)

Examples:
  scan                          # Scan current directory
  scan --target ./src           # Scan specific directory
  scan --include .py,.txt       # Only scan .py and .txt files
  scan --exclude __pycache__    # Exclude __pycache__ directories
"""
    
    def execute(self, *args, **kwargs) -> bool:
        """Execute the scan command"""
        try:
            # Parse arguments
            target_dir = self._get_arg('--target', args, kwargs, default='.')
            include_exts = self._get_arg('--include', args, kwargs, default=None)
            exclude_pattern = self._get_arg('--exclude', args, kwargs, default='__pycache__')
            recursive = self._get_flag('--recursive', args, kwargs, default=True)
            
            self.context.log(f"Scanning directory: {target_dir}")
            
            # Convert to Path object
            target_path = Path(target_dir).resolve()
            
            if not target_path.exists():
                self.context.log(f"Error: Directory '{target_dir}' does not exist", "ERROR")
                return False
            
            # Perform scan
            scan_results = self._scan_directory(
                target_path,
                include_exts=include_exts.split(',') if include_exts else None,
                exclude_pattern=exclude_pattern,
                recursive=recursive
            )
            
            # Store results in memory
            self.context.set_memory('last_scan', scan_results)
            self.context.set_memory('scan_timestamp', str(Path.cwd()))
            
            # Display summary
            self._display_summary(scan_results)
            
            self.context.log("Scan completed successfully")
            return True
            
        except Exception as e:
            self.context.log(f"Scan failed: {e}", "ERROR")
            return False
    
    def _scan_directory(self, directory: Path, include_exts=None, 
                       exclude_pattern=None, recursive=True) -> Dict[str, Any]:
        """Scan directory and collect file information"""
        results = {
            'root': str(directory),
            'python_files': [],
            'resource_files': [],
            'directories': [],
            'total_files': 0,
            'total_size': 0
        }
        
        # Determine which files to process
        if recursive:
            files = directory.rglob('*')
        else:
            files = directory.glob('*')
        
        for item in files:
            # Skip excluded patterns
            if exclude_pattern and exclude_pattern in str(item):
                self.context.log_verbose(f"Excluding: {item}")
                continue
            
            if item.is_file():
                file_info = self._analyze_file(item)
                
                # Filter by extension if specified
                if include_exts and file_info['extension'] not in include_exts:
                    continue
                
                # Categorize file
                if file_info['extension'] == '.py':
                    results['python_files'].append(file_info)
                else:
                    results['resource_files'].append(file_info)
                
                results['total_files'] += 1
                results['total_size'] += file_info['size']
                
            elif item.is_dir():
                results['directories'].append(str(item.relative_to(directory)))
        
        return results
    
    def _analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single file and extract information"""
        stat = file_path.stat()
        
        info = {
            'path': str(file_path),
            'name': file_path.name,
            'extension': file_path.suffix,
            'size': stat.st_size,
            'modified': stat.st_mtime,
        }
        
        # For Python files, extract additional info
        if file_path.suffix == '.py':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    info['lines'] = len(content.splitlines())
                    info['has_main'] = '__main__' in content
                    info['imports'] = self._extract_imports(content)
            except Exception as e:
                self.context.log_verbose(f"Could not analyze {file_path}: {e}")
        
        return info
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements from Python file"""
        imports = []
        for line in content.splitlines():
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line)
        return imports
    
    def _display_summary(self, results: Dict[str, Any]):
        """Display scan results summary"""
        print("\n" + "="*50)
        print("SCAN RESULTS SUMMARY")
        print("="*50)
        print(f"Root Directory: {results['root']}")
        print(f"Total Files: {results['total_files']}")
        print(f"Total Size: {self._format_size(results['total_size'])}")
        print(f"Python Files: {len(results['python_files'])}")
        print(f"Resource Files: {len(results['resource_files'])}")
        print(f"Directories: {len(results['directories'])}")
        
        if self.context.verbose:
            print("\nPython Files:")
            for py_file in results['python_files']:
                print(f"  - {py_file['name']} ({py_file.get('lines', '?')} lines)")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def _get_arg(self, flag: str, args: tuple, kwargs: dict, default=None):
        """Get argument value from args or kwargs"""
        # Check kwargs first
        if flag.lstrip('-') in kwargs:
            return kwargs[flag.lstrip('-')]
        
        # Check args
        if flag in args:
            idx = args.index(flag)
            if idx + 1 < len(args):
                return args[idx + 1]
        
        return default
    
    def _get_flag(self, flag: str, args: tuple, kwargs: dict, default=False):
        """Check if flag is present"""
        return flag in args or flag.lstrip('-') in kwargs


class ScanPythonCommand(Command):
    """
    Scan Python files specifically and extract detailed information.
    """
    
    @classmethod
    def get_name(cls) -> str:
        return "scan-python"
    
    @classmethod
    def get_aliases(cls) -> List[str]:
        return ["spy", "scan-py"]
    
    @classmethod
    def get_description(cls) -> str:
        return "Scan Python files and extract dependencies, entry points, etc."
    
    @classmethod
    def get_flags(cls) -> List[str]:
        return ["--target", "--deep", "--stdlib"]
    
    @classmethod
    def get_help(cls) -> str:
        return """
Scan Python Command
===================

Usage: scan-python [options]

Description:
  Scans Python files in the project and extracts detailed information
  including dependencies, entry points, and module structure.

Options:
  --target <path>    Specify target directory (default: current directory)
  --find-main        Find potential entry point files

Examples:
  scan-python                # Scan all Python files
  scan-python --find-main    # Find entry points
"""
    
    def execute(self, *args, **kwargs) -> bool:
        """Execute Python-specific scan"""
        try:
            target_dir = Path(kwargs.get('target', '.')).resolve()
            find_main = '--find-main' in args or kwargs.get('find_main', False)
            
            self.context.log(f"Scanning Python files in: {target_dir}")
            
            python_files = list(target_dir.rglob('*.py'))
            
            if not python_files:
                self.context.log("No Python files found", "WARN")
                return True
            
            results = {
                'python_files': [],
                'entry_points': [],
                'dependencies': set(),
                'total_lines': 0
            }
            
            for py_file in python_files:
                if '__pycache__' in str(py_file):
                    continue
                
                file_info = self._analyze_python_file(py_file)
                results['python_files'].append(file_info)
                results['total_lines'] += file_info.get('lines', 0)
                results['dependencies'].update(file_info.get('dependencies', []))
                
                if find_main and file_info.get('has_main'):
                    results['entry_points'].append(str(py_file))
            
            # Convert set to list for JSON serialization
            results['dependencies'] = sorted(list(results['dependencies']))
            
            # Store in memory
            self.context.set_memory('python_scan', results)
            
            # Display results
            self._display_python_summary(results)
            
            return True
            
        except Exception as e:
            self.context.log(f"Python scan failed: {e}", "ERROR")
            return False
    
    def _analyze_python_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a Python file for dependencies and structure"""
        info = {
            'path': str(file_path),
            'name': file_path.name,
            'dependencies': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
                
                info['lines'] = len(lines)
                info['has_main'] = '__main__' in content
                info['has_class'] = 'class ' in content
                info['has_function'] = 'def ' in content
                
                # Extract dependencies
                for line in lines:
                    line = line.strip()
                    if line.startswith('import '):
                        module = line.replace('import ', '').split()[0].split('.')[0]
                        info['dependencies'].append(module)
                    elif line.startswith('from '):
                        module = line.split()[1].split('.')[0]
                        info['dependencies'].append(module)
        
        except Exception as e:
            self.context.log_verbose(f"Error analyzing {file_path}: {e}")
        
        return info
    
    def _display_python_summary(self, results: Dict[str, Any]):
        """Display Python scan summary"""
        print("\n" + "="*50)
        print("PYTHON SCAN RESULTS")
        print("="*50)
        print(f"Python Files Found: {len(results['python_files'])}")
        print(f"Total Lines of Code: {results['total_lines']}")
        print(f"Unique Dependencies: {len(results['dependencies'])}")
        
        if results['entry_points']:
            print(f"\nEntry Points Found:")
            for entry in results['entry_points']:
                print(f"  - {entry}")
        
        if results['dependencies']:
            print(f"\nDependencies:")
            for dep in sorted(results['dependencies']):
                print(f"  - {dep}")


class ScanIconCommand(Command):
    """Scan for suitable icon and splash images for the build."""
    
    IMAGE_EXTENSIONS = {'.png', '.ico', '.icns', '.jpg', '.jpeg', '.bmp'}
    ICON_SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256), (512, 512)]
    SPLASH_MIN_SIZE = (400, 300)
    
    @classmethod
    def get_name(cls) -> str:
        return "scan-icon"
    
    @classmethod
    def get_aliases(cls) -> List[str]:
        return ["icon", "scan-splash", "splash"]
    
    @classmethod
    def get_description(cls) -> str:
        return "Scan for icon and splash images suitable for builds"
    
    @classmethod
    def get_flags(cls) -> List[str]:
        return ["--type", "--target", "--auto-select"]
    
    @classmethod
    def get_help(cls) -> str:
        return """
Scan Icon/Splash Command
========================

Usage: scan-icon [options]

Description:
  Scans the project for suitable icon and splash images.
  For icons: looks for square images in common sizes (16x16 to 512x512)
  For splash: looks for larger images (minimum 400x300)
  
  If multiple candidates found, prompts user to select.
  Selected image is stored in build configuration.

Options:
  --type <icon|splash>   Scan for specific type (default: both)
  --target <path>        Directory to scan (default: current directory)
  --auto                 Auto-select best match without prompting

Examples:
  scan-icon                     # Scan for both icon and splash
  scan-icon --type icon         # Only scan for icon
  scan-icon --target ./assets   # Scan specific directory
  scan-icon --auto              # Auto-select best match
"""
    
    def execute(self, *args, **kwargs) -> bool:
        """Execute icon/splash scan"""
        if not PIL_AVAILABLE:
            self.context.log("Warning: PIL/Pillow not installed. Image analysis limited.", "WARN")
            self.context.log("Install with: pip install Pillow", "INFO")
        
        try:
            scan_type = kwargs.get('type', 'both')  # 'icon', 'splash', or 'both'
            target_dir = Path(kwargs.get('target', '.')).resolve()
            auto_select = '--auto' in args or kwargs.get('auto', False)
            
            # Parse from args
            if '--type' in args:
                idx = args.index('--type')
                if idx + 1 < len(args):
                    scan_type = args[idx + 1]
            
            if '--target' in args:
                idx = args.index('--target')
                if idx + 1 < len(args):
                    target_dir = Path(args[idx + 1]).resolve()
            
            if not target_dir.exists():
                self.context.log(f"Error: Directory '{target_dir}' does not exist", "ERROR")
                return False
            
            self.context.log(f"Scanning for images in: {target_dir}")
            
            # Find all image files
            image_files = self._find_image_files(target_dir)
            
            if not image_files:
                self.context.log("No image files found", "WARN")
                return True
            
            self.context.log(f"Found {len(image_files)} image file(s)")
            
            # Scan for icons
            if scan_type in ['icon', 'both']:
                icon_candidates = self._find_icon_candidates(image_files)
                if icon_candidates:
                    selected_icon = self._select_image(icon_candidates, 'icon', auto_select)
                    if selected_icon:
                        self.context.set_config('build_icon', str(selected_icon))
                        self.context.log(f"Icon set to: {selected_icon}", "INFO")
                else:
                    self.context.log("No suitable icon candidates found", "WARN")
            
            # Scan for splash
            if scan_type in ['splash', 'both']:
                splash_candidates = self._find_splash_candidates(image_files)
                if splash_candidates:
                    selected_splash = self._select_image(splash_candidates, 'splash', auto_select)
                    if selected_splash:
                        self.context.set_config('build_splash', str(selected_splash))
                        self.context.log(f"Splash set to: {selected_splash}", "INFO")
                else:
                    self.context.log("No suitable splash candidates found", "WARN")
            
            # Save config
            self._save_config()
            
            return True
            
        except Exception as e:
            self.context.log(f"Icon scan failed: {e}", "ERROR")
            import traceback
            if self.context.verbose:
                traceback.print_exc()
            return False
    
    def _find_image_files(self, directory: Path) -> List[Path]:
        """Find all image files in directory"""
        images = []
        for ext in self.IMAGE_EXTENSIONS:
            images.extend(directory.rglob(f'*{ext}'))
        return sorted(images)
    
    def _find_icon_candidates(self, image_files: List[Path]) -> List[Dict[str, Any]]:
        """Find suitable icon candidates"""
        candidates = []
        
        for img_path in image_files:
            # Quick filename heuristics
            name_lower = img_path.name.lower()
            if 'icon' in name_lower or img_path.suffix.lower() in ['.ico', '.icns']:
                score = 10
            else:
                score = 0
            
            if PIL_AVAILABLE:
                try:
                    with Image.open(img_path) as img:
                        width, height = img.size
                        
                        # Icons should be square
                        if width != height:
                            continue
                        
                        # Check if size matches common icon sizes
                        if (width, height) in self.ICON_SIZES:
                            score += 5
                        
                        # Prefer larger icons (can be downscaled)
                        if width >= 256:
                            score += 3
                        elif width >= 128:
                            score += 2
                        elif width >= 64:
                            score += 1
                        
                        candidates.append({
                            'path': img_path,
                            'size': (width, height),
                            'score': score,
                            'format': img.format
                        })
                except Exception as e:
                    self.context.log_verbose(f"Could not analyze {img_path}: {e}")
            else:
                # Without PIL, use filename heuristics only
                if score > 0:
                    candidates.append({
                        'path': img_path,
                        'size': 'unknown',
                        'score': score,
                        'format': img_path.suffix
                    })
        
        # Sort by score (highest first)
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates
    
    def _find_splash_candidates(self, image_files: List[Path]) -> List[Dict[str, Any]]:
        """Find suitable splash screen candidates"""
        candidates = []
        
        for img_path in image_files:
            # Quick filename heuristics
            name_lower = img_path.name.lower()
            if any(term in name_lower for term in ['splash', 'logo', 'banner', 'background']):
                score = 10
            else:
                score = 0
            
            if PIL_AVAILABLE:
                try:
                    with Image.open(img_path) as img:
                        width, height = img.size
                        
                        # Splash should be reasonably large
                        if width < self.SPLASH_MIN_SIZE[0] or height < self.SPLASH_MIN_SIZE[1]:
                            continue
                        
                        # Prefer landscape orientation
                        if width > height:
                            score += 3
                        
                        # Prefer common aspect ratios
                        aspect = width / height
                        if 1.3 <= aspect <= 1.8:  # Roughly 4:3 to 16:9
                            score += 2
                        
                        candidates.append({
                            'path': img_path,
                            'size': (width, height),
                            'score': score,
                            'format': img.format
                        })
                except Exception as e:
                    self.context.log_verbose(f"Could not analyze {img_path}: {e}")
            else:
                # Without PIL, use filename heuristics only
                if score > 0:
                    candidates.append({
                        'path': img_path,
                        'size': 'unknown',
                        'score': score,
                        'format': img_path.suffix
                    })
        
        # Sort by score (highest first)
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates
    
    def _select_image(self, candidates: List[Dict[str, Any]], img_type: str, auto_select: bool) -> Optional[Path]:
        """Select image from candidates (with user prompt if needed)"""
        if not candidates:
            return None
        
        # Auto-select best match
        if auto_select:
            self.context.log(f"Auto-selecting best {img_type}: {candidates[0]['path'].name}")
            return candidates[0]['path']
        
        # Only one candidate, use it
        if len(candidates) == 1:
            self.context.log(f"Found one {img_type} candidate: {candidates[0]['path'].name}")
            return candidates[0]['path']
        
        # Multiple candidates, prompt user
        print(f"\nFound {len(candidates)} {img_type} candidate(s):")
        for i, candidate in enumerate(candidates, 1):
            size_str = f"{candidate['size'][0]}x{candidate['size'][1]}" if candidate['size'] != 'unknown' else 'unknown size'
            print(f"  {i}. {candidate['path'].name} ({size_str}, score: {candidate['score']})")
        print(f"  0. Skip {img_type} selection")
        
        while True:
            try:
                choice = input(f"\nSelect {img_type} [1-{len(candidates)}, 0 to skip]: ").strip()
                choice_num = int(choice)
                
                if choice_num == 0:
                    self.context.log(f"Skipping {img_type} selection")
                    return None
                
                if 1 <= choice_num <= len(candidates):
                    return candidates[choice_num - 1]['path']
                else:
                    print(f"Invalid selection. Enter 1-{len(candidates)} or 0.")
            except (ValueError, KeyboardInterrupt):
                print(f"\nSkipping {img_type} selection")
                return None
    
    def _save_config(self):
        """Save updated configuration to file"""
        try:
            with open(self.context.config_path, 'w') as f:
                json.dump(self.context.config, f, indent=2)
            self.context.log_verbose("Configuration saved")
        except Exception as e:
            self.context.log(f"Warning: Could not save config: {e}", "WARN")
