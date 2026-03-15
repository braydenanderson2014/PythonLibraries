"""
Template for creating custom BuildCLI modules.

Copy this file and modify it to create your own modules.
"""

from typing import Dict, List, Any, Callable


# Module metadata - REQUIRED
MODULE_INFO = {
    'name': 'template',  # Module name (should match filename)
    'version': '1.0.0',  # Module version
    'description': 'Template module for BuildCLI',  # Brief description
    'author': 'Your Name',  # Author name
    'commands': ['template-cmd'],  # List of commands this module provides
    'dependencies': [],  # Optional: List of required Python packages
    'repository_url': None,  # Optional: URL for updates
}


async def template_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """
    Template command implementation.
    
    Args:
        args: List of command arguments (everything after the command name)
        modifiers: Dictionary of modifiers/options (e.g., {'dry_run': True, 'verbose': True})
    
    Returns:
        Any: Command result (True for success, False for failure, or any data)
    
    Raises:
        ValueError: For invalid arguments
        RuntimeError: For execution errors
    """
    # Handle dry-run mode
    if modifiers.get('dry_run', False):
        print("[DRY RUN] Would execute template command")
        return True
    
    # Handle verbose mode
    if modifiers.get('verbose', False):
        print(f"Template command called with args: {args}")
        print(f"Modifiers: {modifiers}")
    
    # Your command implementation here
    print("Template command executed successfully!")
    
    # Example argument handling
    if args:
        print(f"Received arguments: {', '.join(args)}")
    
    # Example modifier handling
    if modifiers.get('example_flag', False):
        print("Example flag is set!")
    
    # Return success
    return True


# REQUIRED: Command registration function
async def register_commands() -> Dict[str, Callable]:
    """
    Register all commands provided by this module.
    
    Returns:
        Dictionary mapping command names to their handler functions
    """
    return {
        'template-cmd': template_command,
        # Add more commands here as needed
    }


# OPTIONAL: Legacy support function
def get_commands() -> List[str]:
    """
    Get list of command names provided by this module.
    This is for legacy compatibility.
    
    Returns:
        List of command names
    """
    return MODULE_INFO['commands']


# OPTIONAL: Module initialization function
async def initialize_module(config, logger):
    """
    Initialize the module (called when module is loaded).
    
    Args:
        config: BuildCLI configuration object
        logger: BuildCLI logger object
    """
    logger.debug(f"Initializing {MODULE_INFO['name']} module")
    # Add any initialization code here
    pass


# OPTIONAL: Module cleanup function
async def cleanup_module():
    """
    Clean up module resources (called when module is unloaded).
    """
    # Add any cleanup code here
    pass


# Example of more complex command with error handling
async def advanced_example_command(args: List[str], modifiers: Dict[str, Any]) -> Any:
    """
    Advanced example showing error handling and complex logic.
    """
    try:
        # Validate arguments
        if not args:
            raise ValueError("At least one argument is required")
        
        # Handle different argument patterns
        if args[0] == 'help':
            print("Advanced example command help:")
            print("  Usage: advanced-example <action> [options]")
            print("  Actions: help, process, validate")
            return True
        
        elif args[0] == 'process':
            # Processing logic here
            items = args[1:] if len(args) > 1 else ['default']
            
            for item in items:
                if modifiers.get('dry_run', False):
                    print(f"[DRY RUN] Would process: {item}")
                else:
                    print(f"Processing: {item}")
                    # Add actual processing logic here
            
            return True
        
        elif args[0] == 'validate':
            # Validation logic here
            print("Validating...")
            # Add validation logic here
            return True
        
        else:
            raise ValueError(f"Unknown action: {args[0]}")
    
    except ValueError as e:
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


# Example usage in BuildCLI:
# python main.py template-cmd arg1 arg2 --dry-run --verbose
# python main.py advanced-example process item1 item2 --dry-run