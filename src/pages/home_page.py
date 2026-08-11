from playwright.sync_api import Page, expect

from src.pages.auth.login_modal_page import LoginModalPage
from src.pages.auth.signup_modal_page import SignupModalPage
from src.pages.base_page import BasePage
from src.pages.components.nav_bar import NavBar


class HomePage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.nav_bar = NavBar(page)
        # Aliased for backward compatibility with existing call sites
        # (tests reach these directly, e.g. `home_page.welcome_label`).
        self.login_nav_link = self.nav_bar.login_nav_link
        self.signup_nav_link = self.nav_bar.signup_nav_link
        self.logout_nav_link = self.nav_bar.logout_nav_link
        self.welcome_label = self.nav_bar.welcome_label
        self.cart_nav_link = self.nav_bar.cart_nav_link
        self.product_cards = page.locator('.card')

        self.login_modal = LoginModalPage(page)
        self.signup_modal = SignupModalPage(page)

    def open(self) -> None:
        self.goto('/')
        # Verifies the grid actually rendered so a broken load doesn't
        # surface confusingly later, deeper into a test.
        expect(self.product_cards.first).to_be_visible()

    def is_loaded(self, timeout_ms: int = 10_000) -> bool:
        try:
            self.product_cards.first.wait_for(state='visible', timeout=timeout_ms)
            return True
        except Exception:
            return False

    def open_login_modal(self) -> None:
        self.login_nav_link.click()
        expect(self.login_modal.modal).to_be_visible()
        expect(self.login_modal.username_input).to_be_visible()

    def open_signup_modal(self) -> None:
        self.signup_nav_link.click()
        expect(self.signup_modal.modal).to_be_visible()
        expect(self.signup_modal.username_input).to_be_visible()

    def is_logged_in(self) -> bool:
        return self.nav_bar.is_logged_in()

    def logout(self, timeout_ms: int = 5_000) -> None:
        self.nav_bar.logout(timeout_ms)

    def get_product_names(self) -> list[str]:
        return self.page.locator('.card-title a.hrefch').all_inner_texts()
