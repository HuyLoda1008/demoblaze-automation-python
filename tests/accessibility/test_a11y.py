"""axe-core is vendored (tests/accessibility/axe.min.js, pinned to the same
4.12.1 build the TypeScript sibling project's @axe-core/playwright pulls)
and injected manually via page.add_script_tag() rather than depending on a
thin/less-maintained Python wrapper package.

KNOWN_VIOLATION_IDS is an allowlist, not an exact-match list. An earlier
exact-match version flaked because DemoBlaze's rotating catalog/ad content
made `link-name` flip in/out across identical Home-page reruns (verified
live: 3 reruns, same browser/machine). The allowlist approach still fails on
a genuinely NEW violation type; it just tolerates which KNOWN ones show up
on a given run.
"""

from pathlib import Path
from typing import Any, cast

import pytest
from playwright.sync_api import Page

from src.pages.cart.cart_page import CartPage
from src.pages.home_page import HomePage
from src.pages.product.product_detail_page import ProductDetailPage

pytestmark = [pytest.mark.a11y, pytest.mark.regression]

AXE_SCRIPT_PATH = Path(__file__).parent / 'axe.min.js'
PRODUCT_ID = 2  # Nokia lumia 1520

KNOWN_VIOLATION_IDS = {
    'color-contrast',
    'empty-heading',
    'image-alt',
    'landmark-one-main',
    'link-name',
    'page-has-heading-one',
    'region',
}


def run_axe(page: Page) -> list[dict[str, Any]]:
    page.add_script_tag(path=str(AXE_SCRIPT_PATH))
    results = page.evaluate('async () => await axe.run()')
    return cast('list[dict[str, Any]]', results['violations'])


def assert_known_violations_only(page: Page) -> None:
    violations = run_axe(page)
    violation_ids = {v['id'] for v in violations}

    unknown = violation_ids - KNOWN_VIOLATION_IDS
    assert not unknown, f'New, previously-unseen accessibility violation type(s): {unknown}'

    # A standing assertion that the one violation confirmed present on
    # every run never silently disappears.
    assert 'image-alt' in violation_ids


def test_home_page_has_no_accessibility_violations_beyond_the_known_baseline(
    page: Page, home_page: HomePage
) -> None:
    home_page.open()
    assert home_page.is_loaded()
    assert_known_violations_only(page)


def test_product_detail_page_has_no_accessibility_violations_beyond_the_known_baseline(
    page: Page, product_detail_page: ProductDetailPage
) -> None:
    product_detail_page.open(PRODUCT_ID)
    assert product_detail_page.is_loaded()
    assert_known_violations_only(page)


def test_cart_page_has_no_accessibility_violations_beyond_the_known_baseline(
    page: Page, cart_page: CartPage
) -> None:
    cart_page.open()
    assert cart_page.is_loaded()
    assert_known_violations_only(page)
