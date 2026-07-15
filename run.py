"""
Medical Data Collector — CLI entry point.

Usage:
    python run.py collect            # run full sync for all enabled portals
    python run.py analyze-api        # run API analyzer (step 1: discovery)
    python run.py status             # show sync statistics from DB
"""

import sys
import yaml
from pathlib import Path


def load_config(path: str = "config/settings.yaml") -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def cmd_analyze_api(config: dict):
    from tools.api_analyzer import run as analyze
    analyze()


def cmd_status(config: dict):
    from database.models import init_database, get_connection
    from rich.table import Table
    from rich.console import Console

    db_path = config["paths"]["state_db"]
    init_database(db_path)
    conn = get_connection(db_path)

    console = Console()
    table = Table(title="Sync Status")
    table.add_column("Portal")
    table.add_column("Total", justify="right")
    table.add_column("Downloaded", justify="right")
    table.add_column("OCR done", justify="right")
    table.add_column("Imported", justify="right")

    rows = conn.execute(
        """SELECT portal_id,
           COUNT(*) as total,
           SUM(downloaded) as downloaded,
           SUM(ocr_done) as ocr_done,
           SUM(master_imported) as imported
           FROM documents GROUP BY portal_id"""
    ).fetchall()

    for r in rows:
        table.add_row(r["portal_id"], str(r["total"]), str(r["downloaded"] or 0),
                      str(r["ocr_done"] or 0), str(r["imported"] or 0))

    console.print(table)
    conn.close()


def cmd_collect(config: dict):
    from database.models import init_database
    from database.delta_manager import DeltaManager
    from core.state_manager import StateManager
    from core.logger import get_logger
    from core.browser_manager import BrowserManager
    from portals.diagnostyka_pl import DiagnostykaPl

    log = get_logger("collector", config["paths"]["logs"])
    db_path = config["paths"]["state_db"]
    init_database(db_path)

    delta = DeltaManager(db_path)
    state = StateManager(db_path)
    bm = BrowserManager(config, log)

    portal_cfg = config.get("portals", {}).get("diagnostyka_pl", {})
    if not portal_cfg.get("enabled", False):
        log.info("diagnostyka_pl is disabled in config")
        return

    download_dir = config["paths"]["downloads"]
    log.info(f"💾 Download directory: {download_dir}")
    log.info(f"🗄️  Database: {db_path}")

    log.info("=" * 60)
    log.info("🚀 === Medical Data Collector START ===")
    log.info("=" * 60)
    sync_id = state.start_sync("diagnostyka_pl", "")

    try:
        # PHASE 1: Launch browser
        log.info("\n[PHASE 1] Launching browser...")
        context, page = bm.launch_pwa()
        log.info("✓ Browser launched")

        # PHASE 2: Create portal adapter
        portal = DiagnostykaPl(page, config, download_dir, log)

        # PHASE 3: Wait for login
        log.info("\n[PHASE 2] Waiting for login...")
        log.info("👤 Please log in to Diagnostyka manually in the browser window.")
        if not portal.wait_for_login():
            log.error("❌ Login failed or timed out. Aborting.")
            state.finish_sync(sync_id, status="failed", error_message="login_timeout")
            return

        log.info("✓✓✓ Login confirmed!")

        # PHASE 4: Fetch document list
        log.info("\n[PHASE 3] Fetching document list...")
        docs = portal.fetch_document_list()
        on_portal = len(docs)
        log.info(f"📊 Total on portal: {on_portal} documents")

        # PHASE 5: Delta check
        log.info("\n[PHASE 4] Checking database...")
        known_ids = delta.get_known_ids("diagnostyka_pl")
        log.info(f"📦 Already in DB: {len(known_ids)} documents")

        new_docs = [d for d in docs if d.portal_document_id not in known_ids]
        skipped = on_portal - len(new_docs)
        log.info(f"✨ New documents: {len(new_docs)} | Skipped: {skipped}")

        if len(new_docs) == 0:
            log.info("ℹ️  No new documents to download")
            state.finish_sync(
                sync_id, status="success",
                documents_on_portal=on_portal,
                documents_in_db=len(known_ids),
                documents_new=0,
                documents_skipped=skipped,
                documents_downloaded=0,
            )
            return

        # Register new documents
        for doc in new_docs:
            delta.register_document(
                "diagnostyka_pl", doc.portal_document_id,
                doc.document_date, doc.document_name, doc.document_type
            )

        # PHASE 6: Download
        log.info(f"\n[PHASE 5] Downloading {len(new_docs)} documents...")
        downloaded = 0
        for idx, doc in enumerate(new_docs, 1):
            log.info(f"   [{idx}/{len(new_docs)}] {doc.document_name} ({doc.document_date})")
            result = portal.download_document(doc)
            if result:
                file_hash = DeltaManager.hash_file(result)
                size = Path(result).stat().st_size
                delta.mark_downloaded("diagnostyka_pl", doc.portal_document_id,
                                      result, file_hash, size)
                downloaded += 1
                log.info(f"       ✓ Downloaded {size} bytes → {Path(result).name}")
            else:
                log.warning(f"       ✗ Failed to download")

        # PHASE 7: Summary
        log.info("\n[PHASE 6] Sync summary...")
        state.finish_sync(
            sync_id, status="success",
            documents_on_portal=on_portal,
            documents_in_db=len(known_ids),
            documents_new=len(new_docs),
            documents_skipped=skipped,
            documents_downloaded=downloaded,
        )

        stats = delta.get_stats("diagnostyka_pl")
        log.info("=" * 60)
        log.info(f"✓ SUCCESS — Downloaded: {downloaded} | Total in DB: {stats.get('total', 0)}")
        log.info("=" * 60)

        # Podsumowanie pobranych plików
        log.info("\n📋 LISTA POBRANYCH PLIKÓW:")
        log.info("-" * 80)
        total_size = 0
        file_list = sorted(Path(download_dir).glob("*.*"))
        for f in file_list:
            size = f.stat().st_size
            total_size += size
            log.info(f"  {f.name:<70} {size // 1024:>6} KB")
        log.info("-" * 80)
        log.info(f"  Łącznie: {len(file_list)} plików | {total_size // 1024 // 1024} MB ({total_size:,} B)")
        log.info("=" * 60)

    except Exception as e:
        log.exception(f"❌ Collector error: {e}")
        state.finish_sync(sync_id, status="failed", error_message=str(e))
    finally:
        log.info("\n🔌 Closing browser...")
        bm.close()
        log.info("✓ Done")


COMMANDS = {
    "collect": cmd_collect,
    "analyze-api": cmd_analyze_api,
    "status": cmd_status,
}


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "collect"
    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd}")
        print(f"Available: {', '.join(COMMANDS)}")
        sys.exit(1)

    config = load_config()

    # Parse --limit i --last flags
    limit = None
    for arg in sys.argv[2:]:
        if arg.startswith("--limit="):
            limit = int(arg.split("=")[1])
            config["collector_limit"] = limit
        if arg == "--last":
            config["collector_last"] = True

    COMMANDS[cmd](config)
