#!/usr/bin/env python3
"""
Test script to verify imports in file_service.py work correctly
"""

import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from api.app.services import file_service
    print("✅ Successfully imported file_service")
    
    # Test if PyMuPDF is available
    if hasattr(file_service, 'HAS_PYMUPDF'):
        if file_service.HAS_PYMUPDF:
            print("✅ PyMuPDF is available - PDF processing enabled")
        else:
            print("⚠️  PyMuPDF is not available - PDF processing disabled")
    
    # Test other imports
    print("✅ All imports successful")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)

print("🎉 Import test completed successfully!")
