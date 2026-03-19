"""Camoufox-backed browser session replacing Scrapling's DynamicSession.

Inherits from DynamicSession and only overrides start() to launch
Camoufox (Firefox) instead of Playwright Chromium. All other methods
(fetch, page pooling, response handling) are inherited unchanged.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from playwright.sync_api import sync_playwright
from camoufox import NewBrowser

from scrapling.engines._browsers._controllers import DynamicSession

from scrapling_enhanced.config import CamoufoxConfig
from scrapling_enhanced.engine._fingerprint import generate_rotated_fingerprint
from scrapling_enhanced.utils.addons import validate_addon_paths

log = logging.getLogger(__name__)


class CamoufoxDynamicSession(DynamicSession):
    """Browser session using Camoufox instead of Playwright Chromium.

    Inherits DynamicSession's fetch(), page pooling, response handling,
    and config validation. Only overrides start() to launch Camoufox.
    """

    def __init__(
        self,
        *,
        camoufox_config: Optional[CamoufoxConfig] = None,
        **kwargs: Any,
    ):
        # Store Camoufox config before parent init
        self._camoufox_config = camoufox_config or CamoufoxConfig()
        # Parent __init__ calls __validate__() which sets _config,
        # _context_options, _browser_options via DynamicSessionMixin
        super().__init__(**kwargs)

    def start(self) -> None:
        """Launch Camoufox browser instead of Playwright Chromium."""
        if self.playwright is not None:
            raise RuntimeError("Session has been already started")

        self.playwright = sync_playwright().start()

        try:
            # Build Camoufox kwargs from config
            camoufox_kwargs = self._camoufox_config.to_camoufox_kwargs()

            # Validate addon paths
            if "addons" in camoufox_kwargs:
                camoufox_kwargs["addons"] = validate_addon_paths(camoufox_kwargs["addons"])
                if camoufox_kwargs["addons"] is None:
                    log.warning("All configured addons were invalid; launching Camoufox without addons")
                    del camoufox_kwargs["addons"]

            # Generate rotated fingerprint if enabled
            if self._camoufox_config.rotate_fingerprint:
                fp_kwargs: dict[str, Any] = {}
                if self._camoufox_config.os:
                    fp_kwargs["os"] = self._camoufox_config.os
                if self._camoufox_config.window:
                    fp_kwargs["window"] = self._camoufox_config.window
                camoufox_kwargs["fingerprint"] = generate_rotated_fingerprint(**fp_kwargs)

            # Proxy: prefer CamoufoxConfig, fallback to Scrapling config
            if "proxy" not in camoufox_kwargs and self._config.proxy:
                camoufox_kwargs["proxy"] = CamoufoxConfig.translate_scrapling_proxy(
                    self._config.proxy
                )

            # Launch Camoufox (returns Playwright Browser object)
            self.browser = NewBrowser(self.playwright, **camoufox_kwargs)

            # Create context if not using proxy rotation
            if not self._config.proxy_rotator:
                self.context = self.browser.new_context(**self._context_options)
                self.context = self._initialize_context(self._config, self.context)

            self._is_alive = True

        except Exception:
            if hasattr(self, "browser") and self.browser is not None:
                try:
                    self.browser.close()
                except Exception:
                    pass
                self.browser = None
            self.playwright.stop()
            self.playwright = None
            raise
