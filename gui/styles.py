"""
Dark Mode Stylesheet for PyQt6 Medical Data Collector
Minimalist, professional design inspired by modern medical portals.
"""

DARK_STYLESHEET = """
/* Main window and base colors */
QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
}

QMainWindow {
    background-color: #1e1e1e;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #3a3a3a;
    background-color: #252525;
}

QTabBar::tab {
    background-color: #2d2d2d;
    color: #a0a0a0;
    padding: 8px 20px;
    margin-right: 2px;
    border: 1px solid #3a3a3a;
    border-bottom: none;
}

QTabBar::tab:selected {
    background-color: #0d7377;
    color: #ffffff;
    font-weight: bold;
    border: 1px solid #0d7377;
    border-bottom: 3px solid #14919b;
}

QTabBar::tab:hover {
    background-color: #323232;
}

/* Buttons */
QPushButton {
    background-color: #0d7377;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 11px;
}

QPushButton:hover {
    background-color: #14919b;
}

QPushButton:pressed {
    background-color: #0a5a63;
}

QPushButton:disabled {
    background-color: #3a3a3a;
    color: #707070;
}

/* Primary Button (Download) */
QPushButton#primaryButton {
    background-color: #14919b;
    font-weight: bold;
    padding: 10px 20px;
    font-size: 12px;
}

QPushButton#primaryButton:hover {
    background-color: #1ab3be;
}

/* Secondary Button */
QPushButton#secondaryButton {
    background-color: #3a3a3a;
    color: #e0e0e0;
}

QPushButton#secondaryButton:hover {
    background-color: #4a4a4a;
}

/* Danger Button */
QPushButton#dangerButton {
    background-color: #d32f2f;
}

QPushButton#dangerButton:hover {
    background-color: #f44336;
}

/* Line Edit / Input Fields */
QLineEdit {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 11px;
}

QLineEdit:focus {
    border: 2px solid #0d7377;
    background-color: #323232;
}

/* Combo Box */
QComboBox {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    padding: 6px 10px;
}

QComboBox:focus {
    border: 2px solid #0d7377;
}

QComboBox::drop-down {
    border: none;
}

QComboBox::down-arrow {
    image: url(none);
}

QAbstractItemView {
    background-color: #252525;
    color: #e0e0e0;
    border: 1px solid #3a3a3a;
    selection-background-color: #0d7377;
}

/* Checkbox */
QCheckBox {
    color: #e0e0e0;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 3px;
    border: 1px solid #3a3a3a;
    background-color: #2d2d2d;
}

QCheckBox::indicator:checked {
    background-color: #0d7377;
    border: 1px solid #0d7377;
}

/* Labels */
QLabel {
    color: #e0e0e0;
}

QLabel#titleLabel {
    font-size: 14px;
    font-weight: bold;
    color: #14919b;
}

QLabel#statusLabel {
    font-size: 12px;
    color: #a0a0a0;
}

QLabel#statsLabel {
    font-size: 11px;
    color: #808080;
}

/* Progress Bar */
QProgressBar {
    background-color: #2d2d2d;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    text-align: center;
    color: #e0e0e0;
    height: 24px;
}

QProgressBar::chunk {
    background-color: #0d7377;
    border-radius: 3px;
}

/* Table Widget */
QTableWidget {
    background-color: #252525;
    gridline-color: #3a3a3a;
    border: 1px solid #3a3a3a;
}

QTableWidget::item {
    padding: 4px;
    border: none;
    background-color: #252525;
    color: #e0e0e0;
}

QTableWidget::item:selected {
    background-color: #0d7377;
    color: #ffffff;
}

QTableWidget::item:hover {
    background-color: #323232;
}

QHeaderView::section {
    background-color: #2d2d2d;
    color: #e0e0e0;
    padding: 6px;
    border: none;
    border-right: 1px solid #3a3a3a;
    font-weight: bold;
    font-size: 11px;
}

/* Tree Widget */
QTreeWidget {
    background-color: #252525;
    gridline-color: #3a3a3a;
    border: 1px solid #3a3a3a;
}

QTreeWidget::item {
    padding: 4px 0px;
    border: none;
    background-color: #252525;
    color: #e0e0e0;
}

QTreeWidget::item:selected {
    background-color: #0d7377;
    color: #ffffff;
}

QTreeWidget::item:hover {
    background-color: #323232;
}

/* Scroll Bar */
QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 12px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #3a3a3a;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4a4a4a;
}

QScrollBar:horizontal {
    background-color: #1e1e1e;
    height: 12px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #3a3a3a;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #4a4a4a;
}

/* Group Box */
QGroupBox {
    color: #e0e0e0;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px 0 3px;
}

/* Frames */
QFrame {
    background-color: #1e1e1e;
    border: none;
}

QFrame#contentFrame {
    background-color: #252525;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
}

/* Status Bar */
QStatusBar {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border-top: 1px solid #3a3a3a;
}

/* Menu Bar */
QMenuBar {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border-bottom: 1px solid #3a3a3a;
}

QMenuBar::item:selected {
    background-color: #0d7377;
}

/* Menu */
QMenu {
    background-color: #252525;
    color: #e0e0e0;
    border: 1px solid #3a3a3a;
}

QMenu::item:selected {
    background-color: #0d7377;
}

/* Dialogs */
QDialog {
    background-color: #1e1e1e;
}

QFileDialog {
    background-color: #1e1e1e;
}
"""


def get_stylesheet():
    """Zwróć dark mode stylesheet."""
    return DARK_STYLESHEET
