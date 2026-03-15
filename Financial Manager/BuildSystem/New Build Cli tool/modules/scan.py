"""
Project Scanning Module for BuildCLI

Provides intelligent project file discovery and mapping capabilities for build configurations.
Scans projects to find icons, splash screens, main files, documentation, and other assets.
Creates mapping configurations for automated build setup.
"""

# Module information for BuildCLI
MODULE_INFO = {
    'name': 'scan',
    'version': '1.0.0',
    'description': 'Intelligent project file discovery and mapping system for automated build configuration',
    'author': 'BuildCLI Team',
    'commands': ['scan-project', 'scan-apply', 'scan-mappings', 'scan-cache']
}

import os
import re
import json
import asyncio
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
import mimetypes
from datetime import datetime

from utils.logger import Logger

logger = Logger().logger

@dataclass
class FileMapping:
    """Represents a discovered file and its mapped purpose."""
    file_path: str
    file_type: str  # icon, splash, main, docs, config, data, etc.
    confidence: float  # 0.0 to 1.0
    size: int
    modified: str
    description: str

@dataclass 
class ProjectScan:
    """Results of a project scan."""
    project_path: str
    scan_date: str
    python_files: List[FileMapping]
    icon_files: List[FileMapping]
    splash_files: List[FileMapping]
    documentation_files: List[FileMapping]
    config_files: List[FileMapping]
    data_files: List[FileMapping]
    asset_files: List[FileMapping]
    requirements_files: List[FileMapping]
    readme_files: List[FileMapping]
    license_files: List[FileMapping]
    main_candidates: List[FileMapping]
    total_files: int
    project_type: str  # gui, cli, library, web, etc.
    suggested_mappings: Dict[str, str]

class ProjectScanner:
    """Scans projects for relevant files and creates intelligent mappings."""
    
    # File pattern definitions
    ICON_PATTERNS = [
        r'.*\.ico$',
        r'.*icon.*\.(png|jpg|jpeg|bmp|gif)$',
        r'.*logo.*\.(png|jpg|jpeg|bmp|gif)$',
        r'.*app.*\.(ico|png|jpg|jpeg|bmp)$',
    ]
    
    SPLASH_PATTERNS = [
        r'.*splash.*\.(png|jpg|jpeg|bmp|gif)$',
        r'.*loading.*\.(png|jpg|jpeg|bmp|gif)$',
        r'.*startup.*\.(png|jpg|jpeg|bmp|gif)$',
        r'.*banner.*\.(png|jpg|jpeg|bmp|gif)$',
    ]
    
    MAIN_FILE_PATTERNS = [
        r'^main\.py$',
        r'^app\.py$',
        r'^run\.py$',
        r'^start\.py$',
        r'.*__main__\.py$',
        r'^cli\.py$',
        r'^gui\.py$',
        r'^server\.py$',
    ]
    
    MAIN_FILE_NAMES = [
        'main.py', 'app.py', 'run.py', 'start.py', '__main__.py',
        'cli.py', 'gui.py', 'server.py', 'manage.py', 'wsgi.py'
    ]
    
    DOC_PATTERNS = [
        r'^README.*\.(md|txt|rst)$',
        r'^CHANGELOG.*\.(md|txt|rst)$',
        r'^HISTORY.*\.(md|txt|rst)$',
        r'.*\.md$',
        r'.*\.rst$',
        r'^docs/.*',
        r'^documentation/.*',
        r'^manual.*\.(pdf|doc|docx)$',
    ]
    
    CONFIG_PATTERNS = [
        r'.*config.*\.(json|yaml|yml|ini|toml|cfg)$',
        r'.*settings.*\.(json|yaml|yml|ini|toml|py)$',
        r'^setup\.py$',
        r'^setup\.cfg$',
        r'^pyproject\.toml$',
        r'^\.env.*$',
        r'.*\.conf$',
    ]
    
    REQUIREMENTS_PATTERNS = [
        r'^requirements.*\.txt$',
        r'^Pipfile$',
        r'^poetry\.lock$',
        r'^environment\.yml$',
    ]
    
    LICENSE_PATTERNS = [
        r'^LICENSE.*',
        r'^COPYING.*',
        r'^COPYRIGHT.*',
    ]
    
    DATA_EXTENSIONS = {
        '.json', '.xml', '.csv', '.xlsx', '.xls', '.db', '.sqlite',
        '.sql', '.yaml', '.yml', '.ini', '.cfg', '.conf'
    }
    
    IMAGE_EXTENSIONS = {
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.svg', '.webp'
    }
    
    AUDIO_EXTENSIONS = {
        '.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a'
    }
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.scan_cache_dir = Path.home() / '.buildcli' / 'scan_cache'
        self.scan_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # File type mappings for build configuration
        self.file_type_mappings = {
            'icon': '[icon]',
            'splash': '[splash]',
            'main': '[main]',
            'docs': '[docs]',
            'config': '[config]', 
            'data': '[data]',
            'assets': '[assets]',
            'requirements': '[requirements]',
            'readme': '[readme]',
            'license': '[license]'
        }
    
    def get_cache_file(self, project_path: str) -> Path:
        """Get the cache file path for a project scan."""
        project_name = Path(project_path).name
        return self.scan_cache_dir / f"{project_name}_scan.json"
    
    async def scan_project(self, project_path: str, use_cache: bool = True) -> ProjectScan:
        """Scan a project directory for relevant files."""
        project_path = os.path.abspath(project_path)
        
        if not os.path.exists(project_path):
            raise FileNotFoundError(f"Project path not found: {project_path}")
        
        # Check cache
        cache_file = self.get_cache_file(project_path)
        if use_cache and cache_file.exists():
            try:
                cached_scan = self.load_scan_from_cache(cache_file)
                if cached_scan and self._is_cache_valid(cached_scan, project_path):
                    logger.info(f"Using cached scan for {project_path}")
                    return cached_scan
            except Exception as e:
                logger.warning(f"Failed to load cached scan: {e}")
        
        logger.info(f"Scanning project: {project_path}")
        
        scan_result = ProjectScan(
            project_path=project_path,
            scan_date=datetime.now().isoformat(),
            python_files=[],
            icon_files=[],
            splash_files=[],
            documentation_files=[],
            config_files=[],
            data_files=[],
            asset_files=[],
            requirements_files=[],
            readme_files=[],
            license_files=[],
            main_candidates=[],
            total_files=0,
            project_type='unknown',
            suggested_mappings={}
        )
        
        # Scan directory recursively
        for root, dirs, files in os.walk(project_path):
            # Skip common build/cache directories
            dirs[:] = [d for d in dirs if not self._should_skip_directory(d)]
            
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, project_path)
                
                if self._should_skip_file(file):
                    continue
                
                scan_result.total_files += 1
                file_mapping = self._analyze_file(file_path, relative_path)
                
                if file_mapping:
                    self._categorize_file(scan_result, file_mapping)
        
        # Analyze project type and create suggestions
        scan_result.project_type = self._determine_project_type(scan_result)
        scan_result.suggested_mappings = self._create_suggested_mappings(scan_result)
        
        # Cache the results
        self.save_scan_to_cache(scan_result, cache_file)
        
        logger.info(f"Scan completed: {scan_result.total_files} files analyzed")
        return scan_result
    
    def _analyze_file(self, file_path: str, relative_path: str) -> Optional[FileMapping]:
        """Analyze a single file and determine its type and confidence."""
        try:
            file_stat = os.stat(file_path)
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1].lower()
            
            # Determine file type and confidence
            file_type, confidence = self._classify_file(file_name, relative_path, file_ext)
            
            if file_type == 'unknown' and confidence < 0.1:
                return None
            
            return FileMapping(
                file_path=relative_path,
                file_type=file_type,
                confidence=confidence,
                size=file_stat.st_size,
                modified=datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                description=self._get_file_description(file_type, file_name, file_ext)
            )
            
        except Exception as e:
            logger.debug(f"Error analyzing file {file_path}: {e}")
            return None
    
    def _classify_file(self, file_name: str, relative_path: str, file_ext: str) -> Tuple[str, float]:
        """Classify a file and return type with confidence score."""
        file_name_lower = file_name.lower()
        relative_path_lower = relative_path.lower()
        
        # Check for Python files
        if file_ext == '.py':
            # Check if it's a main file candidate
            for pattern in self.MAIN_FILE_PATTERNS:
                if re.match(pattern, file_name_lower, re.IGNORECASE):
                    return 'main', 0.9
            
            # Check if it contains main execution patterns
            if self._contains_main_patterns(relative_path):
                return 'main', 0.7
            
            return 'python', 0.8
        
        # Check for icon files
        for pattern in self.ICON_PATTERNS:
            if re.match(pattern, file_name_lower, re.IGNORECASE):
                confidence = 0.9 if file_ext == '.ico' else 0.7
                return 'icon', confidence
        
        # Check for splash screens
        for pattern in self.SPLASH_PATTERNS:
            if re.match(pattern, file_name_lower, re.IGNORECASE):
                return 'splash', 0.8
        
        # Check for documentation
        for pattern in self.DOC_PATTERNS:
            if re.match(pattern, file_name_lower, re.IGNORECASE) or re.match(pattern, relative_path_lower, re.IGNORECASE):
                confidence = 0.9 if file_name_lower.startswith('readme') else 0.7
                return 'docs', confidence
        
        # Check for config files
        for pattern in self.CONFIG_PATTERNS:
            if re.match(pattern, file_name_lower, re.IGNORECASE):
                return 'config', 0.8
        
        # Check for requirements files
        for pattern in self.REQUIREMENTS_PATTERNS:
            if re.match(pattern, file_name_lower, re.IGNORECASE):
                return 'requirements', 0.9
        
        # Check for license files
        for pattern in self.LICENSE_PATTERNS:
            if re.match(pattern, file_name_lower, re.IGNORECASE):
                return 'license', 0.9
        
        # Check for data files
        if file_ext in self.DATA_EXTENSIONS:
            return 'data', 0.6
        
        # Check for image assets
        if file_ext in self.IMAGE_EXTENSIONS:
            return 'assets', 0.5
        
        # Check for audio assets
        if file_ext in self.AUDIO_EXTENSIONS:
            return 'assets', 0.5
        
        return 'unknown', 0.1
    
    def _contains_main_patterns(self, file_path: str) -> bool:
        """Check if a Python file contains main execution patterns."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Look for common main patterns
            main_patterns = [
                r'if\s+__name__\s*==\s*["\']__main__["\']',
                r'def\s+main\s*\(',
                r'app\.run\s*\(',
                r'sys\.exit\s*\(',
                r'argparse\.ArgumentParser',
                r'click\.',
            ]
            
            for pattern in main_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True
            
            return False
        except Exception:
            return False
    
    def _categorize_file(self, scan_result: ProjectScan, file_mapping: FileMapping):
        """Categorize a file mapping into the appropriate list."""
        file_type = file_mapping.file_type
        
        if file_type == 'python' or file_type == 'main':
            scan_result.python_files.append(file_mapping)
            if file_type == 'main':
                scan_result.main_candidates.append(file_mapping)
        elif file_type == 'icon':
            scan_result.icon_files.append(file_mapping)
        elif file_type == 'splash':
            scan_result.splash_files.append(file_mapping)
        elif file_type == 'docs':
            scan_result.documentation_files.append(file_mapping)
            if 'readme' in file_mapping.file_path.lower():
                scan_result.readme_files.append(file_mapping)
        elif file_type == 'config':
            scan_result.config_files.append(file_mapping)
        elif file_type == 'data':
            scan_result.data_files.append(file_mapping)
        elif file_type == 'assets':
            scan_result.asset_files.append(file_mapping)
        elif file_type == 'requirements':
            scan_result.requirements_files.append(file_mapping)
        elif file_type == 'license':
            scan_result.license_files.append(file_mapping)
    
    def _determine_project_type(self, scan_result: ProjectScan) -> str:
        """Determine the type of project based on scan results."""
        # Check for common frameworks and patterns
        python_files = [f.file_path.lower() for f in scan_result.python_files]
        all_files = [f.file_path.lower() for f in 
                    scan_result.python_files + scan_result.config_files + scan_result.data_files]
        
        # Web frameworks
        if any('django' in f or 'manage.py' in f for f in python_files):
            return 'django_web'
        if any('flask' in f or 'app.py' in f for f in python_files):
            return 'flask_web'
        if any('fastapi' in f or 'uvicorn' in f for f in python_files):
            return 'fastapi_web'
        
        # GUI frameworks
        if any('tkinter' in f or 'gui' in f for f in python_files):
            return 'gui_tkinter'
        if any('pyqt' in f or 'pyside' in f for f in python_files):
            return 'gui_qt'
        if any('kivy' in f for f in python_files):
            return 'gui_kivy'
        
        # CLI applications
        if any('cli' in f or 'command' in f for f in python_files):
            return 'cli'
        
        # Data science
        if any('jupyter' in f or '.ipynb' in f for f in all_files):
            return 'data_science'
        
        # Library/package
        if any('setup.py' in f or '__init__.py' in f for f in python_files):
            return 'library'
        
        # Default based on main candidates
        if scan_result.main_candidates:
            return 'application'
        
        return 'script'
    
    def _create_suggested_mappings(self, scan_result: ProjectScan) -> Dict[str, str]:
        """Create suggested file mappings for build configuration."""
        mappings = {}
        
        # Main file suggestion
        if scan_result.main_candidates:
            best_main = max(scan_result.main_candidates, key=lambda x: x.confidence)
            mappings['main_file'] = best_main.file_path
        elif scan_result.python_files:
            # Fallback to first Python file
            mappings['main_file'] = scan_result.python_files[0].file_path
        
        # Icon suggestion
        if scan_result.icon_files:
            best_icon = max(scan_result.icon_files, key=lambda x: x.confidence)
            mappings['icon'] = best_icon.file_path
        
        # Documentation
        if scan_result.readme_files:
            best_readme = max(scan_result.readme_files, key=lambda x: x.confidence)
            mappings['readme'] = best_readme.file_path
        
        # Requirements
        if scan_result.requirements_files:
            best_req = max(scan_result.requirements_files, key=lambda x: x.confidence)
            mappings['requirements'] = best_req.file_path
        
        # Data files (select top 3 by confidence)
        if scan_result.data_files:
            sorted_data = sorted(scan_result.data_files, key=lambda x: x.confidence, reverse=True)
            mappings['data_files'] = [f.file_path for f in sorted_data[:3]]
        
        # Asset files (select top 5 by confidence)
        if scan_result.asset_files:
            sorted_assets = sorted(scan_result.asset_files, key=lambda x: x.confidence, reverse=True)
            mappings['asset_files'] = [f.file_path for f in sorted_assets[:5]]
        
        return mappings
    
    def _should_skip_directory(self, dir_name: str) -> bool:
        """Check if a directory should be skipped during scanning."""
        skip_dirs = {
            '__pycache__', '.git', '.svn', '.hg', '.bzr',
            'node_modules', '.venv', 'venv', 'env',
            '.pytest_cache', '.mypy_cache', '.tox',
            'build', 'dist', '.egg-info', '.eggs',
            '.coverage', 'htmlcov', '.cache'
        }
        return dir_name in skip_dirs or dir_name.startswith('.')
    
    def _should_skip_file(self, file_name: str) -> bool:
        """Check if a file should be skipped during scanning."""
        skip_extensions = {'.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib'}
        skip_files = {'.gitignore', '.gitattributes', '.DS_Store', 'Thumbs.db'}
        
        return (os.path.splitext(file_name)[1] in skip_extensions or
                file_name in skip_files or
                file_name.startswith('.'))
    
    def _get_file_description(self, file_type: str, file_name: str, file_ext: str) -> str:
        """Get a human-readable description for a file."""
        descriptions = {
            'main': f'Main executable Python file ({file_name})',
            'python': f'Python source file ({file_name})',
            'icon': f'Application icon ({file_ext.upper()} format)',
            'splash': f'Splash screen image ({file_ext.upper()} format)',
            'docs': f'Documentation file ({file_name})',
            'config': f'Configuration file ({file_ext.upper()} format)',
            'data': f'Data file ({file_ext.upper()} format)',
            'assets': f'Asset file ({file_ext.upper()} format)',
            'requirements': f'Dependencies file ({file_name})',
            'license': f'License file ({file_name})',
        }
        return descriptions.get(file_type, f'File ({file_name})')
    
    def _is_cache_valid(self, cached_scan: ProjectScan, project_path: str) -> bool:
        """Check if a cached scan is still valid."""
        try:
            # Simple validation - check if project directory was modified recently
            cache_date = datetime.fromisoformat(cached_scan.scan_date)
            project_mtime = datetime.fromtimestamp(os.path.getmtime(project_path))
            
            # Cache is valid if project wasn't modified after scan
            return project_mtime <= cache_date
        except Exception:
            return False
    
    def save_scan_to_cache(self, scan_result: ProjectScan, cache_file: Path):
        """Save scan results to cache."""
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(scan_result), f, indent=2, default=str)
            logger.debug(f"Scan results cached to {cache_file}")
        except Exception as e:
            logger.warning(f"Failed to cache scan results: {e}")
    
    def load_scan_from_cache(self, cache_file: Path) -> Optional[ProjectScan]:
        """Load scan results from cache."""
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert dictionaries back to FileMapping objects
            for field_name in ['python_files', 'icon_files', 'splash_files', 'documentation_files',
                             'config_files', 'data_files', 'asset_files', 'requirements_files',
                             'readme_files', 'license_files', 'main_candidates']:
                if field_name in data:
                    data[field_name] = [FileMapping(**item) for item in data[field_name]]
            
            return ProjectScan(**data)
        except Exception as e:
            logger.debug(f"Failed to load cached scan: {e}")
            return None
    
    async def apply_scan_to_build_config(self, scan_result: ProjectScan, build_config_name: str) -> bool:
        """Apply scan results to a build configuration."""
        from modules.build import build_manager
        
        try:
            # Set active config first to load it properly
            config = build_manager.set_active_config(build_config_name)
            if not config:
                logger.error(f"Build configuration '{build_config_name}' not found")
                return False
            
            # Apply suggested mappings
            mappings = scan_result.suggested_mappings
            
            if 'main_file' in mappings:
                config.source_file = mappings['main_file']
                logger.info(f"Set main file: {mappings['main_file']}")
            
            if 'icon' in mappings:
                icon_path = os.path.join(scan_result.project_path, mappings['icon'])
                if os.path.exists(icon_path):
                    config.icon = icon_path
                    logger.info(f"Set icon: {mappings['icon']}")
            
            if 'data_files' in mappings:
                if config.data_files is None:
                    config.data_files = []
                for data_file in mappings['data_files']:
                    data_tuple = (os.path.join(scan_result.project_path, data_file), '.')
                    if data_tuple not in config.data_files:
                        config.data_files.append(data_tuple)
                logger.info(f"Added {len(mappings['data_files'])} data files")
            
            if 'asset_files' in mappings:
                if config.data_files is None:
                    config.data_files = []
                for asset_file in mappings['asset_files']:
                    asset_tuple = (os.path.join(scan_result.project_path, asset_file), 'assets')
                    if asset_tuple not in config.data_files:
                        config.data_files.append(asset_tuple)
                logger.info(f"Added {len(mappings['asset_files'])} asset files")
            
            # Set project type specific options
            if scan_result.project_type.startswith('gui'):
                config.console = False
                logger.info("Disabled console for GUI application")
            elif scan_result.project_type == 'cli':
                config.console = True
                logger.info("Enabled console for CLI application")
            
            # Save updated configuration
            build_manager.save_config(config)
            logger.info(f"Applied scan results to build configuration '{build_config_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply scan results to build config: {e}")
            return False


# Global scanner instance
project_scanner = ProjectScanner()


async def scan_project_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Scan a project directory for relevant files."""
    project_path = args[0] if len(args) > 0 else '.'
    use_cache = not modifiers.get('no_cache', False)
    
    try:
        scan_result = await project_scanner.scan_project(project_path, use_cache)
        
        print(f"Project Scan Results: {scan_result.project_path}")
        print(f"Project Type: {scan_result.project_type}")
        print(f"Total Files: {scan_result.total_files}")
        print(f"Scan Date: {scan_result.scan_date}")
        print()
        
        # Display file categories
        categories = [
            ('Main Candidates', scan_result.main_candidates),
            ('Python Files', scan_result.python_files),
            ('Icons', scan_result.icon_files),
            ('Splash Screens', scan_result.splash_files),
            ('Documentation', scan_result.documentation_files),
            ('Configuration', scan_result.config_files),
            ('Requirements', scan_result.requirements_files),
            ('Data Files', scan_result.data_files),
            ('Assets', scan_result.asset_files),
            ('License Files', scan_result.license_files),
        ]
        
        for category_name, files in categories:
            if files:
                print(f"{category_name}: ({len(files)})")
                for file_mapping in sorted(files, key=lambda x: x.confidence, reverse=True)[:5]:
                    confidence = f"{file_mapping.confidence:.1%}"
                    size = f"{file_mapping.size:,} bytes"
                    print(f"  {file_mapping.file_path} ({confidence}, {size})")
                if len(files) > 5:
                    print(f"  ... and {len(files) - 5} more")
                print()
        
        # Display suggested mappings
        if scan_result.suggested_mappings:
            print("Suggested Mappings:")
            for key, value in scan_result.suggested_mappings.items():
                if isinstance(value, list):
                    print(f"  {key}: {len(value)} files")
                    for item in value[:3]:
                        print(f"    - {item}")
                    if len(value) > 3:
                        print(f"    ... and {len(value) - 3} more")
                else:
                    print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to scan project: {e}")
        return False


async def scan_apply_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Apply scan results to a build configuration."""
    if len(args) < 2:
        logger.error("Usage: scan-apply <project_path> <build_config_name>")
        return False
    
    project_path = args[0]
    build_config_name = args[1]
    
    try:
        # Scan project
        scan_result = await project_scanner.scan_project(project_path)
        
        # Apply to build configuration
        success = await project_scanner.apply_scan_to_build_config(scan_result, build_config_name)
        
        if success:
            print(f"Successfully applied scan results to '{build_config_name}'")
            print(f"Updated configuration with {len(scan_result.suggested_mappings)} mappings")
            return True
        else:
            print(f"Failed to apply scan results to '{build_config_name}'")
            return False
            
    except Exception as e:
        logger.error(f"Failed to apply scan results: {e}")
        return False


async def scan_mappings_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Show or configure file type mappings."""
    action = args[0] if len(args) > 0 else 'show'
    
    if action == 'show':
        print("File Type Mappings:")
        for file_type, mapping in project_scanner.file_type_mappings.items():
            print(f"  {file_type}: {mapping}")
        
        print("\nSupported File Types:")
        print("  icon - Application icons (.ico, .png, etc.)")
        print("  splash - Splash screen images")
        print("  main - Main executable Python files")
        print("  docs - Documentation files (.md, .rst, etc.)")
        print("  config - Configuration files (.json, .yaml, etc.)")
        print("  data - Data files (.csv, .json, .xml, etc.)")
        print("  assets - Asset files (images, audio, etc.)")
        print("  requirements - Dependency files (requirements.txt, etc.)")
        print("  readme - README files")
        print("  license - License files")
        
        return True
    
    elif action == 'set':
        if len(args) < 3:
            logger.error("Usage: scan-mappings set <file_type> <mapping>")
            return False
        
        file_type = args[1]
        mapping = args[2]
        
        if file_type in project_scanner.file_type_mappings:
            project_scanner.file_type_mappings[file_type] = mapping
            print(f"Updated mapping: {file_type} -> {mapping}")
            return True
        else:
            logger.error(f"Unknown file type: {file_type}")
            return False
    
    else:
        logger.error(f"Unknown action: {action}. Use 'show' or 'set'")
        return False


async def scan_cache_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """Manage scan cache."""
    action = args[0] if len(args) > 0 else 'list'
    
    if action == 'list':
        cache_files = list(project_scanner.scan_cache_dir.glob("*_scan.json"))
        if not cache_files:
            print("No cached scans found.")
            return True
        
        print("Cached Project Scans:")
        for cache_file in cache_files:
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                project_name = cache_file.stem.replace('_scan', '')
                scan_date = data.get('scan_date', 'Unknown')
                total_files = data.get('total_files', 0)
                project_type = data.get('project_type', 'unknown')
                
                print(f"  {project_name}")
                print(f"    Path: {data.get('project_path', 'Unknown')}")
                print(f"    Type: {project_type}")
                print(f"    Files: {total_files}")
                print(f"    Scanned: {scan_date}")
                print()
                
            except Exception as e:
                logger.warning(f"Failed to read cache file {cache_file}: {e}")
        
        return True
    
    elif action == 'clear':
        try:
            cache_files = list(project_scanner.scan_cache_dir.glob("*_scan.json"))
            for cache_file in cache_files:
                cache_file.unlink()
            
            print(f"Cleared {len(cache_files)} cached scans")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
    
    else:
        logger.error(f"Unknown action: {action}. Use 'list' or 'clear'")
        return False


async def register_commands():
    """Register scan commands with the CLI."""
    return {
        'scan-project': scan_project_command,
        'scan-apply': scan_apply_command,
        'scan-mappings': scan_mappings_command,
        'scan-cache': scan_cache_command,
    }


# Module info
MODULE_INFO = {
    'name': 'scan',
    'version': '1.0.0',
    'description': 'Intelligent project file discovery and mapping system for automated build configuration',
    'author': 'BuildCLI',
    'commands': ['scan-project', 'scan-apply', 'scan-mappings', 'scan-cache']
}