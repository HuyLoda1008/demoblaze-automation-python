"""Deliberately scoped-down, "honest" interpretation of performance testing
-- navigation-timing smoke checks, not a k6/Lighthouse pipeline. DemoBlaze
has no SLA and is under real shared load (see "Known site quirks" in the
README), so absolute numbers aren't meaningful to compare run-over-run. This
demonstrates wiring perf assertions into the same suite/reporting pipeline,
not a certification of the site's actual performance.
"""

import logging

import pytest
from playwright.sync_api import Page

from src.utils.perf_utils import get_navigation_timing

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.perf


def test_home_page_finishes_loading_within_a_generous_budget(page: Page) -> None:
    page.goto('/')
    timing = get_navigation_timing(page)
    logger.info('Home page navigation timing: %s', timing)

    assert timing.dom_content_loaded_ms > 0
    assert timing.load_event_ms < 15_000


def test_product_detail_page_finishes_loading_within_a_generous_budget(page: Page) -> None:
    page.goto('/prod.html?idp_=1')
    timing = get_navigation_timing(page)
    logger.info('Product detail page navigation timing: %s', timing)

    assert timing.dom_content_loaded_ms > 0
    assert timing.load_event_ms < 15_000
