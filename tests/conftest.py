import logging
from typing import Generator

import pytest
from playwright.sync_api import APIRequestContext, Page, Playwright

from config.environments import EnvConfig, get_env_config
from src.fixtures.cart_cleanup import CartCleanup
from src.pages.cart.cart_page import CartPage
from src.pages.home_page import HomePage
from src.pages.product.product_detail_page import ProductDetailPage
from src.utils.api_client import DemoblazeApiClient

logger = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def env() -> EnvConfig:
    return get_env_config()


@pytest.fixture(scope='session')
def base_url(env: EnvConfig) -> str:
    return env.base_url


@pytest.fixture
def home_page(page: Page) -> Generator[HomePage, None, None]:
    home = HomePage(page)
    yield home
    # Best-effort: leave the shared test account logged out regardless of
    # outcome. Never let a teardown-time failure mask the real test result.
    try:
        if home.is_logged_in():
            home.logout()
    except Exception as err:
        logger.warning('Login teardown: failed to log out at end of test: %s', err)


@pytest.fixture
def product_detail_page(page: Page) -> ProductDetailPage:
    return ProductDetailPage(page)


@pytest.fixture
def cart_page(page: Page) -> CartPage:
    return CartPage(page)


@pytest.fixture
def cart_cleanup(cart_page: CartPage) -> Generator[CartCleanup, None, None]:
    cleanup = CartCleanup(cart_page)
    yield cleanup
    cleanup.cleanup()


@pytest.fixture(scope='session')
def api_request_context(playwright: Playwright, env: EnvConfig) -> Generator[APIRequestContext, None, None]:
    context = playwright.request.new_context(base_url=env.api_base_url)
    yield context
    context.dispose()


@pytest.fixture
def api_client(api_request_context: APIRequestContext, env: EnvConfig) -> DemoblazeApiClient:
    return DemoblazeApiClient(api_request_context, env.api_base_url)
