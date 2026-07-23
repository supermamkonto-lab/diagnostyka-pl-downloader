# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Medical Data Collector — Multi-Lab** — Automatyczne pobieranie wyników badań (PDF + CDA/XML) z wielu portali laboratoriów w Polsce.

Currently supported laboratories:
- **Diagnostyka.pl** (wyniki.diag.pl) — login: PESEL + hasło
- **Badaj.to** (wyniki.badaj.to) — login: numer karty KK + hasło

This is a Python-based web scraper that:
- Launches Chrome browser for manual login (credentials never saved)
- Detects login and manages session cookies
- Fetches document list from multiple portals
- Downloads PDFs and CDA/XML files with deduplication
- Tracks sync state in SQLite database
- Supports optional OCR and database import pipelines
- Manages multiple laboratories in single database

## Quick Commands

### Running the Collector
```bash
cd /home/user/diagnostyka-pl-downloader

# Full sync — download all new documents
python run.py collect

# Test sync — download only last N orders (for quick testing)
python run.py collect --limit=1      # Last 1 order
python run.py collect --limit=5      # Last 5 orders

# Show sync statistics
python run.py status

# API discovery (debug tool) — captures network traffic for API reverse-engineering
python run.py analyze-api
```

### Installing Dependencies
```bash
pip install -r requirements.txt
python -m playwright install chromium
```

## Architecture & Key Modules

### Entry Point
- **`run.py`** — CLI dispatcher for three commands: `collect`, `status`, `analyze-api`. Orchestrates phases 1–7 of the sync workflow (launch browser → login → fetch list → delta check → download → summary).

### Core Module (`core/`)
- **`browser_manager.py`** — Chrome PWA launch via `launch_persistent_context()` (headless=False, persistent profile). Returns (context, page) for Playwright automation. Profile stored in `state/chrome_profile/`.
- **`session_manager.py`** — JWT token management (refresh, extraction from cookies).
- **`download_manager.py`** — File download with retries, resume support, hash verification.
- **`state_manager.py`** — Tracks sync lifecycle: start_sync(), finish_sync() → records to `sync_log` table.
- **`logger.py`** — Structured logging to both console (rich) and daily log files (`logs/YYYY-MM-DD_run.log`).

### Database Module (`database/`)
- **`models.py`** — SQLite schema with two main tables:
  - `documents` — portal_id, portal_document_id, document_date, document_name, file_path, file_hash, downloaded flag, ocr_done flag.
  - `sync_log` — tracks each sync run (start, end, document counts, status, error_message).
- **`delta_manager.py`** — Detects new documents by comparing portal list against known IDs in DB. Methods: `get_known_ids()`, `register_document()`, `mark_downloaded()`, `get_stats()`, `hash_file()`.

### Portal Adapter (`portals/`)
- **`base_portal.py`** — Abstract base class defining portal interface.
- **`diagnostyka_pl.py`** — Diagnostyka.pl (wyniki.diag.pl) implementation:
  - API base: `https://api.wyniki.diag.pl`
  - Auth: Cookie-based JWT (`jwt` cookie on wyniki.diag.pl)
  - Login: PESEL + hasło
  - Key methods: `wait_for_login()` (5-min timeout, persistent cookies), `fetch_document_list()` (scrolls to load all orders), `download_document()` (fetches PDF fileType=1 + CDA fileType=4).
  - Login detection: checks for JWT cookie presence; falls back to persistent session from previous run.
- **`badaj_to.py`** — Badaj.to (Śląskie Laboratoria Analityczne / ProfLab) implementation:
  - Base: `https://wyniki.badaj.to`
  - Auth: POST `/Login/Authenticate` with `numerKarty` (card number) + `haslo` (password)
  - CAPTCHA: Cloudflare Turnstile (requires manual interaction)
  - Login detection: checks for session cookie presence
  - Document fetching: HTML scraping (API structure TBD)

### Pipeline Module (`pipeline/`)
- **`ocr_dispatcher.py`** — Optional OCR processing (disabled by default, requires Tesseract).
- **`database_updater.py`** — Import processed documents into master lab database (not implemented in MVP).

### Tools Module (`tools/`)
- **`api_analyzer.py`** — Network traffic sniffer for reverse-engineering API endpoints. Captures all XHR requests during login flow. Outputs JSON report to `tools/api_reports/`.

## Configuration (`config/settings.yaml`)

Key sections:
- **paths** — `downloads` (output folder), `state_db` (SQLite path), `logs`.
- **chrome** — `executable` (Chrome binary path), `remote_debugging_port` (9222 for CDP).
- **portals.diagnostyka_pl** — `enabled`, `request_delay_ms`, `max_retries`.
- **portals.badaj_to** — `enabled`, `login_fields` (numerKarty/haslo), `captcha_sitekey`, `request_delay_ms`, `max_retries`.
- **ocr** — `enabled` (false by default), `engine` (tesseract), `language`.

### Important Config Notes
- `request_delay_ms: 1500` — safety delay between API requests to avoid rate-limiting.
- `max_retries: 3` — retry failed downloads up to 3 times.
- Chrome launches in non-headless mode with persistent profile to preserve login sessions across runs.
- Each portal can be independently enabled/disabled via config.
- Database stores documents from all portals with `portal_id` field for distinction.

## Sync Workflow (Multi-Lab, 7 Phases per Portal)

1. **Launch browser** (once) — BrowserManager calls `launch_persistent_context()`.
2. **For each enabled portal:**
   - **Wait for login** — Portal-specific login (PESEL or card number). 5-min timeout.
   - **Fetch document list** — Portal adapter calls API or scrapes, returns list of PortalDocument objects.
   - **Delta check** — DeltaManager queries DB for known document IDs in that portal, identifies new ones.
   - **Register new docs** — Insert new records into `documents` table with portal_id (downloaded=0).
   - **Download** — Loop through new documents, call `download_document()`, mark as downloaded (set hash, file_path, size).
   - **Summary** — Log stats per portal, update `sync_log` with counts.
3. **Final summary** — Report total downloads from all portals, close browser.

## Database Schema (Key Points)

### `documents` table
```sql
portal_id            -- e.g., "diagnostyka_pl"
portal_document_id   -- unique ID from API
document_date        -- blood draw date (YYYY-MM-DD)
document_name        -- e.g., "morfologia"
document_type        -- e.g., "LAB"
file_path            -- local path to downloaded PDF/XML
file_hash            -- SHA256 of file (for deduplication)
file_size_bytes      -- bytes
downloaded           -- 0 or 1
ocr_done             -- 0 or 1 (for future OCR pipeline)
master_imported      -- 0 or 1 (for future DB import)
created_at / updated_at
```

### `sync_log` table
Records metadata for each sync run: start time, end time, document counts on portal vs. DB, status ("success"/"failed"), error_message.

## File Naming Convention

Downloaded files are saved as: `YYYY-MM-DD_document_name.pdf` or `.xml`

Example: `2026-07-14_morfologia.pdf`, `2026-07-14_APPT_elektrolity.xml`

Date is the blood draw date from the API, not the download date.

## Debugging & Troubleshooting

### Check logs
```bash
type logs/2026-07-23_run.log
```

Logs include detailed phase info (launch, login, fetch, delta, download, summary) with timestamps and status.

### Check database state
```bash
sqlite3 state/collector.db "SELECT portal_id, COUNT(*) as count, SUM(downloaded) as dl FROM documents GROUP BY portal_id;"
```

### Simulate a download attempt
```bash
python run.py collect --limit=1
```

Minimal test: fetches only the most recent order. Useful for:
- Testing config changes
- Verifying login still works
- Checking API connectivity
- Inspecting file naming

### Analyze API traffic
```bash
python run.py analyze-api
```

Captures all network requests during login; outputs JSON to `tools/api_reports/diag_api_capture_*.json`.

## Development Notes

### Session Persistence
- Chrome profile stored in `state/chrome_profile/`. JWT cookies persist between runs → subsequent runs may auto-login without manual credential entry.
- To force fresh login: delete `state/chrome_profile/`.

### Rate Limiting
- Default `request_delay_ms: 1500` (1.5s between API calls).
- If you see 429/503 errors: increase delay or reduce `--limit`.
- Portal may block aggressive scraping; always use sensible delays.

### File Deduplication
- DeltaManager compares `file_hash` of downloaded file against DB.
- If file already exists (same hash): skipped automatically.
- Prevents redundant downloads on re-runs.

### Adding a New Portal (e.g., synlab.pl, medicover.pl)
1. Create `portals/synlab_pl.py` inheriting from `BasePortal`.
2. Implement required methods:
   - `wait_for_login()` — detect successful authentication (cookie, URL change, or element presence)
   - `fetch_document_list()` — return list of `PortalDocument` objects
   - `download_document(doc)` — download PDF/CDA and return local file path
3. Add config section to `settings.yaml`:
   ```yaml
   synlab_pl:
     enabled: true
     base_url: https://wyniki.synlab.pl
     request_delay_ms: 1500
     max_retries: 3
   ```
4. The portal will automatically integrate into `run.py:cmd_collect()` loop (no code changes needed).
5. Update `CLAUDE.md` with login/auth details for the new portal.

### Extending the Pipeline
- OCR: Enable `ocr.enabled = true` in config; hook into pipeline after download phase.
- Master DB import: Implement `DatabaseUpdater.import_documents()` to push records to external database.
- Both are scaffolded but not active in MVP.

## Dependencies

- **playwright** ≥1.49.0 — browser automation
- **pyyaml** 6.0.1 — config parsing
- **httpx** 0.27.0 — HTTP client for API calls
- **rich** 13.7.1 — colored terminal output
- **click** 8.1.7 — CLI framework (reserved for future expansion)
- **python-dateutil** 2.9.0 — date handling

## Important Constraints

1. **No credential storage** — Login is interactive, browser-driven only. Passwords never logged or saved.
2. **Persistent session** — Chrome profile maintained to avoid repeated manual login.
3. **Graceful degradation** — Missing CDA files don't fail the sync; retry logic for network errors.
4. **Rate-limited requests** — Configurable delay between API calls to avoid server blocking.
