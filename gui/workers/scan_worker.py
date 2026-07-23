"""
Scan Worker — Async document list fetching in separate thread.
"""

from PyQt6.QtCore import QThread, pyqtSignal
from typing import List, Optional
from gui.widgets.document_list import Document
import yaml
from pathlib import Path
from core.logger import get_logger
from core.browser_manager import BrowserManager
from portals.diagnostyka_pl import DiagnostykaPl
from portals.badaj_to import BadajTo


class ScanWorker(QThread):
    """Worker dla asynchronicznego skanowania listy dokumentów."""

    # Sygnały
    progress = pyqtSignal(int, str)  # progress %, message
    documents_found = pyqtSignal(list)  # List[Document]
    login_required = pyqtSignal()
    error_occurred = pyqtSignal(str)  # error message
    finished_signal = pyqtSignal()
    portal_ready = pyqtSignal(object)  # portal instance for later use

    def __init__(self, portal_id: str, login_required: bool = False):
        super().__init__()
        self.portal_id = portal_id
        self.login_required = login_required
        self._is_running = True
        self.config = None
        self.logger = None
        self.browser_manager = None
        self.context = None
        self.page = None

    def _load_config(self):
        """Załaduj konfigurację z settings.yaml."""
        config_path = Path("config/settings.yaml")
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.logger = get_logger("ScanWorker")

    def run(self):
        """Uruchom skanowanie."""
        portal = None
        try:
            self.progress.emit(5, "Ładowanie konfiguracji...")
            self._load_config()

            # Check if portal is enabled
            portal_config = self.config.get("portals", {}).get(self.portal_id, {})
            if not portal_config.get("enabled", False):
                self.error_occurred.emit(f"Portal {self.portal_id} jest wyłączony w konfiguracji")
                return

            self.progress.emit(10, "Uruchamianie przeglądarki...")
            self.browser_manager = BrowserManager(self.config, self.logger)
            self.context, self.page = self.browser_manager.launch_pwa()

            # Create portal adapter based on type
            if self.portal_id == "diagnostyka_pl":
                portal = DiagnostykaPl(self.page, portal_config,
                                      self.config["paths"]["downloads"],
                                      self.logger)
            elif self.portal_id == "badaj_to":
                portal = BadajTo(self.page, portal_config,
                               self.config["paths"]["downloads"],
                               self.logger)
            else:
                self.error_occurred.emit(f"Nieznany portal: {self.portal_id}")
                return

            self.progress.emit(20, "Czekam na zalogowanie...")
            if not portal.wait_for_login():
                self.error_occurred.emit("Nie udało się zalogować — timeout")
                return

            self.progress.emit(50, "Pobieranie listy dokumentów...")
            portal_documents = portal.fetch_document_list()

            if not portal_documents:
                self.progress.emit(80, "Brak dokumentów do pobrania")
                self.documents_found.emit([])
            else:
                self.progress.emit(80, f"Znaleziono {len(portal_documents)} dokumentów...")

                # Convert PortalDocument to GUI Document
                gui_documents = self._convert_portal_documents(portal_documents)
                self.documents_found.emit(gui_documents)

            # Wyślij portal instance żeby LabTab mógł go użyć do pobierania
            self.portal_ready.emit(portal)

            self.progress.emit(100, "Skanowanie ukończone!")
            self.finished_signal.emit()

        except Exception as e:
            if self.logger:
                self.logger.exception(f"Błąd w ScanWorker: {e}")
            self.error_occurred.emit(f"Błąd: {str(e)}")
            # Zamknij browser tylko jeśli było błąd
            if self.browser_manager:
                try:
                    self.browser_manager.close()
                except:
                    pass

    def _convert_portal_documents(self, portal_docs) -> List[Document]:
        """Konwertuj PortalDocument na GUI Document."""
        gui_docs = []
        for pdoc in portal_docs:
            doc = Document(
                id=str(pdoc.portal_document_id),
                date=pdoc.document_date or "unknown",
                name=pdoc.document_name or "Unknown",
                file_type=pdoc.file_type or "PDF",
                size_mb=pdoc.size_mb or 0.0,
                checked=False
            )
            gui_docs.append(doc)
        return gui_docs

    def stop(self):
        """Zatrzymaj worker."""
        self._is_running = False
        if self.browser_manager:
            try:
                self.browser_manager.close()
            except:
                pass
        self.wait()
