# 🦊 scrapling-enhanced

> **Scrapling, but with a Firefox brain transplant.**

A **drop-in wrapper** around [Scrapling](https://github.com/D4Vinci/Scrapling) that swaps its Chromium-based browser engine for [Camoufox](https://github.com/daijro/camoufox) — an anti-detect Firefox build that injects fingerprints at the **C++ level**, not via JavaScript. All of Scrapling's parsing, adaptive selectors, and response handling work completely unchanged. Only the engine changes.

```python
# Before — original Scrapling
from scrapling import DynamicFetcher
response = DynamicFetcher.fetch("https://example.com")

# After — exact same call, Camoufox under the hood 🦊
from scrapling_enhanced import DynamicFetcher
response = DynamicFetcher.fetch("https://example.com")
```

---

## 🤔 Why does this exist?

Standard Scrapling uses **Playwright/Chromium** (`DynamicFetcher`) and **Patchright/Chromium** (`StealthyFetcher`). Both share the same browser engine fingerprint pool — detectable by sophisticated WAFs that have learned to profile Chromium bots.

**Camoufox** is a custom Firefox build where fingerprint spoofing happens at the **C++ source level**, not via JavaScript injection. This means:

- 🚫 No `Object.defineProperty` hooks that leak into DevTools
- 🎨 Canvas, WebGL, WebRTC, fonts, screen, navigator, and timing APIs are spoofed **before the page JS ever runs**
- 🦊 Built on Firefox's Juggler protocol — returns standard Playwright `Browser`/`Page` objects
- 🎲 Every session can have a completely unique browser identity via BrowserForge fingerprints
- 🔐 Firefox JA3/JA4 TLS fingerprint — a completely different pool from Chromium

---

## ⚡ Installation

```bash
pip install scrapling-enhanced
```

Install the Camoufox Firefox binary (one-time, ~150MB):

```bash
python -m camoufox fetch
```

**Requirements:** Python 3.10+

---

## 🚀 Quick Start

### Drop-in replacement (zero config)

```python
from scrapling_enhanced import DynamicFetcher

response = DynamicFetcher.fetch("https://example.com")
print(response.css("h1::text").get())
print(response.status)  # 200
```

### With Camoufox stealth features

```python
from scrapling_enhanced import DynamicFetcher, CamoufoxConfig

config = CamoufoxConfig(
    headless=True,
    humanize=True,           # human-like mouse movement
    rotate_fingerprint=True, # fresh BrowserForge identity every session
    os="windows",
    locale="en-US",
)
DynamicFetcher.configure(camoufox_config=config)
response = DynamicFetcher.fetch("https://example.com")
```

### Full stealth mode for anti-bot sites

```python
from scrapling_enhanced import StealthyFetcher, CamoufoxConfig

config = CamoufoxConfig(
    headless=True,
    humanize=2.0,        # 2× slower human-like cursor movement
    block_webrtc=True,   # prevent IP leaks
    geoip=True,          # auto-set timezone, locale, language from proxy IP
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

### High-volume scraping with fingerprint rotation

```python
from scrapling_enhanced import DynamicFetcher, CamoufoxConfig

DynamicFetcher.configure(
    camoufox_config=CamoufoxConfig(
        rotate_fingerprint=True,  # unique identity per session
        os="windows",
        window=(1920, 1080),
        headless=True,
    )
)

urls = ["https://example.com/page/1", "https://example.com/page/2"]
for url in urls:
    response = DynamicFetcher.fetch(url, network_idle=True)
    print(response.css(".price::text").get())
```

---

## 🔬 scrapling-enhanced vs. Original Scrapling

### 🌐 Browser Engine

| | Original Scrapling | scrapling-enhanced |
|---|---|---|
| `DynamicFetcher` engine | Playwright + Chromium | Camoufox + Firefox 🦊 |
| `StealthyFetcher` engine | Patchright + patched Chromium | Camoufox + Firefox 🦊 |
| `Fetcher` / `AsyncFetcher` | httpx (unchanged) | httpx (identical pass-through) |
| Fingerprint injection layer | JavaScript (`Object.defineProperty`) | **C++ source patch** |
| Detectable JS patches | ⚠️ Yes — visible in DevTools | ✅ No — set before JS context exists |
| Browser identity pool | Chromium-only | Firefox-only |
| TLS/JA3 fingerprint | Chromium JA3 | Firefox JA3 (different pool) |

### 🛡️ Fingerprinting Capabilities

| Feature | Original Scrapling | scrapling-enhanced |
|---|---|---|
| Canvas spoofing | JS injection | **C++ level** ✅ |
| WebGL vendor/renderer | JS injection | **C++ level** + `webgl_config` field ✅ |
| Navigator properties | Patchright patches | **C++ level** ✅ |
| Screen/window size | Browser launch flags | `window` + `screen` fields |
| Fonts | Not configurable | `fonts`, `custom_fonts_only` fields |
| OS targeting | Not exposed | `os` field (`"windows"`, `"macos"`, `"linux"`) |
| Firefox version targeting | N/A | `ff_version` field |
| Manual property overrides | Not exposed | `config` dict field |
| BrowserForge `Fingerprint` object | Not exposed | `fingerprint` field |
| Per-session rotation | ❌ Not available | ✅ `rotate_fingerprint=True` |

### 🌍 Network & Privacy Controls

| Feature | Original Scrapling | scrapling-enhanced |
|---|---|---|
| WebRTC blocking | `block_webrtc=True` on fetch | `CamoufoxConfig(block_webrtc=True)` |
| WebGL blocking | `allow_webgl=False` on fetch | `CamoufoxConfig(block_webgl=True)` |
| Image blocking | ❌ Not available | ✅ `CamoufoxConfig(block_images=True)` |
| GeoIP auto-config | ❌ Not available | ✅ `CamoufoxConfig(geoip=True)` — sets timezone, locale, language from proxy IP |
| COOP disable | ❌ Not available | ✅ `CamoufoxConfig(disable_coop=True)` |

### 🖥️ Display Modes

| Mode | Original Scrapling | scrapling-enhanced |
|---|---|---|
| Headless | `headless=True` | `CamoufoxConfig(headless=True)` |
| Headed | `headless=False` | `CamoufoxConfig(headless=False)` |
| Virtual display (Xvfb) | ❌ Not available | ✅ `CamoufoxConfig(headless="virtual")` |

### ☁️ Cloudflare Solver

| | Original Scrapling | scrapling-enhanced |
|---|---|---|
| Solver implementation | Patchright-backed | Camoufox-backed, fully inherited |
| Turnstile `non-interactive` | ✅ Solved | ✅ Solved |
| Turnstile `embedded` | ✅ Solved | ✅ Solved |
| Turnstile `managed` | ✅ Solved (Chromium IPs get this less) | ⚠️ Needs residential proxy — Firefox IPs get `managed` more often |

---

## 🗺️ When to Use What

| Use case | Recommended |
|----------|-------------|
| General scraping, most public sites | `scrapling_enhanced.DynamicFetcher` |
| Cloudflare Turnstile (`embedded`/`non-interactive`) | `StealthyFetcher` + `solve_cloudflare=True` |
| Cloudflare Turnstile `managed` tier | `StealthyFetcher` + residential proxy + `geoip=True` |
| Sites that fingerprint canvas/WebGL at JS level | `DynamicFetcher` (C++ spoofing beats JS-level detection) |
| Sites that detect Chromium-based bots specifically | `scrapling_enhanced` (Firefox engine + different JA3) |
| Sites that work fine with Chromium and Patchright | Original `scrapling.StealthyFetcher` |
| HTTP-only APIs, no JavaScript needed | `Fetcher` or `AsyncFetcher` (identical to Scrapling) |
| High-volume scraping with fingerprint diversity | `DynamicFetcher` + `CamoufoxConfig(rotate_fingerprint=True)` |

---

## 📖 API Reference

### `DynamicFetcher`

Subclass of Scrapling's `DynamicFetcher`. Uses Camoufox/Firefox instead of Playwright/Chromium. **All Scrapling `DynamicFetcher` parameters work unchanged.**

#### `DynamicFetcher.configure(**kwargs)`

Set persistent options for all subsequent `fetch()` calls. Call once before scraping.

| Parameter | Type | Description |
|-----------|------|-------------|
| `camoufox_config` | `CamoufoxConfig` | Camoufox browser options |
| `huge_tree` | `bool` | Allow parsing of very large HTML documents |
| `adaptive` | `bool` | Enable adaptive selector storage |
| `storage` | `StorageBackend` | Storage backend for adaptive selectors |
| `storage_args` | `dict` | Arguments passed to the storage backend |
| `keep_cdata` | `bool` | Preserve CDATA sections in parsed tree |
| `keep_comments` | `bool` | Preserve HTML comments in parsed tree |
| `adaptive_domain` | `str` | Domain scope for adaptive selectors |

#### `DynamicFetcher.fetch(url, **kwargs) → Response`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | required | Target URL |
| `headless` | `bool` | `True` | Run browser without visible window |
| `network_idle` | `bool` | `False` | Wait for network idle before capturing |
| `timeout` | `int` | `30000` | Page load timeout (ms) |
| `wait` | `int` | `0` | Extra wait after page load (ms) |
| `proxy` | `str\|dict` | `None` | Proxy — overrides `CamoufoxConfig.proxy` |
| `proxy_rotator` | `ProxyRotator` | `None` | Scrapling `ProxyRotator` instance |
| `screenshot` | `bool` | `False` | Capture screenshot into response |
| `page_action` | `callable` | `None` | Async callable called with Playwright `Page` before capture |
| `locale` | `str` | `None` | Browser locale (e.g. `"tr-TR"`) |
| `timezone_id` | `str` | `None` | Timezone override |
| `cookies` | `list[dict]` | `None` | Cookies to inject before navigation |
| `extra_headers` | `dict` | `None` | Additional HTTP headers |

> ℹ️ `async_fetch` is not yet implemented and will raise `NotImplementedError`.

---

### `StealthyFetcher`

Subclass of Scrapling's `StealthyFetcher`. Uses Camoufox/Firefox instead of Patchright/Chromium. **Inherits Scrapling's Cloudflare Turnstile solver.**

Accepts all the same parameters as `DynamicFetcher`, plus:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `solve_cloudflare` | `bool` | `False` | Enable Cloudflare Turnstile solver. Auto-sets `disable_coop=True`. |
| `block_webrtc` | `bool` | `False` | Block WebRTC. Mapped to Camoufox's `block_webrtc`. |
| `allow_webgl` | `bool` | `True` | `False` maps to Camoufox's `block_webgl=True`. |
| `hide_canvas` | `bool` | `True` | Scrapling flag — ignored (canvas is spoofed at C++ level). |

> ⚠️ **Cloudflare `managed` tier:** Residential proxy required. The solver handles `embedded` and `non-interactive` variants out of the box.

---

### `CamoufoxConfig`

Dataclass holding all Camoufox browser options. Pass an instance to `configure(camoufox_config=...)`. All fields default to `None` — only non-`None` fields are forwarded to Camoufox.

#### 🧬 Fingerprint Fields

| Field | Type | Description |
|-------|------|-------------|
| `config` | `dict[str, Any]` | Manual fingerprint property overrides (e.g. `{"navigator.platform": "Win32"}`) |
| `fingerprint` | `Fingerprint` | Pre-generated BrowserForge `Fingerprint` object. Overrides `config`. |
| `os` | `str \| list[str]` | Target OS: `"windows"`, `"macos"`, `"linux"` |
| `ff_version` | `int` | Target Firefox version. ⚠️ Emits `LeakWarning` — use with `i_know_what_im_doing=True` |
| `rotate_fingerprint` | `bool` | **scrapling-enhanced extension.** Fresh BrowserForge identity every session. Respects `os` and `window`. |

#### 🖥️ Display & Interaction Fields

| Field | Type | Description |
|-------|------|-------------|
| `headless` | `bool \| "virtual"` | `True` = headless, `False` = headed, `"virtual"` = Xvfb virtual display (Linux) |
| `screen` | `Screen` | BrowserForge `Screen` object for screen dimensions |
| `window` | `tuple[int, int]` | Window size `(width, height)`. Also constrains fingerprint generation. |
| `humanize` | `bool \| float` | Human-like cursor movement. `float` = delay multiplier. |

#### 🧩 Addon Fields

| Field | Type | Description |
|-------|------|-------------|
| `addons` | `list[str]` | Paths to `.xpi` Firefox addon files. Invalid paths are skipped with a warning. |
| `exclude_addons` | `list[DefaultAddons]` | Remove specific Camoufox default addons |

#### 🔒 Network & Privacy Fields

| Field | Type | Description |
|-------|------|-------------|
| `block_images` | `bool` | Block image loading (faster scraping) |
| `block_webrtc` | `bool` | Block WebRTC to prevent IP leaks |
| `block_webgl` | `bool` | Block WebGL |
| `webgl_config` | `tuple[str, str]` | Custom WebGL `(vendor, renderer)` strings |
| `disable_coop` | `bool` | Disable Cross-Origin-Opener-Policy. Auto-set by `solve_cloudflare`. ⚠️ Detectable by sophisticated WAFs. |
| `proxy` | `dict[str, str]` | `{"server": "http://host:port", "username": "...", "password": "..."}` |

#### 🌍 Geolocation & Locale Fields

| Field | Type | Description |
|-------|------|-------------|
| `geoip` | `bool \| str` | `True` = auto-detect geo from proxy IP. `"1.2.3.4"` = use specific IP. Sets timezone, locale, language. |
| `locale` | `str \| list[str]` | Browser locale (e.g. `"tr-TR"`, `"en-US"`) |

#### 🔠 Font Fields

| Field | Type | Description |
|-------|------|-------------|
| `fonts` | `list[str]` | Custom font list |
| `custom_fonts_only` | `bool` | Use only custom fonts (removes defaults) |

#### ⚙️ Advanced Fields

| Field | Type | Description |
|-------|------|-------------|
| `main_world_eval` | `bool` | Enable JS evaluation in the main world |
| `enable_cache` | `bool` | Enable browser HTTP cache |
| `firefox_user_prefs` | `dict[str, Any]` | Raw `about:config` preferences |
| `executable_path` | `str \| Path` | Path to a custom Camoufox binary |
| `args` | `list[str]` | Extra Firefox command-line arguments |
| `env` | `dict[str, str \| float \| bool]` | Environment variables for the browser process |
| `debug` | `bool` | Enable Camoufox debug logging |
| `i_know_what_im_doing` | `bool` | Suppress `LeakWarning`s for risky options |

---

## 🔄 Proxy Formats

### 1. In CamoufoxConfig (recommended)

```python
config = CamoufoxConfig(
    proxy={"server": "http://host:8080", "username": "user", "password": "pass"},
    geoip=True,  # auto-set geo from proxy IP
)
```

### 2. As a fetch kwarg (string or dict)

```python
response = DynamicFetcher.fetch(
    "https://example.com",
    proxy="http://user:pass@host:8080",
)
```

### 3. Via Scrapling's ProxyRotator

```python
from scrapling.fetchers import ProxyRotator

rotator = ProxyRotator(["http://proxy1:8080", "http://proxy2:8080"])
response = DynamicFetcher.fetch("https://example.com", proxy_rotator=rotator)
```

> 📌 **Priority:** `CamoufoxConfig.proxy` takes precedence over fetch kwargs.

---

## 🎲 Fingerprint Rotation

When `rotate_fingerprint=True`, each `fetch()` call generates a completely new browser identity using BrowserForge before launching the browser.

```python
config = CamoufoxConfig(
    rotate_fingerprint=True,
    os="windows",         # keep fingerprints consistent to Windows
    window=(1920, 1080),  # constrain screen size in fingerprint
    headless=True,
)
DynamicFetcher.configure(camoufox_config=config)

# Each call gets a different identity 🎭
response1 = DynamicFetcher.fetch("https://example.com")
response2 = DynamicFetcher.fetch("https://example.com")
```

Fingerprint generation covers navigator, screen, canvas, WebGL, fonts, and timing — all correlated for a believable profile.

---

## 🐧 Virtual Display (Linux)

On Linux servers without a display, use `headless="virtual"` to run headed Firefox under Xvfb — useful for sites that detect headless mode:

```python
config = CamoufoxConfig(headless="virtual")
```

Camoufox manages the Xvfb process internally. No extra setup required.

---

## 🧩 Addon Loading

Load Firefox extensions (`.xpi` files):

```python
config = CamoufoxConfig(
    addons=[
        "/path/to/ublock_origin.xpi",
        "/path/to/my_extension.xpi",
    ]
)
```

Invalid paths are skipped with a `WARNING` log message. Browser always launches — even if all addons are invalid.

---

## 📦 Response Object

`fetch()` returns Scrapling's standard `Response` object with full parsing capabilities:

```python
response = DynamicFetcher.fetch("https://example.com")

# Status & metadata
response.status          # 200
response.url             # final URL after redirects

# CSS selectors (Scrapling syntax)
response.css("h1::text").get()            # first match as string
response.css("h1::text").getall()         # all matches as list
response.css(".item::attr(href)").get()   # attribute value

# XPath
response.xpath("//h1/text()").get()
response.xpath("//a/@href").getall()

# find / find_all (tag-based)
response.find("h1")
response.find_all("a", class_="link")

# Text content
response.get_all_text()

# Adaptive selectors — remembers element positions across site changes 🧠
response.css(".price").get(auto_save=True)

# Re-fetch similar pages
similar = response.find_similar(".product-card")
```

---

## 🪄 Pass-Through Classes

These are re-exported from Scrapling unchanged — use them exactly as in original Scrapling:

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

## 🧩 Configuration Patterns

### Configure once, fetch many times

```python
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

### Reset config

```python
DynamicFetcher._camoufox_config = None  # back to Camoufox defaults
```

---

## 📋 Logging

scrapling-enhanced uses Python's standard `logging` module.

| Logger | Emits |
|--------|-------|
| `scrapling_enhanced.engine._base` | Browser launch, proxy fallback, addon warnings |
| `scrapling_enhanced.engine._stealth` | Stealth session events, COOP setting |
| `scrapling_enhanced.utils.addons` | Per-addon validation warnings |

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## ⚠️ Camoufox LeakWarnings

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

## 🛡️ Anti-Bot Detection Notes

### ✅ What Camoufox protects against

- Canvas fingerprinting (C++ level spoofing)
- WebGL vendor/renderer fingerprinting
- WebRTC IP leaks
- Navigator property enumeration (platform, userAgent, hardwareConcurrency, etc.)
- Font fingerprinting
- Screen/window size fingerprinting
- Timing side-channels
- Headless detection via `navigator.webdriver`

### 🔧 What requires additional measures

| Problem | Solution |
|---------|----------|
| **IP reputation** — WAFs score IPs independently of browser fingerprint | Use a residential proxy + `geoip=True` |
| **Cloudflare `managed` tier** — served to lower-trust IPs | Residential proxy (match target country) |
| **TLS/HTTP2 fingerprint** — some WAFs differentiate at JA3/JA4 layer | Camoufox uses Firefox's native TLS stack — already different from Chromium |

---

## 🏗️ Architecture

### Class Hierarchy

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
```

The **only override** in both session classes is `start()` — which swaps `playwright.chromium.launch()` for `NewBrowser(playwright, **camoufox_kwargs)`. Everything else is inherited from Scrapling with zero changes.

### Key Internal Modules

| Module | Responsibility |
|--------|----------------|
| `scrapling_enhanced.config` | `CamoufoxConfig` dataclass, proxy translation |
| `scrapling_enhanced.engine._base` | `CamoufoxDynamicSession` |
| `scrapling_enhanced.engine._stealth` | `CamoufoxStealthySession`, param mapping |
| `scrapling_enhanced.engine._fingerprint` | `generate_rotated_fingerprint()` wrapper |
| `scrapling_enhanced.utils.addons` | `validate_addon_paths()` |
| `scrapling_enhanced.utils.geoproxy` | `merge_geoip_into_kwargs()` |
| `scrapling_enhanced.fetchers.dynamic` | `DynamicFetcher` — public classmethod API |
| `scrapling_enhanced.fetchers.stealth` | `StealthyFetcher` — public classmethod API |

---

## 🧪 Running Tests

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

> 📊 **Test suite:** 80 unit tests covering config, engine, fetchers, fingerprint, addons, geoproxy. Integration tests cover live fetch, CSS/XPath parsing, and fingerprint rotation.

---

## 🛠️ Development

```bash
git clone https://github.com/tpaine1737/scrapling-enhanced
cd scrapling-enhanced
pip install -e ".[dev]"

# Lint
ruff check src/ tests/

# Type check
mypy src/scrapling_enhanced/

# Run all checks
ruff check src/ tests/ && mypy src/scrapling_enhanced/ && pytest tests/ --ignore=tests/test_integration.py
```

---

## 📦 Dependencies

| Package | Version | Role |
|---------|---------|------|
| `scrapling` | `>=0.4` | Core scraping engine, parsing, adaptive selectors |
| `camoufox` | `>=0.4,<1.0` | Anti-detect Firefox browser |
| `playwright` | (via camoufox) | Browser automation protocol |
| `browserforge` | (via camoufox) | Fingerprint generation |

---

## 📄 License

MIT
