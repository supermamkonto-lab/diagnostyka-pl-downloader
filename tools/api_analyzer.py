"""
API Analyzer — captures all network traffic on diag.pl after login.
Uses the user's real Chrome profile so login is not required again.

Usage:
    python run.py analyze-api
"""

import json
import time
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, Request, Response


PORTAL_URL = "https://diag.pl/pacjent/wyniki-online"
CAPTURE_DURATION_SECONDS = 120
OUTPUT_DIR = Path("tools/api_reports")

# Real Chrome profile — user is already logged in here
CHROME_EXECUTABLE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROME_USER_DATA = r"C:\Users\Pablo\AppData\Local\Google\Chrome\User Data"
CHROME_PROFILE = "Default"

EXCLUDED_EXTENSIONS = {".css", ".js", ".png", ".jpg", ".ico", ".svg", ".woff", ".woff2", ".ttf", ".gif", ".webp"}
INCLUDED_CONTENT_TYPES = {"application/json", "text/json", "application/vnd"}


def is_api_request(url: str, content_type: str) -> bool:
    parsed = urlparse(url)
    ext = Path(parsed.path).suffix.lower()
    if ext in EXCLUDED_EXTENSIONS:
        return False
    if any(ct in (content_type or "") for ct in INCLUDED_CONTENT_TYPES):
        return True
    if "/api/" in url or "/rest/" in url or "/graphql" in url:
        return True
    return False


def run():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"diag_api_capture_{timestamp}.json"

    captured: list[dict] = []
    auth_tokens: list[str] = []

    print("\n" + "="*60)
    print("  DIAGNOSTYKA API ANALYZER")
    print("="*60)
    print(f"\nUżywa Twojego profilu Chrome (jesteś już zalogowany)")
    print(f"Target: {PORTAL_URL}")
    print(f"\nPo otwarciu przeglądarki:")
    print(f"  1. Kliknij na kilka wyników badań")
    print(f"  2. Otwórz PDF jednego wyniku")
    print(f"  3. Poczekaj {CAPTURE_DURATION_SECONDS}s — skrypt sam się zamknie")
    print(f"\nOutput: {output_file}\n")

    # WAŻNE: zamknij Chrome przed uruchomieniem!
    print("UWAGA: Zamknij Chrome jeśli jest otwarty, a potem wciśnij Enter...")
    input()

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            CHROME_USER_DATA,
            executable_path=CHROME_EXECUTABLE,
            channel="chrome",
            headless=False,
            args=[
                f"--profile-directory={CHROME_PROFILE}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-extensions-except=",
            ],
            slow_mo=30,
        )

        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        def on_request(req: Request):
            auth = req.headers.get("authorization", "")
            if auth and auth not in auth_tokens:
                auth_tokens.append(auth)

        def on_response(resp: Response):
            try:
                url = resp.url
                content_type = resp.headers.get("content-type", "")
                if not is_api_request(url, content_type):
                    return
                try:
                    body = resp.json()
                except Exception:
                    body = None
                entry = {
                    "url": url,
                    "method": resp.request.method,
                    "status": resp.status,
                    "content_type": content_type,
                    "request_headers": dict(resp.request.headers),
                    "response_preview": _truncate(body or resp.text()[:500]),
                }
                captured.append(entry)
                print(f"  [API] {resp.request.method} {resp.status} {url}")
            except Exception:
                pass

        page.on("request", on_request)
        page.on("response", on_response)

        page.goto(PORTAL_URL, wait_until="domcontentloaded")
        print(f"\nPrzechwytywanie aktywne przez {CAPTURE_DURATION_SECONDS}s — klikaj po wynikach!\n")
        time.sleep(CAPTURE_DURATION_SECONDS)

        # Deduplicate
        seen = set()
        unique = []
        for e in captured:
            key = (e["method"], e["url"].split("?")[0])
            if key not in seen:
                seen.add(key)
                unique.append(e)

        report = {
            "capture_time": timestamp,
            "portal": PORTAL_URL,
            "auth_tokens_found": auth_tokens,
            "total_api_calls": len(captured),
            "unique_endpoints": len(unique),
            "endpoints": unique,
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print(f"  Przechwycono: {len(captured)} wywołań API ({len(unique)} unikalnych)")
        print(f"  Tokeny auth: {len(auth_tokens)}")
        print(f"  Raport: {output_file}")
        print("="*60)

        ctx.close()
    return output_file


def _truncate(obj, max_len=500):
    if obj is None:
        return None
    s = json.dumps(obj, ensure_ascii=False)
    return s[:max_len] + ("..." if len(s) > max_len else "")


if __name__ == "__main__":
    run()
