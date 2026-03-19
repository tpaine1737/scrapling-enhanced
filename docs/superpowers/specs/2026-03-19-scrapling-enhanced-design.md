# scrapling-enhanced Design Spec

## Overview

**scrapling-enhanced** is a Python library that wraps [Scrapling](https://github.com/D4Vinci/Scrapling) and replaces its Chromium-based browser engine with [Camoufox](https://github.com/daijro/camoufox) — a custom anti-detect Firefox build with C++-level fingerprint injection. The library provides a drop-in replacement API for Scrapling while exposing all Camoufox-specific features as first-class configuration.

## Goals

- Drop-in compatible with Scrapling's public API (classmethod-based pattern)
- Camoufox as the default and native browser engine for all browser-based fetchers
- Full exposure of Camoufox features: fingerprint config/rotation, addon loading, virtual display, geo-proxy auto-config, WebRTC/WebGL control, humanize, COOP disable
- Comprehensive test suite from day one
- Python 3.10+, PyPI-ready

## Architecture

### Approach: Engine Replacement (Wrapper)

scrapling-enhanced imports Scrapling as a dependency and creates new Camoufox-backed session classes (`CamoufoxDynamicSession`, `CamoufoxStealthySession`) that replace Scrapling's `DynamicSession`/`StealthySession`. The fetcher classes (`DynamicFetcher`, `StealthyFetcher`) are subclassed to route through these Camoufox sessions instead of Playwright/Chromium sessions.

```
User code imports from scrapling_enhanced
    -> Same classmethod API as scrapling (drop-in)
    -> DynamicFetcher.fetch() / StealthyFetcher.fetch() use CamoufoxSession internally
        -> CamoufoxSession wraps camoufox sync/async API
        -> Fingerprints, addons, virtual display, geo-proxy all configurable
    -> DynamicFetcher.configure() accepts camoufox_config parameter
    -> HTTP fetchers (Fetcher, AsyncFetcher) pass through to scrapling unchanged
    -> Parsing (Selector, Selectors) pass through unchanged
```

### Key architectural decisions

1. **Scrapling uses classmethods, not instances.** `DynamicFetcher.fetch(url)` and `StealthyFetcher.fetch(url)` are `@classmethod`s. Configuration is done via `DynamicFetcher.configure(**kwargs)`. Our wrapper subclasses these and overrides the classmethods.

2. **The real work is in session classes.** `DynamicFetcher.fetch()` internally creates a `DynamicSession`. We replace `DynamicSession` with `CamoufoxDynamicSession` which uses Camoufox instead of Playwright/Chromium.

3. **Camoufox is Playwright-compatible.** Camoufox returns standard Playwright `Browser`/`Page` objects via Firefox's Juggler protocol. All page actions (click, scroll, fill, wait) work natively. Juggler sends inputs through Firefox's native input handlers with built-in human-like cursor movement.

4. **Virtual display is handled by Camoufox natively.** Camoufox's `headless='virtual'` parameter manages Xvfb internally — no custom `_display.py` module needed.

## Package Structure

```
scrapling-enhanced/
├── pyproject.toml
├── src/
│   └── scrapling_enhanced/
│       ├── __init__.py              # Re-exports scrapling API + enhanced classes
│       ├── py.typed                 # PEP 561 marker
│       ├── config.py                # CamoufoxConfig dataclass
│       ├── engine/
│       │   ├── __init__.py
│       │   ├── _base.py             # CamoufoxDynamicSession, AsyncCamoufoxDynamicSession
│       │   ├── _stealth.py          # CamoufoxStealthySession, AsyncCamoufoxStealthySession
│       │   └── _fingerprint.py      # Fingerprint management & rotation
│       ├── fetchers/
│       │   ├── __init__.py
│       │   ├── dynamic.py           # Enhanced DynamicFetcher (Camoufox-native)
│       │   └── stealth.py           # Enhanced StealthyFetcher (Camoufox-native)
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

Central dataclass for configuring Camoufox. Fields are split into two categories:

1. **Camoufox-native parameters** — map directly to `Camoufox()`/`NewBrowser()` kwargs
2. **scrapling-enhanced extensions** — custom logic built on top of Camoufox

```python
@dataclass
class CamoufoxConfig:
    # --- Camoufox-native parameters (passed to Camoufox()/NewBrowser()) ---

    # Fingerprint
    config: dict[str, Any] | None = None           # Manual fingerprint properties dict
    fingerprint: Fingerprint | None = None          # BrowserForge Fingerprint object
    os: tuple[str, ...] | list[str] | str | None = None  # Target OS(es)
    ff_version: int | None = None                   # Target Firefox version

    # Display & interaction
    headless: bool | Literal['virtual'] | None = None  # True, False, or 'virtual' (Xvfb)
    screen: Screen | None = None                    # BrowserForge Screen object
    window: tuple[int, int] | None = None           # Window size (width, height)
    humanize: bool | float | None = None            # Human-like cursor movement

    # Addons
    addons: list[str] | None = None                 # Paths to .xpi files
    exclude_addons: list[DefaultAddons] | None = None  # Remove default addons

    # Network & privacy
    block_images: bool | None = None                # Block image loading
    block_webrtc: bool | None = None                # Block WebRTC
    block_webgl: bool | None = None                 # Block WebGL
    webgl_config: tuple[str, str] | None = None     # Custom WebGL vendor/renderer
    disable_coop: bool | None = None                # Disable COOP (for cross-origin iframes)
    proxy: dict[str, str] | None = None             # Proxy config {"server": ..., "username": ..., "password": ...}

    # Geolocation & locale
    geoip: str | bool | None = None                 # GeoIP: True=auto from proxy, or IP string
    locale: str | list[str] | None = None           # Locale override

    # Fonts
    fonts: list[str] | None = None                  # Custom font list
    custom_fonts_only: bool | None = None           # Only use custom fonts

    # Advanced
    main_world_eval: bool | None = None             # Enable main world JS eval
    enable_cache: bool | None = None                # Enable browser cache
    firefox_user_prefs: dict[str, Any] | None = None  # Custom Firefox prefs
    executable_path: str | Path | None = None       # Custom Camoufox binary path
    args: list[str] | None = None                   # Extra browser args
    env: dict[str, str | float | bool] | None = None  # Environment variables
    debug: bool | None = None                       # Debug mode
    i_know_what_im_doing: bool | None = None        # Disable Camoufox safety warnings

    # --- scrapling-enhanced extensions (NOT Camoufox-native) ---

    rotate_fingerprint: bool = False                # Generate new BrowserForge fingerprint per context
                                                    # Uses generate_fingerprint(**config) internally

    def to_camoufox_kwargs(self) -> dict[str, Any]:
        """Convert to kwargs dict for Camoufox()/NewBrowser().

        This method:
        - Filters out None values and scrapling-enhanced extensions (rotate_fingerprint)
        - Passes headless='virtual' directly (Camoufox() handles Xvfb translation)
        - Translates Scrapling proxy format (str|Dict|Tuple) to Camoufox format (Dict[str,str])
          when proxy comes from Scrapling's configure() rather than CamoufoxConfig
        """
        ...
```

**Proxy handling:** Proxy can come from two sources:
1. `CamoufoxConfig.proxy` — already in Camoufox's `dict[str, str]` format, passed directly
2. Scrapling's `configure(proxy=...)` — can be `str | Dict | Tuple`, auto-translated to Camoufox's format by `to_camoufox_kwargs()`. Scrapling's proxy takes precedence if both are set.

**`headless='virtual'` handling:** The `'virtual'` literal is passed to `Camoufox()`/`NewBrowser()` directly (not to `launch_options()`). `NewBrowser()` internally converts it to `headless=False` + starts Xvfb. Our `to_camoufox_kwargs()` does not need to handle this translation.

**Fingerprint rotation:** `rotate_fingerprint` is a scrapling-enhanced extension. When `True`, each new browser context calls `camoufox.utils.generate_fingerprint(**config)` to create a fresh fingerprint (where `config` is the fingerprint properties dict, including OS filtering). This field is excluded from `to_camoufox_kwargs()` output.

## API Surface

### Scrapling's actual API pattern (classmethods)

Scrapling uses `@classmethod` for `fetch` and `async_fetch`. Instance creation is deprecated.

```python
# Scrapling's real pattern:
from scrapling import DynamicFetcher
response = DynamicFetcher.fetch("https://example.com")

# With configuration:
DynamicFetcher.configure(headless=True, network_idle=True)
response = DynamicFetcher.fetch("https://example.com")
```

### Drop-in usage (existing Scrapling code works unchanged)

```python
from scrapling_enhanced import DynamicFetcher

response = DynamicFetcher.fetch("https://example.com")
print(response.css("h1::text").get())
```

### With Camoufox features

```python
from scrapling_enhanced import DynamicFetcher, CamoufoxConfig

config = CamoufoxConfig(
    rotate_fingerprint=True,
    headless='virtual',
    geoip=True,
    humanize=2.0,
    addons=["./my_addon.xpi"],
    disable_coop=True,
)
DynamicFetcher.configure(camoufox_config=config)
response = DynamicFetcher.fetch("https://example.com")
```

### Async API

```python
from scrapling_enhanced import DynamicFetcher, CamoufoxConfig

config = CamoufoxConfig(humanize=True, geoip=True)
DynamicFetcher.configure(camoufox_config=config)
response = await DynamicFetcher.async_fetch("https://example.com")
```

### What passes through unchanged from Scrapling

- `Fetcher`, `AsyncFetcher`, `FetcherSession` — HTTP-only, no browser
- `Selector`, `Selectors` — parsing
- `TextHandler`, `AttributesHandler` — custom type handlers
- `ProxyRotator` — proxy management (from `scrapling.fetchers`)
- All CSS/XPath/find methods, adaptive parsing, `auto_save`, `find_similar`

### What changes

- `DynamicFetcher` — subclassed; `fetch()`/`async_fetch()` create `CamoufoxDynamicSession` instead of `DynamicSession`
- `StealthyFetcher` — subclassed; `fetch()`/`async_fetch()` create `CamoufoxStealthySession` instead of `StealthySession`
- `DynamicSession` / `AsyncDynamicSession` — replaced by Camoufox-backed equivalents
- `StealthySession` / `AsyncStealthySession` — replaced by Camoufox-backed equivalents
- `configure()` accepts new `camoufox_config` parameter on browser fetchers

## Engine Internals

### Session class hierarchy

```
Scrapling's DynamicSession (uses Playwright/Chromium)
    -> CamoufoxDynamicSession (uses Camoufox/Firefox)
        Overrides: start(), _create_browser(), _create_context()
        Delegates: fetch(), page pooling, response handling

Scrapling's StealthySession (uses Patchright/Chromium)
    -> CamoufoxStealthySession (uses Camoufox/Firefox)
        Overrides: start(), _create_browser(), _create_context()
        Delegates: fetch(), Cloudflare solving, page pooling
```

### CamoufoxSession lifecycle

```
session.start()    -> launches Camoufox via Camoufox(**config.to_camoufox_kwargs())
                   -> CamoufoxConfig.to_camoufox_kwargs() translates config to native kwargs
session.fetch(url) -> acquires page from pool, navigates, captures response, returns page
session.close()    -> shuts down browser (Camoufox handles virtual display cleanup)
```

### Key implementation details

1. **Browser launch**: `CamoufoxDynamicSession.start()` uses `Camoufox(**config.to_camoufox_kwargs())` context manager. The `CamoufoxConfig.to_camoufox_kwargs()` method translates the dataclass fields into Camoufox's native kwargs, filtering out `None` values.

2. **Fingerprint rotation**: When `rotate_fingerprint=True`, `_fingerprint.py` generates a fresh `BrowserForge.Fingerprint` for each new browser context via `camoufox.utils.generate_fingerprint()`. OS consistency is enforced by passing the `os` parameter.

3. **Virtual display**: Handled natively by Camoufox when `headless='virtual'` is set. No custom display management code needed — Camoufox starts/stops Xvfb internally.

4. **Geo-proxy integration**: When `geoip=True` and a proxy is set, Camoufox internally resolves the proxy IP's geolocation (using bundled GeoLite2-City.mmdb) and auto-sets timezone, locale, and language.

5. **Addon loading**: Passes `.xpi` file paths directly to Camoufox's `addons` parameter. `utils/addons.py` provides validation (file exists, valid .xpi) and helpers for managing `exclude_addons`.

6. **Page pooling**: Inherits Scrapling's pool pattern. Since Camoufox returns standard Playwright `Browser`/`BrowserContext`/`Page` objects, the pool semantics are compatible. The `persistent_context` mode maps to Camoufox's `persistent_context=True` parameter.

7. **Response handling**: Unchanged from Scrapling — captures final document response during navigation, wraps in Scrapling's `ResponseFactory` for full `Selector`-based parsing.

### Scrapling session parameters mapped to Camoufox

| Scrapling parameter | Camoufox equivalent | Notes |
|---------------------|---------------------|-------|
| `headless` | `headless` | Same semantics, plus `'virtual'` option |
| `proxy` | `proxy` | Dict format compatible |
| `proxy_rotator` | Per-fetch proxy selection | Rotator selects, passed to Camoufox |
| `timeout` | Playwright page timeout | Set on page object |
| `locale` | `locale` | Direct pass-through |
| `timezone_id` | Via `geoip` or `config` dict | Set in fingerprint config |
| `blocked_domains` | Route blocking via page | Handled at page level |
| `block_webrtc` (Stealth) | `block_webrtc` | Direct mapping |
| `allow_webgl` (Stealth) | `block_webgl` (inverted) | Invert boolean |
| `hide_canvas` (Stealth) | N/A | Camoufox handles canvas fingerprinting at C++ level; this param is ignored |
| `solve_cloudflare` (Stealth) | `disable_coop=True` + page interaction | COOP must be disabled for Turnstile iframes; CF solving logic reused from Scrapling |
| `init_script` | `main_world_eval` + page.add_init_script | Two-step |

### Error handling

- Browser launch failures -> clear error about Camoufox installation
- Fingerprint inconsistencies -> warning log, auto-correct via BrowserForge
- Virtual display failures -> Camoufox handles internally, falls back to headless
- Addon load failures -> skip addon with warning, continue launch
- Missing GeoLite2 DB -> warning, skip geoip auto-config

## Testing Strategy

### Test layers

1. **Unit tests** (`test_config.py`, `test_fingerprint.py`, `test_addons.py`, `test_geoproxy.py`)
   - CamoufoxConfig validation, defaults, and `to_camoufox_kwargs()` conversion
   - Fingerprint generation, rotation, OS consistency
   - Addon path validation (.xpi existence check)
   - GeoIP parameter handling

2. **Engine tests** (`test_engine.py`)
   - CamoufoxDynamicSession and CamoufoxStealthySession lifecycle (start -> fetch -> close)
   - Page pool management with Camoufox contexts
   - Config dict translation correctness
   - Error handling (missing install, bad config)
   - Async session equivalents

3. **Fetcher tests** (`test_fetchers.py`)
   - Drop-in compatibility: same classmethod signatures as Scrapling
   - `DynamicFetcher.fetch()` and `StealthyFetcher.fetch()` route through Camoufox sessions
   - `DynamicFetcher.configure(camoufox_config=...)` accepted and applied
   - `Fetcher` / `AsyncFetcher` pass through unchanged
   - Response objects have full Scrapling parsing capabilities
   - `async_fetch()` works with async Camoufox sessions

4. **Integration tests** (`test_integration.py`)
   - Real browser launch with Camoufox
   - Fetch live page, verify Selector/CSS/XPath parsing works
   - Fingerprint rotation produces different identities
   - Proxy rotation with geo-auto-config
   - `humanize` produces non-instant interactions
   - Addon loading works

### Tools

- `pytest` + `pytest-asyncio`
- Integration tests marked `@pytest.mark.integration` (skippable in CI without browser)

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
- Camoufox handles its own Firefox binary download on install
- `src/` layout with `py.typed` marker for PEP 561
