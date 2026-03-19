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

    @patch("scrapling_enhanced.engine._base.sync_playwright")
    @patch("scrapling_enhanced.engine._base.NewBrowser")
    def test_start_with_proxy_rotator_skips_context(self, mock_new_browser, mock_sync_pw):
        mock_pw = MagicMock()
        mock_sync_pw.return_value.start.return_value = mock_pw
        mock_browser = MagicMock()
        mock_new_browser.return_value = mock_browser

        cfg = CamoufoxConfig(headless=True)
        session = CamoufoxDynamicSession(camoufox_config=cfg)
        # Simulate proxy_rotator being set
        session._config.proxy_rotator = MagicMock()

        session.start()

        # With proxy_rotator set, new_context should NOT be called
        mock_browser.new_context.assert_not_called()
        assert session._is_alive is True


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
        # Import whatever the correct StealthySession class is
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

        assert mock_new_browser.call_args[0][0] is mock_pw  # playwright as first positional arg
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

    @patch("scrapling_enhanced.engine._stealth.sync_playwright")
    @patch("scrapling_enhanced.engine._stealth.NewBrowser")
    def test_maps_scrapling_allow_webgl_false(self, mock_new_browser, mock_sync_pw):
        mock_pw = MagicMock()
        mock_sync_pw.return_value.start.return_value = mock_pw
        mock_browser = MagicMock()
        mock_new_browser.return_value = mock_browser

        session = CamoufoxStealthySession(
            camoufox_config=CamoufoxConfig(headless=True),
            allow_webgl=False,
        )
        session.start()

        call_kwargs = mock_new_browser.call_args[1]
        assert call_kwargs.get("block_webgl") is True


class TestStealthyFetchInherited:
    """Verify fetch() and _cloudflare_solver() are inherited from StealthySession."""

    def test_fetch_not_overridden(self):
        assert "fetch" not in CamoufoxStealthySession.__dict__

    def test_cloudflare_solver_not_overridden(self):
        assert "_cloudflare_solver" not in CamoufoxStealthySession.__dict__
