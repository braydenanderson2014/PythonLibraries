#!/usr/bin/env python3
"""Debug script to test module loading."""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.config import Config
from utils.logger import Logger
from core.module_manager import ModuleManager

async def debug_module_loading():
    config = Config()
    logger = Logger("DEBUG")
    module_manager = ModuleManager(config, logger)
    
    print("Starting module loading debug...")
    
    try:
        await module_manager.load_builtin_modules()
        print(f"Loaded modules: {list(module_manager.loaded_modules.keys())}")
        print(f"Command handlers: {list(module_manager.command_handlers.keys())}")
        
        for module_name, module in module_manager.loaded_modules.items():
            print(f"Module {module_name}: {module}")
            if hasattr(module, 'register_commands'):
                print(f"  Has register_commands: Yes")
                try:
                    commands = await module.register_commands()
                    print(f"  Commands: {list(commands.keys())}")
                except Exception as e:
                    print(f"  Error calling register_commands: {e}")
            else:
                print(f"  Has register_commands: No")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_module_loading())