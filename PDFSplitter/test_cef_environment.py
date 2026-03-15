#!/usr/bin/env python3
"""
Simple CEF Python test to verify installation and basic functionality.
This script tests if CEF Python can be imported and initialized.
"""

import sys
import os

def test_cef_import():
    """Test if CEF Python can be imported."""
    print("Testing CEF Python import...")
    try:
        import cefpython3 as cef
        print("✅ CEF Python imported successfully")
        print(f"   Version: {cef.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import CEF Python: {e}")
        return False
    except Exception as e:
        print(f"❌ CEF Python import error: {e}")
        return False

def test_cef_initialization():
    """Test CEF Python initialization (without GUI)."""
    print("\nTesting CEF Python initialization...")
    try:
        import cefpython3 as cef
        
        # Basic settings for testing
        settings = {
            "multi_threaded_message_loop": False,
            "debug": False,
            "log_severity": cef.LOGSEVERITY_ERROR,
            "log_file": "",
        }
        
        # Initialize CEF
        cef.Initialize(settings)
        print("✅ CEF Python initialized successfully")
        
        # Shutdown CEF
        cef.Shutdown()
        print("✅ CEF Python shutdown successfully")
        return True
        
    except Exception as e:
        print(f"❌ CEF Python initialization failed: {e}")
        try:
            import cefpython3 as cef
            cef.Shutdown()
        except:
            pass
        return False

def test_system_dependencies():
    """Test system dependencies for CEF Python."""
    print("\nTesting system dependencies...")
    
    required_libs = [
        'libX11-xcb.so.1',
        'libxcomposite.so.1', 
        'libxdamage.so.1',
        'libxrandr.so.2',
        'libgtk-3.so.0'
    ]
    
    missing_libs = []
    
    for lib in required_libs:
        try:
            import ctypes
            ctypes.CDLL(lib)
            print(f"  ✅ {lib} - Available")
        except OSError:
            print(f"  ❌ {lib} - Missing")
            missing_libs.append(lib)
    
    if missing_libs:
        print(f"\n⚠️  Missing system libraries: {', '.join(missing_libs)}")
        return False
    else:
        print("✅ All required system dependencies available")
        return True

def test_python_dependencies():
    """Test Python dependencies."""
    print("\nTesting Python dependencies...")
    
    deps = {
        'tkinter': 'Standard GUI library',
        'threading': 'Standard threading library',
        'tempfile': 'Standard temporary file library',
        'markdown': 'Markdown processing',
        'bs4': 'BeautifulSoup HTML parsing'
    }
    
    missing_deps = []
    
    for dep, description in deps.items():
        try:
            __import__(dep)
            print(f"  ✅ {dep} - Available ({description})")
        except ImportError:
            print(f"  ❌ {dep} - Missing ({description})")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"\n⚠️  Missing Python dependencies: {', '.join(missing_deps)}")
        return False
    else:
        print("✅ All required Python dependencies available")
        return True

def test_directory_access():
    """Test if we can create temporary files for CEF."""
    print("\nTesting directory access...")
    try:
        import tempfile
        import os
        
        # Test temporary directory access
        temp_dir = tempfile.gettempdir()
        test_file = os.path.join(temp_dir, "cef_test.html")
        
        with open(test_file, 'w') as f:
            f.write("<html><body><h1>CEF Test</h1></body></html>")
        
        print(f"  ✅ Can write to temp directory: {temp_dir}")
        
        # Cleanup
        os.remove(test_file)
        print("  ✅ File cleanup successful")
        return True
        
    except Exception as e:
        print(f"  ❌ Directory access failed: {e}")
        return False

def main():
    """Run all CEF Python tests."""
    print("CEF Python Environment Test")
    print("=" * 50)
    
    tests = [
        ("Python Dependencies", test_python_dependencies),
        ("System Dependencies", test_system_dependencies),
        ("Directory Access", test_directory_access),
        ("CEF Import", test_cef_import),
        ("CEF Initialization", test_cef_initialization),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * (len(test_name) + 1))
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! CEF Python is ready to use.")
        print("\nNext steps:")
        print("1. Run the enhanced renderer test: python test_cef_renderers.py")
        print("2. Integrate CEF into your application")
        print("3. Test HTML/Markdown rendering with CEF")
    else:
        print("❌ Some tests failed. Please address the issues above.")
        print("\nTroubleshooting:")
        print("- Install missing system dependencies with apt-get")
        print("- Install missing Python packages with pip")
        print("- Check file permissions for temporary directories")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
