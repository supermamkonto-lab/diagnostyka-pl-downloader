"""
Download Worker — Async file downloading in separate thread with progress tracking.
"""

from PyQt6.QtCore import QThread, pyqtSignal
from typing import List, Optional, Any
from gui.widgets.document_list import Document
from pathlib import Path
import time


class DownloadWorker(QThread):
    """Worker dla asynchronicznego pobierania plików."""

    # Sygnały
    progress = pyqtSignal(int)  # Overall progress %
    current_file = pyqtSignal(str, float, float)  # filename, current_mb, total_mb
    file_completed = pyqtSignal(str, bool)  # filename, success
    speed_updated = pyqtSignal(float, int)  # speed_mbps, eta_seconds
    error_occurred = pyqtSignal(str)  # error message
    finished_signal = pyqtSignal(int, int)  # completed_count, failed_count

    def __init__(self, documents: List[Document], download_folder: str,
                 portal_id: str, portal_instance: Any = None,
                 portal_documents: List[Any] = None):
        super().__init__()
        self.documents = documents
        self.download_folder = download_folder
        self.portal_id = portal_id
        self.portal = portal_instance
        self.portal_documents = portal_documents or []
        self._is_running = True

    def run(self):
        """Uruchom pobieranie."""
        completed = 0
        failed = 0

        try:
            # Ensure download folder exists
            download_path = Path(self.download_folder).expanduser()
            download_path.mkdir(parents=True, exist_ok=True)

            total = len(self.documents)

            # Build mapping of document IDs to portal documents
            doc_map = {str(pdoc.portal_document_id): pdoc for pdoc in self.portal_documents}

            for idx, gui_doc in enumerate(self.documents):
                if not self._is_running:
                    break

                progress_pct = int((idx / total) * 100)
                self.progress.emit(progress_pct)

                # Pobierz odpowiadający portal dokument
                portal_doc = doc_map.get(gui_doc.id)
                if not portal_doc:
                    self.file_completed.emit(gui_doc.name, False)
                    failed += 1
                    continue

                success = self._download_file(gui_doc, portal_doc, idx + 1, total)

                if success:
                    completed += 1
                    self.file_completed.emit(gui_doc.name, True)
                else:
                    failed += 1
                    self.file_completed.emit(gui_doc.name, False)

            self.progress.emit(100)
            self.finished_signal.emit(completed, failed)

        except Exception as e:
            self.error_occurred.emit(str(e))

    def _download_file(self, gui_doc: Document, portal_doc: Any, current: int, total: int) -> bool:
        """Pobierz pojedynczy plik."""
        try:
            filename = gui_doc.name

            if not self.portal:
                # Jeśli brak portalu, symuluj
                self.current_file.emit(filename, 0, gui_doc.size_mb)
                time.sleep(0.3)
                self.current_file.emit(filename, gui_doc.size_mb, gui_doc.size_mb)
                self.speed_updated.emit(10.0, 0)
                return True

            # Użyj prawdziwego portalu do pobrania
            self.current_file.emit(filename, 0, gui_doc.size_mb)

            start_time = time.time()
            result = self.portal.download_document(portal_doc)
            elapsed = time.time() - start_time

            if result:
                self.current_file.emit(filename, gui_doc.size_mb, gui_doc.size_mb)
                speed = gui_doc.size_mb / max(elapsed, 0.1) if elapsed > 0 else 0
                self.speed_updated.emit(speed, 0)
                return True
            else:
                return False

        except Exception as e:
            self.error_occurred.emit(f"Błąd pobierania {gui_doc.name}: {str(e)}")
            return False

    def stop(self):
        """Zatrzymaj worker."""
        self._is_running = False
        self.wait()
