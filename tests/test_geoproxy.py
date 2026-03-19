from scrapling_enhanced.utils.geoproxy import merge_geoip_into_kwargs


class TestMergeGeoipIntoKwargs:
    def test_geoip_true_with_proxy(self):
        kwargs = {"proxy": {"server": "http://1.2.3.4:8080"}}
        result = merge_geoip_into_kwargs(kwargs, geoip=True)
        assert result["geoip"] is True
        assert result is kwargs

    def test_geoip_ip_string(self):
        kwargs = {}
        result = merge_geoip_into_kwargs(kwargs, geoip="1.2.3.4")
        assert result["geoip"] == "1.2.3.4"
        assert result is kwargs

    def test_geoip_none_no_change(self):
        kwargs = {"headless": True}
        result = merge_geoip_into_kwargs(kwargs, geoip=None)
        assert "geoip" not in result
        assert result["headless"] is True
        assert result is kwargs

    def test_geoip_false_no_change(self):
        kwargs = {}
        result = merge_geoip_into_kwargs(kwargs, geoip=False)
        # False means explicitly disabled — still pass it through
        assert result["geoip"] is False
        assert result is kwargs
