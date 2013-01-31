from functools import wraps

from mock import Mock, patch

from valcom.errorbundle import ErrorBundle
from valcom.libs.zip import ZipPackage
from valcom.tests import TestCase


def _do_test(path, test, failure=True, set_type=0,
             listed=False, xpi_mode="r"):

    package_data = open(path, "rb")
    package = ZipPackage(package_data, mode=xpi_mode, name=path)
    err = ErrorBundle()
    if listed:
        err.save_resource("listed", True)

    # Populate in the dependencies.
    if set_type:
        err.set_type(set_type) # Conduit test requires type

    test(err, package)

    print err.print_summary(verbose=True)
    assert err.failed() if failure else not err.failed()

    return err


def safe(func):
    """
    Make sure that a test does not access external resources.

    Note: This will mock `requests.get`. If you are mocking it yourself
    already, this will throw an assertion error.
    """
    @patch("appvalidator.testcases.webappbase.test_icon")
    @wraps(func)
    def wrap(test_icon, *args, **kwargs):
        # Assert that we're not double-mocking `requests.get`.
        from requests import get as _r_g
        assert not isinstance(_r_g, Mock), "`requests.get` already mocked"

        with patch("requests.get") as r_g:
            request = Mock()
            request.text = "foo bar"
            request.status_code = 200
            # The first bit is the return value. The second bit tells whatever
            # is requesting the data that there's no more data.
            request.raw.read.side_effect = [request.text, ""]
            r_g.return_value = request
            return func(*args, **kwargs)
    return wrap


class MockXPI:

    def __init__(self, data=None):
        if not data:
            data = {}
        self.zf = Mock()
        self.data = data
        self.filename = "mock_xpi.xpi"

    def test(self):
        return True

    def info(self, name):
        return {"name_lower": name.lower(),
                "extension": name.lower().split(".")[-1]}

    def __iter__(self):
        for name in self.data.keys():
            yield name

    def __contains__(self, name):
        return name in self.data

    def read(self, name):
        return open(self.data[name]).read()
