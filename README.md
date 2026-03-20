# scrapling-enhanced

A drop-in wrapper around [Scrapling](https://github.com/D4Vinci/Scrapling) that replaces its Chromium-based browser engine with [Camoufox](https://github.com/daijro/camoufox) — an anti-detect Firefox build with C++-level fingerprint injection. All of Scrapling's parsing, adaptive selectors, and response handling work unchanged. Only the browser engine changes.

```python
# Before (original Scrapling)
from scrapling import DynamicFetcher
response = DynamicFetcher.fetch("https://example.com")

# After (scrapling-enhanced — exact same call, Camoufox under the hood)
from scrapling_enhanced import DynamicFetcher
response = DynamicFetcher.fetch("https://example.com")
```

---

## Why Camoufox?

Standard Scrapling uses Playwright/Chromium (DynamicFetcher) and Patchright/Chromium (StealthyFetcher). Both are Chromium-based and share the same browser engine fingerprint pool — detectable by sophisticated WAFs.

Camoufox is a custom Firefox build where fingerprint spoofing happens at the **C++ level**, not via JavaScript injection. This means:

- Canvas, WebGL, WebRTC, fonts, screen, navigator, and timing APIs are spoofed before the page JS ever runs
- No `Object.defineProperty` patches that can be detected
- Built on Firefox's Juggler protocol — returns standard Playwright `Browser`/`Page` objects
- Every launch can have a completely unique browser identity via BrowserForge fingerprints

---

## Installation

```bash
pip install scrapling-enhanced
```

Install the Camoufox Firefox binary (one-time):

```bash
python -m camoufox fetch
```

**Requirements:** Python 3.10+

---

## Quick Start

### Basic fetch (drop-in replacement)

```python
from scrapling_enhanced import DynamicFetcher

response = DynamicFetcher.fetch("https://example.com")
print(response.css("h1::text").get())
print(response.status)  # 200
```

### With Camoufox features

```python
from scrapling_enhanced import DynamicFetcher, CamoufoxConfig

config = CamoufoxConfig(
    headless=True,
    humanize=True,          # human-like mouse movement
    rotate_fingerprint=True, # new BrowserForge identity per session
    os="windows",
    locale="en-US",
)
DynamicFetcher.configure(camoufox_config=config)
response = DynamicFetcher.fetch("https://example.com")
```

### Stealth mode (for anti-bot sites)

```python
from scrapling_enhanced import StealthyFetcher, CamoufoxConfig

config = CamoufoxConfig(
    headless=True,
    humanize=2.0,           # 2-second humanize delay multiplier
    block_webrtc=True,      # prevent IP leaks
    geoip=True,             # auto geo from proxy IP
    proxy={
        "server": "http://proxy.example.com:8080",
        "username": "user",
        "password": "pass",
    },
)
StealthyFetcher.configure(camoufox_config=config)
response = StealthyFetcher.fetch(
    "https://example.com",
    solve_cloudflare=True,  # inherited Scrapling CF solver
)
```

---

## API Reference

### `DynamicFetcher`

Subclass of Scrapling's `DynamicFetcher`. Uses Camoufox/Firefox instead of Playwright/Chromium. All Scrapling `DynamicFetcher` parameters work unchanged.

#### `DynamicFetcher.configure(**kwargs)`

Set persistent options for all subsequent `fetch()` calls. Call once before scraping.

| Parameter | Type | Description |
|-----------|------|-------------|
| `camoufox_config` | `CamoufoxConfig` | Camoufox browser options. See [CamoufoxConfig](#camoufoxconfig). |
| `huge_tree` | `bool` | Allow parsing of very large HTML documents. |
| `adaptive` | `bool` | Enable adaptive selector storage. |
| `storage` | `StorageBackend` | Storage backend for adaptive selectors. |
| `storage_args` | `dict` | Arguments passed to the storage backend. |
| `keep_cdata` | `bool` | Preserve CDATA sections in parsed tree. |
| `keep_comments` | `bool` | Preserve HTML comments in parsed tree. |
| `adaptive_domain` | `str` | Domain scope for adaptive selectors. |

#### `DynamicFetcher.fetch(url, **kwargs) → Response`

Fetch a URL using a Camoufox browser session. Returns a Scrapling `Response` object.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | required | Target URL |
| `headless` | `bool` | `True` | Run browser without visible window |
| `network_idle` | `bool` | `False` | Wait for network to go idle before capturing |
| `timeout` | `int` | `30000` | Page load timeout in milliseconds |
| `wait` | `int` | `0` | Extra wait after page load (ms) |
| `proxy` | `str\|dict` | `None` | Proxy — overrides `CamoufoxConfig.proxy` |
| `proxy_rotator` | `ProxyRotator` | `None` | Scrapling `ProxyRotator` instance |
| `selector_config` | `dict` | `{}` | Parser selector overrides |
| `screenshot` | `bool` | `False` | Capture screenshot into response |
| `page_action` | `callable` | `None` | Async callable called with the Playwright `Page` before capture |
| `locale` | `str` | `None` | Browser locale (e.g. `"tr-TR"`) |
| `timezone_id` | `str` | `None` | Timezone override |
| `cookies` | `list[dict]` | `None` | Cookies to inject before navigation |
| `extra_headers` | `dict` | `None` | Additional HTTP headers |

#### `DynamicFetcher.async_fetch(url, **kwargs)`

Not yet implemented. Raises `NotImplementedError`.

---

### `StealthyFetcher`

Subclass of Scrapling's `StealthyFetcher`. Uses Camoufox/Firefox instead of Patchright/Chromium. Inherits Scrapling's Cloudflare Turnstile solver.

Accepts all the same parameters as `DynamicFetcher` plus:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `solve_cloudflare` | `bool` | `False` | Enable Cloudflare Turnstile solver. Automatically sets `disable_coop=True` in Camoufox. |
| `block_webrtc` | `bool` | `False` | Block WebRTC at Scrapling config level. Mapped to Camoufox's `block_webrtc`. |
| `allow_webgl` | `bool` | `True` | If `False`, mapped to Camoufox's `block_webgl=True`. |
| `hide_canvas` | `bool` | `True` | Scrapling flag — ignored for Camoufox (canvas spoofed at C++ level). |

**Cloudflare note:** The solver works against Turnstile `embedded` and `non-interactive` variants. The `managed` variant (served to certain IP ranges or browser types) requires a residential proxy to resolve.

---

### `CamoufoxConfig`

Dataclass holding all Camoufox browser options. Pass an instance to `configure(camoufox_config=...)`.

All fields default to `None` (not set). Only non-`None` fields are forwarded to Camoufox.

#### Fingerprint fields

| Field | Type | Description |
|-------|------|-------------|
| `config` | `dict[str, Any]` | Manual fingerprint property overrides. Keys match Camoufox's property names (e.g. `{"navigator.platform": "Win32"}`). |
| `fingerprint` | `Fingerprint` | A pre-generated BrowserForge `Fingerprint` object. Overrides `config`. |
| `os` | `str \| list[str] \| tuple[str, ...]` | Target OS for fingerprint generation. Values: `"windows"`, `"macos"`, `"linux"`. Can be a list to allow any of them. |
| `ff_version` | `int` | Target Firefox version. **Warning:** Camoufox will emit a `LeakWarning` — only use if needed, pass `i_know_what_im_doing=True`. |
| `rotate_fingerprint` | `bool` | **scrapling-enhanced extension.** When `True`, generates a fresh BrowserForge fingerprint for every session via `camoufox.utils.generate_fingerprint()`. Respects `os` and `window` for consistency. |

#### Display & interaction fields

| Field | Type | Description |
|-------|------|-------------|
| `headless` | `bool \| "virtual"` | `True` = headless, `False` = headed, `"virtual"` = headed with Xvfb virtual display (Linux). |
| `screen` | `Screen` | BrowserForge `Screen` object specifying screen dimensions. |
| `window` | `tuple[int, int]` | Window size as `(width, height)`. Also used to constrain fingerprint generation when `rotate_fingerprint=True`. |
| `humanize` | `bool \| float` | Human-like cursor movement. `True` = enabled with default delay, `float` = delay multiplier (e.g. `2.0` = 2× slower). |

#### Addon fields

| Field | Type | Description |
|-------|------|-------------|
| `addons` | `list[str]` | Paths to `.xpi` Firefox addon files. Invalid paths are skipped with a warning. |
| `exclude_addons` | `list[DefaultAddons]` | Remove specific Camoufox default addons. |

#### Network & privacy fields

| Field | Type | Description |
|-------|------|-------------|
| `block_images` | `bool` | Block image loading (faster scraping). |
| `block_webrtc` | `bool` | Block WebRTC to prevent IP leaks. |
| `block_webgl` | `bool` | Block WebGL. |
| `webgl_config` | `tuple[str, str]` | Custom WebGL vendor and renderer strings `(vendor, renderer)`. |
| `disable_coop` | `bool` | Disable Cross-Origin-Opener-Policy. Required for `solve_cloudflare` (set automatically). **Warning:** Detectable by sophisticated WAFs. |
| `proxy` | `dict[str, str]` | Proxy config: `{"server": "http://host:port", "username": "...", "password": "..."}`. See also [Proxy formats](#proxy-formats). |

#### Geolocation & locale fields

| Field | Type | Description |
|-------|------|-------------|
| `geoip` | `bool \| str` | `True` = auto-detect geo from proxy IP (using bundled GeoLite2-City.mmdb). `"1.2.3.4"` = use that IP for lookup. Sets timezone, locale, language to match. |
| `locale` | `str \| list[str]` | Browser locale override (e.g. `"tr-TR"`, `"en-US"`). |

#### Font fields

| Field | Type | Description |
|-------|------|-------------|
| `fonts` | `list[str]` | Custom font list to add to browser. |
| `custom_fonts_only` | `bool` | If `True`, only use fonts from `fonts` (removes defaults). |

#### Advanced fields

| Field | Type | Description |
|-------|------|-------------|
| `main_world_eval` | `bool` | Enable JavaScript evaluation in the main world. |
| `enable_cache` | `bool` | Enable browser HTTP cache. |
| `firefox_user_prefs` | `dict[str, Any]` | Raw Firefox `about:config` preferences. |
| `executable_path` | `str \| Path` | Path to a custom Camoufox binary. |
| `args` | `list[str]` | Extra Firefox command-line arguments. |
| `env` | `dict[str, str \| float \| bool]` | Environment variables for the browser process. |
| `debug` | `bool` | Enable Camoufox debug logging. |
| `i_know_what_im_doing` | `bool` | Suppress Camoufox `LeakWarning`s for risky options (`ff_version`, `disable_coop`). |

#### Methods

```python
config.to_camoufox_kwargs() -> dict[str, Any]
```
Returns a dict suitable for passing to `NewBrowser()`. Filters out `None` values and scrapling-enhanced extension fields (`rotate_fingerprint`).

```python
CamoufoxConfig.translate_scrapling_proxy(proxy) -> dict[str, str] | None
```
Static method. Converts any Scrapling proxy format to Camoufox's dict format:
- `None` → `None`
- `"http://user:pass@host:8080"` → `{"server": "http://host:8080", "username": "user", "password": "pass"}`
- `{"server": ..., "username": ..., "password": ...}` → passed through
- `("http://host:8080", "user", "pass")` → dict equivalent

---

## Proxy Formats

Proxy can be provided in three ways:

### 1. In CamoufoxConfig (recommended for Camoufox-specific settings)

```python
config = CamoufoxConfig(
    proxy={"server": "http://host:8080", "username": "user", "password": "pass"},
    geoip=True,  # auto-set geo from proxy IP
)
```

### 2. As a Scrapling fetch kwarg (string or dict)

```python
response = DynamicFetcher.fetch(
    "https://example.com",
    proxy="http://user:pass@host:8080",  # string format
)
```

### 3. Via Scrapling's ProxyRotator

```python
from scrapling.fetchers import ProxyRotator

rotator = ProxyRotator(["http://proxy1:8080", "http://proxy2:8080"])
response = DynamicFetcher.fetch("https://example.com", proxy_rotator=rotator)
```

**Priority:** `CamoufoxConfig.proxy` takes precedence over Scrapling fetch kwargs. If both are absent, no proxy is used.

---

## Fingerprint Rotation

When `rotate_fingerprint=True`, each `fetch()` call generates a completely new browser identity using BrowserForge before launching the browser.

```python
from scrapling_enhanced import DynamicFetcher, CamoufoxConfig

config = CamoufoxConfig(
    rotate_fingerprint=True,
    os="windows",          # keep fingerprints consistent to Windows
    window=(1920, 1080),   # constrain screen size in fingerprint
    headless=True,
)
DynamicFetcher.configure(camoufox_config=config)

# Each call gets a different identity
response1 = DynamicFetcher.fetch("https://example.com")
response2 = DynamicFetcher.fetch("https://example.com")
```

Fingerprint generation uses `camoufox.utils.generate_fingerprint()` internally, which produces a correlated `Fingerprint` object covering navigator, screen, canvas, WebGL, fonts, and timing.

---

## Virtual Display (Linux)

On Linux servers without a display, use `headless="virtual"` to run a headed Firefox under Xvfb — useful for sites that detect headless mode:

```python
config = CamoufoxConfig(headless="virtual")
```

Camoufox manages the Xvfb process internally. No extra setup required.

---

## Addon Loading

Load Firefox extensions (`.xpi` files):

```python
config = CamoufoxConfig(
    addons=[
        "/path/to/ublock_origin.xpi",
        "/path/to/my_extension.xpi",
    ]
)
```

Invalid paths (not found or wrong extension) are skipped with a `WARNING` log message. If all addon paths are invalid, the browser launches without addons and logs a warning.

---

## Response Object

`fetch()` returns Scrapling's standard `Response` object with full parsing capabilities:

```python
response = DynamicFetcher.fetch("https://example.com")

# Status
response.status          # 200
response.url             # final URL after redirects

# CSS selectors (Scrapling syntax)
response.css("h1::text").get()            # first match as string
response.css("h1::text").getall()         # all matches as list
response.css(".item")                     # list of Selector objects
response.css(".item::attr(href)").get()   # attribute value

# XPath
response.xpath("//h1/text()").get()
response.xpath("//a/@href").getall()

# find / find_all (tag-based)
response.find("h1")
response.find_all("a", class_="link")

# Text content
response.get_all_text()
response.css(".title").get_all_text()

# Adaptive selectors (Scrapling feature)
# Remembers element positions across site changes
response.css(".price").get(auto_save=True)

# Re-fetch similar pages
similar = response.find_similar(".product-card")
```

---

## Pass-Through Classes

These are re-exported from Scrapling unchanged — use them exactly as you would in original Scrapling:

| Class | Description |
|-------|-------------|
| `Fetcher` | HTTP-only fetcher (no browser) |
| `AsyncFetcher` | Async HTTP-only fetcher |
| `Selector` | Parse HTML from a string |
| `Selectors` | Multiple selector support |
| `TextHandler` | Custom text handler type |
| `AttributesHandler` | Custom attribute handler type |

```python
from scrapling_enhanced import Fetcher, Selector

# HTTP fetch (no browser)
response = Fetcher.get("https://api.example.com/data")

# Parse HTML string directly
sel = Selector("<html><body><h1>Hello</h1></body></html>")
print(sel.css("h1::text").get())
```

---

## Configuration Patterns

### Global configure once, fetch many times

```python
from scrapling_enhanced import DynamicFetcher, CamoufoxConfig

DynamicFetcher.configure(
    camoufox_config=CamoufoxConfig(
        headless=True,
        humanize=True,
        block_webrtc=True,
        os="windows",
    )
)

urls = ["https://example.com/1", "https://example.com/2"]
for url in urls:
    response = DynamicFetcher.fetch(url, network_idle=True)
    print(response.css("h1::text").get())
```

### Per-fetch config (override global)

```python
# Set default
DynamicFetcher.configure(camoufox_config=CamoufoxConfig(headless=True))

# Override for a specific call by passing a new config directly to fetch
# (Not directly supported — create a new configure() call or use different fetcher instance)
```

### Reset config

```python
DynamicFetcher._camoufox_config = None  # back to Camoufox defaults
```

---

## Logging

scrapling-enhanced uses Python's standard `logging` module. Logger names:

| Logger | Emits |
|--------|-------|
| `scrapling_enhanced.engine._base` | Browser launch, proxy fallback, addon warnings |
| `scrapling_enhanced.engine._stealth` | Stealth session events, COOP setting |
| `scrapling_enhanced.utils.addons` | Per-addon validation warnings |

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Camoufox LeakWarnings

Camoufox emits `LeakWarning` for options that may increase detection risk:

| Option | Warning |
|--------|---------|
| `ff_version` | Spoofing Firefox version is detectable |
| `disable_coop` | Disabling COOP is detectable by sophisticated WAFs |

Suppress with `i_know_what_im_doing=True`:

```python
config = CamoufoxConfig(
    ff_version=120,
    disable_coop=True,
    i_know_what_im_doing=True,
)
```

---

## Anti-Bot Detection Notes

### What Camoufox protects against
- Canvas fingerprinting (spoofed at C++ level)
- WebGL vendor/renderer fingerprinting
- WebRTC IP leak
- Navigator property enumeration (platform, userAgent, hardwareConcurrency, etc.)
- Font fingerprinting
- Screen/window size fingerprinting
- Timing side-channels
- Headless detection via `navigator.webdriver`

### What requires additional measures
- **IP reputation:** Cloudflare and similar WAFs score IPs independently of browser fingerprint. Datacenter or flagged IPs may receive harder challenges regardless of browser stealth.
  - **Solution:** Use a residential proxy with `geoip=True`.
- **Cloudflare Turnstile "managed" mode:** Served to lower-trust IPs. The inherited Scrapling solver handles `embedded` and `non-interactive` variants but loops on `managed`.
  - **Solution:** Residential proxy (Turkish or target-country IP for country-specific sites).
- **TLS/HTTP2 fingerprint:** Firefox and Chromium have different JA3/JA4 TLS fingerprints. Some WAFs differentiate at this layer.
  - Camoufox uses Firefox's native TLS stack — cannot be changed.

---

## Architecture (for library contributors and AI agents)

### Class hierarchy

```
scrapling.DynamicFetcher
    └── scrapling_enhanced.fetchers.dynamic.DynamicFetcher   ← public API
            uses: CamoufoxDynamicSession as context manager

scrapling.StealthyFetcher
    └── scrapling_enhanced.fetchers.stealth.StealthyFetcher  ← public API
            uses: CamoufoxStealthySession as context manager

scrapling.engines._browsers._controllers.DynamicSession
    └── CamoufoxDynamicSession   ← overrides only start()
            start() calls: NewBrowser(playwright, **camoufox_kwargs)

scrapling.engines._browsers._stealth.StealthySession
    └── CamoufoxStealthySession  ← overrides only start()
            start() calls: NewBrowser(playwright, **camoufox_kwargs)
            maps: block_webrtc, allow_webgl → Camoufox kwargs
            maps: solve_cloudflare=True → disable_coop=True
```

### Session lifecycle

```
CamoufoxDynamicSession.__init__(camoufox_config, **scrapling_kwargs)
    -> stores _camoufox_config
    -> super().__init__(**scrapling_kwargs)  # validates config, sets _config, _context_options

CamoufoxDynamicSession.start()             # called by __enter__
    -> sync_playwright().start()
    -> _camoufox_config.to_camoufox_kwargs()
    -> validate_addon_paths() if addons
    -> generate_rotated_fingerprint() if rotate_fingerprint
    -> translate_scrapling_proxy() if proxy fallback needed
    -> NewBrowser(playwright, **camoufox_kwargs)  # returns Playwright Browser
    -> browser.new_context(**_context_options)     # if no proxy_rotator
    -> _initialize_context(_config, context)       # Scrapling inherited
    -> _is_alive = True

session.fetch(url)                         # inherited from DynamicSession
    -> page pool management
    -> page.goto(url)
    -> ResponseFactory.from_page(page)
    -> returns Response

CamoufoxDynamicSession.close()             # called by __exit__
    -> inherited from DynamicSession
```

### CamoufoxConfig.to_camoufox_kwargs() contract

- Returns only non-`None` fields
- Excludes `rotate_fingerprint` (scrapling-enhanced extension, not Camoufox-native)
- Does NOT modify proxy format — proxy must already be in `{"server": ...}` dict form
- `headless="virtual"` passes through unchanged (Camoufox handles Xvfb internally)
- Boolean `False` values ARE included (e.g. `headless=False`, `block_webgl=False`)

### Key internal modules

| Module | Responsibility |
|--------|----------------|
| `scrapling_enhanced.config` | `CamoufoxConfig` dataclass, proxy translation |
| `scrapling_enhanced.engine._base` | `CamoufoxDynamicSession` |
| `scrapling_enhanced.engine._stealth` | `CamoufoxStealthySession`, Scrapling→Camoufox param mapping |
| `scrapling_enhanced.engine._fingerprint` | `generate_rotated_fingerprint()` wrapper |
| `scrapling_enhanced.utils.addons` | `validate_addon_paths()` — existence + `.xpi` check |
| `scrapling_enhanced.utils.geoproxy` | `merge_geoip_into_kwargs()` — utility for programmatic kwargs assembly |
| `scrapling_enhanced.fetchers.dynamic` | `DynamicFetcher` — public classmethod API |
| `scrapling_enhanced.fetchers.stealth` | `StealthyFetcher` — public classmethod API |

### What is intentionally NOT reimplemented

The following are fully inherited from Scrapling and work unchanged:
- `fetch()` method and page pool logic
- Response building via `ResponseFactory`
- Cloudflare solver (`_cloudflare_solver`)
- Proxy rotation via `ProxyRotator`
- Adaptive selector storage
- CSS/XPath/find parsing
- `page_action` callback mechanism
- `screenshot`, `network_idle`, `timeout`, `wait`, `cookies`, `extra_headers`

The only override is `start()` in both session classes, which swaps `playwright.chromium.launch()` for `NewBrowser(playwright, **camoufox_kwargs)`.

---

## Running Tests

```bash
# Unit tests (no browser required)
pytest tests/ --ignore=tests/test_integration.py

# Integration tests (requires Camoufox browser installed)
pytest tests/ --run-integration

# Specific test file
pytest tests/test_config.py -v

# With coverage
pytest tests/ --ignore=tests/test_integration.py --cov=scrapling_enhanced
```

**Test suite:** 80 unit tests covering config, engine, fetchers, fingerprint, addons, geoproxy. Integration tests cover live fetch, CSS/XPath parsing, fingerprint rotation.

---

## Development

```bash
git clone https://github.com/yourname/scrapling-enhanced
cd scrapling-enhanced
pip install -e ".[dev]"

# Lint
ruff check src/ tests/

# Type check
mypy src/scrapling_enhanced/

# All checks
ruff check src/ tests/ && mypy src/scrapling_enhanced/ && pytest tests/ --ignore=tests/test_integration.py
```

---

## Dependencies

| Package | Version | Role |
|---------|---------|------|
| `scrapling` | `>=0.4` | Core scraping engine, parsing, adaptive selectors |
| `camoufox` | `>=0.4,<1.0` | Anti-detect Firefox browser |
| `playwright` | (via camoufox) | Browser automation protocol |
| `browserforge` | (via camoufox) | Fingerprint generation |

---

## License

MIT
