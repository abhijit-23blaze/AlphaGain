#!/usr/bin/env python3
"""
Script to inspect the Agno package structure
"""

import agno
import sys

def inspect_module(module):
    print(f"\nModule: {module.__name__}")
    print("=" * 50)
    print(f"Dir: {dir(module)}")
    print("-" * 50)
    
    # Try to check if Agent exists in different possible locations
    try:
        if hasattr(module, 'agent'):
            print("Agent module exists!")
            submodule = getattr(module, 'agent')
            print(f"Dir of agent submodule: {dir(submodule)}")
            if hasattr(submodule, 'Agent'):
                print("Agent class found in module.agent!")
    except Exception as e:
        print(f"Error checking agent module: {e}")
    
    # Try other possible locations
    possible_locations = ['Agent', 'agents', 'client', 'core']
    for loc in possible_locations:
        try:
            if hasattr(module, loc):
                submodule = getattr(module, loc)
                print(f"\nFound: {loc}")
                print(f"Dir: {dir(submodule)}")
        except Exception as e:
            print(f"Error checking {loc}: {e}")

    # Print version info if available
    if hasattr(module, '__version__'):
        print(f"\nVersion: {module.__version__}")

if __name__ == "__main__":
    inspect_module(agno) 