#!/bin/bash

# Test script to demonstrate the improved GitHub Actions workflow
# This simulates how the workflow would behave with different project structures

echo "🧪 Testing Multi-Platform Build Workflow with Targeted Scanning"
echo "=============================================================="

# Create test project structures
echo "📁 Creating test project structures..."

# Structure 1: Build script in root
mkdir -p test_projects/root_build/{assets,config,docs/tutorials}
echo 'print("Hello from root build!")' > test_projects/root_build/main.py
echo '{"app": "settings"}' > test_projects/root_build/config/app_config.json
touch test_projects/root_build/assets/app_icon.png
touch test_projects/root_build/assets/splash_screen.png
echo "# Tutorial 1" > test_projects/root_build/docs/tutorials/getting_started.md

# Structure 2: Build script in BuildSystems
mkdir -p test_projects/buildsystems/{BuildSystems,assets,resources,tutorials}
echo 'print("Hello from BuildSystems!")' > test_projects/buildsystems/main.py
echo '{"database": "config"}' > test_projects/buildsystems/resources/db_config.json
touch test_projects/buildsystems/assets/app_logo.png
touch test_projects/buildsystems/resources/splash_image.png
echo "# User Guide" > test_projects/buildsystems/tutorials/user_guide.md

echo "✅ Test project structures created"
echo ""

# Simulate workflow commands for each structure
echo "🔍 Simulating workflow scanning for root_build structure..."
echo "Commands that would be run:"
echo "  python build_cli.py --set-root ."
echo "  python build_cli.py --scan-dir ./assets --scan icons --contains icon"
echo "  python build_cli.py --scan-dir ./assets --scan icons --contains splash"
echo "  python build_cli.py --scan-dir ./config --scan config"
echo "  python build_cli.py --scan-dir ./docs --scan help --contains tutorial"
echo ""

echo "🔍 Simulating workflow scanning for buildsystems structure..."
echo "Commands that would be run:"
echo "  python BuildSystems/build_cli.py --set-root .."
echo "  python BuildSystems/build_cli.py --scan-dir ./assets --scan icons --contains logo"
echo "  python BuildSystems/build_cli.py --scan-dir ./resources --scan icons --contains splash"
echo "  python BuildSystems/build_cli.py --scan-dir ./resources --scan config"
echo "  python BuildSystems/build_cli.py --scan-dir ./tutorials --scan help"
echo ""

# Show the difference
echo "📊 Benefits of Targeted Scanning:"
echo "✅ No scanning of virtual environments or dependencies"
echo "✅ Precise file matching with --contains filters"
echo "✅ Proper project root detection for subdirectory builds"
echo "✅ Respects common project structure conventions"
echo ""

echo "🔧 Project Structure Support:"
echo "• Root build: build_cli.py in project root"
echo "• BuildSystems: build_cli.py in BuildSystems/ subdirectory"  
echo "• Scripts: build_cli.py in scripts/ subdirectory"
echo "• Tools: build_cli.py in tools/ subdirectory"
echo ""

echo "🎯 Filtering Examples:"
echo "• Icons: Looks for 'icon', 'splash', 'logo' in filenames"
echo "• Config: Looks for 'config', 'settings' in filenames"
echo "• Help: Looks for 'tutorial', 'guide', 'manual' in filenames"
echo ""

echo "✨ Workflow is now ready for precise, targeted scanning!"

# Cleanup
rm -rf test_projects
