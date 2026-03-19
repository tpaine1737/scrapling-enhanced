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
