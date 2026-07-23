"""
Badaj.to (Śląskie Laboratoria Analityczne / ProfLab) portal adapter.
API odkryte przez reverse-engineering poprzez Playwright.

Architektura auth:
- Login: numer karty (numerKarty) + hasło (haslo)
- POST: https://wyniki.badaj.to/Login/Authenticate
- CAPTCHA: Cloudflare Turnstile (wymaga ręcznej interakcji)
- Session: Cookie-based (session cookie)
"""

import time
import json
import httpx
from pathlib import Path
from typing import Optional
from playwright.sync_api import Page, Request, Response

from portals.base_portal import BasePortal, PortalDocument


_LOGIN_URL = "https://wyniki.badaj.to/"
_AUTH_ENDPOINT = "https://wyniki.badaj.to/Login/Authenticate"
_API_BASE = "https://wyniki.badaj.to/api"


class BadajToPl(BasePortal):
    PORTAL_ID = "badaj_to"

    def __init__(self, page: Page, config: dict, download_dir: str, logger):
        super().__init__(page, config, download_dir, logger)
        self._cookies: list[dict] = []
        self._http: Optional[httpx.Client] = None
        self._intercepted_order_ids: list[str] = []

    # ------------------------------------------------------------------ #
    # Login detection — numer karty + hasło                             #
    # ------------------------------------------------------------------ #

    def wait_for_login(self) -> bool:
        # Sprawdź czy już zalogowany (persistent session)
        try:
            existing_cookies = self.page.context.cookies()
            session_cookie = next((c for c in existing_cookies if c.get("name") == "session" or "proflab" in c.get("name", "").lower()), None)
            if session_cookie:
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
        self.log.info("ℹ️  Wymagane: numer karty KK + hasło + rozwiązanie CAPTCHA Turnstile")

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
                        session_cookie = next((c for c in cookies_list if "session" in c.get("name", "").lower() or "proflab" in c.get("name", "").lower()), None)
                        session_status = "✓ Present" if session_cookie else "✗ Missing"
                        self.log.info(f"[{check_count}s] 📄 Title: {title} | Session: {session_status}")
                    except Exception as debug_err:
                        self.log.warning(f"[{check_count}s] ⚠️  Cannot get page state: {debug_err}")

                # Szukaj login formu
                login_form = self.page.query_selector('input[name="numerKarty"]')

                if first_check:
                    if login_form:
                        self.log.info("✓ Login form ZNALEZIONY — czekam na wpisanie numeru karty i hasła")
                    else:
                        self.log.warning(f"⚠️  Login form nie znaleziony")
                    first_check = False

                # Sprawdzenie czy wpisano dane (czy form jest uzupełniony)
                numerKarty_input = self.page.query_selector('input[name="numerKarty"]')
                haslo_input = self.page.query_selector('input[name="haslo"]')

                if numerKarty_input and haslo_input:
                    numer_val = numerKarty_input.input_value() if hasattr(numerKarty_input, 'input_value') else ""
                    haslo_val = haslo_input.input_value() if hasattr(haslo_input, 'input_value') else ""

                    if numer_val and haslo_val:
                        self.log.info(f"✓ Dane wpisane (numer karty: {numer_val[:4]}***)")

                # Sprawdzenie czy zalogowano się (odpytaj URL)
                current_url = self.page.url

                # Jeśli URL zmienił się z /logowanie — znaczy zalogowano
                if "/logowanie" not in current_url.lower() and current_url != _LOGIN_URL:
                    self.log.info("✓✓✓ ZALOGOWANO! (URL zmienił się)")
                    time.sleep(2)
                    self._cookies = self.page.context.cookies()
                    self.log.info(f"🔐 Cookies: {len(self._cookies)} | Session: ✓ Established")
                    return True

            except Exception as e:
                self.log.warning(f"⚠️  Error during wait: {type(e).__name__}: {str(e)[:100]}")
            time.sleep(1)

        self.log.error("❌ TIMEOUT (5 min) — nie zalogowałeś się")
        self.log.info("💡 Podpowiedź: wpisz numer karty KK + hasło + rozwiąż CAPTCHA")
        return False

    def get_auth_headers(self) -> dict:
        """Zwróć headery z sesją do API callsów."""
        cookie_header = self._cookies_to_header(self._cookies)
        return {
            **cookie_header,
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }

    def _http_client(self) -> httpx.Client:
        if not self._http:
            self._http = httpx.Client(
                headers=self.get_auth_headers(),
                timeout=30,
            )
        return self._http

    # ------------------------------------------------------------------ #
    # Document list fetching                                             #
    # ------------------------------------------------------------------ #

    def fetch_document_list(self) -> list[PortalDocument]:
        """Pobiera listę zleceń poprzez API lub scraping."""
        limit = self.config.get("collector_limit")

        self.log.info("📋 Pobieranie zleceń z badaj.to...")

        # Najpierw spróbuj znaleźć API endpointy przez network monitoring
        # Fallback: scraping strony
        try:
            # Spróbuj nawigować do strony z wynikami
            orders_url = "https://wyniki.badaj.to/Orders"
            self.page.goto(orders_url, wait_until="networkidle", timeout=120000)
            self.log.info("✓ Strona zleceń załadowana")

            time.sleep(2)  # Czekaj na AJAX

            # Spróbuj znaleźć tabelę z zleceniami
            table_rows = self.page.query_selector_all("table tbody tr, [data-testid='order-row'], .order-item")

            if not table_rows:
                self.log.warning("⚠️  Nie znaleziono zleceń na stronie")
                return []

            self.log.info(f"✓ Znaleziono {len(table_rows)} zleceń")

            documents = []
            for idx, row in enumerate(table_rows[:limit] if limit else table_rows, 1):
                try:
                    # Parsuj wiersz tabeli
                    # Struktura może być inna — dostosuj do rzeczywistego HTML-a
                    cells = row.query_selector_all("td")

                    if len(cells) >= 3:
                        order_id = cells[0].text_content().strip()
                        order_date = cells[1].text_content().strip()
                        order_name = cells[2].text_content().strip() if len(cells) > 2 else "Unknown"

                        doc = PortalDocument(
                            portal_id=self.PORTAL_ID,
                            portal_document_id=order_id,
                            document_date=order_date,
                            document_name=order_name,
                            document_type="LAB",
                        )
                        documents.append(doc)
                        self.log.debug(f"  [{idx}] {order_id} | {order_date} | {order_name}")
                except Exception as e:
                    self.log.warning(f"  ⚠️  Błąd parsowania wiersza {idx}: {e}")
                    continue

            return documents

        except Exception as e:
            self.log.error(f"❌ Błąd pobierania listy zleceń: {e}")
            return []

    # ------------------------------------------------------------------ #
    # Document download                                                  #
    # ------------------------------------------------------------------ #

    def download_document(self, doc: PortalDocument) -> Optional[str]:
        """Pobierz PDF (i opcjonalnie CDA) dla jednego dokumentu."""
        self.log.info(f"📥 Pobieranie: {doc.document_name} ({doc.document_date})")

        try:
            # Spróbuj pobrać PDF
            # Endpoint może być: /api/document/{id}/pdf lub /Orders/Download/{id}
            pdf_url = f"https://wyniki.badaj.to/Orders/Download/{doc.portal_document_id}"

            # Pobierz poprzez Playwright (aby mieć sesję)
            response = self.page.goto(pdf_url, wait_until="domcontentloaded", timeout=60000)

            if response and response.ok:
                # Plik został pobrany — zapisz go
                filename = f"{doc.document_date}_{doc.document_name}.pdf"
                dest_path = Path(self.download_dir) / filename

                # Pobierz zawartość
                pdf_data = self.page.content()
                # To jest HTML, nie PDF — spróbuj innego podejścia

                # Fallback: użyj httpx z cookies
                client = self._http_client()
                pdf_resp = client.get(pdf_url, follow_redirects=True)

                if pdf_resp.status_code == 200 and b"%PDF" in pdf_resp.content:
                    # To jest PDF!
                    dest_path.write_bytes(pdf_resp.content)
                    self.log.info(f"✓ Pobrano: {filename} ({len(pdf_resp.content) // 1024} KB)")
                    return str(dest_path)
                else:
                    self.log.warning(f"❌ Endpoint nie zwrócił PDF")
                    return None
            else:
                self.log.warning(f"❌ Błąd pobierania: HTTP {response.status if response else 'no response'}")
                return None

        except Exception as e:
            self.log.error(f"❌ Błąd podczas pobierania: {e}")
            return None

    @staticmethod
    def _cookies_to_header(cookies: list[dict]) -> dict:
        if not cookies:
            return {}
        parts = [f"{c['name']}={c['value']}" for c in cookies if "name" in c and "value" in c]
        return {"Cookie": "; ".join(parts)} if parts else {}
