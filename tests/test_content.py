from mock import patch
from nose.tools import eq_

from helper import MockXPI, TestCase

from valcom.libs.zip import ZipPackage
import appvalidator.testcases.content as content
from appvalidator.errorbundle import ErrorBundle
from appvalidator.constants import *


class MockTestEndpoint(object):
    """
    Simulates a test module and reports whether individual tests have been
    attempted on it.
    """

    def __init__(self, expected, td_error=False):
        expectations = {}
        for expectation in expected:
            expectations[expectation] = {"count": 0, "subpackage": 0}

        self.expectations = expectations
        self.td_error = td_error
        self.found_tiers = []

    def _tier_test(self, err, package, name):
        "A simulated test case for tier errors"
        print "Generating subpackage tier error..."
        self.found_tiers.append(err.tier)
        err.error(("foo", ),
                  "Tier error",
                  "Just a test")

    def __getattribute__(self, name):
        """Detects requests for validation tests and returns an
        object that simulates the outcome of a test."""

        print "Requested: %s" % name

        if name == "test_package" and self.td_error:
            return self._tier_test

        if name in ("expectations",
                    "assert_expectation",
                    "td_error",
                    "_tier_test",
                    "found_tiers"):
            return object.__getattribute__(self, name)

        if name in self.expectations:
            self.expectations[name]["count"] += 1

        if name == "test_package":
            def wrap(package, name):
                pass
        elif name in ("test_css_file", "test_js_file", "process"):
            def wrap(err, name, file_data):
                pass
        else:
            def wrap(err, pak):
                if isinstance(pak, ZipPackage) and pak.subpackage:
                    self.expectations[name]["subpackage"] += 1

        return wrap

    def assert_expectation(self, name, count, type_="count"):
        """Asserts that a particular test has been run a certain number
        of times"""

        print self.expectations
        assert name in self.expectations
        eq_(self.expectations[name][type_], count)


class MockMarkupEndpoint(MockTestEndpoint):
    "Simulates the markup test module"

    def __getattribute__(self, name):

        if name == "MarkupParser":
            return lambda x: self

        return MockTestEndpoint.__getattribute__(self, name)

class TestContent(TestCase):

    def _run_test(self, mock_package):
        return content.test_packed_packages(self.err, mock_package)

    @patch("appvalidator.testcases.content.testendpoint_markup",
           MockMarkupEndpoint(("process", )))
    def test_markup(self):
        "Tests markup files in the content validator."
        self.setup_err()
        mock_package = MockXPI({"foo.xml": "tests/resources/content/junk.xpi"})

        eq_(self._run_test(mock_package), 1)
        content.testendpoint_markup.assert_expectation("process", 1)
        content.testendpoint_markup.assert_expectation(
            "process", 0, "subpackage")

    @patch("appvalidator.testcases.content.testendpoint_css",
           MockTestEndpoint(("test_css_file", )))
    def test_css(self):
        "Tests css files in the content validator."

        self.setup_err()
        mock_package = MockXPI(
            {"foo.css": "tests/resources/content/junk.xpi"})

        eq_(self._run_test(mock_package), 1)
        content.testendpoint_css.assert_expectation("test_css_file", 1)
        content.testendpoint_css.assert_expectation(
            "test_css_file", 0, "subpackage")

    @patch("appvalidator.testcases.content.testendpoint_js",
           MockTestEndpoint(("test_js_file", )))
    def test_js(self):
        """Test that JS files are properly tested in the content validator."""

        self.setup_err()
        mock_package = MockXPI(
            {"foo.js": "tests/resources/content/junk.xpi"})

        eq_(self._run_test(mock_package), 1)
        content.testendpoint_js.assert_expectation("test_js_file", 1)
        content.testendpoint_js.assert_expectation(
            "test_js_file", 0, "subpackage")

    def test_hidden_files(self):
        """Tests that hidden files are reported."""

        def test_structure(structure):
            self.setup_err()
            mock_package = MockXPI(
                dict([(structure, "tests/resources/content/junk.xpi")]))
            content.test_packed_packages(self.err, mock_package)
            print self.err.print_summary(verbose=True)
            self.assert_failed()

        for structure in (".hidden", "dir/__MACOSX/foo", "dir/.foo.swp",
                          "dir/file.old", "dir/file.xul~"):
            yield test_structure, structure
