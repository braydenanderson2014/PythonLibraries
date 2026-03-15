#!/usr/bin/env python3
"""
Modular Build System v2
A flexible, extensible command-based build system with dynamic command registration.
"""

import json
import os
import sys
import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional
from abc import ABC, abstractmethod
import traceback


class BuildContext:
    """
    Shared context object that provides common functionality and data to all commands.
    This allows commands to access shared resources without tight coupling.
    """
    
    def __init__(self, config_path: str = "build_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.project_root = Path.cwd()
        self.memory = self._load_memory()
        self.verbose = False
        self.dry_run = False
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to load config from {self.config_path}: {e}")
                return {}
        return {}
    
    def _load_memory(self) -> Dict[str, Any]:
        """Load persistent memory from JSON file"""
        memory_path = self.config.get('memory_file', 'build_memory.json')
        if os.path.exists(memory_path):
            try:
                with open(memory_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to load memory from {memory_path}: {e}")
                return {}
        return {}
    
    def save_memory(self):
        """Persist memory to JSON file"""
        memory_path = self.config.get('memory_file', 'build_memory.json')
        try:
            with open(memory_path, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            print(f"Error: Failed to save memory to {memory_path}: {e}")
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value with optional default"""
        return self.config.get(key, default)
    
    def set_config(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
    
    def get_memory(self, key: str, default: Any = None) -> Any:
        """Get value from persistent memory"""
        return self.memory.get(key, default)
    
    def set_memory(self, key: str, value: Any):
        """Set value in persistent memory"""
        self.memory[key] = value
        self.save_memory()
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with level"""
        prefix = f"[{level}]"
        print(f"{prefix} {message}")
    
    def log_verbose(self, message: str):
        """Log verbose message (only if verbose mode is enabled)"""
        if self.verbose:
            self.log(message, "VERBOSE")


class Command(ABC):
    """
    Abstract base class for all commands.
    Each command must implement the execute method and provide metadata.
    """
    
    def __init__(self, context: BuildContext):
        self.context = context
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> bool:
        """
        Execute the command.
        Returns True on success, False on failure.
        """
        pass
    
    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """Return the command name (e.g., 'scan', 'build', 'clean')"""
        pass
    
    @classmethod
    def get_aliases(cls) -> List[str]:
        """Return list of command aliases (optional)"""
        return []
    
    @classmethod
    def get_description(cls) -> str:
        """Return command description"""
        return "No description available"
    
    @classmethod
    def get_help(cls) -> str:
        """Return detailed help text"""
        return cls.get_description()
    
    @classmethod
    def get_flags(cls) -> List[str]:
        """Return list of available flags/options for this command"""
        return []


class CommandRegistry:
    """
    Central registry for all available commands.
    Handles command discovery, registration, and execution.
    """
    
    def __init__(self, context: BuildContext):
        self.context = context
        self.commands: Dict[str, type[Command]] = {}
        self.aliases: Dict[str, str] = {}  # alias -> command_name mapping
        
    def register_command(self, command_class: type[Command]):
        """Register a command class"""
        command_name = command_class.get_name()
        
        if command_name in self.commands:
            self.context.log(f"Warning: Command '{command_name}' is already registered. Overwriting.", "WARN")
        
        self.commands[command_name] = command_class
        
        # Register aliases
        for alias in command_class.get_aliases():
            if alias in self.aliases:
                self.context.log(f"Warning: Alias '{alias}' is already registered. Overwriting.", "WARN")
            self.aliases[alias] = command_name
        
        self.context.log_verbose(f"Registered command: {command_name}")
    
    def discover_commands(self, modules_dir: str = "modules"):
        """
        Discover and register all commands in the modules directory.
        Scans for Python files and looks for Command subclasses.
        """
        modules_path = Path(modules_dir)
        
        if not modules_path.exists():
            self.context.log(f"Modules directory '{modules_dir}' not found. Creating it.", "WARN")
            modules_path.mkdir(parents=True, exist_ok=True)
            return
        
        self.context.log_verbose(f"Discovering commands in '{modules_dir}'...")
        
        # Add parent directory to Python path so modules can import build_system
        parent_dir = str(Path(__file__).parent.absolute())
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        # Scan for Python files
        for python_file in modules_path.glob("*.py"):
            if python_file.name.startswith("_"):
                continue  # Skip private modules
            
            module_name = python_file.stem
            
            try:
                self.context.log_verbose(f"Loading module: {module_name}")
                
                # Import the module
                spec = importlib.util.spec_from_file_location(module_name, python_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    
                    # Find all Command subclasses in the module
                    found_commands = 0
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        # Check if it's a Command subclass by checking the class name hierarchy
                        try:
                            if (hasattr(obj, '__mro__') and 
                                any(base.__name__ == 'Command' for base in obj.__mro__) and
                                obj.__name__ != 'Command'):
                                self.context.log_verbose(f"  Registering command class: {name}")
                                self.register_command(obj)
                                found_commands += 1
                        except Exception as e:
                            self.context.log_verbose(f"  Error checking class {name}: {e}")
                    
                    self.context.log_verbose(f"  Found {found_commands} command(s) in {module_name}")
                else:
                    self.context.log(f"Could not load spec for module '{module_name}'", "WARN")
                        
            except Exception as e:
                self.context.log(f"Error loading module '{module_name}': {e}", "ERROR")
                if self.context.verbose:
                    traceback.print_exc()
    
    def get_command(self, name: str) -> Optional[type[Command]]:
        """Get command class by name or alias"""
        # Check direct name match
        if name in self.commands:
            return self.commands[name]
        
        # Check alias match
        if name in self.aliases:
            return self.commands[self.aliases[name]]
        
        return None
    
    def list_commands(self) -> List[str]:
        """Return list of all registered command names"""
        return sorted(self.commands.keys())
    
    def execute_command(self, command_name: str, *args, **kwargs) -> bool:
        """
        Execute a command by name with error handling.
        Returns True on success, False on failure.
        """
        command_class = self.get_command(command_name)
        
        if command_class is None:
            self.context.log(f"Error: Unknown command '{command_name}'", "ERROR")
            return False
        
        try:
            self.context.log_verbose(f"Executing command: {command_name}")
            
            # Instantiate and execute command
            command_instance = command_class(self.context)
            result = command_instance.execute(*args, **kwargs)
            
            if result:
                self.context.log_verbose(f"Command '{command_name}' completed successfully")
            else:
                self.context.log(f"Command '{command_name}' failed", "ERROR")
            
            return result
            
        except Exception as e:
            self.context.log(f"Error executing command '{command_name}': {e}", "ERROR")
            if self.context.verbose:
                traceback.print_exc()
            return False


class BuildSystem:
    """
    Main build system coordinator.
    Manages context, registry, and command execution.
    """
    
    def __init__(self, config_path: str = "build_config.json"):
        self.context = BuildContext(config_path)
        self.registry = CommandRegistry(self.context)
        
    def initialize(self, modules_dir: str = "modules"):
        """Initialize the build system and discover commands"""
        self.context.log("Initializing Build System v2...")
        self.registry.discover_commands(modules_dir)
        self.context.log(f"Discovered {len(self.registry.commands)} command(s)")
        
    def run_command(self, command_name: str, *args, **kwargs) -> bool:
        """Run a single command"""
        return self.registry.execute_command(command_name, *args, **kwargs)
    
    def run_interactive(self):
        """Run in interactive mode with command prompt"""
        self.context.log("Entering interactive mode. Type 'help' for commands, 'exit' to quit.")
        
        while True:
            try:
                user_input = input("\nbuild> ").strip()
                
                if not user_input:
                    continue
                
                # Parse command and arguments
                parts = user_input.split()
                command_name = parts[0]
                args = parts[1:]
                
                # Handle built-in commands
                if command_name in ['exit', 'quit']:
                    self.context.log("Exiting...")
                    break
                elif command_name == 'help':
                    self._show_help(args[0] if args else None)
                    continue
                elif command_name == 'list':
                    self._list_commands()
                    continue
                elif command_name == 'verbose':
                    self.context.verbose = not self.context.verbose
                    self.context.log(f"Verbose mode: {'ON' if self.context.verbose else 'OFF'}")
                    continue
                
                # Execute registered command
                self.run_command(command_name, *args)
                
            except KeyboardInterrupt:
                print("\n")
                self.context.log("Interrupted. Type 'exit' to quit.")
            except EOFError:
                print("\n")
                break
            except Exception as e:
                self.context.log(f"Error: {e}", "ERROR")
                if self.context.verbose:
                    traceback.print_exc()
    
    def _show_help(self, command_name: Optional[str] = None):
        """Show help information"""
        if command_name:
            # Show help for specific command
            command_class = self.registry.get_command(command_name)
            if command_class:
                print(f"\nCommand: {command_class.get_name()}")
                aliases = command_class.get_aliases()
                if aliases:
                    print(f"Aliases: {', '.join(aliases)}")
                print(f"Description: {command_class.get_description()}")
                print(f"\n{command_class.get_help()}")
            else:
                self.context.log(f"Unknown command: {command_name}", "ERROR")
        else:
            # Show general help
            print("\nAvailable commands:")
            print("  help [command]  - Show this help or help for a specific command")
            print("  list            - List all available commands")
            print("  verbose         - Toggle verbose mode")
            print("  exit/quit       - Exit the build system")
            print("\nRegistered commands:")
            self._list_commands()
    
    def _list_commands(self):
        """List all registered commands"""
        commands = self.registry.list_commands()
        if not commands:
            print("  No commands registered")
            return
        
        for cmd_name in commands:
            cmd_class = self.registry.commands[cmd_name]
            aliases = cmd_class.get_aliases()
            flags = cmd_class.get_flags()
            
            alias_str = f" (aliases: {', '.join(aliases)})" if aliases else ""
            flags_str = f"\n    Flags: {', '.join(flags)}" if flags else ""
            
            print(f"  {cmd_name}{alias_str} - {cmd_class.get_description()}{flags_str}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Modular Build System v2",
        allow_abbrev=False
    )
    parser.add_argument('command', nargs='?', help='Command to execute')
    parser.add_argument('args', nargs='*', help='Command arguments')
    parser.add_argument('-c', '--config', default='build_config.json', help='Config file path')
    parser.add_argument('-m', '--modules', default='modules', help='Modules directory path')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('-i', '--interactive', action='store_true', help='Run in interactive mode')
    
    # Parse only known args to allow command-specific arguments
    args, unknown = parser.parse_known_args()
    
    # Combine parsed args with unknown args for the command
    all_args = list(args.args) + unknown
    
    # Initialize build system
    build_system = BuildSystem(args.config)
    build_system.context.verbose = args.verbose
    build_system.initialize(args.modules)
    
    # Run command or enter interactive mode
    if args.interactive or not args.command:
        build_system.run_interactive()
    else:
        success = build_system.run_command(args.command, *all_args)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
