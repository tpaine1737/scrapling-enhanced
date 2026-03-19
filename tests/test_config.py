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

    def test_translate_tuple_proxy_with_auth(self):
        result = CamoufoxConfig.translate_scrapling_proxy(("http://host:8080", "user", "pass"))
        assert result == {"server": "http://host:8080", "username": "user", "password": "pass"}

    def test_translate_tuple_proxy_server_only(self):
        result = CamoufoxConfig.translate_scrapling_proxy(("http://host:8080",))
        assert result == {"server": "http://host:8080"}
