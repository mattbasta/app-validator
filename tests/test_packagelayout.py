from itertools import repeat

from mock import MagicMock

import appvalidator.testcases.packagelayout as packagelayout
from appvalidator.errorbundle import ErrorBundle
from helper import _do_test, TestCase


def test_blacklisted_files():
    """Tests that the validator will throw warnings on extensions
    containing files that have extensions which are not considered
    safe."""

    err = _do_test("tests/resources/packagelayout/ext_blacklist.xpi",
                   packagelayout.test_blacklisted_files,
                   True)
    assert err.metadata["contains_binary_extension"]


def test_blacklisted_magic_numbers():
    "Tests that blacklisted magic numbers are banned"

    err = _do_test("tests/resources/packagelayout/magic_number.xpi",
                   packagelayout.test_blacklisted_files,
                   True)
    assert err.metadata["contains_binary_content"]
    assert "binary_components" not in err.metadata


def test_duplicate_files():
    """Test that duplicate files in a package are caught."""

    package = MagicMock()
    package.subpackage = False
    zf = MagicMock()
    zf.namelist.return_value = ["foo.bar", "foo.bar"]
    package.zf = zf

    err = ErrorBundle()
    packagelayout.test_layout_all(err, package)
    assert err.failed()


class TestMETAINF(TestCase):

    def setUp(self):
        self.setup_err()
        self.package = MagicMock()
        self.package.subpackage = False

    def test_metainf_pass(self):
        self.package.zf.namelist.return_value = ["META-INF-foo.js"]
        packagelayout.test_layout_all(self.err, self.package)
        self.assert_silent()

    def test_metainf_fail(self):
        """Test that META-INF directories fail validation."""

        self.package.zf.namelist.return_value = ["META-INF/foo.js"]
        packagelayout.test_layout_all(self.err, self.package)
        self.assert_failed(with_errors=True)
