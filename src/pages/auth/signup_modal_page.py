from playwright.sync_api import Page, expect

from src.pages.base_page import BasePage
from src.utils.dialog_handler import with_dialog


class SignupModalPage(BasePage):
    """Success message: 'Sign up successful.'; failure (duplicate username):
    'This user already exist.' -- both via native alert(). The #errors DOM
    label is dead markup, same pattern as the login modal."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.modal = page.locator('#signInModal')
        self.username_input = page.locator('#sign-username')
        self.password_input = page.locator('#sign-password')
        self.submit_button = self.modal.get_by_role('button', name='Sign up')

    def is_loaded(self, timeout_ms: int = 10_000) -> bool:
        try:
            self.modal.wait_for(state='visible', timeout=timeout_ms)
            self.submit_button.wait_for(state='visible', timeout=timeout_ms)
            return True
        except Exception:
            return False

    def signup(self, username: str, password: str) -> str:
        self.username_input.wait_for(state='visible')
        self.username_input.fill(username)
        expect(self.username_input).to_have_value(username)
        self.password_input.fill(password)
        expect(self.password_input).to_have_value(password)
        return with_dialog(self.page, lambda: self.submit_button.click())
