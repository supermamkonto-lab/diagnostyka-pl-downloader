"""SQLite schema and connection management."""

import sqlite3
from pathlib import Path
from datetime import datetime


SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    portal_id           TEXT NOT NULL,
    portal_document_id  TEXT NOT NULL,
    document_date       TEXT,
    document_name       TEXT,
    document_type       TEXT,
    download_date       TEXT,
    file_path           TEXT,
    file_hash           TEXT,
    file_size_bytes     INTEGER,
    downloaded          INTEGER DEFAULT 0,
    ocr_done            INTEGER DEFAULT 0,
    ocr_text_path       TEXT,
    master_imported     INTEGER DEFAULT 0,
    created_at          TEXT DEFAULT (datetime('now')),
    updated_at          TEXT DEFAULT (datetime('now')),
    UNIQUE(portal_id, portal_document_id)
);

CREATE TABLE IF NOT EXISTS sync_log (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    portal_id           TEXT,
    sync_start          TEXT,
    sync_end            TEXT,
    documents_on_portal INTEGER DEFAULT 0,
    documents_in_db     INTEGER DEFAULT 0,
    documents_new       INTEGER DEFAULT 0,
    documents_skipped   INTEGER DEFAULT 0,
    documents_downloaded INTEGER DEFAULT 0,
    documents_ocr       INTEGER DEFAULT 0,
    documents_imported  INTEGER DEFAULT 0,
    status              TEXT,
    error_message       TEXT,
    log_file_path       TEXT
);

CREATE INDEX IF NOT EXISTS idx_documents_portal ON documents(portal_id);
CREATE INDEX IF NOT EXISTS idx_documents_downloaded ON documents(downloaded);
CREATE INDEX IF NOT EXISTS idx_documents_ocr ON documents(ocr_done);
"""


def get_connection(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_database(db_path: str) -> sqlite3.Connection:
    conn = get_connection(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn
