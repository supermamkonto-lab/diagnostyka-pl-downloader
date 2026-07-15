"""Chrome launch and CDP connection management for Diagnostyka PWA."""

import subprocess
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, BrowserContext, Page


class BrowserManager:
    def __init__(self, config: dict, logger):
        self.config = config
        self.log = logger
        self._playwright = None
        self._context: BrowserContext | None = None

    def launch_pwa(self) -> tuple[BrowserContext, Page]:
        """
        Launch Chrome normally (without PWA mode) using launch_persistent_context.
        Returns (context, page).
        User must complete login manually — we do not touch credentials.
        """
        chrome_cfg = self.config.get("chrome", {})
        executable = chrome_cfg.get("executable", "chrome")
        port = chrome_cfg.get("remote_debugging_port", 9222)

        # Use dedicated Playwright profile (persistent between runs)
        profile_dir = Path(self.config.get("paths", {}).get("state_db", "state/collector.db")).parent / "chrome_profile"
        profile_dir.mkdir(parents=True, exist_ok=True)

        self.log.info(f"Launching Chrome (dedicated profile)")

        self._playwright = sync_playwright().start()

        profile_directory = chrome_cfg.get("profile_directory", "Default")
        launch_args = [
            f"--remote-debugging-port={port}",
            f"--profile-directory={profile_directory}",
            "--no-first-run",
            "--no-default-browser-check",
        ]

        self._context = self._playwright.chromium.launch_persistent_context(
            str(profile_dir),
            executable_path=executable,
            headless=False,
            args=launch_args,
            slow_mo=50,
        )

        page = self._context.pages[0] if self._context.pages else self._context.new_page()
        self.log.info("Navigating to diag.pl...")
        page.goto("https://wyniki.diag.pl", wait_until="domcontentloaded")
        return self._context, page

    def connect_cdp(self) -> tuple[BrowserContext, Page]:
        """Connect to already-running Chrome via CDP (remote debugging port)."""
        port = self.config.get("chrome", {}).get("remote_debugging_port", 9222)
        self.log.info(f"Connecting to Chrome via CDP on port {port}")

        self._playwright = sync_playwright().start()
        browser = self._playwright.chromium.connect_over_cdp(f"http://localhost:{port}")
        ctx = browser.contexts[0]
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        return ctx, page

    def close(self):
        if self._context:
            self._context.close()
        if self._playwright:
            self._playwright.stop()
