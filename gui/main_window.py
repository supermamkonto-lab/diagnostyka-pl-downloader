"""
Main Window — Medical Data Collector GUI Application
Multi-lab interface with tabs for each laboratory.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QStatusBar
)
from PyQt6.QtGui import QIcon, QFont, QColor
from PyQt6.QtCore import Qt, QSize

from gui.styles import get_stylesheet
from gui.tabs.lab_tab import LabTab


class MainWindow(QMainWindow):
    """Główne okno aplikacji."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Medical Data Collector — Multi-Lab")
        self.setGeometry(100, 100, 1366, 768)  # Domyślnie HD, ale responsywne
        self.setMinimumSize(1200, 600)

        # Apply dark mode stylesheet
        self.setStyleSheet(get_stylesheet())

        # Inicjalizuj UI
        self.init_ui()

    def init_ui(self):
        """Inicjalizuj interfejs użytkownika."""
        # Główny widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header z tytułem
        header_layout = QHBoxLayout()
        title_label = QLabel("Medical Data Collector")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #14919b;")

        version_label = QLabel("v1.0 — Multi-Lab Edition")
        version_label.setStyleSheet("color: #808080; font-size: 11px;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(version_label)

        layout.addLayout(header_layout)

        # Separator
        separator = QLabel()
        separator.setStyleSheet("background-color: #3a3a3a; height: 1px;")
        layout.addWidget(separator)

        # Tab Widget — dla każdego laboratorium
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Utwórz tab dla Diagnostyki.pl
        self.diag_tab = LabTab(
            lab_name="Diagnostyka.pl",
            portal_id="diagnostyka_pl",
            total_files=166,
            parent=self
        )
        self.tabs.addTab(self.diag_tab, "📋 Diagnostyka.pl")

        # Utwórz tab dla Badaj.to
        self.badaj_tab = LabTab(
            lab_name="Badaj.to",
            portal_id="badaj_to",
            total_files=50,
            parent=self
        )
        self.tabs.addTab(self.badaj_tab, "📋 Badaj.to")

        layout.addWidget(self.tabs)

        # Footer — status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status("Gotów")

        # Set central widget layout
        central_widget.setLayout(layout)

        # Ustaw rozmiar okna
        self.resize(1366, 768)

    def update_status(self, message: str):
        """Zaktualizuj status bar."""
        self.status_bar.showMessage(f"🟢 {message}")

    def closeEvent(self, event):
        """Obsługuj zamknięcie okna."""
        # TODO: Pytaj jeśli pobieranie w toku
        event.accept()
