"""Abstract base class for all portal adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from playwright.sync_api import Page


@dataclass
class PortalDocument:
    portal_document_id: str
    document_name: str
    document_date: Optional[str]
    document_type: Optional[str]
    download_url: Optional[str] = None
    metadata: Optional[dict] = None


class BasePortal(ABC):
    PORTAL_ID: str = ""

    def __init__(self, page: Page, config: dict, download_dir: str, logger):
        self.page = page
        self.config = config
        self.download_dir = download_dir
        self.log = logger

    @abstractmethod
    def wait_for_login(self) -> bool:
        """Block until user completes login. Return True when logged in."""

    @abstractmethod
    def get_auth_token(self) -> Optional[str]:
        """Extract Bearer token or session cookie after login."""

    @abstractmethod
    def fetch_document_list(self) -> list[PortalDocument]:
        """Return complete list of documents available on portal."""

    @abstractmethod
    def download_document(self, doc: PortalDocument) -> Optional[str]:
        """Download single document. Return local file path or None on failure."""
