"""
Command queue management for BuildCLI.
"""

import asyncio
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from utils.logger import Logger


class CommandStatus(Enum):
    """Command execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class QueuedCommand:
    """Represents a queued command."""
    command: str
    args: List[str]
    modifiers: Dict[str, Any]
    chain_type: str = "sequential"
    status: CommandStatus = CommandStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    
    def __post_init__(self):
        """Post-initialization processing."""
        if not hasattr(self, 'id'):
            self.id = id(self)


class CommandQueue:
    """Manages a queue of commands with support for chaining and parallel execution."""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.commands: List[QueuedCommand] = []
        self.command_handlers: Dict[str, Callable] = {}
        self._execution_lock = asyncio.Lock()
    
    def add_command(self, command: str, args: List[str], modifiers: Dict[str, Any], chain_type: str = "sequential") -> QueuedCommand:
        """
        Add a command to the queue.
        
        Args:
            command: The command name
            args: Command arguments
            modifiers: Command modifiers/options
            chain_type: Type of chaining ('sequential', 'and', 'or')
            
        Returns:
            The queued command object
        """
        queued_cmd = QueuedCommand(
            command=command,
            args=args,
            modifiers=modifiers,
            chain_type=chain_type
        )
        
        self.commands.append(queued_cmd)
        self.logger.debug(f"Added command to queue: {command} with args {args}")
        
        return queued_cmd
    
    def register_handler(self, command: str, handler: Callable) -> None:
        """
        Register a command handler.
        
        Args:
            command: The command name
            handler: The async function to handle the command
        """
        self.command_handlers[command] = handler
        self.logger.debug(f"Registered handler for command: {command}")
    
    def clear_queue(self) -> None:
        """Clear all commands from the queue."""
        self.commands.clear()
        self.logger.debug("Command queue cleared")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get the current status of the command queue.
        
        Returns:
            Dictionary with queue statistics and command statuses
        """
        status_counts = {}
        for status in CommandStatus:
            status_counts[status.value] = sum(1 for cmd in self.commands if cmd.status == status)
        
        return {
            'total_commands': len(self.commands),
            'status_counts': status_counts,
            'commands': [
                {
                    'id': cmd.id,
                    'command': cmd.command,
                    'status': cmd.status.value,
                    'chain_type': cmd.chain_type,
                    'execution_time': cmd.execution_time
                }
                for cmd in self.commands
            ]
        }
    
    async def execute_all(self) -> bool:
        """
        Execute all commands in the queue according to their chain types.
        
        Returns:
            True if all commands executed successfully, False otherwise
        """
        if not self.commands:
            self.logger.info("No commands to execute")
            return True
        
        async with self._execution_lock:
            self.logger.info(f"Executing {len(self.commands)} commands")
            
            # Group commands by chain type for execution strategy
            command_groups = self._group_commands_by_chain()
            
            overall_success = True
            
            for group in command_groups:
                group_success = await self._execute_command_group(group)
                
                if not group_success:
                    overall_success = False
                    
                    # Handle chain failure logic
                    if group[0].chain_type == "and":
                        # Stop execution on AND chain failure
                        self.logger.info("Stopping execution due to AND chain failure")
                        break
                    elif group[0].chain_type == "or":
                        # Continue to next group on OR chain failure
                        self.logger.info("Continuing execution despite OR chain failure")
                        continue
            
            self._log_execution_summary()
            return overall_success
    
    def _group_commands_by_chain(self) -> List[List[QueuedCommand]]:
        """Group commands by their chain types for execution."""
        groups = []
        current_group = []
        
        for cmd in self.commands:
            if not current_group:
                current_group = [cmd]
            elif cmd.chain_type == current_group[0].chain_type:
                current_group.append(cmd)
            else:
                groups.append(current_group)
                current_group = [cmd]
        
        if current_group:
            groups.append(current_group)
        
        return groups
    
    async def _execute_command_group(self, commands: List[QueuedCommand]) -> bool:
        """
        Execute a group of commands with the same chain type.
        
        Args:
            commands: List of commands to execute
            
        Returns:
            True if the group executed successfully
        """
        if not commands:
            return True
        
        chain_type = commands[0].chain_type
        
        if chain_type == "and":
            # Execute sequentially, stop on first failure
            return await self._execute_sequential_and(commands)
        elif chain_type == "or":
            # Execute sequentially, stop on first success
            return await self._execute_sequential_or(commands)
        else:
            # Default sequential execution
            return await self._execute_sequential(commands)
    
    async def _execute_sequential(self, commands: List[QueuedCommand]) -> bool:
        """Execute commands sequentially."""
        success_count = 0
        
        for cmd in commands:
            success = await self._execute_single_command(cmd)
            if success:
                success_count += 1
        
        return success_count == len(commands)
    
    async def _execute_sequential_and(self, commands: List[QueuedCommand]) -> bool:
        """Execute commands sequentially with AND logic (stop on first failure)."""
        for cmd in commands:
            success = await self._execute_single_command(cmd)
            if not success:
                # Mark remaining commands as skipped
                remaining_commands = commands[commands.index(cmd) + 1:]
                for remaining_cmd in remaining_commands:
                    remaining_cmd.status = CommandStatus.SKIPPED
                    self.logger.info(f"Skipping command: {remaining_cmd.command}")
                return False
        
        return True
    
    async def _execute_sequential_or(self, commands: List[QueuedCommand]) -> bool:
        """Execute commands sequentially with OR logic (stop on first success)."""
        for cmd in commands:
            success = await self._execute_single_command(cmd)
            if success:
                # Mark remaining commands as skipped
                remaining_commands = commands[commands.index(cmd) + 1:]
                for remaining_cmd in remaining_commands:
                    remaining_cmd.status = CommandStatus.SKIPPED
                    self.logger.info(f"Skipping command: {remaining_cmd.command} (OR condition satisfied)")
                return True
        
        return False
    
    async def _execute_single_command(self, cmd: QueuedCommand) -> bool:
        """
        Execute a single command.
        
        Args:
            cmd: The command to execute
            
        Returns:
            True if the command executed successfully
        """
        import time
        
        start_time = time.time()
        cmd.status = CommandStatus.RUNNING
        
        self.logger.info(f"Executing command: {cmd.command}")
        
        try:
            # Check if we have a handler for this command
            if cmd.command in self.command_handlers:
                handler = self.command_handlers[cmd.command]
                
                # Handle dry-run mode
                if cmd.modifiers.get('dry_run', False):
                    self.logger.info(f"[DRY RUN] Would execute: {cmd.command} {' '.join(cmd.args)}")
                    cmd.status = CommandStatus.SUCCESS
                    return True
                
                # Execute the command handler
                result = await handler(cmd.args, cmd.modifiers)
                cmd.result = result
                cmd.status = CommandStatus.SUCCESS
                
                self.logger.info(f"Command completed successfully: {cmd.command}")
                return True
            
            else:
                error_msg = f"No handler registered for command: {cmd.command}"
                cmd.error = error_msg
                cmd.status = CommandStatus.FAILED
                self.logger.error(error_msg)
                return False
        
        except Exception as e:
            error_msg = f"Command failed: {cmd.command} - {str(e)}"
            cmd.error = error_msg
            cmd.status = CommandStatus.FAILED
            self.logger.error(error_msg)
            return False
        
        finally:
            cmd.execution_time = time.time() - start_time
    
    def _log_execution_summary(self) -> None:
        """Log a summary of command execution results."""
        status_counts = {}
        total_time = 0.0
        
        for cmd in self.commands:
            status = cmd.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            total_time += cmd.execution_time
        
        self.logger.info("Execution Summary:")
        self.logger.info(f"  Total commands: {len(self.commands)}")
        self.logger.info(f"  Total execution time: {total_time:.2f}s")
        
        for status, count in status_counts.items():
            self.logger.info(f"  {status.capitalize()}: {count}")
        
        # Log failed commands
        failed_commands = [cmd for cmd in self.commands if cmd.status == CommandStatus.FAILED]
        if failed_commands:
            self.logger.error("Failed commands:")
            for cmd in failed_commands:
                self.logger.error(f"  {cmd.command}: {cmd.error}")