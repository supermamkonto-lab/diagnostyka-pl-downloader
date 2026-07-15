"""Delta detection — compares portal document list against local database."""

import hashlib
from pathlib import Path
from typing import Optional
from database.models import get_connection


class DeltaManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_known_ids(self, portal_id: str) -> set[str]:
        conn = get_connection(self.db_path)
        rows = conn.execute(
            "SELECT portal_document_id FROM documents WHERE portal_id = ?",
            (portal_id,)
        ).fetchall()
        conn.close()
        return {row["portal_document_id"] for row in rows}

    def get_undownloaded(self, portal_id: str) -> list[dict]:
        conn = get_connection(self.db_path)
        rows = conn.execute(
            "SELECT * FROM documents WHERE portal_id = ? AND downloaded = 0",
            (portal_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def register_document(self, portal_id: str, portal_document_id: str,
                          document_date: Optional[str] = None,
                          document_name: Optional[str] = None,
                          document_type: Optional[str] = None) -> bool:
        """Insert new document record. Returns True if inserted (new), False if already exists."""
        conn = get_connection(self.db_path)
        try:
            conn.execute(
                """INSERT OR IGNORE INTO documents
                   (portal_id, portal_document_id, document_date, document_name, document_type)
                   VALUES (?, ?, ?, ?, ?)""",
                (portal_id, portal_document_id, document_date, document_name, document_type)
            )
            inserted = conn.total_changes > 0
            conn.commit()
            return inserted
        finally:
            conn.close()

    def mark_downloaded(self, portal_id: str, portal_document_id: str,
                        file_path: str, file_hash: str, file_size: int):
        conn = get_connection(self.db_path)
        conn.execute(
            """UPDATE documents SET
               downloaded = 1, download_date = datetime('now'),
               file_path = ?, file_hash = ?, file_size_bytes = ?,
               updated_at = datetime('now')
               WHERE portal_id = ? AND portal_document_id = ?""",
            (file_path, file_hash, file_size, portal_id, portal_document_id)
        )
        conn.commit()
        conn.close()

    def mark_ocr_done(self, portal_id: str, portal_document_id: str, ocr_text_path: str):
        conn = get_connection(self.db_path)
        conn.execute(
            """UPDATE documents SET ocr_done = 1, ocr_text_path = ?, updated_at = datetime('now')
               WHERE portal_id = ? AND portal_document_id = ?""",
            (ocr_text_path, portal_id, portal_document_id)
        )
        conn.commit()
        conn.close()

    def get_stats(self, portal_id: str) -> dict:
        conn = get_connection(self.db_path)
        row = conn.execute(
            """SELECT
               COUNT(*) as total,
               SUM(downloaded) as downloaded,
               SUM(ocr_done) as ocr_done,
               SUM(master_imported) as imported
               FROM documents WHERE portal_id = ?""",
            (portal_id,)
        ).fetchone()
        conn.close()
        return dict(row) if row else {}

    @staticmethod
    def hash_file(file_path: str) -> str:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
