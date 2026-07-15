"""MASTER_LAB_DATABASE updater — delta import of downloaded documents."""

from pathlib import Path
from typing import Optional
from database.models import get_connection
from database.delta_manager import DeltaManager


class DatabaseUpdater:
    """
    Imports downloaded (and optionally OCR'd) documents into MASTER_LAB_DATABASE.
    MASTER_LAB_DATABASE path is read from config; this class only appends — never deletes.
    """

    def __init__(self, config: dict, delta: DeltaManager, logger):
        self.config = config
        self.delta = delta
        self.log = logger
        self._master_db = config.get("paths", {}).get("master_lab_db")

    def import_pending(self, portal_id: str) -> int:
        """Import all downloaded-but-not-yet-imported documents. Returns count imported."""
        if not self._master_db:
            self.log.warning("master_lab_db not configured — skipping import")
            return 0

        conn = get_connection(self.delta.db_path)
        rows = conn.execute(
            """SELECT * FROM documents
               WHERE portal_id = ? AND downloaded = 1 AND master_imported = 0""",
            (portal_id,)
        ).fetchall()
        conn.close()

        imported = 0
        for row in rows:
            doc = dict(row)
            if self._import_document(doc):
                self._mark_imported(doc["portal_id"], doc["portal_document_id"])
                imported += 1

        self.log.info(f"Imported {imported} documents into MASTER_LAB_DATABASE")
        return imported

    def _import_document(self, doc: dict) -> bool:
        """
        Write document metadata into MASTER_LAB_DATABASE.
        Schema will be extended once MASTER_LAB_DATABASE structure is defined.
        """
        try:
            master_conn = get_connection(self._master_db)
            master_conn.execute(
                """CREATE TABLE IF NOT EXISTS lab_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_portal TEXT,
                    portal_document_id TEXT,
                    document_date TEXT,
                    document_name TEXT,
                    document_type TEXT,
                    file_path TEXT,
                    file_hash TEXT,
                    ocr_text_path TEXT,
                    imported_at TEXT DEFAULT (datetime('now')),
                    UNIQUE(source_portal, portal_document_id)
                )"""
            )
            master_conn.execute(
                """INSERT OR IGNORE INTO lab_documents
                   (source_portal, portal_document_id, document_date, document_name,
                    document_type, file_path, file_hash, ocr_text_path)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (doc["portal_id"], doc["portal_document_id"], doc.get("document_date"),
                 doc.get("document_name"), doc.get("document_type"),
                 doc.get("file_path"), doc.get("file_hash"), doc.get("ocr_text_path"))
            )
            master_conn.commit()
            master_conn.close()
            return True
        except Exception as e:
            self.log.error(f"Import failed for {doc['portal_document_id']}: {e}")
            return False

    def _mark_imported(self, portal_id: str, portal_document_id: str):
        conn = get_connection(self.delta.db_path)
        conn.execute(
            """UPDATE documents SET master_imported = 1, updated_at = datetime('now')
               WHERE portal_id = ? AND portal_document_id = ?""",
            (portal_id, portal_document_id)
        )
        conn.commit()
        conn.close()
