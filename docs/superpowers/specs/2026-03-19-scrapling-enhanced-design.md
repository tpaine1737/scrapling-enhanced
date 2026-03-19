# scrapling-enhanced Design Spec

## Overview

**scrapling-enhanced** is a Python library that wraps [Scrapling](https://github.com/D4Vinci/Scrapling) and replaces its Chromium-based browser engine with [Camoufox](https://github.com/daijro/camoufox) — a custom anti-detect Firefox build with C++-level fingerprint injection. The library provides a drop-in replacement API for Scrapling while exposing all Camoufox-specific features as first-class configuration.

## Goals

- Drop-in compatible with Scrapling's public API
- Camoufox as the default and native browser engine for all browser-based fetchers
- Full exposure of Camoufox features: fingerprint config/rotation, addon loading, virtual display, geo-proxy auto-config, WebRTC/WebGL control
- Comprehensive test suite from day one
- Python 3.10+, PyPI-ready

## Architecture

### Approach: Engine Replacement (Wrapper)

scrapling-enhanced imports Scrapling as a dependency and creates a new Camoufox engine that plugs into Scrapling's engine architecture. HTTP-only classes pass through unchanged. Browser-based fetchers route through the Camoufox engine.

```
User code imports from scrapling_enhanced
    -> Same API as scrapling (drop-in)
    -> Browser fetchers route through CamoufoxEngine
        -> CamoufoxEngine uses camoufox sync/async API
        -> Fingerprints, addons, virtual display, geo-proxy all configurable
    -> HTTP fetchers (Fetcher) pass through to scrapling unchanged
    -> Parsing (Selector, Spider, etc.) pass through unchanged
```

Since Camoufox is built on Playwright (using Firefox's Juggler protocol), all Playwright page actions (click, scroll, fill, type, wait) work natively. Juggler sends inputs through Firefox's native input handlers, making interactions indistinguishable from real user actions.

## Package Structure

```
scrapling-enhanced/
├── pyproject.toml
├── src/
│   └── scrapling_enhanced/
│       ├── __init__.py              # Re-exports scrapling API + enhanced classes
│       ├── config.py                # CamoufoxConfig dataclass
│       ├── engine/
│       │   ├── __init__.py
│       │   ├── _base.py             # CamoufoxSession, AsyncCamoufoxSession
│       │   ├── _fingerprint.py      # Fingerprint management & rotation
│       │   └── _display.py          # Virtual display management
│       ├── fetchers/
│       │   ├── __init__.py
│       │   ├── fetcher.py           # Enhanced DynamicFetcher (Camoufox-native)
│       │   └── session.py           # Enhanced DynamicSession / StealthySession
│       └── utils/
│           ├── __init__.py
│           ├── addons.py            # Firefox addon loading helpers
│           └── geoproxy.py          # Proxy-based geolocation auto-config
├── tests/
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_engine.py
│   ├── test_fetchers.py
│   ├── test_fingerprint.py
│   ├── test_addons.py
│   ├── test_geoproxy.py
│   └── test_integration.py
└── docs/
```

## CamoufoxConfig

Central dataclass for all Camoufox-specific settings:

```python
@dataclass
class CamoufoxConfig:
    # Fingerprint
    fingerprint: dict | None = None          # Manual fingerprint properties
    auto_fingerprint: bool = True            # Auto-generate via BrowserForge
    rotate_fingerprint: bool = False         # New identity per context
    os_target: str | None = None             # "windows", "macos", "linux"

    # Display
    virtual_display: bool = False            # Run headful in virtual display
    display_size: tuple[int, int] = (1920, 1080)

    # Addons
    addons: list[str] = field(default_factory=list)  # Paths to .xpi files
    ublock: bool = True                      # Built-in uBlock Origin

    # Network
    webrtc: bool = True                      # Enable/disable WebRTC
    webgl: bool = True                       # Enable/disable WebGL
    load_images: bool = True                 # Toggle image loading

    # Geolocation
    geo_from_proxy: bool = False             # Auto-detect geo from proxy IP
    geolocation: dict | None = None          # Manual {lat, lng, accuracy}
    timezone: str | None = None              # e.g. "America/New_York"
    locale: str | None = None                # e.g. "en-US"
```

## API Surface

### Drop-in usage (existing Scrapling code works unchanged)

```python
from scrapling_enhanced import DynamicFetcher

fetcher = DynamicFetcher()
response = fetcher.fetch("https://example.com")
print(response.css("h1::text").get())
```

### With Camoufox features

```python
from scrapling_enhanced import DynamicFetcher, CamoufoxConfig

config = CamoufoxConfig(
    rotate_fingerprint=True,
    virtual_display=True,
    geo_from_proxy=True,
    addons=["./my_addon.xpi"],
)
fetcher = DynamicFetcher(camoufox_config=config)
response = fetcher.fetch("https://example.com")
```

### What passes through unchanged from Scrapling

- `Fetcher`, `AsyncFetcher`, `FetcherSession` — HTTP-only, no browser
- `Selector`, `Selectors`, `TextHandler`, `AttributesHandler` — parsing
- `Spider`, `Request`, `Response` — spider framework
- `ProxyRotator` — proxy management
- All CSS/XPath/find methods, adaptive parsing, `auto_save`, `find_similar`

### What changes

- `DynamicFetcher` / `DynamicSession` — Camoufox engine instead of Playwright/Chromium
- `StealthyFetcher` / `StealthySession` — Camoufox engine with full config exposure
- New `camoufox_config` parameter on all browser fetchers

## Engine Internals

### CamoufoxSession lifecycle

```
session.start()    -> launches Camoufox via camoufox.sync_api.Camoufox()
session.fetch(url) -> acquires page, navigates, captures response, returns to pool
session.close()    -> shuts down browser + virtual display if active
```

### Key implementation details

1. **Browser launch**: Uses `Camoufox(config={...})` context manager. `CamoufoxConfig` dataclass is translated into Camoufox's native config dict.

2. **Fingerprint rotation**: When `rotate_fingerprint=True`, each new context gets a fresh BrowserForge-generated fingerprint. `_fingerprint.py` manages generation and applies OS-consistent constraints.

3. **Virtual display**: `_display.py` manages Xvfb lifecycle on Linux servers. Starts before browser launch, tears down on close. No-op on macOS/Windows.

4. **Geo-proxy integration**: When `geo_from_proxy=True` and a proxy is set, `geoproxy.py` resolves the proxy IP's geolocation and auto-sets timezone, locale, and language. Uses Camoufox's built-in geoip module.

5. **Addon loading**: Passes `.xpi` file paths to Camoufox's `addons` parameter during browser launch. Validates files exist before launch.

6. **Page pooling**: Reuses Scrapling's pool pattern (max pages, busy tracking) adapted for Camoufox's Firefox contexts.

7. **Response handling**: Captures final document response during navigation, wraps in Scrapling's `ResponseFactory` for full Selector-based parsing.

### Playwright compatibility

Camoufox returns a standard Playwright `Browser`/`Page` object. All Playwright actions (click, scroll, fill, type, wait_for_selector, etc.) work natively. The Juggler protocol sends inputs through Firefox's native input handlers with built-in human-like cursor movement.

### Error handling

- Browser launch failures -> clear error about Camoufox installation
- Fingerprint inconsistencies -> warning log, auto-correct where possible
- Virtual display failures -> fallback to true headless with warning
- Addon load failures -> skip addon with warning, continue launch

## Testing Strategy

### Test layers

1. **Unit tests** (`test_config.py`, `test_fingerprint.py`, `test_addons.py`, `test_geoproxy.py`)
   - CamoufoxConfig validation and defaults
   - Fingerprint generation, rotation, OS consistency
   - Addon path validation
   - Geo-proxy IP -> timezone/locale resolution

2. **Engine tests** (`test_engine.py`)
   - CamoufoxSession lifecycle (start -> fetch -> close)
   - Page pool management
   - Virtual display start/teardown
   - Config dict translation
   - Error handling

3. **Fetcher tests** (`test_fetchers.py`)
   - Drop-in compatibility: same method signatures as Scrapling
   - DynamicFetcher and StealthyFetcher route through Camoufox
   - Fetcher / AsyncFetcher pass through unchanged
   - camoufox_config parameter accepted and applied
   - Response objects have full parsing capabilities

4. **Integration tests** (`test_integration.py`)
   - Real browser launch with Camoufox
   - Fetch live page, verify Selector/CSS/XPath parsing
   - Fingerprint rotation produces different identities
   - Proxy rotation with geo-auto-config
   - Spider framework with Camoufox-backed sessions

### Tools

- `pytest` + `pytest-asyncio`
- Integration tests marked `@pytest.mark.integration` (skippable in CI)

## Dependencies

```toml
[project]
name = "scrapling-enhanced"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "scrapling>=0.4",
    "camoufox>=0.4",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5.0",
    "ruff>=0.4",
    "mypy>=1.10",
]
```

- Minimum versions pinned, not exact — allows upstream updates
- No vendored/forked code — pure wrapper
- Camoufox handles its own Firefox binary download
- `src/` layout with `py.typed` marker for PEP 561
