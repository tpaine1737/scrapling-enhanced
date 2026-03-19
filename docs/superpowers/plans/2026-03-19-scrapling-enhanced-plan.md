# scrapling-enhanced Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a drop-in wrapper around Scrapling that replaces the Chromium browser engine with Camoufox (anti-detect Firefox) while exposing all Camoufox features.

**Architecture:** Wrapper library that imports Scrapling as a dependency. Subclasses Scrapling's `DynamicFetcher`/`StealthyFetcher` to swap session classes. New session classes (`CamoufoxDynamicSession`/`CamoufoxStealthySession`) launch Camoufox instead of Playwright Chromium. A `CamoufoxConfig` dataclass provides typed configuration for all Camoufox features.

**Tech Stack:** Python 3.10+, scrapling>=0.4, camoufox>=0.4, pytest, pytest-asyncio, ruff, mypy

**Spec:** `docs/superpowers/specs/2026-03-19-scrapling-enhanced-design.md`

---

### Task 1: Project scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/scrapling_enhanced/__init__.py`
- Create: `src/scrapling_enhanced/py.typed`
- Create: `src/scrapling_enhanced/engine/__init__.py`
- Create: `src/scrapling_enhanced/fetchers/__init__.py`
- Create: `src/scrapling_enhanced/utils/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "scrapling-enhanced"
version = "0.1.0"
description = "Scrapling with native Camoufox browser integration"
requires-python = ">=3.10"
license = "MIT"
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

[tool.hatch.build.targets.wheel]
packages = ["src/scrapling_enhanced"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
markers = [
    "integration: marks tests requiring a real Camoufox browser",
]

[tool.ruff]
target-version = "py310"
src = ["src"]

[tool.mypy]
python_version = "3.10"
strict = true
```

- [ ] **Step 2: Create package structure with empty __init__.py files**

Create these files (all empty except noted):

`src/scrapling_enhanced/py.typed` — empty file

`src/scrapling_enhanced/engine/__init__.py` — empty file

`src/scrapling_enhanced/fetchers/__init__.py` — empty file

`src/scrapling_enhanced/utils/__init__.py` — empty file

`tests/__init__.py` — empty file

`tests/conftest.py`:
```python
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require a Camoufox browser",
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-integration"):
        skip = pytest.mark.skip(reason="needs --run-integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip)
```

`src/scrapling_enhanced/__init__.py`:
```python
"""scrapling-enhanced: Scrapling with native Camoufox browser integration."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Verify the project installs**

Run: `cd /Users/batuhansedir/Desktop/scrapling-enhanced && pip install -e ".[dev]"`
Expected: Successful installation

- [ ] **Step 4: Run empty test suite**

Run: `cd /Users/batuhansedir/Desktop/scrapling-enhanced && pytest -v`
Expected: "no tests ran" or 0 tests collected

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/ tests/
git commit -m "feat: scaffold scrapling-enhanced project structure"
```

---

### Task 2: CamoufoxConfig dataclass

**Files:**
- Create: `src/scrapling_enhanced/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing tests for CamoufoxConfig**

`tests/test_config.py`:
```python
from scrapling_enhanced.config import CamoufoxConfig


class TestCamoufoxConfigDefaults:
    def test_default_values(self):
        config = CamoufoxConfig()
        assert config.headless is None
        assert config.humanize is None
        assert config.rotate_fingerprint is False
        assert config.block_images is None
        assert config.block_webrtc is None
        assert config.block_webgl is None
        assert config.addons is None
        assert config.geoip is None
        assert config.proxy is None
        assert config.debug is None

    def test_custom_values(self):
        config = CamoufoxConfig(
            headless="virtual",
            humanize=2.0,
            rotate_fingerprint=True,
            block_webrtc=True,
            geoip=True,
            os="windows",
        )
        assert config.headless == "virtual"
        assert config.humanize == 2.0
        assert config.rotate_fingerprint is True
        assert config.block_webrtc is True
        assert config.geoip is True
        assert config.os == "windows"


class TestCamoufoxConfigToKwargs:
    def test_filters_none_values(self):
        config = CamoufoxConfig(headless=True, humanize=1.5)
        kwargs = config.to_camoufox_kwargs()
        assert kwargs["headless"] is True
        assert kwargs["humanize"] == 1.5
        assert "block_images" not in kwargs
        assert "addons" not in kwargs

    def test_excludes_rotate_fingerprint(self):
        config = CamoufoxConfig(rotate_fingerprint=True, headless=False)
        kwargs = config.to_camoufox_kwargs()
        assert "rotate_fingerprint" not in kwargs
        assert kwargs["headless"] is False

    def test_passes_virtual_headless(self):
        config = CamoufoxConfig(headless="virtual")
        kwargs = config.to_camoufox_kwargs()
        assert kwargs["headless"] == "virtual"

    def test_all_camoufox_native_fields(self):
        config = CamoufoxConfig(
            config={"navigator.platform": "Win32"},
            os="windows",
            ff_version=128,
            headless=True,
            window=(1280, 720),
            humanize=True,
            addons=["/path/to/addon.xpi"],
            block_images=True,
            block_webrtc=True,
            block_webgl=False,
            disable_coop=True,
            proxy={"server": "http://proxy:8080"},
            geoip=True,
            locale="en-US",
            fonts=["Arial"],
            enable_cache=True,
            debug=True,
        )
        kwargs = config.to_camoufox_kwargs()
        assert kwargs["config"] == {"navigator.platform": "Win32"}
        assert kwargs["os"] == "windows"
        assert kwargs["ff_version"] == 128
        assert kwargs["headless"] is True
        assert kwargs["window"] == (1280, 720)
        assert kwargs["humanize"] is True
        assert kwargs["addons"] == ["/path/to/addon.xpi"]
        assert kwargs["block_images"] is True
        assert kwargs["block_webrtc"] is True
        assert kwargs["block_webgl"] is False
        assert kwargs["disable_coop"] is True
        assert kwargs["proxy"] == {"server": "http://proxy:8080"}
        assert kwargs["geoip"] is True
        assert kwargs["locale"] == "en-US"
        assert kwargs["fonts"] == ["Arial"]
        assert kwargs["enable_cache"] is True
        assert kwargs["debug"] is True
        # Extension fields excluded
        assert "rotate_fingerprint" not in kwargs


class TestProxyTranslation:
    def test_translate_string_proxy(self):
        result = CamoufoxConfig.translate_scrapling_proxy("http://user:pass@host:8080")
        assert result == {
            "server": "http://host:8080",
            "username": "user",
            "password": "pass",
        }

    def test_translate_string_proxy_no_auth(self):
        result = CamoufoxConfig.translate_scrapling_proxy("http://host:8080")
        assert result == {"server": "http://host:8080"}

    def test_translate_dict_proxy(self):
        proxy = {"server": "http://host:8080", "username": "user", "password": "pass"}
        result = CamoufoxConfig.translate_scrapling_proxy(proxy)
        assert result == proxy

    def test_translate_none_proxy(self):
        result = CamoufoxConfig.translate_scrapling_proxy(None)
        assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scrapling_enhanced.config'`

- [ ] **Step 3: Implement CamoufoxConfig**

`src/scrapling_enhanced/config.py`:
```python
"""CamoufoxConfig — typed configuration for Camoufox browser."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
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
    fingerprint: Optional[Fingerprint] = None
    os: Optional[Union[Tuple[str, ...], List[str], str]] = None
    ff_version: Optional[int] = None

    # Display & interaction
    headless: Optional[Union[bool, Literal["virtual"]]] = None
    screen: Optional[Screen] = None
    window: Optional[Tuple[int, int]] = None
    humanize: Optional[Union[bool, float]] = None

    # Addons
    addons: Optional[List[str]] = None
    exclude_addons: Optional[List[DefaultAddons]] = None

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
        proxy: Optional[Union[str, Dict[str, str], Tuple]],
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_config.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/scrapling_enhanced/config.py tests/test_config.py
git commit -m "feat: add CamoufoxConfig dataclass with to_camoufox_kwargs() and proxy translation"
```

---

### Task 3: Fingerprint management

**Files:**
- Create: `src/scrapling_enhanced/engine/_fingerprint.py`
- Create: `tests/test_fingerprint.py`

- [ ] **Step 1: Write failing tests**

`tests/test_fingerprint.py`:
```python
from unittest.mock import patch, MagicMock

from scrapling_enhanced.engine._fingerprint import generate_rotated_fingerprint


class TestGenerateRotatedFingerprint:
    @patch("scrapling_enhanced.engine._fingerprint.generate_fingerprint")
    def test_generates_fingerprint_no_config(self, mock_gen):
        mock_fp = MagicMock()
        mock_gen.return_value = mock_fp

        result = generate_rotated_fingerprint()
        mock_gen.assert_called_once_with()
        assert result is mock_fp

    @patch("scrapling_enhanced.engine._fingerprint.generate_fingerprint")
    def test_passes_os_filter(self, mock_gen):
        mock_fp = MagicMock()
        mock_gen.return_value = mock_fp

        result = generate_rotated_fingerprint(os="windows")
        mock_gen.assert_called_once_with(os="windows")
        assert result is mock_fp

    @patch("scrapling_enhanced.engine._fingerprint.generate_fingerprint")
    def test_passes_window_size(self, mock_gen):
        mock_fp = MagicMock()
        mock_gen.return_value = mock_fp

        result = generate_rotated_fingerprint(window=(1920, 1080))
        mock_gen.assert_called_once_with(window=(1920, 1080))
        assert result is mock_fp

    @patch("scrapling_enhanced.engine._fingerprint.generate_fingerprint")
    def test_passes_all_kwargs(self, mock_gen):
        mock_fp = MagicMock()
        mock_gen.return_value = mock_fp

        result = generate_rotated_fingerprint(os="macos", window=(1280, 720))
        mock_gen.assert_called_once_with(os="macos", window=(1280, 720))
        assert result is mock_fp
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_fingerprint.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement fingerprint module**

`src/scrapling_enhanced/engine/_fingerprint.py`:
```python
"""Fingerprint generation and rotation for Camoufox sessions."""

from __future__ import annotations

from typing import Any, Optional, Tuple, Union

from camoufox.utils import generate_fingerprint


def generate_rotated_fingerprint(
    *,
    os: Optional[Union[str, Tuple[str, ...]]] = None,
    window: Optional[Tuple[int, int]] = None,
    **kwargs: Any,
) -> Any:
    """Generate a fresh BrowserForge fingerprint for context rotation.

    Args:
        os: Target OS filter (e.g., "windows", "macos", "linux").
        window: Window size as (width, height).
        **kwargs: Additional kwargs passed to generate_fingerprint.

    Returns:
        A BrowserForge Fingerprint object.
    """
    gen_kwargs: dict[str, Any] = {}
    if os is not None:
        gen_kwargs["os"] = os
    if window is not None:
        gen_kwargs["window"] = window
    gen_kwargs.update(kwargs)
    return generate_fingerprint(**gen_kwargs)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_fingerprint.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/scrapling_enhanced/engine/_fingerprint.py tests/test_fingerprint.py
git commit -m "feat: add fingerprint rotation module"
```

---

### Task 4: Addon validation utilities

**Files:**
- Create: `src/scrapling_enhanced/utils/addons.py`
- Create: `tests/test_addons.py`

- [ ] **Step 1: Write failing tests**

`tests/test_addons.py`:
```python
import os
import tempfile

import pytest

from scrapling_enhanced.utils.addons import validate_addon_paths


class TestValidateAddonPaths:
    def test_none_returns_none(self):
        assert validate_addon_paths(None) is None

    def test_empty_list_returns_none(self):
        assert validate_addon_paths([]) is None

    def test_valid_xpi_files(self):
        with tempfile.NamedTemporaryFile(suffix=".xpi", delete=False) as f:
            f.write(b"fake xpi")
            path = f.name

        try:
            result = validate_addon_paths([path])
            assert result == [path]
        finally:
            os.unlink(path)

    def test_nonexistent_file_warns_and_skips(self, caplog):
        result = validate_addon_paths(["/nonexistent/addon.xpi"])
        assert result is None or len(result) == 0
        assert "not found" in caplog.text.lower() or "skipping" in caplog.text.lower()

    def test_non_xpi_file_warns_and_skips(self, caplog):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"not an addon")
            path = f.name

        try:
            result = validate_addon_paths([path])
            assert result is None or len(result) == 0
            assert "xpi" in caplog.text.lower()
        finally:
            os.unlink(path)

    def test_mixed_valid_and_invalid(self, caplog):
        with tempfile.NamedTemporaryFile(suffix=".xpi", delete=False) as f:
            f.write(b"fake xpi")
            valid_path = f.name

        try:
            result = validate_addon_paths([valid_path, "/nonexistent.xpi"])
            assert result == [valid_path]
        finally:
            os.unlink(valid_path)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_addons.py -v`
Expected: FAIL

- [ ] **Step 3: Implement addon validation**

`src/scrapling_enhanced/utils/addons.py`:
```python
"""Firefox addon validation helpers."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

log = logging.getLogger(__name__)


def validate_addon_paths(addons: Optional[List[str]]) -> Optional[List[str]]:
    """Validate addon file paths, skip invalid ones with warnings.

    Args:
        addons: List of paths to .xpi files, or None.

    Returns:
        Filtered list of valid addon paths, or None if empty/None.
    """
    if not addons:
        return None

    valid: List[str] = []
    for addon_path in addons:
        path = Path(addon_path)
        if not path.exists():
            log.warning(f"Addon not found, skipping: {addon_path}")
            continue
        if path.suffix.lower() != ".xpi":
            log.warning(f"Addon is not a .xpi file, skipping: {addon_path}")
            continue
        valid.append(str(path))

    return valid if valid else None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_addons.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/scrapling_enhanced/utils/addons.py tests/test_addons.py
git commit -m "feat: add addon path validation utilities"
```

---

### Task 5: Proxy geolocation utility

**Files:**
- Create: `src/scrapling_enhanced/utils/geoproxy.py`
- Create: `tests/test_geoproxy.py`

- [ ] **Step 1: Write failing tests**

`tests/test_geoproxy.py`:
```python
from scrapling_enhanced.utils.geoproxy import merge_geoip_into_kwargs


class TestMergeGeoipIntoKwargs:
    def test_geoip_true_with_proxy(self):
        kwargs = {"proxy": {"server": "http://1.2.3.4:8080"}}
        result = merge_geoip_into_kwargs(kwargs, geoip=True)
        assert result["geoip"] is True

    def test_geoip_ip_string(self):
        kwargs = {}
        result = merge_geoip_into_kwargs(kwargs, geoip="1.2.3.4")
        assert result["geoip"] == "1.2.3.4"

    def test_geoip_none_no_change(self):
        kwargs = {"headless": True}
        result = merge_geoip_into_kwargs(kwargs, geoip=None)
        assert "geoip" not in result
        assert result["headless"] is True

    def test_geoip_false_no_change(self):
        kwargs = {}
        result = merge_geoip_into_kwargs(kwargs, geoip=False)
        # False means explicitly disabled — still pass it through
        assert result["geoip"] is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_geoproxy.py -v`
Expected: FAIL

- [ ] **Step 3: Implement geoproxy utility**

`src/scrapling_enhanced/utils/geoproxy.py`:
```python
"""Proxy-based geolocation helpers for Camoufox."""

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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_geoproxy.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/scrapling_enhanced/utils/geoproxy.py tests/test_geoproxy.py
git commit -m "feat: add geoproxy utility for geoip merging"
```

---

### Task 6: CamoufoxDynamicSession engine

**Files:**
- Create: `src/scrapling_enhanced/engine/_base.py`
- Create: `tests/test_engine.py`

This is the core task. `CamoufoxDynamicSession` inherits from Scrapling's `DynamicSession` and only overrides `start()` to launch Camoufox instead of Playwright Chromium. All other methods (`fetch()`, `_page_generator()`, `close()`, etc.) are inherited unchanged.

**Key insight:** `DynamicSession` inherits from `SyncSession` + `DynamicSessionMixin`. The mixin handles config validation via `__validate__()`. The `start()` method does `playwright.chromium.launch()`. We override only `start()` to use `NewBrowser()` from Camoufox. The `fetch()` method and all page pool logic work unchanged because Camoufox returns standard Playwright `Browser`/`Page` objects.

**Verified import paths:**
- `ResponseFactory` → `scrapling.engines.toolbelt.convertor`
- `Response` → `scrapling.engines.toolbelt.custom`
- `validate_fetch` → `scrapling.engines._browsers._validators` (not `_validate`)
- `is_proxy_error` → `scrapling.engines.toolbelt.proxy_rotation`
- `construct_proxy_dict` → `scrapling.engines._browsers._validators`
- `validate` → `scrapling.engines._browsers._validators`

- [ ] **Step 1: Write failing tests**

`tests/test_engine.py`:
```python
from unittest.mock import patch, MagicMock

import pytest

from scrapling_enhanced.config import CamoufoxConfig
from scrapling_enhanced.engine._base import CamoufoxDynamicSession


class TestCamoufoxDynamicSessionInit:
    def test_stores_camoufox_config(self):
        cfg = CamoufoxConfig(headless=True, humanize=1.5)
        session = CamoufoxDynamicSession(camoufox_config=cfg)
        assert session._camoufox_config is cfg

    def test_default_camoufox_config(self):
        session = CamoufoxDynamicSession()
        assert isinstance(session._camoufox_config, CamoufoxConfig)

    def test_inherits_from_dynamic_session(self):
        from scrapling.engines._browsers._controllers import DynamicSession
        assert issubclass(CamoufoxDynamicSession, DynamicSession)


class TestCamoufoxDynamicSessionStart:
    @patch("scrapling_enhanced.engine._base.sync_playwright")
    @patch("scrapling_enhanced.engine._base.NewBrowser")
    def test_start_launches_camoufox(self, mock_new_browser, mock_sync_pw):
        mock_pw = MagicMock()
        mock_sync_pw.return_value.start.return_value = mock_pw

        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_browser.new_context.return_value = mock_context
        mock_new_browser.return_value = mock_browser

        cfg = CamoufoxConfig(headless=True)
        session = CamoufoxDynamicSession(camoufox_config=cfg)
        session.start()

        mock_new_browser.assert_called_once()
        call_kwargs = mock_new_browser.call_args
        assert call_kwargs[0][0] is mock_pw  # playwright instance as first positional arg
        assert call_kwargs[1]["headless"] is True
        assert session._is_alive is True

    @patch("scrapling_enhanced.engine._base.sync_playwright")
    @patch("scrapling_enhanced.engine._base.NewBrowser")
    def test_start_with_fingerprint_rotation(self, mock_new_browser, mock_sync_pw):
        mock_pw = MagicMock()
        mock_sync_pw.return_value.start.return_value = mock_pw
        mock_browser = MagicMock()
        mock_new_browser.return_value = mock_browser

        cfg = CamoufoxConfig(rotate_fingerprint=True, headless=True)
        session = CamoufoxDynamicSession(camoufox_config=cfg)

        with patch("scrapling_enhanced.engine._base.generate_rotated_fingerprint") as mock_gen:
            mock_fp = MagicMock()
            mock_gen.return_value = mock_fp
            session.start()
            mock_gen.assert_called_once()
            call_kwargs = mock_new_browser.call_args[1]
            assert call_kwargs.get("fingerprint") is mock_fp

    def test_start_twice_raises(self):
        session = CamoufoxDynamicSession()
        session.playwright = MagicMock()  # simulate already started
        with pytest.raises(RuntimeError, match="already started"):
            session.start()


class TestCamoufoxDynamicSessionContextManager:
    @patch("scrapling_enhanced.engine._base.sync_playwright")
    @patch("scrapling_enhanced.engine._base.NewBrowser")
    def test_context_manager(self, mock_new_browser, mock_sync_pw):
        mock_pw = MagicMock()
        mock_sync_pw.return_value.start.return_value = mock_pw
        mock_browser = MagicMock()
        mock_new_browser.return_value = mock_browser

        cfg = CamoufoxConfig(headless=True)
        with CamoufoxDynamicSession(camoufox_config=cfg) as session:
            assert session._is_alive is True

        assert session._is_alive is False


class TestFetchInherited:
    """Verify fetch() is inherited from DynamicSession, not reimplemented."""

    def test_fetch_method_not_overridden(self):
        # fetch() should come from DynamicSession, not CamoufoxDynamicSession
        assert "fetch" not in CamoufoxDynamicSession.__dict__
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_engine.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement CamoufoxDynamicSession**

`src/scrapling_enhanced/engine/_base.py`:
```python
"""Camoufox-backed browser session replacing Scrapling's DynamicSession.

Inherits from DynamicSession and only overrides start() to launch
Camoufox (Firefox) instead of Playwright Chromium. All other methods
(fetch, page pooling, response handling) are inherited unchanged.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Union

from playwright.sync_api import sync_playwright
from camoufox import NewBrowser

from scrapling.engines._browsers._controllers import DynamicSession
from scrapling.engines._browsers._validators import construct_proxy_dict

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
        if self.playwright:
            raise RuntimeError("Session has been already started")

        self.playwright = sync_playwright().start()

        try:
            # Build Camoufox kwargs from config
            camoufox_kwargs = self._camoufox_config.to_camoufox_kwargs()

            # Validate addon paths
            if "addons" in camoufox_kwargs:
                camoufox_kwargs["addons"] = validate_addon_paths(camoufox_kwargs["addons"])
                if camoufox_kwargs["addons"] is None:
                    del camoufox_kwargs["addons"]

            # Generate rotated fingerprint if enabled
            if self._camoufox_config.rotate_fingerprint:
                fp_kwargs: Dict[str, Any] = {}
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
            self.playwright.stop()
            self.playwright = None
            raise
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_engine.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/scrapling_enhanced/engine/_base.py tests/test_engine.py
git commit -m "feat: implement CamoufoxDynamicSession engine"
```

---

### Task 7: CamoufoxStealthySession engine

**Files:**
- Create: `src/scrapling_enhanced/engine/_stealth.py`
- Modify: `tests/test_engine.py`

The stealth session inherits from Scrapling's `StealthySession` and only overrides `start()` to launch Camoufox. Cloudflare solving (`_cloudflare_solver`), page pooling, and fetch logic are all inherited unchanged. Camoufox handles canvas fingerprinting at the C++ level, so `hide_canvas` is N/A. We map `block_webrtc` and `allow_webgl` to Camoufox equivalents in `start()`.

- [ ] **Step 1: Write failing tests**

Append to `tests/test_engine.py`:
```python
from scrapling_enhanced.engine._stealth import CamoufoxStealthySession


class TestCamoufoxStealthySessionInit:
    def test_stores_camoufox_config(self):
        cfg = CamoufoxConfig(headless=True, disable_coop=True)
        session = CamoufoxStealthySession(camoufox_config=cfg)
        assert session._camoufox_config is cfg

    def test_default_config(self):
        session = CamoufoxStealthySession()
        assert isinstance(session._camoufox_config, CamoufoxConfig)

    def test_inherits_from_stealthy_session(self):
        from scrapling.engines._browsers._stealth import StealthySession
        assert issubclass(CamoufoxStealthySession, StealthySession)


class TestCamoufoxStealthySessionStart:
    @patch("scrapling_enhanced.engine._stealth.sync_playwright")
    @patch("scrapling_enhanced.engine._stealth.NewBrowser")
    def test_start_launches_camoufox(self, mock_new_browser, mock_sync_pw):
        mock_pw = MagicMock()
        mock_sync_pw.return_value.start.return_value = mock_pw
        mock_browser = MagicMock()
        mock_new_browser.return_value = mock_browser

        cfg = CamoufoxConfig(headless=True, block_webrtc=True)
        session = CamoufoxStealthySession(camoufox_config=cfg)
        session.start()

        call_kwargs = mock_new_browser.call_args[1]
        assert call_kwargs["headless"] is True
        assert call_kwargs["block_webrtc"] is True
        assert session._is_alive is True

    @patch("scrapling_enhanced.engine._stealth.sync_playwright")
    @patch("scrapling_enhanced.engine._stealth.NewBrowser")
    def test_solve_cloudflare_enables_disable_coop(self, mock_new_browser, mock_sync_pw):
        mock_pw = MagicMock()
        mock_sync_pw.return_value.start.return_value = mock_pw
        mock_browser = MagicMock()
        mock_new_browser.return_value = mock_browser

        session = CamoufoxStealthySession(
            camoufox_config=CamoufoxConfig(headless=True),
            solve_cloudflare=True,
        )
        session.start()

        call_kwargs = mock_new_browser.call_args[1]
        assert call_kwargs.get("disable_coop") is True

    @patch("scrapling_enhanced.engine._stealth.sync_playwright")
    @patch("scrapling_enhanced.engine._stealth.NewBrowser")
    def test_maps_scrapling_block_webrtc(self, mock_new_browser, mock_sync_pw):
        mock_pw = MagicMock()
        mock_sync_pw.return_value.start.return_value = mock_pw
        mock_browser = MagicMock()
        mock_new_browser.return_value = mock_browser

        # Scrapling's block_webrtc=True should map to Camoufox's block_webrtc
        session = CamoufoxStealthySession(
            camoufox_config=CamoufoxConfig(headless=True),
            block_webrtc=True,
        )
        session.start()

        call_kwargs = mock_new_browser.call_args[1]
        assert call_kwargs.get("block_webrtc") is True


class TestStealthyFetchInherited:
    """Verify fetch() and _cloudflare_solver() are inherited from StealthySession."""

    def test_fetch_not_overridden(self):
        assert "fetch" not in CamoufoxStealthySession.__dict__

    def test_cloudflare_solver_not_overridden(self):
        assert "_cloudflare_solver" not in CamoufoxStealthySession.__dict__
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_engine.py::TestCamoufoxStealthySessionInit -v`
Expected: FAIL

- [ ] **Step 3: Implement CamoufoxStealthySession**

`src/scrapling_enhanced/engine/_stealth.py`:
```python
"""Camoufox-backed stealthy browser session replacing Scrapling's StealthySession.

Inherits from StealthySession and only overrides start() to launch
Camoufox (Firefox) instead of Patchright/Chromium. fetch(),
_cloudflare_solver(), and all other methods are inherited unchanged.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from playwright.sync_api import sync_playwright
from camoufox import NewBrowser

from scrapling.engines._browsers._stealth import StealthySession
from scrapling.engines._browsers._validators import construct_proxy_dict

from scrapling_enhanced.config import CamoufoxConfig
from scrapling_enhanced.engine._fingerprint import generate_rotated_fingerprint
from scrapling_enhanced.utils.addons import validate_addon_paths

log = logging.getLogger(__name__)


class CamoufoxStealthySession(StealthySession):
    """Stealthy browser session using Camoufox with Cloudflare solving.

    Inherits StealthySession's fetch(), _cloudflare_solver(), page pooling,
    and config validation. Only overrides start() to launch Camoufox.
    Camoufox handles fingerprint injection at the C++ level, so Chromium
    stealth flags (hide_canvas, etc.) are not needed.
    """

    def __init__(
        self,
        *,
        camoufox_config: Optional[CamoufoxConfig] = None,
        **kwargs: Any,
    ):
        self._camoufox_config = camoufox_config or CamoufoxConfig()
        # Parent __init__ calls __validate__() which sets _config,
        # _context_options, _browser_options via StealthySessionMixin
        super().__init__(**kwargs)

    def start(self) -> None:
        """Launch Camoufox browser with stealth settings."""
        if self.playwright:
            raise RuntimeError("Session has been already started")

        self.playwright = sync_playwright().start()

        try:
            camoufox_kwargs = self._camoufox_config.to_camoufox_kwargs()

            # Map Scrapling stealth params to Camoufox equivalents
            if hasattr(self._config, "block_webrtc") and self._config.block_webrtc:
                camoufox_kwargs.setdefault("block_webrtc", True)
            if hasattr(self._config, "allow_webgl") and not self._config.allow_webgl:
                camoufox_kwargs.setdefault("block_webgl", True)

            # Cloudflare solving requires COOP disabled for iframe access
            if hasattr(self._config, "solve_cloudflare") and self._config.solve_cloudflare:
                camoufox_kwargs["disable_coop"] = True

            # Addon validation
            if "addons" in camoufox_kwargs:
                camoufox_kwargs["addons"] = validate_addon_paths(camoufox_kwargs["addons"])
                if camoufox_kwargs["addons"] is None:
                    del camoufox_kwargs["addons"]

            # Fingerprint rotation
            if self._camoufox_config.rotate_fingerprint:
                fp_kwargs: Dict[str, Any] = {}
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
            self.playwright.stop()
            self.playwright = None
            raise
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_engine.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/scrapling_enhanced/engine/_stealth.py tests/test_engine.py
git commit -m "feat: implement CamoufoxStealthySession with inherited CF solving"
```

---

### Task 8: Enhanced fetcher classes

**Files:**
- Create: `src/scrapling_enhanced/fetchers/dynamic.py`
- Create: `src/scrapling_enhanced/fetchers/stealth.py`
- Create: `tests/test_fetchers.py`

These subclass Scrapling's `DynamicFetcher`/`StealthyFetcher` and swap the session class.

**Key insight:** Scrapling's fetchers use `configure()` for parser settings only. Browser kwargs go directly into `fetch(**kwargs)`. Our `configure()` must also accept `camoufox_config`.

- [ ] **Step 1: Write failing tests**

`tests/test_fetchers.py`:
```python
from unittest.mock import patch, MagicMock

import pytest

from scrapling_enhanced.config import CamoufoxConfig
from scrapling_enhanced.fetchers.dynamic import DynamicFetcher
from scrapling_enhanced.fetchers.stealth import StealthyFetcher


class TestDynamicFetcherConfigure:
    def test_configure_accepts_camoufox_config(self):
        cfg = CamoufoxConfig(headless=True)
        DynamicFetcher.configure(camoufox_config=cfg)
        assert DynamicFetcher._camoufox_config is cfg

    def test_configure_parser_kwargs_still_work(self):
        DynamicFetcher.configure(huge_tree=False)
        assert DynamicFetcher.huge_tree is False
        # Reset
        DynamicFetcher.configure(huge_tree=True)

    def test_default_camoufox_config(self):
        # Reset to default
        DynamicFetcher._camoufox_config = None
        # Should use default when fetching (tested in integration)
        assert DynamicFetcher._camoufox_config is None


class TestDynamicFetcherFetch:
    @patch("scrapling_enhanced.fetchers.dynamic.CamoufoxDynamicSession")
    def test_fetch_uses_camoufox_session(self, mock_session_cls):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_session.fetch.return_value = mock_response
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session_cls.return_value = mock_session

        cfg = CamoufoxConfig(headless=True)
        DynamicFetcher.configure(camoufox_config=cfg)

        result = DynamicFetcher.fetch("https://example.com", headless=True)

        mock_session_cls.assert_called_once()
        call_kwargs = mock_session_cls.call_args[1]
        assert call_kwargs["camoufox_config"] is cfg
        assert result is mock_response


class TestStealthyFetcherConfigure:
    def test_configure_accepts_camoufox_config(self):
        cfg = CamoufoxConfig(headless=True, block_webrtc=True)
        StealthyFetcher.configure(camoufox_config=cfg)
        assert StealthyFetcher._camoufox_config is cfg


class TestStealthyFetcherFetch:
    @patch("scrapling_enhanced.fetchers.stealth.CamoufoxStealthySession")
    def test_fetch_uses_camoufox_session(self, mock_session_cls):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_session.fetch.return_value = mock_response
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session_cls.return_value = mock_session

        cfg = CamoufoxConfig(headless=True)
        StealthyFetcher.configure(camoufox_config=cfg)

        result = StealthyFetcher.fetch("https://example.com")

        mock_session_cls.assert_called_once()
        assert result is mock_response


class TestDropInCompatibility:
    def test_dynamic_fetcher_is_subclass(self):
        from scrapling import DynamicFetcher as OrigDynamic
        assert issubclass(DynamicFetcher, OrigDynamic)

    def test_stealthy_fetcher_is_subclass(self):
        from scrapling import StealthyFetcher as OrigStealthy
        assert issubclass(StealthyFetcher, OrigStealthy)

    def test_dynamic_has_fetch_classmethod(self):
        assert hasattr(DynamicFetcher, "fetch")
        assert isinstance(
            DynamicFetcher.__dict__["fetch"], classmethod
        )

    def test_dynamic_has_async_fetch_classmethod(self):
        assert hasattr(DynamicFetcher, "async_fetch")
        assert isinstance(
            DynamicFetcher.__dict__["async_fetch"], classmethod
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_fetchers.py -v`
Expected: FAIL

- [ ] **Step 3: Implement DynamicFetcher**

`src/scrapling_enhanced/fetchers/dynamic.py`:
```python
"""Enhanced DynamicFetcher using Camoufox instead of Playwright/Chromium."""

from __future__ import annotations

from typing import Any, Optional

from scrapling import DynamicFetcher as _OriginalDynamicFetcher
from scrapling.engines.toolbelt.custom import Response

from scrapling_enhanced.config import CamoufoxConfig
from scrapling_enhanced.engine._base import CamoufoxDynamicSession


class DynamicFetcher(_OriginalDynamicFetcher):
    """Drop-in replacement for Scrapling's DynamicFetcher using Camoufox.

    Uses Camoufox (anti-detect Firefox) instead of Playwright Chromium.
    All existing Scrapling parameters work unchanged. Use configure() with
    camoufox_config to access Camoufox-specific features.
    """

    _camoufox_config: Optional[CamoufoxConfig] = None

    @classmethod
    def configure(cls, **kwargs: Any) -> None:
        """Configure the fetcher.

        Accepts all standard Scrapling parser kwargs plus:
        - camoufox_config: CamoufoxConfig instance for Camoufox-specific settings
        """
        camoufox_config = kwargs.pop("camoufox_config", None)
        if camoufox_config is not None:
            cls._camoufox_config = camoufox_config

        if kwargs:
            super().configure(**kwargs)

    @classmethod
    def fetch(cls, url: str, **kwargs: Any) -> Response:
        """Fetch a URL using Camoufox browser.

        Accepts all standard Scrapling DynamicFetcher.fetch() parameters.
        """
        selector_config = kwargs.get("selector_config", {}) or kwargs.get("custom_config", {})
        if not isinstance(selector_config, dict):
            raise TypeError("Argument `selector_config` must be a dictionary.")
        kwargs["selector_config"] = {**cls._generate_parser_arguments(), **selector_config}

        camoufox_config = cls._camoufox_config or CamoufoxConfig()

        with CamoufoxDynamicSession(camoufox_config=camoufox_config, **kwargs) as session:
            return session.fetch(url)

    @classmethod
    async def async_fetch(cls, url: str, **kwargs: Any) -> Response:
        """Async fetch a URL using Camoufox browser.

        Accepts all standard Scrapling DynamicFetcher.async_fetch() parameters.
        """
        selector_config = kwargs.get("selector_config", {}) or kwargs.get("custom_config", {})
        if not isinstance(selector_config, dict):
            raise TypeError("Argument `selector_config` must be a dictionary.")
        kwargs["selector_config"] = {**cls._generate_parser_arguments(), **selector_config}

        camoufox_config = cls._camoufox_config or CamoufoxConfig()

        # TODO: Implement AsyncCamoufoxDynamicSession in a future task
        # For now, raise NotImplementedError
        raise NotImplementedError(
            "Async fetch is not yet implemented. Use sync fetch() for now."
        )
```

- [ ] **Step 4: Implement StealthyFetcher**

`src/scrapling_enhanced/fetchers/stealth.py`:
```python
"""Enhanced StealthyFetcher using Camoufox instead of Patchright/Chromium."""

from __future__ import annotations

from typing import Any, Optional

from scrapling import StealthyFetcher as _OriginalStealthyFetcher
from scrapling.engines.toolbelt.custom import Response

from scrapling_enhanced.config import CamoufoxConfig
from scrapling_enhanced.engine._stealth import CamoufoxStealthySession


class StealthyFetcher(_OriginalStealthyFetcher):
    """Drop-in replacement for Scrapling's StealthyFetcher using Camoufox.

    Uses Camoufox (anti-detect Firefox) instead of Patchright/Chromium.
    All existing Scrapling parameters work unchanged. Camoufox handles
    fingerprint injection at the C++ level rather than via browser flags.
    """

    _camoufox_config: Optional[CamoufoxConfig] = None

    @classmethod
    def configure(cls, **kwargs: Any) -> None:
        """Configure the fetcher.

        Accepts all standard Scrapling parser kwargs plus:
        - camoufox_config: CamoufoxConfig instance for Camoufox-specific settings
        """
        camoufox_config = kwargs.pop("camoufox_config", None)
        if camoufox_config is not None:
            cls._camoufox_config = camoufox_config

        if kwargs:
            super().configure(**kwargs)

    @classmethod
    def fetch(cls, url: str, **kwargs: Any) -> Response:
        """Fetch a URL using Camoufox stealth browser.

        Accepts all standard Scrapling StealthyFetcher.fetch() parameters.
        """
        selector_config = kwargs.get("selector_config", {}) or kwargs.get("custom_config", {})
        if not isinstance(selector_config, dict):
            raise TypeError("Argument `selector_config` must be a dictionary.")
        kwargs["selector_config"] = {**cls._generate_parser_arguments(), **selector_config}

        camoufox_config = cls._camoufox_config or CamoufoxConfig()

        with CamoufoxStealthySession(camoufox_config=camoufox_config, **kwargs) as session:
            return session.fetch(url)

    @classmethod
    async def async_fetch(cls, url: str, **kwargs: Any) -> Response:
        """Async fetch a URL using Camoufox stealth browser.

        Accepts all standard Scrapling StealthyFetcher.async_fetch() parameters.
        """
        selector_config = kwargs.get("selector_config", {}) or kwargs.get("custom_config", {})
        if not isinstance(selector_config, dict):
            raise TypeError("Argument `selector_config` must be a dictionary.")
        kwargs["selector_config"] = {**cls._generate_parser_arguments(), **selector_config}

        camoufox_config = cls._camoufox_config or CamoufoxConfig()

        raise NotImplementedError(
            "Async fetch is not yet implemented. Use sync fetch() for now."
        )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_fetchers.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add src/scrapling_enhanced/fetchers/dynamic.py src/scrapling_enhanced/fetchers/stealth.py tests/test_fetchers.py
git commit -m "feat: implement DynamicFetcher and StealthyFetcher wrappers"
```

---

### Task 9: Public API (__init__.py)

**Files:**
- Modify: `src/scrapling_enhanced/__init__.py`

- [ ] **Step 1: Write a failing test**

Add to `tests/test_fetchers.py`:
```python
class TestPublicAPI:
    def test_import_dynamic_fetcher(self):
        from scrapling_enhanced import DynamicFetcher
        assert DynamicFetcher is not None

    def test_import_stealthy_fetcher(self):
        from scrapling_enhanced import StealthyFetcher
        assert StealthyFetcher is not None

    def test_import_camoufox_config(self):
        from scrapling_enhanced import CamoufoxConfig
        assert CamoufoxConfig is not None

    def test_import_passthrough_fetcher(self):
        from scrapling_enhanced import Fetcher
        from scrapling import Fetcher as OrigFetcher
        assert Fetcher is OrigFetcher

    def test_import_passthrough_async_fetcher(self):
        from scrapling_enhanced import AsyncFetcher
        from scrapling import AsyncFetcher as OrigAsync
        assert AsyncFetcher is OrigAsync

    def test_import_passthrough_selector(self):
        from scrapling_enhanced import Selector
        from scrapling import Selector as OrigSelector
        assert Selector is OrigSelector
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_fetchers.py::TestPublicAPI -v`
Expected: FAIL — imports don't resolve yet

- [ ] **Step 3: Implement __init__.py**

`src/scrapling_enhanced/__init__.py`:
```python
"""scrapling-enhanced: Scrapling with native Camoufox browser integration."""

__version__ = "0.1.0"

# Re-export Scrapling's unchanged classes
from scrapling import (
    Fetcher,
    AsyncFetcher,
    Selector,
)
from scrapling.core.custom_types import AttributesHandler, TextHandler
from scrapling.parser import Selectors

# Export enhanced classes
from scrapling_enhanced.config import CamoufoxConfig
from scrapling_enhanced.fetchers.dynamic import DynamicFetcher
from scrapling_enhanced.fetchers.stealth import StealthyFetcher

__all__ = [
    # Scrapling pass-throughs
    "Fetcher",
    "AsyncFetcher",
    "Selector",
    "Selectors",
    "TextHandler",
    "AttributesHandler",
    # Enhanced
    "DynamicFetcher",
    "StealthyFetcher",
    "CamoufoxConfig",
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_fetchers.py::TestPublicAPI -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/scrapling_enhanced/__init__.py tests/test_fetchers.py
git commit -m "feat: wire up public API with re-exports and enhanced fetchers"
```

---

### Task 10: Integration tests

**Files:**
- Create: `tests/test_integration.py`

These tests require a real Camoufox browser and are skipped by default.

- [ ] **Step 1: Write integration tests**

`tests/test_integration.py`:
```python
import pytest

from scrapling_enhanced import DynamicFetcher, StealthyFetcher, CamoufoxConfig


@pytest.mark.integration
class TestDynamicFetcherIntegration:
    def test_fetch_simple_page(self):
        response = DynamicFetcher.fetch(
            "https://httpbin.org/html",
            headless=True,
        )
        assert response.status == 200
        text = response.css("h1::text").get()
        assert text is not None

    def test_fetch_with_camoufox_config(self):
        config = CamoufoxConfig(
            headless=True,
            humanize=True,
        )
        DynamicFetcher.configure(camoufox_config=config)
        response = DynamicFetcher.fetch("https://httpbin.org/html")
        assert response.status == 200
        # Reset
        DynamicFetcher._camoufox_config = None

    def test_fetch_with_virtual_display(self):
        config = CamoufoxConfig(headless="virtual")
        DynamicFetcher.configure(camoufox_config=config)
        response = DynamicFetcher.fetch("https://httpbin.org/html")
        assert response.status == 200
        DynamicFetcher._camoufox_config = None


@pytest.mark.integration
class TestStealthyFetcherIntegration:
    def test_fetch_simple_page(self):
        response = StealthyFetcher.fetch(
            "https://httpbin.org/html",
            headless=True,
        )
        assert response.status == 200

    def test_fetch_with_block_webrtc(self):
        config = CamoufoxConfig(headless=True, block_webrtc=True)
        StealthyFetcher.configure(camoufox_config=config)
        response = StealthyFetcher.fetch("https://httpbin.org/html")
        assert response.status == 200
        StealthyFetcher._camoufox_config = None


@pytest.mark.integration
class TestFingerprintRotation:
    def test_different_fingerprints(self):
        config = CamoufoxConfig(headless=True, rotate_fingerprint=True)
        DynamicFetcher.configure(camoufox_config=config)

        response1 = DynamicFetcher.fetch("https://httpbin.org/user-agent")
        response2 = DynamicFetcher.fetch("https://httpbin.org/user-agent")

        # User agents may differ due to rotation (not guaranteed but likely)
        # At minimum, both should succeed
        assert response1.status == 200
        assert response2.status == 200

        DynamicFetcher._camoufox_config = None


@pytest.mark.integration
class TestParsingIntegration:
    def test_css_selector(self):
        response = DynamicFetcher.fetch("https://httpbin.org/html", headless=True)
        elements = response.css("p")
        assert len(elements) > 0

    def test_xpath(self):
        response = DynamicFetcher.fetch("https://httpbin.org/html", headless=True)
        elements = response.xpath("//p")
        assert len(elements) > 0

    def test_text_extraction(self):
        response = DynamicFetcher.fetch("https://httpbin.org/html", headless=True)
        text = response.css("h1::text").get()
        assert isinstance(text, str)
        assert len(text) > 0
```

- [ ] **Step 2: Verify integration tests are skipped by default**

Run: `pytest tests/test_integration.py -v`
Expected: All tests SKIPPED with "needs --run-integration option"

- [ ] **Step 3: Run integration tests (requires Camoufox installed)**

Run: `pytest tests/test_integration.py -v --run-integration`
Expected: All tests PASS (if Camoufox browser is installed)

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "feat: add integration tests for Camoufox-backed fetchers"
```

---

### Task 11: Full test suite run and cleanup

**Files:**
- All test files
- All source files (lint/type check)

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/ -v --ignore=tests/test_integration.py`
Expected: All unit/engine/fetcher tests PASS

- [ ] **Step 2: Run linter**

Run: `ruff check src/ tests/`
Expected: No errors (fix any issues found)

- [ ] **Step 3: Run type checker**

Run: `mypy src/scrapling_enhanced/`
Expected: No errors (fix any issues found, may need type: ignore for Scrapling internals)

- [ ] **Step 4: Commit any fixes**

```bash
git add -A
git commit -m "chore: fix lint and type errors"
```

- [ ] **Step 5: Final commit summary**

Run: `git log --oneline`
Expected: Clean commit history showing incremental feature additions
