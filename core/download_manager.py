"""PDF download with retry, deduplication, and rate limiting."""

import time
import httpx
from pathlib import Path
from typing import Optional
from database.delta_manager import DeltaManager


class DownloadManager:
    def __init__(self, config: dict, delta: DeltaManager, logger):
        self.config = config
        self.delta = delta
        self.log = logger
        self._delay_ms = config.get("portals", {}).get(
            "diagnostyka_pl", {}
        ).get("request_delay_ms", 1500)
        self._max_retries = config.get("portals", {}).get(
            "diagnostyka_pl", {}
        ).get("max_retries", 3)

    def download(self, portal_id: str, portal_document_id: str,
                 url: str, filename: str, download_dir: str,
                 headers: dict = None, cookies: list[dict] = None) -> Optional[str]:
        """
        Download a file with retry. Returns local path or None on failure.
        Skips if already downloaded (checks DB, then verifies file exists).
        """
        dest_dir = Path(download_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / filename

        # Skip if already on disk with matching hash
        known = self._get_existing(portal_id, portal_document_id)
        if known and known.get("downloaded") and Path(known["file_path"] or "").exists():
            self.log.debug(f"Skipping (already downloaded): {filename}")
            return known["file_path"]

        cookie_header = self._cookies_to_header(cookies or [])
        all_headers = {**(headers or {}), **cookie_header}

        for attempt in range(1, self._max_retries + 1):
            try:
                self.log.info(f"Downloading [{attempt}/{self._max_retries}]: {filename}")
                with httpx.stream("GET", url, headers=all_headers,
                                  follow_redirects=True, timeout=60) as r:
                    r.raise_for_status()
                    with open(dest_path, "wb") as f:
                        for chunk in r.iter_bytes(chunk_size=65536):
                            f.write(chunk)

                file_hash = DeltaManager.hash_file(str(dest_path))
                file_size = dest_path.stat().st_size
                self.delta.mark_downloaded(
                    portal_id, portal_document_id,
                    str(dest_path), file_hash, file_size
                )
                self.log.info(f"Saved: {dest_path} ({file_size // 1024} KB)")
                time.sleep(self._delay_ms / 1000)
                return str(dest_path)

            except Exception as e:
                self.log.warning(f"Download failed (attempt {attempt}): {e}")
                if attempt < self._max_retries:
                    time.sleep(self._delay_ms / 1000 * attempt)

        self.log.error(f"All retries exhausted for {filename}")
        return None

    def _get_existing(self, portal_id: str, portal_document_id: str) -> Optional[dict]:
        from database.models import get_connection
        db_path = self.delta.db_path
        conn = get_connection(db_path)
        row = conn.execute(
            "SELECT * FROM documents WHERE portal_id = ? AND portal_document_id = ?",
            (portal_id, portal_document_id)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def _cookies_to_header(cookies: list[dict]) -> dict:
        if not cookies:
            return {}
        parts = [f"{c['name']}={c['value']}" for c in cookies if "name" in c and "value" in c]
        return {"Cookie": "; ".join(parts)} if parts else {}
