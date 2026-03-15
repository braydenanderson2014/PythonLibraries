#!/usr/bin/env python3
"""
BuildCLI - A modular command-line interface tool with command chaining support.

This is the main entry point for the BuildCLI tool. It handles argument parsing,
command queuing, and execution coordination.
"""

import sys
import os
import argparse
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add the current directory to Python path for module imports
sys.path.insert(0, str(Path(__file__).parent))

from core.cli_parser import CLIParser
from core.command_queue import CommandQueue
from core.module_manager import ModuleManager
from core.config import Config
from utils.logger import Logger


class BuildCLI:
    """Main CLI application class."""
    
    def __init__(self):
        self.config = Config()
        self.logger = Logger(self.config.log_level)
        self.module_manager = ModuleManager(self.config, self.logger)
        self.command_queue = CommandQueue(self.logger)
        self.cli_parser = CLIParser(self.module_manager, self.logger)
    
    async def initialize(self):
        """Initialize the CLI application."""
        try:
            # Load built-in modules
            await self.module_manager.load_builtin_modules()
            
            # Check for updates to remote modules if configured
            if self.config.auto_update_modules:
                await self.module_manager.update_remote_modules()
            
            self.logger.debug("BuildCLI initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize BuildCLI: {e}")
            raise
    
    async def run(self, args: Optional[List[str]] = None) -> int:
        """
        Run the CLI application.
        
        Args:
            args: Command line arguments (defaults to sys.argv[1:])
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        try:
            if args is None:
                args = sys.argv[1:]
            
            # Parse arguments and build command queue
            parsed_commands = self.cli_parser.parse_arguments(args)
            
            if not parsed_commands:
                self.cli_parser.print_help()
                return 0
            
            # Register command handlers from modules
            command_handlers = self.module_manager.get_command_handlers()
            for command_name, handler in command_handlers.items():
                self.command_queue.register_handler(command_name, handler)
            
            # Add commands to queue
            for command_info in parsed_commands:
                self.command_queue.add_command(
                    command_info['command'],
                    command_info['args'],
                    command_info['modifiers'],
                    command_info.get('chain_type', 'sequential')
                )
            
            # Execute command queue
            success = await self.command_queue.execute_all()
            
            return 0 if success else 1
            
        except KeyboardInterrupt:
            self.logger.info("Operation cancelled by user")
            return 130
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return 1
    
    def print_version(self):
        """Print version information."""
        print(f"BuildCLI v{self.config.version}")
        print(f"Python {sys.version}")
    
    def print_help(self):
        """Print help information."""
        self.cli_parser.print_help()


async def main():
    """Main entry point."""
    cli = BuildCLI()
    
    try:
        await cli.initialize()
        
        # Make module manager accessible globally for system commands
        import __main__
        __main__._module_manager = cli.module_manager
        
        exit_code = await cli.run()
        sys.exit(exit_code)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # Handle special cases before async initialization
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--version', '-v']:
            cli = BuildCLI()
            cli.print_version()
            sys.exit(0)
        elif sys.argv[1] in ['--help', '-h']:
            cli = BuildCLI()
            cli.print_help()
            sys.exit(0)
    
    # Run the async main function
    asyncio.run(main())