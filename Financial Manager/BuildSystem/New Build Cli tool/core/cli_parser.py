"""
Command line argument parser for BuildCLI.
"""

import argparse
import shlex
from typing import List, Dict, Any, Optional, Tuple
from core.module_manager import ModuleManager
from utils.logger import Logger


class CLIParser:
    """Command line interface parser with support for command chaining and modifiers."""
    
    def __init__(self, module_manager: ModuleManager, logger: Logger):
        self.module_manager = module_manager
        self.logger = logger
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser."""
        parser = argparse.ArgumentParser(
            prog='buildcli',
            description='A modular build tool with command chaining support',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self._get_usage_examples()
        )
        
        parser.add_argument(
            '--version', '-v',
            action='version',
            version='%(prog)s 1.0.0'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
        
        parser.add_argument(
            '--quiet', '-q',
            action='store_true',
            help='Suppress non-error output'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be executed without running commands'
        )
        
        parser.add_argument(
            '--parallel', '-p',
            action='store_true',
            help='Enable parallel execution of independent commands'
        )
        
        parser.add_argument(
            '--sequential', '-s',
            action='store_true',
            help='Force sequential execution of all commands'
        )
        
        parser.add_argument(
            'commands',
            nargs='*',
            help='Commands to execute (supports chaining with && and ||)'
        )
        
        return parser
    
    def _get_usage_examples(self) -> str:
        """Get usage examples for help text."""
        return """
Examples:
  buildcli build --release                    # Single command with modifier
  buildcli clean && build --debug             # Chain commands with AND
  buildcli test || build --force              # Chain commands with OR
  buildcli clean && build --release && deploy # Multiple chained commands
  buildcli install-module mymodule            # Install a module from repository
  buildcli list-modules                       # List available modules
  buildcli --parallel build test lint         # Run commands in parallel
        """
    
    def parse_arguments(self, args: List[str]) -> List[Dict[str, Any]]:
        """
        Parse command line arguments and return a list of command dictionaries.
        
        Args:
            args: List of command line arguments
            
        Returns:
            List of command dictionaries with 'command', 'args', and 'modifiers' keys
        """
        if not args:
            return []
        
        # Parse global options first
        global_args, remaining = self._parse_global_args(args)
        
        if not remaining:
            return []
        
        # Parse command chains
        command_chains = self._parse_command_chains(remaining)
        
        # Convert to command dictionaries
        commands = []
        for chain in command_chains:
            for command_str in chain['commands']:
                command_info = self._parse_single_command(command_str, global_args)
                command_info['chain_type'] = chain['type']
                commands.append(command_info)
        
        return commands
    
    def _parse_global_args(self, args: List[str]) -> Tuple[Dict[str, Any], List[str]]:
        """Parse global arguments and return remaining args."""
        global_options = {}
        remaining = []
        i = 0
        
        while i < len(args):
            arg = args[i]
            
            if arg in ['--verbose']:
                global_options['verbose'] = True
            elif arg in ['--quiet', '-q']:
                global_options['quiet'] = True
            elif arg in ['--dry-run']:
                global_options['dry_run'] = True
            elif arg in ['--parallel', '-p']:
                global_options['parallel'] = True
            elif arg in ['--sequential', '-s']:
                global_options['sequential'] = True
            else:
                remaining.extend(args[i:])
                break
            
            i += 1
        
        return global_options, remaining
    
    def _parse_command_chains(self, args: List[str]) -> List[Dict[str, Any]]:
        """
        Parse command chains separated by && (AND) or || (OR).
        
        Returns:
            List of chain dictionaries with 'type' and 'commands' keys
        """
        chains = []
        current_chain = {'type': 'sequential', 'commands': []}
        current_command = []
        
        i = 0
        while i < len(args):
            arg = args[i]
            
            if arg == '&&':
                if current_command:
                    current_chain['commands'].append(' '.join(current_command))
                    current_command = []
                
                if current_chain['commands']:
                    current_chain['type'] = 'and'
                    chains.append(current_chain)
                    current_chain = {'type': 'and', 'commands': []}
            
            elif arg == '||':
                if current_command:
                    current_chain['commands'].append(' '.join(current_command))
                    current_command = []
                
                if current_chain['commands']:
                    current_chain['type'] = 'or'
                    chains.append(current_chain)
                    current_chain = {'type': 'or', 'commands': []}
            
            else:
                current_command.append(arg)
            
            i += 1
        
        # Add the last command
        if current_command:
            current_chain['commands'].append(' '.join(current_command))
        
        if current_chain['commands']:
            chains.append(current_chain)
        
        return chains
    
    def _parse_single_command(self, command_str: str, global_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a single command string into command, args, and modifiers.
        
        Args:
            command_str: The command string to parse
            global_args: Global arguments that apply to all commands
            
        Returns:
            Dictionary with 'command', 'args', and 'modifiers' keys
        """
        # Split the command string using shell-like parsing
        try:
            parts = shlex.split(command_str)
        except ValueError:
            # Fallback to simple split if shlex fails
            parts = command_str.split()
        
        if not parts:
            return {'command': '', 'args': [], 'modifiers': global_args.copy()}
        
        command = parts[0]
        args = []
        modifiers = global_args.copy()
        
        # Parse arguments and modifiers
        i = 1
        while i < len(parts):
            part = parts[i]
            
            if part.startswith('--'):
                # Long option
                if '=' in part:
                    key, value = part[2:].split('=', 1)
                    modifiers[key] = value
                else:
                    key = part[2:]
                    # Check if next argument is a value
                    if i + 1 < len(parts) and not parts[i + 1].startswith('-'):
                        modifiers[key] = parts[i + 1]
                        i += 1
                    else:
                        modifiers[key] = True
            
            elif part.startswith('-') and len(part) > 1:
                # Short option(s)
                for char in part[1:]:
                    modifiers[char] = True
            
            else:
                # Regular argument
                args.append(part)
            
            i += 1
        
        return {
            'command': command,
            'args': args,
            'modifiers': modifiers
        }
    
    def print_help(self):
        """Print help information."""
        self.parser.print_help()
        
        # Print available modules
        modules = self.module_manager.get_available_modules()
        if modules:
            print("\nAvailable modules:")
            for module_name, module_info in modules.items():
                description = module_info.get('description', 'No description available')
                print(f"  {module_name:<20} {description}")
        else:
            print("\nNo modules currently available. Use 'install-module' to add modules.")