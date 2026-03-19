"""CamoufoxConfig — typed configuration for Camoufox browser."""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
from urllib.parse import urlparse

try:
    from browserforge.fingerprints import Fingerprint, Screen
    from camoufox.addons import DefaultAddons
except ImportError:
    Fingerprint = Any  # type: ignore[assignment,misc]
    Screen = Any  # type: ignore[assignment,misc]
    DefaultAddons = Any  # type: ignore[assignment,misc]

# Fields that are scrapling-enhanced extensions, NOT Camoufox-native kwargs
_EXTENSION_FIELDS = frozenset({"rotate_fingerprint"})


@dataclass
class CamoufoxConfig:
    """Configuration for the Camoufox anti-detect browser.

    Fields split into two categories:
    1. Camoufox-native — passed directly to Camoufox()/NewBrowser()
    2. scrapling-enhanced extensions — custom logic (marked below)
    """

    # --- Camoufox-native parameters ---

    # Fingerprint
    config: Optional[Dict[str, Any]] = None
    fingerprint: Optional[Any] = None
    os: Optional[Union[Tuple[str, ...], List[str], str]] = None
    ff_version: Optional[int] = None

    # Display & interaction
    headless: Optional[Union[bool, Literal["virtual"]]] = None
    screen: Optional[Any] = None
    window: Optional[Tuple[int, int]] = None
    humanize: Optional[Union[bool, float]] = None

    # Addons
    addons: Optional[List[str]] = None
    exclude_addons: Optional[List[Any]] = None

    # Network & privacy
    block_images: Optional[bool] = None
    block_webrtc: Optional[bool] = None
    block_webgl: Optional[bool] = None
    webgl_config: Optional[Tuple[str, str]] = None
    disable_coop: Optional[bool] = None
    proxy: Optional[Dict[str, str]] = None

    # Geolocation & locale
    geoip: Optional[Union[str, bool]] = None
    locale: Optional[Union[str, List[str]]] = None

    # Fonts
    fonts: Optional[List[str]] = None
    custom_fonts_only: Optional[bool] = None

    # Advanced
    main_world_eval: Optional[bool] = None
    enable_cache: Optional[bool] = None
    firefox_user_prefs: Optional[Dict[str, Any]] = None
    executable_path: Optional[Union[str, Path]] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, Union[str, float, bool]]] = None
    debug: Optional[bool] = None
    i_know_what_im_doing: Optional[bool] = None

    # --- scrapling-enhanced extensions (NOT Camoufox-native) ---
    rotate_fingerprint: bool = False

    def to_camoufox_kwargs(self) -> Dict[str, Any]:
        """Convert to kwargs dict for Camoufox()/NewBrowser().

        Filters out None values and scrapling-enhanced extension fields.
        """
        kwargs: Dict[str, Any] = {}
        for f in fields(self):
            if f.name in _EXTENSION_FIELDS:
                continue
            value = getattr(self, f.name)
            if value is not None:
                kwargs[f.name] = value
        return kwargs

    @staticmethod
    def translate_scrapling_proxy(
        proxy: Optional[Union[str, Dict[str, str], Tuple[Any, ...]]],
    ) -> Optional[Dict[str, str]]:
        """Translate Scrapling's proxy formats to Camoufox's dict format.

        Scrapling accepts: str ("http://user:pass@host:port"), dict, or tuple.
        Camoufox expects: {"server": ..., "username": ..., "password": ...}
        """
        if proxy is None:
            return None

        if isinstance(proxy, dict):
            return proxy

        if isinstance(proxy, (tuple, list)):
            # Tuple format: (server, username, password) or (server,)
            result: Dict[str, str] = {"server": str(proxy[0])}
            if len(proxy) > 1:
                result["username"] = str(proxy[1])
            if len(proxy) > 2:
                result["password"] = str(proxy[2])
            return result

        # String format: "http://user:pass@host:port"
        parsed = urlparse(proxy)
        server = f"{parsed.scheme}://{parsed.hostname}"
        if parsed.port:
            server += f":{parsed.port}"
        result = {"server": server}
        if parsed.username:
            result["username"] = parsed.username
        if parsed.password:
            result["password"] = parsed.password
        return result
