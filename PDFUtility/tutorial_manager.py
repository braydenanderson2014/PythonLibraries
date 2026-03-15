#!/usr/bin/env python3
"""
Tutorial Management Utility
Helper script for managing tutorial JSON files
"""

import json
import os
import sys
from pathlib import Path
from PDFLogger import Logger

logger = Logger()

def get_tutorials_dir():
    """Get the tutorials directory path"""
    script_dir = Path(__file__).parent
    return script_dir / "Tutorials"

def list_tutorials():
    """List all available tutorials"""
    tutorials_dir = get_tutorials_dir()
    if not tutorials_dir.exists():
        logger.error("TutorialManager", "Tutorials directory not found!")
        return
    
    logger.info("TutorialManager", "Available tutorials:")
    logger.info("TutorialManager", "-" * 40)
    
    for json_file in tutorials_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            name = data.get('name', 'Unknown')
            title = data.get('title', name)
            steps = len(data.get('steps', []))

            logger.info("TutorialManager", f"📚 {name}")
            logger.info("TutorialManager", f"   Title: {title}")
            logger.info("TutorialManager", f"   Steps: {steps}")
            logger.info("TutorialManager", "")

        except Exception as e:
            logger.error("TutorialManager", f"Error reading {json_file.name}: {e}")

def validate_tutorial(filepath):
    """Validate a tutorial JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        errors = []
        
        # Check required fields
        if 'name' not in data:
            errors.append("Missing 'name' field")
        if 'steps' not in data:
            errors.append("Missing 'steps' field")
        elif not isinstance(data['steps'], list):
            errors.append("'steps' must be a list")
        else:
            # Validate each step
            for i, step in enumerate(data['steps']):
                if not isinstance(step, dict):
                    errors.append(f"Step {i} must be a dictionary")
                    continue
                if 'target' not in step:
                    errors.append(f"Step {i} missing 'target' field")
                if 'text' not in step:
                    errors.append(f"Step {i} missing 'text' field")
        
        if errors:
            logger.error("TutorialManager", f"❌ {filepath.name} - Validation errors:")
            for error in errors:
                logger.error("TutorialManager", f"   • {error}")
            return False
        else:
            steps_count = len(data['steps'])
            logger.info("TutorialManager", f"✅ {filepath.name} - Valid ({steps_count} steps)")
            return True
            
    except json.JSONDecodeError as e:
        logger.error("TutorialManager", f"❌ {filepath.name} - JSON parsing error: {e}")
        return False
    except Exception as e:
        logger.error("TutorialManager", f"❌ {filepath.name} - Error: {e}")
        return False

def validate_all():
    """Validate all tutorial files"""
    tutorials_dir = get_tutorials_dir()
    if not tutorials_dir.exists():
        logger.error("TutorialManager", "Tutorials directory not found!")
        return
    
    logger.info("TutorialManager", "Validating all tutorial files:")
    logger.info("TutorialManager", "-" * 40)

    valid_count = 0
    total_count = 0
    
    for json_file in tutorials_dir.glob("*.json"):
        total_count += 1
        if validate_tutorial(json_file):
            valid_count += 1

    logger.info("TutorialManager", "-" * 40)
    logger.info("TutorialManager", f"Summary: {valid_count}/{total_count} tutorials are valid")

def create_template(name):
    """Create a new tutorial template"""
    tutorials_dir = get_tutorials_dir()
    tutorials_dir.mkdir(exist_ok=True)
    
    filepath = tutorials_dir / f"{name}.json"
    if filepath.exists():
        logger.error("TutorialManager", f"Tutorial {name}.json already exists!")
        return
    
    template = {
        "name": name,
        "title": name.replace('_', ' ').title(),
        "description": f"Tutorial for {name}",
        "steps": [
            {
                "target": "example_widget",
                "text": "<b>Example Step</b><br><br>This is an example tutorial step. Replace with your actual content.",
                "button_text": "Next",
                "highlight_style": "pulse",
                "arrow_direction": "auto"
            }
        ]
    }
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=4, ensure_ascii=False)
        logger.info("TutorialManager", f"✅ Created template: {filepath}")
    except Exception as e:
        logger.error("TutorialManager", f"❌ Error creating template: {e}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        logger.info("TutorialManager", "Tutorial Management Utility")
        logger.info("TutorialManager", "Usage:")
        logger.info("TutorialManager", "  python tutorial_manager.py list          - List all tutorials")
        logger.info("TutorialManager", "  python tutorial_manager.py validate      - Validate all tutorials")
        logger.info("TutorialManager", "  python tutorial_manager.py validate FILE - Validate specific file")
        logger.info("TutorialManager", "  python tutorial_manager.py create NAME   - Create new tutorial template")
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_tutorials()
    elif command == "validate":
        if len(sys.argv) > 2:
            filepath = Path(sys.argv[2])
            if not filepath.exists():
                tutorials_dir = get_tutorials_dir()
                filepath = tutorials_dir / filepath
            validate_tutorial(filepath)
        else:
            validate_all()
    elif command == "create":
        if len(sys.argv) > 2:
            create_template(sys.argv[2])
        else:
            logger.error("TutorialManager", "Please specify tutorial name: python tutorial_manager.py create NAME")
    else:
        logger.error("TutorialManager", f"Unknown command: {command}")

if __name__ == "__main__":
    main()
