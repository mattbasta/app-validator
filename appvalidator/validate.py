import json

import constants
import loader
import submain
import webapp
from errorbundle import ErrorBundle


def validate_app(data, listed=True, market_urls=None, url=None,
                 format="json"):
    """
    A handy function for validating apps.

    `data`:
        A copy of the manifest as a JSON string.
    `listed`:
        Whether the app is headed for the app marketplace.
    `market_urls`:
        A list of URLs to use when validating the `installs_allowed_from`
        field of the manifest. Does not apply if `listed` is not set to `True`.
    `url`:
        The URL of the manifest. Used to resolve non-absolute URLs.
    `format`:
        The output format to return the results in.

    Notes:
    - App validation is always determined because there is only one tier.
    - Spidermonkey paths are not accepted by this function because we don't
      perform JavaScript validation on webapps.
    """
    bundle = ErrorBundle(listed=listed)
    bundle.save_resource("market_urls", market_urls)
    bundle.save_resource("manifest_url", url)

    webapp.detect_webapp_string(bundle, data)
    submain.test_inner_package(bundle, None)

    return format_result(bundle, format)


def validate_packaged_app(path, listed=True, format="json", market_urls=None,
                          timeout=None, spidermonkey=False):
    """
    A handy function for validating apps.

    `path`:
        The path to the packaged app.
    `listed`:
        Whether the app is headed for the app marketplace.
    `format`:
        The output format to return the results in.
    `market_urls`:
        A list of URLs to use when validating the `installs_allowed_from`
        field of the manifest. Does not apply if `listed` is not set to `True`.
    `timeout`:
        The amount of time (in seconds) that the validation process may take.
        When this value is `None`, timeouts are disabled.
    `spidermonkey`:
        Path to the local spidermonkey installation. Defaults to `False`, which
        uses the validator's built-in detection of Spidermonkey. Specifying
        `None` will disable JavaScript tests. Any other value is treated as the
        path.
    """
    bundle = ErrorBundle(listed=listed, spidermonkey=spidermonkey)
    bundle.save_resource("packaged", True)

    # Set the market URLs.
    bundle.save_resource("market_urls", market_urls)

    submain.prepare_package(bundle, path, timeout)
    return format_result(bundle, format)


def format_result(bundle, format):
    # Write the results to the pipe
    formats = {"json": lambda b: b.render_json()}
    if format is not None:
        return formats[format](bundle)
    else:
        return bundle
