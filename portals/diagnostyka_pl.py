"""
Diagnostyka (wyniki.diag.pl) portal adapter.
API odkryte 2026-07-14 przez analizę ruchu sieciowego.

Architektura auth:
- Cookie-based JWT: ciasteczko 'jwt' na domenie wyniki.diag.pl
- Token refresh: POST https://api.wyniki.diag.pl/identity/refresh-jwt-token
- Wszystkie requesty idą na: https://api.wyniki.diag.pl
- Login portal: https://wyniki.diag.pl
"""

import time
import json
import httpx
from pathlib import Path
from typing import Optional
from playwright.sync_api import Page, Request, Response

from portals.base_portal import BasePortal, PortalDocument


_API_BASE = "https://api.wyniki.diag.pl"
_LOGIN_URL = "https://wyniki.diag.pl/logowanie-kontem"
_ORDERS_URL = "https://wyniki.diag.pl/zlecenia/laboratoryjne"


class DiagnostykaPl(BasePortal):
    PORTAL_ID = "diagnostyka_pl"

    def __init__(self, page: Page, config: dict, download_dir: str, logger):
        super().__init__(page, config, download_dir, logger)
        self._cookies: list[dict] = []
        self._http: Optional[httpx.Client] = None
        self._intercepted_order_ids: list[str] = []

    # ------------------------------------------------------------------ #
    # Login detection                                                      #
    # ------------------------------------------------------------------ #

    def wait_for_login(self) -> bool:
        # Sprawdź czy już zalogowany (persistent session)
        try:
            existing_cookies = self.page.context.cookies()
            jwt_existing = next((c for c in existing_cookies if c.get("name") == "jwt"), None)
            if jwt_existing:
                self.log.info("✓ Już zalogowany (sesja z poprzedniego uruchomienia)!")
                self._cookies = existing_cookies
                return True
        except Exception:
            pass

        self.log.info(f"Otwieranie portalu: {_LOGIN_URL}")
        try:
            self.page.goto(_LOGIN_URL, timeout=120000, wait_until="domcontentloaded")
            self.log.info("✓ Strona login załadowana")
            time.sleep(3)  # Czekaj na React/rendering
        except Exception as e:
            self.log.error(f"❌ Błąd ładowania strony: {e}")
            return False

        # Log initial state
        title = self.page.title()
        url = self.page.url
        self.log.info(f"📄 Strona: {title}")
        self.log.info(f"🔗 URL: {url}")

        self.log.info("⏳ Czekam na zalogowanie (nie zamykaj Chrome)... [5 minut timeout]")
        deadline = time.time() + 300
        check_count = 0
        first_check = True
        while time.time() < deadline:
            try:
                check_count += 1

                # Log state co 15 sekund
                if check_count % 15 == 0:
                    try:
                        title = self.page.title()
                        url = self.page.url
                        cookies_list = self.page.context.cookies()
                        jwt_cookie = next((c for c in cookies_list if c.get("name") == "jwt"), None)
                        jwt_status = "✓ Present" if jwt_cookie else "✗ Missing"
                        self.log.info(f"[{check_count}s] 📄 Title: {title} | JWT: {jwt_status}")
                    except Exception as debug_err:
                        self.log.warning(f"[{check_count}s] ⚠️  Cannot get page state: {debug_err}")

                # Szukaj login formu w głównym dokumencie
                login_form = self.page.query_selector('input[name="pesel"], input[placeholder*="PESEL"], input[type="text"]')

                if first_check:
                    if login_form:
                        self.log.info("✓ Login form ZNALEZIONY w DOM — wpisujesz PESEL")
                    else:
                        # Sprawdź czy jest w iframe
                        iframes = self.page.query_selector_all("iframe")
                        self.log.warning(f"⚠️  Login form nie znaleziony w głównym DOM (znaleziono {len(iframes)} iframes)")
                    first_check = False

                # Wykryj login przez JWT cookie (najbardziej niezawodne)
                cookies_now = self.page.context.cookies()
                jwt_cookie = next((c for c in cookies_now if c.get("name") == "jwt"), None)
                if jwt_cookie:
                    self.log.info("✓✓✓ ZALOGOWANO! (JWT cookie obecny)")
                    time.sleep(2)
                    self._cookies = cookies_now
                    self.log.info(f"🔐 Cookies: {len(self._cookies)} | JWT: ✓ Present")
                    return True

            except Exception as e:
                self.log.warning(f"⚠️  Error during wait: {type(e).__name__}: {str(e)[:100]}")
            time.sleep(1)

        self.log.error("❌ TIMEOUT (5 min) — nie zalogowałeś się")
        return False

    def get_auth_token(self) -> Optional[str]:
        for c in self._cookies:
            if c.get("name") == "jwt":
                return c.get("value")
        return None

    # ------------------------------------------------------------------ #
    # Orders list — intercept order-sync calls made by the browser        #
    # ------------------------------------------------------------------ #

    def fetch_document_list(self) -> list[PortalDocument]:
        """Pobiera listę zleceń bezpośrednio przez API /orders."""
        client = self._http_client()
        limit = self.config.get("collector_limit")

        # Pobierz zlecenia przez API
        all_order_ids = []
        page_num = 1
        per_page = 20

        self.log.info("📋 Pobieranie zleceń przez API /orders...")

        try:
            # API zwraca wszystkie zlecenia na raz — nie paginuje przez page param
            resp = client.get(
                f"{_API_BASE}/orders",
                params={"limit": 500, "sort": "date_desc"},
            )
            resp.raise_for_status()
            data = resp.json()

            orders = []
            if isinstance(data, list):
                orders = data
            elif isinstance(data, dict):
                orders = data.get("orders") or data.get("items") or data.get("data") or data.get("results") or []

            for order in orders:
                oid = order.get("id") or order.get("orderId") or order.get("uuid") or ""
                if oid:
                    all_order_ids.append(str(oid))

            self.log.info(f"   API zwróciło {len(all_order_ids)} zleceń")

        except Exception as e:
            self.log.error(f"❌ Błąd /orders: {e}")

        # Zastosuj limit
        last_mode = self.config.get("collector_last", False)
        if limit:
            if last_mode:
                # --last: pobierz N najstarszych (koniec listy)
                all_order_ids = all_order_ids[-limit:]
                self.log.info(f"📌 Limit {limit} (LAST/najstarsze): {len(all_order_ids)} zleceń")
            else:
                # domyślnie: N najnowszych (początek listy)
                all_order_ids = all_order_ids[:limit]
                self.log.info(f"📌 Limit {limit} (najnowsze): {len(all_order_ids)} zleceń")

        self.log.info(f"✓ Znaleziono {len(all_order_ids)} zleceń")

        # Pobierz dokumenty dla każdego zlecenia
        docs = []
        for idx, order_id in enumerate(all_order_ids, 1):
            self.log.info(f"📄 [{idx}/{len(all_order_ids)}] Dokumenty dla: {order_id[:40]}...")
            order_docs = self._fetch_documents_for_order(order_id)
            docs.extend(order_docs)
            self.log.info(f"   → {len(order_docs)} dokumentów")

        self.log.info(f"✓ Łącznie dokumentów: {len(docs)}")
        return docs

    # ------------------------------------------------------------------ #
    # Documents for a single order                                        #
    # ------------------------------------------------------------------ #

    def _fetch_documents_for_order(self, order_id: str) -> list[PortalDocument]:
        client = self._http_client()
        try:
            resp = client.get(
                f"{_API_BASE}/documents",
                params={"orderId": order_id},
            )
            resp.raise_for_status()
            data = resp.json()
            documents = data if isinstance(data, list) else data.get("documents") or data.get("items") or []

            result = []
            for doc in documents:
                doc_id = doc.get("id", "")
                doc_date = doc.get("createdAt") or doc.get("date") or ""
                test_names = doc.get("testNames") or doc.get("name") or "dokument"
                is_luxmed = doc.get("isLuxmed", False)

                # Znajdź pliki PDF (type=1) i CDA (type=4)
                files = doc.get("files", [])
                pdf_file = next((f for f in files if f.get("type") == 1 and f.get("isExist")), None)
                cda_file = next((f for f in files if f.get("type") == 4 and f.get("isExist")), None)

                pdf_file_id = pdf_file.get("id", "") if pdf_file else ""
                cda_file_id = cda_file.get("id", "") if cda_file else ""

                luxmed_param = "true" if is_luxmed else "false"

                result.append(PortalDocument(
                    portal_document_id=f"{order_id}::{doc_id}",
                    document_name=test_names,
                    document_date=doc_date[:10] if doc_date else None,
                    document_type="pdf",
                    download_url=f"{_API_BASE}/files/{pdf_file_id}?fileType=1&isLuxmed={luxmed_param}" if pdf_file_id else None,
                    metadata={
                        "order_id": order_id,
                        "doc_id": doc_id,
                        "pdf_file_id": pdf_file_id,
                        "cda_file_id": cda_file_id,
                        "is_luxmed": is_luxmed,
                    },
                ))
            return result

        except Exception as e:
            self.log.warning(f"Błąd pobierania dokumentów dla zlecenia {order_id[:20]}...: {e}")
            # Fallback: single PDF per order
            return [PortalDocument(
                portal_document_id=order_id,
                document_name="wynik",
                document_date=None,
                document_type="pdf",
                download_url=None,
                metadata={"order_id": order_id, "needs_resolution": True},
            )]

    # ------------------------------------------------------------------ #
    # PDF download                                                        #
    # ------------------------------------------------------------------ #

    def download_document(self, doc: PortalDocument) -> Optional[str]:
        if not doc.download_url:
            self.log.warning(f"Brak URL dla {doc.portal_document_id}")
            return None

        delay_ms = self.config.get("portals", {}).get("diagnostyka_pl", {}).get("request_delay_ms", 1500)
        retries = self.config.get("portals", {}).get("diagnostyka_pl", {}).get("max_retries", 3)

        # Pobierz PDF (fileType=1)
        pdf_result = self._download_file(doc.download_url, doc, delay_ms, retries, "pdf")

        # Spróbuj pobrać CDA (fileType=4) — użyj osobnego file_id z metadata
        cda_file_id = doc.metadata.get("cda_file_id") if doc.metadata else None
        if cda_file_id:
            is_luxmed = doc.metadata.get("is_luxmed", False)
            luxmed_param = "true" if is_luxmed else "false"
            cda_url = f"{_API_BASE}/files/{cda_file_id}?fileType=4&isLuxmed={luxmed_param}"
            self._download_file(cda_url, doc, delay_ms, retries, "cda")
        else:
            self.log.debug(f"Brak CDA dla {doc.document_name}")

        return pdf_result

    def _download_file(self, url: str, doc: PortalDocument, delay_ms: int, retries: int, format_type: str) -> Optional[str]:
        # Format: RRRR-MM-DD_nazwa_dokumentu
        # Użyj document_date (dzień pobrania krwi) zamiast czasu serwera
        date_str = doc.document_date or ""
        if len(date_str) >= 10:
            # Konwertuj np. "2026-07-14" lub "2026-07-14T12:00:00" na "2026-07-14"
            date_part = date_str[:10]
        else:
            date_part = "nodate"

        # Nazwa z testNames — skróć do pierwszych 3 badań, max 60 znaków
        raw_name = doc.document_name or "dokument"
        # Usuń "Usługa - pobranie materiału" bo to nie badanie
        parts = [p.strip() for p in raw_name.split(",") if "usługa" not in p.lower() and "pobran" not in p.lower()]
        doc_name = ", ".join(parts[:3])  # max 3 badania
        if len(parts) > 3:
            doc_name += f" +{len(parts)-3}"
        # Bezpieczne znaki dla nazwy pliku
        doc_name = "".join(c if c.isalnum() or c in "-_ ,()" else "_" for c in doc_name)[:60]
        doc_name = doc_name.strip("_").replace("  ", " ")

        ext = "xml" if format_type == "cda" else "pdf"
        filename = f"{date_part}_{doc_name}.{ext}"

        dest = Path(self.download_dir) / filename
        dest.parent.mkdir(parents=True, exist_ok=True)

        if dest.exists() and dest.stat().st_size > 1000:
            self.log.debug(f"Plik już istnieje: {filename}")
            return str(dest)

        for attempt in range(1, retries + 1):
            try:
                self.log.info(f"Pobieranie [{attempt}/{retries}] ({format_type.upper()}): {filename}")
                with self._http_client().stream("GET", url) as r:
                    if r.status_code == 404:
                        self.log.debug(f"{format_type.upper()} niedostępny dla tego dokumentu")
                        return None
                    r.raise_for_status()
                    with open(dest, "wb") as f:
                        for chunk in r.iter_bytes(65536):
                            f.write(chunk)
                size = dest.stat().st_size
                self.log.info(f"Zapisano: {dest.name} ({size // 1024} KB)")

                # Szczegółowy log pobrania
                self.log.info(
                    f"📥 POBRANO | "
                    f"Plik: {dest.name} | "
                    f"Typ: {format_type.upper()} | "
                    f"Rozmiar: {size // 1024} KB ({size:,} B) | "
                    f"Ścieżka: {dest} | "
                    f"Badania: {doc.document_name} | "
                    f"Data badania: {doc.document_date}"
                )

                time.sleep(delay_ms / 1000)
                return str(dest)
            except Exception as e:
                self.log.warning(f"Błąd pobierania {format_type.upper()} (próba {attempt}): {e}")
                time.sleep(delay_ms / 1000 * attempt)

        return None

    # ------------------------------------------------------------------ #
    # Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _capture_cookies(self):
        self._cookies = self.page.context.cookies()
        self._http = None  # reset HTTP client so it picks up new cookies

    def _http_client(self) -> httpx.Client:
        if self._http is None:
            cookie_dict = {c["name"]: c["value"] for c in self._cookies}
            self._http = httpx.Client(
                base_url=_API_BASE,
                cookies=cookie_dict,
                headers={
                    "accept": "application/json, text/plain, */*",
                    "locale": "pl",
                    "origin": "https://wyniki.diag.pl",
                    "referer": "https://wyniki.diag.pl/",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
                },
                follow_redirects=True,
                timeout=60,
            )
        return self._http

    def _refresh_token(self):
        """Odśwież JWT token przed wygaśnięciem."""
        try:
            resp = self._http_client().post(f"{_API_BASE}/identity/refresh-jwt-token")
            if resp.status_code == 200:
                # Nowy token przychodzi w Set-Cookie
                self._capture_cookies()
                self.log.debug("JWT token odświeżony")
        except Exception as e:
            self.log.warning(f"Błąd odświeżania tokenu: {e}")

    @staticmethod
    def _safe_filename(doc: PortalDocument, format_type: str = "pdf") -> str:
        date_part = (doc.document_date or "nodate").replace("/", "-")[:10]
        name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in (doc.document_name or "doc"))[:50]
        doc_id = doc.portal_document_id.split("::")[-1][:20]
        ext = "xml" if format_type == "cda" else "pdf"
        return f"{date_part}_{doc_id}_{name}.{ext}"

    def close(self):
        if self._http:
            self._http.close()
