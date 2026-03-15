#!/bin/bash
# Build script for BuildCLI using PyInstaller

echo "Building BuildCLI executable..."

# Check if PyInstaller is installed
if ! python -m pip show pyinstaller > /dev/null 2>&1; then
    echo "PyInstaller not found. Installing..."
    python -m pip install pyinstaller
    if [ $? -ne 0 ]; then
        echo "Failed to install PyInstaller"
        exit 1
    fi
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist *.spec

echo "Cleaning completed."

# Build the executable
echo "Building executable..."
python -m PyInstaller \
    --onefile \
    --console \
    --name buildcli \
    --distpath dist \
    --workpath build \
    --specpath . \
    --add-data "modules:modules" \
    --add-data "core:core" \
    --add-data "utils:utils" \
    --hidden-import asyncio \
    --hidden-import importlib.util \
    --hidden-import modules.system \
    --hidden-import modules.pyinstaller_module \
    --clean \
    --noconfirm \
    main.py

if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

echo ""
echo "Build completed successfully!"
echo "Executable location: dist/buildcli"

# Make executable (Linux/Mac)
chmod +x dist/buildcli

# Test the executable
echo ""
echo "Testing executable..."
./dist/buildcli --version

if [ $? -ne 0 ]; then
    echo "Warning: Executable test failed"
else
    echo "Executable test passed!"
fi

echo ""
echo "Build process completed."