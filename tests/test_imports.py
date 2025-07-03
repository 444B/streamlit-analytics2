# test_imports.py - Test that all modules import correctly
"""
Quick test to ensure all streamlit-analytics2 modules import correctly
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    print("Testing imports...")
    
    # Test main import
    import streamlit_analytics2 as sa2
    print("✓ Main package imported")
    
    # Test submodules
    from streamlit_analytics2 import main
    print("✓ main module imported")
    
    from streamlit_analytics2 import display
    print("✓ display module imported")
    
    from streamlit_analytics2 import config
    print("✓ config module imported")
    
    from streamlit_analytics2 import storage
    print("✓ storage module imported")
    
    from streamlit_analytics2 import state
    print("✓ state module imported")
    
    # Test functions exist
    assert hasattr(display, 'show_results'), "display.show_results not found"
    print("✓ display.show_results exists")
    
    assert hasattr(config, 'show_config'), "config.show_config not found"
    print("✓ config.show_config exists")
    
    # Test track function
    assert hasattr(sa2, 'track'), "track function not found"
    print("✓ track function exists")
    
    print("\nAll imports successful! ✨")
    
except Exception as e:
    print(f"\n❌ Import error: {str(e)}")
    import traceback
    traceback.print_exc()