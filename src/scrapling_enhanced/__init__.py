"""scrapling-enhanced: Scrapling with native Camoufox browser integration."""

__version__ = "0.1.0"

# Re-export Scrapling's unchanged classes
from scrapling import (
    Fetcher,
    AsyncFetcher,
    Selector,
)

# Try to import optional extras (may not exist in all versions)
try:
    from scrapling.core.custom_types import AttributesHandler, TextHandler  # noqa: F401
except ImportError:
    pass

try:
    from scrapling.parser import Selectors  # noqa: F401
except ImportError:
    pass

# Export enhanced classes
from scrapling_enhanced.config import CamoufoxConfig
from scrapling_enhanced.fetchers.dynamic import DynamicFetcher
from scrapling_enhanced.fetchers.stealth import StealthyFetcher

__all__ = [
    # Scrapling pass-throughs
    "Fetcher",
    "AsyncFetcher",
    "Selector",
    # Enhanced
    "DynamicFetcher",
    "StealthyFetcher",
    "CamoufoxConfig",
]
