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

        # Both should succeed regardless of fingerprint difference
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
