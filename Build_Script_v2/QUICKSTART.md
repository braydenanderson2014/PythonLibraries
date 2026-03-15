# Build System v2 - Quick Start Guide

## Complete Workflow Example

### 1. Setup
```bash
# Install dependencies
pip install -r requirements.txt
```

### 2. Test the Example Application
```bash
# Run the example app
python example_app.py
```

### 3. Use the Build System

#### Interactive Mode
```bash
# Start interactive mode
python build_system.py -i

# In the build prompt:
build> list                           # See available commands
build> scan-python --find-main        # Find entry points
build> scan-icon --target ./assets    # Scan for icons (if you have any)
build> build example_app.py --name MyApp --console
build> exit
```

#### Command Line Mode
```bash
# Scan for Python files
python build_system.py scan-python --find-main

# Build the example
python build_system.py build example_app.py --name ExampleApp

# Clean build artifacts
python build_system.py clean
```

### 4. Advanced Build Options

```bash
# Build as single file without console (GUI mode)
python build_system.py build example_app.py --onefile --noconsole --name MyGUIApp

# Build with custom icon
python build_system.py build --icon path/to/icon.ico --name MyApp

# Preview build command without executing
python build_system.py build --dry-run

# Clean build from scratch
python build_system.py clean --all
python build_system.py build --clean
```

### 5. Using Icon/Splash Detection

If you have image assets in your project:

```bash
# Scan for suitable icons and splash images
python build_system.py scan-icon --target ./assets

# The system will:
# 1. Find all images (.png, .ico, .jpg, etc.)
# 2. Analyze them for suitability
# 3. Prompt you to select (if multiple found)
# 4. Save selection to config
# 5. Automatically use them in builds

# Build with auto-detected assets
python build_system.py build
```

### 6. Check Your Build

Your executable will be in the `dist/` directory:
```bash
ls dist/
# Or on Windows:
dir dist\
```

## Creating Your Own Commands

Create a new file in `modules/my_command.py`:

```python
from build_system import Command, BuildContext
from typing import List

class MyCommand(Command):
    @classmethod
    def get_name(cls) -> str:
        return "mycommand"
    
    @classmethod
    def get_aliases(cls) -> List[str]:
        return ["mc"]
    
    @classmethod
    def get_description(cls) -> str:
        return "My custom command"
    
    def execute(self, *args, **kwargs) -> bool:
        self.context.log("Executing my command!")
        
        # Access config
        project_name = self.context.get_config('project_name')
        
        # Use memory
        self.context.set_memory('my_data', 'some_value')
        
        return True
```

Your command will be automatically discovered on next run!

## Common Workflows

### Workflow 1: Quick Build
```bash
python build_system.py -i
build> build example_app.py
```

### Workflow 2: Production Build with Assets
```bash
python build_system.py scan-icon
python build_system.py build --onefile --noconsole --clean
```

### Workflow 3: Development Iteration
```bash
python build_system.py -v -i
build> clean
build> build --dry-run        # Preview
build> build                  # Actually build
```

## Tips

- Use `--verbose` or `-v` for detailed output
- Use `--dry-run` to preview PyInstaller commands
- Run `scan-python --find-main` if build can't find entry point
- Use `scan-icon --auto` to skip selection prompts
- Configuration persists between runs in `build_config.json`
- Build history saved in `build_memory.json`

## Troubleshooting

### "PyInstaller not found"
```bash
pip install pyinstaller
```

### "No entry point detected"
```bash
# Specify manually
build> build --entry main.py
```

### "Build failed"
```bash
# Try with verbose mode
python build_system.py -v build

# Or clean and rebuild
build> clean --all
build> build --clean
```
