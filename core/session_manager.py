"""Session takeover — extracts tokens/cookies after manual user login."""

import json
import time
from typing import Optional
from playwright.sync_api import Page


class SessionManager:
    def __init__(self, page: Page, portal_config: dict, logger):
        self.page = page
        self.portal_config = portal_config
        self.log = logger
        self._token: Optional[str] = None
        self._cookies: list[dict] = []

    def wait_for_login(self, timeout_seconds: int = 300) -> bool:
        """
        Block until login is detected or timeout.
        Detection strategy (in order):
          1. URL changes away from login page (most reliable)
          2. Bearer token appears in localStorage/sessionStorage
          3. login_success_selector becomes visible in DOM
        """
        success_selector = self.portal_config.get("login_success_selector")

        self.log.info("Waiting for manual login... (you have 5 minutes)")

        deadline = time.time() + timeout_seconds
        initial_url = self.page.url

        while time.time() < deadline:
            try:
                # Check URL changed from login page (most reliable)
                current_url = self.page.url
                if current_url and current_url != initial_url and "login" not in current_url.lower():
                    self.log.info(f"Login detected: URL changed to {current_url}")
                    self._capture_cookies()
                    return True

                # Check for Bearer token in storage
                token = self.page.evaluate(
                    """() => {
                        for (let key of Object.keys(localStorage)) {
                            const val = localStorage.getItem(key);
                            if (val && val.length > 20 && (key.toLowerCase().includes('token') || key.toLowerCase().includes('auth'))) {
                                return val;
                            }
                        }
                        for (let key of Object.keys(sessionStorage)) {
                            const val = sessionStorage.getItem(key);
                            if (val && val.length > 20 && (key.toLowerCase().includes('token') || key.toLowerCase().includes('auth'))) {
                                return val;
                            }
                        }
                        return null;
                    }"""
                )
                if token:
                    self._token = token
                    self.log.info("Login detected: auth token found in storage")
                    self._capture_cookies()
                    return True

                # Check DOM selector
                if success_selector and self.page.query_selector(success_selector):
                    self.log.info(f"Login detected: selector '{success_selector}' visible")
                    self._capture_cookies()
                    return True

            except Exception:
                pass  # page may be navigating

            time.sleep(2)

        self.log.error("Login timeout — user did not complete login within the allowed time")
        return False

    def _capture_cookies(self):
        try:
            self._cookies = self.page.context.cookies()
        except Exception as e:
            self.log.warning(f"Could not capture cookies: {e}")

    def get_auth_headers(self) -> dict:
        headers = {}
        if self._token:
            # Strip JSON wrapper if stored as JSON string
            token = self._token.strip('"')
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def get_cookies(self) -> list[dict]:
        return self._cookies

    @property
    def token(self) -> Optional[str]:
        return self._token
