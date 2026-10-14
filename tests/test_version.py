from devpy.cli.version import _parse_version, get_version


class TestVersion:
    def test_get_version(self):
        v = get_version()
        assert v == "2.0.0"

    def test_parse_version_simple(self):
        assert _parse_version("1.0.0") == (1, 0, 0)

    def test_parse_version_major(self):
        assert _parse_version("2.1.3") == (2, 1, 3)

    def test_parse_version_comparison(self):
        assert _parse_version("2.0.0") > _parse_version("1.9.9")
        assert _parse_version("1.0.1") > _parse_version("1.0.0")
        assert _parse_version("1.1.0") > _parse_version("1.0.9")

    def test_parse_version_equal(self):
        assert _parse_version("1.2.3") == _parse_version("1.2.3")

    def test_parse_version_non_numeric(self):
        assert _parse_version("1.0.0a") == (1, 0, 0)
