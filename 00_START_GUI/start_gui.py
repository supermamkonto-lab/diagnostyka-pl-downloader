#!/usr/bin/env python3
"""
Medical Data Collector GUI Launcher
Starts the desktop application for managing medical document downloads.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import the app
app_root = Path(__file__).parent.parent
sys.path.insert(0, str(app_root))

if __name__ == '__main__':
    try:
        print("=" * 60)
        print("Medical Data Collector — GUI Application")
        print("=" * 60)
        print()

        # Import and run the GUI app
        from gui_app import main
        sys.exit(main())

    except ImportError as e:
        print(f"❌ ERROR: Failed to import GUI application")
        print(f"   {e}")
        print()
        print("Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
