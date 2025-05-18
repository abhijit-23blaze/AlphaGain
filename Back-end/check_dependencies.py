#!/usr/bin/env python3
"""
Utility script to check if all dependencies are properly installed.
Run this script to verify that your environment is set up correctly.
"""

import importlib
import sys

def check_module(module_name):
    try:
        module = importlib.import_module(module_name)
        print(f"✅ {module_name} installed successfully")
        if hasattr(module, '__version__'):
            print(f"   Version: {module.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import {module_name}: {str(e)}")
        return False

def main():
    print("\n=== Checking dependencies ===\n")
    
    required_modules = [
        "fastapi",
        "uvicorn",
        "dotenv",
        "agno",
        "google.generativeai",
        "websockets",
        "pydantic",
        "httpx"
    ]
    
    all_installed = True
    missing_modules = []
    
    # Special case for python-dotenv
    try:
        import dotenv
        print(f"✅ python-dotenv installed successfully")
        if hasattr(dotenv, '__version__'):
            print(f"   Version: {dotenv.__version__}")
    except ImportError:
        print(f"❌ Failed to import python-dotenv")
        all_installed = False
        missing_modules.append("python-dotenv")
    
    # Check other modules
    for module in required_modules:
        if module != "dotenv":  # Skip dotenv as we already handled it
            if not check_module(module):
                all_installed = False
                missing_modules.append(module)
    
    print("\n=== Summary ===\n")
    
    if all_installed:
        print("🎉 All dependencies are installed correctly!")
    else:
        print("❗ Some dependencies are missing:")
        for module in missing_modules:
            print(f"  - {module}")
        print("\nTry running: pip install -r requirements.txt")
    
    # Check for Agno version
    try:
        import agno
        print(f"\nAgno version: {agno.__version__}")
        # Check for compatibility with v1.5.1
        if agno.__version__ != "1.5.1":
            print("\n⚠️  Warning: You are using Agno version {agno.__version__}, but this project was built with version 1.5.1.")
            print("   You may need to adapt the code if there are API changes.")
    except (ImportError, AttributeError):
        pass

if __name__ == "__main__":
    main() 