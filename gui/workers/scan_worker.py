"""
Scan Worker — Async document list fetching in separate thread.
"""

from PyQt6.QtCore import QThread, pyqtSignal
from typing import List, Optional
from gui.widgets.document_list import Document


class ScanWorker(QThread):
    """Worker dla asynchronicznego skanowania listy dokumentów."""

    # Sygnały
    progress = pyqtSignal(int, str)  # progress %, message
    documents_found = pyqtSignal(list)  # List[Document]
    login_required = pyqtSignal()
    error_occurred = pyqtSignal(str)  # error message
    finished_signal = pyqtSignal()

    def __init__(self, portal_id: str, login_required: bool = False):
        super().__init__()
        self.portal_id = portal_id
        self.login_required = login_required
        self._is_running = True

    def run(self):
        """Uruchom skanowanie."""
        try:
            if self.login_required:
                self.progress.emit(0, "Uruchamianie logowania...")
                self.login_required.emit()
                # TODO: Czekaj na zalogowanie

            self.progress.emit(10, "Łączenie z portalem...")
            # TODO: Implementuj rzeczywiste pobieranie z API

            self.progress.emit(50, "Pobieranie listy dokumentów...")
            # TODO: Implementuj rzeczywiste pobieranie

            # Dummy data dla testu
            documents = self._create_dummy_documents()

            self.progress.emit(90, f"Znaleziono {len(documents)} dokumentów...")
            self.documents_found.emit(documents)

            self.progress.emit(100, "Skanowanie ukończone!")
            self.finished_signal.emit()

        except Exception as e:
            self.error_occurred.emit(str(e))

    def _create_dummy_documents(self) -> List[Document]:
        """Utwórz dummy dokumenty dla testowania."""
        # TODO: Usuń gdy będziemy się łączyć z prawdziwym API
        from datetime import datetime, timedelta
        import random

        test_names = [
            "Morfologia", "Elektrolity", "CRP", "Glikemia",
            "Wątroba", "Nerki", "Cholesterol", "APPT",
            "Seria białkowa", "Kwas moczowy", "IGE"
        ]

        documents = []
        date = datetime.now()

        for i in range(20):  # Dummy 20 dokumentów
            doc_date = date - timedelta(days=i)
            doc = Document(
                id=f"doc_{i:03d}",
                date=doc_date.strftime("%Y-%m-%d"),
                name=random.choice(test_names),
                file_type=random.choice(["PDF", "CDA"]),
                size_mb=round(random.uniform(0.5, 10), 1),
                checked=False
            )
            documents.append(doc)

        return documents

    def stop(self):
        """Zatrzymaj worker."""
        self._is_running = False
        self.wait()
