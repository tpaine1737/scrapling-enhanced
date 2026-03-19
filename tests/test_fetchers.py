"""Tests for scrapling_enhanced fetcher classes."""

from unittest.mock import MagicMock, patch

import pytest

from scrapling_enhanced.config import CamoufoxConfig
from scrapling_enhanced.fetchers.dynamic import DynamicFetcher
from scrapling_enhanced.fetchers.stealth import StealthyFetcher


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reset_fetcher(cls):
    """Reset class-level state between tests."""
    cls._camoufox_config = None
    cls.huge_tree = True


# ---------------------------------------------------------------------------
# DynamicFetcher.configure()
# ---------------------------------------------------------------------------

class TestDynamicFetcherConfigure:
    def setup_method(self):
        _reset_fetcher(DynamicFetcher)

    def teardown_method(self):
        _reset_fetcher(DynamicFetcher)

    def test_configure_accepts_camoufox_config(self):
        cfg = CamoufoxConfig(headless=True)
        DynamicFetcher.configure(camoufox_config=cfg)
        assert DynamicFetcher._camoufox_config is cfg

    def test_configure_parser_kwargs_still_work(self):
        DynamicFetcher.configure(huge_tree=False)
        assert DynamicFetcher.huge_tree is False
        # Reset to default
        DynamicFetcher.configure(huge_tree=True)
        assert DynamicFetcher.huge_tree is True

    def test_default_camoufox_config_is_none(self):
        assert DynamicFetcher._camoufox_config is None

    def test_configure_camoufox_config_and_parser_arg_together(self):
        cfg = CamoufoxConfig(headless=False)
        DynamicFetcher.configure(camoufox_config=cfg, huge_tree=False)
        assert DynamicFetcher._camoufox_config is cfg
        assert DynamicFetcher.huge_tree is False

    def test_configure_none_camoufox_config_does_not_overwrite(self):
        cfg = CamoufoxConfig(headless=True)
        DynamicFetcher._camoufox_config = cfg
        # Passing no camoufox_config (omitted) should leave existing value alone
        DynamicFetcher.configure(huge_tree=True)
        assert DynamicFetcher._camoufox_config is cfg

    def test_configure_unknown_kwarg_raises(self):
        with pytest.raises((AttributeError, ValueError)):
            DynamicFetcher.configure(not_a_real_kwarg=True)


# ---------------------------------------------------------------------------
# DynamicFetcher.fetch()
# ---------------------------------------------------------------------------

class TestDynamicFetcherFetch:
    def setup_method(self):
        _reset_fetcher(DynamicFetcher)

    def teardown_method(self):
        _reset_fetcher(DynamicFetcher)

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

        result = DynamicFetcher.fetch("https://example.com")

        mock_session_cls.assert_called_once()
        call_kwargs = mock_session_cls.call_args[1]
        assert call_kwargs["camoufox_config"] is cfg
        assert result is mock_response

    @patch("scrapling_enhanced.fetchers.dynamic.CamoufoxDynamicSession")
    def test_fetch_passes_url_to_session(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session_cls.return_value = mock_session

        DynamicFetcher.fetch("https://example.com/path")

        mock_session.fetch.assert_called_once_with("https://example.com/path")

    @patch("scrapling_enhanced.fetchers.dynamic.CamoufoxDynamicSession")
    def test_fetch_injects_selector_config(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session_cls.return_value = mock_session

        DynamicFetcher.fetch("https://example.com")

        call_kwargs = mock_session_cls.call_args[1]
        assert "selector_config" in call_kwargs
        assert isinstance(call_kwargs["selector_config"], dict)

    @patch("scrapling_enhanced.fetchers.dynamic.CamoufoxDynamicSession")
    def test_fetch_merges_user_selector_config(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session_cls.return_value = mock_session

        DynamicFetcher.fetch("https://example.com", selector_config={"custom_key": "val"})

        call_kwargs = mock_session_cls.call_args[1]
        assert call_kwargs["selector_config"]["custom_key"] == "val"

    def test_fetch_raises_on_non_dict_selector_config(self):
        with pytest.raises(TypeError):
            DynamicFetcher.fetch("https://example.com", selector_config="bad")

    @patch("scrapling_enhanced.fetchers.dynamic.CamoufoxDynamicSession")
    def test_fetch_uses_none_camoufox_config_when_not_set(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session_cls.return_value = mock_session

        DynamicFetcher._camoufox_config = None
        DynamicFetcher.fetch("https://example.com")

        call_kwargs = mock_session_cls.call_args[1]
        assert call_kwargs["camoufox_config"] is None


# ---------------------------------------------------------------------------
# DynamicFetcher.async_fetch()
# ---------------------------------------------------------------------------

class TestDynamicFetcherAsyncFetch:
    @pytest.mark.asyncio
    async def test_async_fetch_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            await DynamicFetcher.async_fetch("https://example.com")


# ---------------------------------------------------------------------------
# StealthyFetcher.configure()
# ---------------------------------------------------------------------------

class TestStealthyFetcherConfigure:
    def setup_method(self):
        _reset_fetcher(StealthyFetcher)

    def teardown_method(self):
        _reset_fetcher(StealthyFetcher)

    def test_configure_accepts_camoufox_config(self):
        cfg = CamoufoxConfig(headless=True, block_webrtc=True)
        StealthyFetcher.configure(camoufox_config=cfg)
        assert StealthyFetcher._camoufox_config is cfg

    def test_configure_parser_kwargs_still_work(self):
        StealthyFetcher.configure(huge_tree=False)
        assert StealthyFetcher.huge_tree is False

    def test_default_camoufox_config_is_none(self):
        assert StealthyFetcher._camoufox_config is None


# ---------------------------------------------------------------------------
# StealthyFetcher.fetch()
# ---------------------------------------------------------------------------

class TestStealthyFetcherFetch:
    def setup_method(self):
        _reset_fetcher(StealthyFetcher)

    def teardown_method(self):
        _reset_fetcher(StealthyFetcher)

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
        call_kwargs = mock_session_cls.call_args[1]
        assert call_kwargs["camoufox_config"] is cfg
        assert result is mock_response

    @patch("scrapling_enhanced.fetchers.stealth.CamoufoxStealthySession")
    def test_fetch_passes_url_to_session(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session_cls.return_value = mock_session

        StealthyFetcher.fetch("https://example.com/stealth")

        mock_session.fetch.assert_called_once_with("https://example.com/stealth")

    def test_fetch_raises_on_non_dict_selector_config(self):
        with pytest.raises(TypeError):
            StealthyFetcher.fetch("https://example.com", selector_config=42)


# ---------------------------------------------------------------------------
# StealthyFetcher.async_fetch()
# ---------------------------------------------------------------------------

class TestStealthyFetcherAsyncFetch:
    @pytest.mark.asyncio
    async def test_async_fetch_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            await StealthyFetcher.async_fetch("https://example.com")


# ---------------------------------------------------------------------------
# Drop-in compatibility
# ---------------------------------------------------------------------------

class TestDropInCompatibility:
    def test_dynamic_fetcher_is_subclass(self):
        from scrapling import DynamicFetcher as OrigDynamic
        assert issubclass(DynamicFetcher, OrigDynamic)

    def test_stealthy_fetcher_is_subclass(self):
        from scrapling import StealthyFetcher as OrigStealthy
        assert issubclass(StealthyFetcher, OrigStealthy)

    def test_dynamic_has_fetch_classmethod(self):
        assert hasattr(DynamicFetcher, "fetch")
        assert isinstance(DynamicFetcher.__dict__["fetch"], classmethod)

    def test_dynamic_has_async_fetch_classmethod(self):
        assert hasattr(DynamicFetcher, "async_fetch")
        assert isinstance(DynamicFetcher.__dict__["async_fetch"], classmethod)

    def test_stealthy_has_fetch_classmethod(self):
        assert hasattr(StealthyFetcher, "fetch")
        assert isinstance(StealthyFetcher.__dict__["fetch"], classmethod)

    def test_stealthy_has_async_fetch_classmethod(self):
        assert hasattr(StealthyFetcher, "async_fetch")
        assert isinstance(StealthyFetcher.__dict__["async_fetch"], classmethod)

    def test_dynamic_has_configure_classmethod(self):
        assert hasattr(DynamicFetcher, "configure")
        assert isinstance(DynamicFetcher.__dict__["configure"], classmethod)

    def test_stealthy_has_configure_classmethod(self):
        assert hasattr(StealthyFetcher, "configure")
        assert isinstance(StealthyFetcher.__dict__["configure"], classmethod)

    def test_dynamic_camoufox_config_class_var_exists(self):
        assert hasattr(DynamicFetcher, "_camoufox_config")

    def test_stealthy_camoufox_config_class_var_exists(self):
        assert hasattr(StealthyFetcher, "_camoufox_config")
