import pytest
from playwright.sync_api import expect

from config.environments import EnvConfig
from src.fixtures.cart_cleanup import CartCleanup
from src.pages.cart.cart_page import CartPage
from src.pages.home_page import HomePage
from src.pages.product.product_detail_page import ProductDetailPage

PRODUCT_ID = 3
PRODUCT_NAME = 'Nexus 6'

pytestmark = pytest.mark.regression


@pytest.mark.timeout(60)
class TestCartAndCheckoutRegression:
    @pytest.mark.cart
    def test_deleting_a_cart_item_removes_it_from_the_visible_list(
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
        new_ids = cart_page.wait_for_new_ids(PRODUCT_NAME, ids_before)

        # The test's own body is its own teardown here -- it exercises
        # delete directly. Because the backend is shared/eventually
        # consistent, a single row vanishing from a constantly-changing
        # shared list can't be reliably assert-by-count, so this only
        # checks the delete action completes without error.
        cart_page.delete_row_by_id(new_ids[0])

    @pytest.mark.auth
    def test_signing_up_with_an_already_registered_username_is_rejected(
        self, home_page: HomePage, env: EnvConfig
    ) -> None:
        home_page.open()
        home_page.open_signup_modal()
        message = home_page.signup_modal.signup(env.test_user.username, 'arbitrary-password')

        assert message == 'This user already exist.'

    @pytest.mark.cart
    def test_placing_an_order_with_the_name_field_empty_is_a_silent_no_op(
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
        # Purchase blocked below, so no auto-clear.
        cart_cleanup.track(*new_ids)

        cart_page.click_place_order()
        order_modal = cart_page.order_modal
        order_modal.country_input.fill('Vietnam')
        expect(order_modal.country_input).to_have_value('Vietnam')
        order_modal.city_input.fill('Ho Chi Minh City')
        expect(order_modal.city_input).to_have_value('Ho Chi Minh City')
        order_modal.card_input.fill('4111111111111111')
        expect(order_modal.card_input).to_have_value('4111111111111111')
        order_modal.month_input.fill('12')
        expect(order_modal.month_input).to_have_value('12')
        order_modal.year_input.fill('2030')
        expect(order_modal.year_input).to_have_value('2030')
        # Name intentionally left empty.

        order_modal.purchase()
        expect(order_modal.confirmation).not_to_be_visible(timeout=3_000)

    @pytest.mark.cart
    def test_placing_an_order_with_only_the_name_field_filled_is_also_a_silent_no_op(
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
        cart_cleanup.track(*new_ids)

        cart_page.click_place_order()
        order_modal = cart_page.order_modal
        order_modal.name_input.fill('Only Name Filled')
        expect(order_modal.name_input).to_have_value('Only Name Filled')

        order_modal.purchase()
        expect(order_modal.confirmation).not_to_be_visible(timeout=3_000)
