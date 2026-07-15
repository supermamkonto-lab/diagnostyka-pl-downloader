"""Session state persistence — tracks sync progress for resume-after-failure."""

import json
from pathlib import Path
from datetime import datetime
from database.models import get_connection


class StateManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def start_sync(self, portal_id: str, log_file_path: str = "") -> int:
        conn = get_connection(self.db_path)
        cursor = conn.execute(
            """INSERT INTO sync_log (portal_id, sync_start, status, log_file_path)
               VALUES (?, datetime('now'), 'running', ?)""",
            (portal_id, log_file_path)
        )
        sync_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return sync_id

    def update_sync(self, sync_id: int, **kwargs):
        if not kwargs:
            return
        fields = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [sync_id]
        conn = get_connection(self.db_path)
        conn.execute(f"UPDATE sync_log SET {fields} WHERE id = ?", values)
        conn.commit()
        conn.close()

    def finish_sync(self, sync_id: int, status: str = "success",
                    error_message: str = None, **counts):
        kwargs = {"sync_end": "datetime('now')", "status": status}
        if error_message:
            kwargs["error_message"] = error_message
        kwargs.update(counts)

        conn = get_connection(self.db_path)
        set_parts = []
        values = []
        for k, v in kwargs.items():
            if v == "datetime('now')":
                set_parts.append(f"{k} = datetime('now')")
            else:
                set_parts.append(f"{k} = ?")
                values.append(v)
        values.append(sync_id)
        conn.execute(
            f"UPDATE sync_log SET {', '.join(set_parts)} WHERE id = ?", values
        )
        conn.commit()
        conn.close()

    def get_last_sync(self, portal_id: str) -> dict | None:
        conn = get_connection(self.db_path)
        row = conn.execute(
            """SELECT * FROM sync_log WHERE portal_id = ?
               ORDER BY sync_start DESC LIMIT 1""",
            (portal_id,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None
