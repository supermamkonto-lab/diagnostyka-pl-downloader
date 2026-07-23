"""
Download Worker — Async file downloading in separate thread with progress tracking.
"""

from PyQt6.QtCore import QThread, pyqtSignal
from typing import List, Optional
from gui.widgets.document_list import Document
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

    def __init__(self, documents: List[Document], download_folder: str, portal_id: str):
        super().__init__()
        self.documents = documents
        self.download_folder = download_folder
        self.portal_id = portal_id
        self._is_running = True

    def run(self):
        """Uruchom pobieranie."""
        completed = 0
        failed = 0

        try:
            total = len(self.documents)

            for idx, doc in enumerate(self.documents):
                if not self._is_running:
                    break

                progress_pct = int((idx / total) * 100)
                self.progress.emit(progress_pct)

                # Symuluj pobieranie
                success = self._download_file(doc, idx + 1, total)

                if success:
                    completed += 1
                    self.file_completed.emit(f"{doc.date}_{doc.name}.{doc.file_type}", True)
                else:
                    failed += 1
                    self.file_completed.emit(f"{doc.date}_{doc.name}.{doc.file_type}", False)

            self.progress.emit(100)
            self.finished_signal.emit(completed, failed)

        except Exception as e:
            self.error_occurred.emit(str(e))

    def _download_file(self, doc: Document, current: int, total: int) -> bool:
        """Pobierz pojedynczy plik."""
        try:
            filename = f"{doc.date}_{doc.name}.{doc.file_type}"
            self.current_file.emit(filename, 0, doc.size_mb)

            # Symuluj pobieranie z progresem
            chunks = 10
            for chunk in range(chunks):
                if not self._is_running:
                    return False

                # Symuluj pobieranie
                time.sleep(0.2)
                downloaded_mb = (chunk + 1) / chunks * doc.size_mb
                self.current_file.emit(filename, downloaded_mb, doc.size_mb)

                # Symuluj prędkość pobierania
                speed = doc.size_mb / (chunks * 0.2) * (chunk + 1) / chunks
                eta = int((doc.size_mb - downloaded_mb) / max(speed, 0.1))
                self.speed_updated.emit(speed, eta)

            return True

        except Exception as e:
            self.error_occurred.emit(f"Błąd pobierania {doc.name}: {str(e)}")
            return False

    def stop(self):
        """Zatrzymaj worker."""
        self._is_running = False
        self.wait()
