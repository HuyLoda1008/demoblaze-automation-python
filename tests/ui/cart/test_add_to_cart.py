import pytest

from src.fixtures.cart_cleanup import CartCleanup
from src.pages.cart.cart_page import CartPage
from src.pages.product.product_detail_page import ProductDetailPage

PRODUCT_ID = 1
PRODUCT_NAME = 'Samsung galaxy s6'

pytestmark = pytest.mark.cart


# DemoBlaze's shared/unpartitioned cart backend can take up to ~30s to
# reflect an add under heavy public concurrent traffic, so the timeout is
# extended beyond the default.
@pytest.mark.timeout(60)
class TestAddToCart:
    @pytest.mark.smoke
    def test_adding_a_product_increases_the_cart_by_one_and_shows_its_name(
        self,
        product_detail_page: ProductDetailPage,
        cart_page: CartPage,
        cart_cleanup: CartCleanup,
    ) -> None:
        product_detail_page.open(PRODUCT_ID)
        cart_page.open()
        ids_before = cart_page.get_row_ids_by_name(PRODUCT_NAME)

        product_detail_page.open(PRODUCT_ID)
        message = product_detail_page.add_to_cart()
        assert message == 'Product added'

        cart_page.open()
        new_ids = cart_page.wait_for_new_ids(PRODUCT_NAME, ids_before)
        # No purchase happens in this test, so teardown must explicitly delete it.
        cart_cleanup.track(*new_ids)

    @pytest.mark.regression
    def test_adding_the_same_product_twice_appends_two_separate_rows_not_a_quantity_increment(
        self,
        product_detail_page: ProductDetailPage,
        cart_page: CartPage,
        cart_cleanup: CartCleanup,
    ) -> None:
        product_detail_page.open(PRODUCT_ID)
        cart_page.open()
        ids_before = cart_page.get_row_ids_by_name(PRODUCT_NAME)

        product_detail_page.open(PRODUCT_ID)
        product_detail_page.add_to_cart()
        product_detail_page.open(PRODUCT_ID)
        product_detail_page.add_to_cart()

        cart_page.open()
        # Diffing against ids_before (not an absolute/delta count) is
        # required because the cart is shared across real concurrent
        # visitors and eventually consistent -- other visitors' adds of the
        # same product can land in this window too, so we only assert AT
        # LEAST 2 new rows (proving no qty-increment happened), never an
        # exact count.
        new_ids = cart_page.wait_for_new_ids(PRODUCT_NAME, ids_before, min_new=2)
        assert len(new_ids) >= 2
        cart_cleanup.track(*new_ids)
