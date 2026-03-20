"""Proxy-based geolocation helpers for Camoufox.

Note: The engine handles geoip via CamoufoxConfig.to_camoufox_kwargs().
This utility is provided for programmatic kwargs construction outside the
standard fetch() flow.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Union


def merge_geoip_into_kwargs(
    kwargs: Dict[str, Any],
    geoip: Optional[Union[str, bool]],
) -> Dict[str, Any]:
    """Merge geoip setting into Camoufox launch kwargs.

    When geoip=True: Camoufox auto-detects geolocation from the proxy IP
    using its bundled GeoLite2-City.mmdb database.

    When geoip is an IP string: Camoufox uses that IP for geolocation lookup.

    Args:
        kwargs: Existing Camoufox launch kwargs (modified in place and returned).
        geoip: GeoIP setting from CamoufoxConfig.

    Returns:
        The kwargs dict with geoip merged in.
    """
    if geoip is not None:
        kwargs["geoip"] = geoip
    return kwargs
