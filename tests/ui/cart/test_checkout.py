import pytest
from playwright.sync_api import expect

from src.fixtures.cart_cleanup import CartCleanup
from src.pages.cart.cart_page import CartPage
from src.pages.checkout.order_modal_page import OrderFormData
from src.pages.product.product_detail_page import ProductDetailPage

PRODUCT_ID = 2
PRODUCT_NAME = 'Nokia lumia 1520'

VALID_ORDER = OrderFormData(
    name='QA Automation',
    country='Vietnam',
    city='Ho Chi Minh City',
    card='4111111111111111',
    month='12',
    year='2030',
)

pytestmark = pytest.mark.cart


@pytest.mark.timeout(60)
class TestCheckout:
    @pytest.mark.smoke
    def test_add_to_cart_then_place_an_order_completes_with_a_purchase_confirmation(
        self,
        product_detail_page: ProductDetailPage,
        cart_page: CartPage,
    ) -> None:
        product_detail_page.open(PRODUCT_ID)
        cart_page.open()
        ids_before = cart_page.get_row_ids_by_name(PRODUCT_NAME)

        product_detail_page.open(PRODUCT_ID)
        product_detail_page.add_to_cart()

        cart_page.open()
        cart_page.wait_for_new_ids(PRODUCT_NAME, ids_before)
        cart_page.click_place_order()
        cart_page.order_modal.fill_order_form(VALID_ORDER)
        cart_page.order_modal.purchase()

        confirmation = cart_page.order_modal.get_confirmation()
        assert confirmation.name == VALID_ORDER.name
        assert confirmation.card_number == VALID_ORDER.card
        assert confirmation.id != ''
        # No cart_cleanup.track() -- a successful purchase triggers
        # DemoBlaze's own POST /deletecart as a side effect (verified via
        # network capture), which clears the cart itself.

    @pytest.mark.regression
    def test_a_non_numeric_credit_card_value_is_accepted_demoblaze_does_not_validate_its_format(
        self,
        product_detail_page: ProductDetailPage,
        cart_page: CartPage,
    ) -> None:
        product_detail_page.open(PRODUCT_ID)
        cart_page.open()
        ids_before = cart_page.get_row_ids_by_name(PRODUCT_NAME)

        product_detail_page.open(PRODUCT_ID)
        product_detail_page.add_to_cart()

        cart_page.open()
        cart_page.wait_for_new_ids(PRODUCT_NAME, ids_before)
        cart_page.click_place_order()
        # Name is the ONLY field DemoBlaze validates before allowing purchase.
        order_data = OrderFormData(**{**VALID_ORDER.__dict__, 'card': 'abcd'})
        cart_page.order_modal.fill_order_form(order_data)
        cart_page.order_modal.purchase()

        confirmation = cart_page.order_modal.get_confirmation()
        assert confirmation.card_number == 'abcd'
        # No cart_cleanup.track() -- same auto-clear reasoning as above.

    @pytest.mark.regression
    def test_submitting_the_order_form_with_all_fields_empty_is_a_silent_no_op(
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

        cart_page.open()
        new_ids = cart_page.wait_for_new_ids(PRODUCT_NAME, ids_before)
        # Purchase is blocked by validation below, so DemoBlaze's auto-clear
        # never fires -- cleanup needed explicitly.
        cart_cleanup.track(*new_ids)

        cart_page.click_place_order()
        cart_page.order_modal.purchase()

        # No error message exists to assert against instead -- only that
        # the confirmation never appears.
        expect(cart_page.order_modal.confirmation).not_to_be_visible(timeout=3_000)
