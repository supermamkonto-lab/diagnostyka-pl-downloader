#!/usr/bin/env python3
"""
Medical Data Collector — Multi-Lab GUI Application
PyQt6-based desktop application for managing downloads from multiple medical laboratories.
"""

import sys
from pathlib import Path

# Dodaj bieżący katalog do sys.path aby móc importować moduły
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    """Uruchom aplikację GUI."""
    app = QApplication(sys.argv)

    # Ustaw style aplikacji
    app.setStyle('Fusion')

    # Utwórz i pokaż główne okno
    window = MainWindow()
    window.show()

    # Uruchom event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
