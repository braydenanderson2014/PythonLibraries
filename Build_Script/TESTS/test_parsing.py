#!/usr/bin/env python3

import sys
sys.argv = ['build_cli.py', '--install-needed', 'build_cli.py']

from build_cli import parse_command_queue

commands = parse_command_queue()
print('Parsed commands:', commands)

for i, cmd in enumerate(commands):
    print(f"Command {i}: {cmd}")
