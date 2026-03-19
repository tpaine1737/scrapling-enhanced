import logging
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
        caplog.set_level(logging.WARNING)
        result = validate_addon_paths(["/nonexistent/addon.xpi"])
        assert result is None
        assert "not found" in caplog.text.lower() or "skipping" in caplog.text.lower()

    def test_non_xpi_file_warns_and_skips(self, caplog):
        caplog.set_level(logging.WARNING)
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"not an addon")
            path = f.name

        try:
            result = validate_addon_paths([path])
            assert result is None
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
