"""
Laboratory Tab — Document list, filtering, selection, and download interface.
This is the main UI for each laboratory.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QCheckBox, QFileDialog, QProgressBar, QScrollArea,
    QFrame, QSpinBox, QComboBox, QMessageBox, QDateEdit
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QThread

from pathlib import Path
from datetime import datetime, timedelta

from gui.workers.scan_worker import ScanWorker
from gui.workers.download_worker import DownloadWorker
from gui.widgets.document_list import DocumentListWidget


class LabTab(QWidget):
    """Tab dla pojedynczego laboratorium."""

    # Sygnały
    status_changed = pyqtSignal(str)
    progress_updated = pyqtSignal(int, str)

    def __init__(self, lab_name: str, portal_id: str, total_files: int, parent=None):
        super().__init__(parent)
        self.lab_name = lab_name
        self.portal_id = portal_id
        self.total_files = total_files
        self.parent_window = parent

        self.selected_documents = []
        self.download_folder = str(Path.home() / "Downloads")
        self.portal_instance = None
        self.portal_documents = []

        self.init_ui()

    def init_ui(self):
        """Inicjalizuj interfejs tabu."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # ===== STATUS BAR =====
        status_frame = QFrame()
        status_frame.setObjectName("contentFrame")
        status_layout = QHBoxLayout()

        self.status_label = QLabel("🔴 Nie zalogowany")
        self.status_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")

        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        status_frame.setLayout(status_layout)
        main_layout.addWidget(status_frame)

        # ===== TOOLBAR — Login, Scan, Settings =====
        toolbar_layout = QHBoxLayout()

        self.login_btn = QPushButton("🔐 Zaloguj")
        self.login_btn.setObjectName("primaryButton")
        self.login_btn.clicked.connect(self.on_login)

        self.scan_btn = QPushButton("🔍 Skanuj")
        self.scan_btn.setEnabled(False)
        self.scan_btn.clicked.connect(self.on_scan)

        self.settings_btn = QPushButton("⚙️ Ustawienia")
        self.settings_btn.clicked.connect(self.on_settings)

        toolbar_layout.addWidget(self.login_btn)
        toolbar_layout.addWidget(self.scan_btn)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.settings_btn)

        main_layout.addLayout(toolbar_layout)

        # ===== FILTERS =====
        filter_frame = QFrame()
        filter_frame.setObjectName("contentFrame")
        filter_layout = QHBoxLayout()

        # Filtrowanie po dacie
        filter_layout.addWidget(QLabel("Filtruj od:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        filter_layout.addWidget(self.date_from)

        filter_layout.addWidget(QLabel("do:"))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        filter_layout.addWidget(self.date_to)

        # Filtrowanie po typie badania
        filter_layout.addWidget(QLabel("Typ badania:"))
        self.type_filter = QLineEdit()
        self.type_filter.setPlaceholderText("np. CRP, Morfologia...")
        self.type_filter.textChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.type_filter)

        filter_layout.addWidget(QLabel("Wyszukaj:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Szukaj...")
        self.search_input.textChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.search_input)

        filter_layout.addStretch()

        filter_frame.setLayout(filter_layout)
        main_layout.addWidget(filter_frame)

        # ===== DOCUMENT LIST =====
        self.doc_list = DocumentListWidget()
        main_layout.addWidget(self.doc_list, 1)  # Zajmuj najwidęcej miejsca

        # ===== SELECTION STATS =====
        stats_layout = QHBoxLayout()

        self.stats_label = QLabel("Zaznaczono: 0/0 plików | Rozmiar: 0 MB")
        self.stats_label.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        stats_layout.addWidget(self.stats_label)

        # Quick selection buttons
        stats_layout.addStretch()
        select_all_btn = QPushButton("Zaznacz wszystko")
        select_all_btn.setObjectName("secondaryButton")
        select_all_btn.clicked.connect(self.on_select_all)
        stats_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Odznacz wszystko")
        deselect_all_btn.setObjectName("secondaryButton")
        deselect_all_btn.clicked.connect(self.on_deselect_all)
        stats_layout.addWidget(deselect_all_btn)

        main_layout.addLayout(stats_layout)

        # ===== FOLDER SELECTION =====
        folder_frame = QFrame()
        folder_frame.setObjectName("contentFrame")
        folder_layout = QHBoxLayout()

        folder_layout.addWidget(QLabel("Pobierz do:"))
        self.folder_label = QLineEdit()
        self.folder_label.setReadOnly(True)
        self.folder_label.setText(self.download_folder)
        folder_layout.addWidget(self.folder_label)

        browse_btn = QPushButton("📂 Przeglądaj...")
        browse_btn.clicked.connect(self.on_browse_folder)
        folder_layout.addWidget(browse_btn)

        folder_frame.setLayout(folder_layout)
        main_layout.addWidget(folder_frame)

        # ===== PROGRESS BAR =====
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_label = QLabel("Gotów")
        self.progress_label.setStyleSheet("color: #a0a0a0; font-size: 10px;")

        progress_layout = QVBoxLayout()
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        main_layout.addLayout(progress_layout)

        # ===== BUTTONS — Download, etc =====
        buttons_layout = QHBoxLayout()

        self.download_btn = QPushButton("⬇️ POBIERZ ZAZNACZONE")
        self.download_btn.setObjectName("primaryButton")
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self.on_download)
        self.download_btn.setMinimumHeight(40)

        self.cancel_btn = QPushButton("Anuluj")
        self.cancel_btn.setObjectName("dangerButton")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.on_cancel)

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.download_btn, 2)
        buttons_layout.addWidget(self.cancel_btn)

        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

        # Workers
        self.scan_worker = None
        self.download_worker = None

    def on_login(self):
        """Obsługuj logowanie."""
        self.login_btn.setEnabled(False)
        self.login_btn.setText("⏳ Logowanie...")
        self.status_label.setText("🟡 Logowanie...")
        self.status_label.setStyleSheet("color: #ffb81c;")

        self._start_scan(login_required=True)

    def on_scan(self):
        """Obsługuj skanowanie listy dokumentów."""
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("⏳ Skanowanie...")
        self._start_scan(login_required=False)

    def _start_scan(self, login_required: bool = False):
        """Uruchom ScanWorker."""
        if self.scan_worker and self.scan_worker.isRunning():
            return

        self.scan_worker = ScanWorker(self.portal_id, login_required)
        self.scan_worker.progress.connect(self._on_scan_progress)
        self.scan_worker.documents_found.connect(self._on_documents_found)
        self.scan_worker.error_occurred.connect(self._on_scan_error)
        self.scan_worker.finished_signal.connect(self._on_scan_finished)
        self.scan_worker.portal_ready.connect(self._on_portal_ready)
        self.scan_worker.start()

    def _on_scan_progress(self, pct: int, msg: str):
        """Odbierz progress ze skanowania."""
        self.progress_bar.setValue(pct)
        self.progress_label.setText(msg)

    def _on_documents_found(self, documents):
        """Odbierz listę dokumentów."""
        self.doc_list.clear_documents()
        self.doc_list.add_documents(documents)
        self.portal_documents = documents
        self.update_stats()

    def _on_scan_error(self, error_msg: str):
        """Obsługuj błąd skanowania."""
        self.progress_label.setText(f"❌ Błąd: {error_msg}")
        self.status_label.setText(f"🔴 Błąd: {error_msg[:50]}...")
        self.status_label.setStyleSheet("color: #ff6b6b;")
        self.login_btn.setEnabled(True)
        self.login_btn.setText("🔐 Zaloguj")
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("🔍 Skanuj")

    def _on_portal_ready(self, portal_instance):
        """Odbierz portal instance ze ScanWorkera."""
        self.portal_instance = portal_instance

    def _on_scan_finished(self):
        """Obsługuj koniec skanowania."""
        self.set_logged_in()
        self.progress_bar.setValue(100)
        self.progress_label.setText("Skanowanie ukończone!")
        self.scan_btn.setText("🔍 Skanuj")
        self.scan_btn.setEnabled(True)

    def on_filter_changed(self):
        """Obsługuj zmianę filtrów."""
        # TODO: Filtruj listę dokumentów
        pass

    def on_select_all(self):
        """Zaznacz wszystkie dokumenty."""
        self.doc_list.select_all()
        self.update_stats()

    def on_deselect_all(self):
        """Odznacz wszystkie dokumenty."""
        self.doc_list.deselect_all()
        self.update_stats()

    def on_browse_folder(self):
        """Otwórz dialog wyboru folderu."""
        folder = QFileDialog.getExistingDirectory(
            self,
            f"Wybierz folder dla {self.lab_name}",
            self.download_folder
        )
        if folder:
            self.download_folder = folder
            self.folder_label.setText(folder)

    def on_download(self):
        """Uruchom pobieranie zaznaczonych dokumentów."""
        # Pobierz zaznaczone dokumenty
        selected = self.doc_list.get_selected()
        if not selected:
            QMessageBox.warning(self, "Brak zaznaczenia", "Zaznacz przynajmniej jeden plik!")
            return

        if not self.portal_instance:
            QMessageBox.warning(self, "Błąd", "Brak połączenia z portalem. Spróbuj zalogować się ponownie.")
            return

        self.download_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Rozpoczynanie pobierania...")

        self.download_worker = DownloadWorker(
            selected,
            self.download_folder,
            self.portal_id,
            self.portal_instance,
            self.portal_documents
        )

        self.download_worker.progress.connect(self._on_download_progress)
        self.download_worker.current_file.connect(self._on_current_file)
        self.download_worker.file_completed.connect(self._on_file_completed)
        self.download_worker.speed_updated.connect(self._on_speed_updated)
        self.download_worker.error_occurred.connect(self._on_download_error)
        self.download_worker.finished_signal.connect(self._on_download_finished)
        self.download_worker.start()

    def on_cancel(self):
        """Anuluj pobieranie."""
        if self.download_worker:
            self.download_worker.stop()
        self.cancel_btn.setEnabled(False)
        self.progress_label.setText("Anulowano")

    def _on_download_progress(self, pct: int):
        """Odbierz progress pobierania."""
        self.progress_bar.setValue(pct)

    def _on_current_file(self, filename: str, current_mb: float, total_mb: float):
        """Odbierz info o bieżącym pliku."""
        if total_mb > 0:
            pct = int((current_mb / total_mb) * 100)
            self.progress_label.setText(f"{filename} ({current_mb:.1f}/{total_mb:.1f} MB)")
        else:
            self.progress_label.setText(f"{filename}")

    def _on_file_completed(self, filename: str, success: bool):
        """Odbierz informację o ukończeniu pobierania pliku."""
        status = "✓" if success else "✗"
        self.progress_label.setText(f"{status} {filename}")

    def _on_speed_updated(self, speed_mbps: float, eta_seconds: int):
        """Odbierz update prędkości i ETA."""
        if eta_seconds > 0:
            eta_str = f"{eta_seconds}s" if eta_seconds < 60 else f"{eta_seconds // 60}m"
            self.progress_label.setText(f"Prędkość: {speed_mbps:.1f} MB/s | ETA: {eta_str}")

    def _on_download_error(self, error_msg: str):
        """Obsługuj błąd pobierania."""
        self.progress_label.setText(f"❌ Błąd: {error_msg}")
        QMessageBox.warning(self, "Błąd pobierania", error_msg)

    def _on_download_finished(self, completed: int, failed: int):
        """Obsługuj koniec pobierania."""
        self.progress_bar.setValue(100)
        self.download_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

        total = completed + failed
        msg = f"Ukończone! {completed}/{total} plików pobranych pomyślnie."
        self.progress_label.setText(msg)

        if failed > 0:
            QMessageBox.information(self, "Pobieranie ukończone",
                                  f"{completed} plików pobranych.\n{failed} błędów.")
        else:
            QMessageBox.information(self, "Powodzenie", msg)

    def on_settings(self):
        """Otwórz ustawienia."""
        # TODO: Dialog ustawień
        pass

    def update_stats(self):
        """Zaktualizuj statystyki zaznaczenia."""
        selected = self.doc_list.get_selected_count()
        total = self.doc_list.get_total_count()
        size = self.doc_list.get_selected_size()

        self.stats_label.setText(
            f"Zaznaczono: {selected}/{total} plików | Rozmiar: {size:.1f} MB"
        )
        self.download_btn.setEnabled(selected > 0)

    def set_logged_in(self):
        """Oznacz że jest zalogowany."""
        self.status_label.setText("🟢 Zalogowany")
        self.status_label.setStyleSheet("color: #51cf66; font-weight: bold;")
        self.login_btn.setEnabled(True)
        self.login_btn.setText("🔐 Zaloguj Ponownie")
        self.scan_btn.setEnabled(True)
