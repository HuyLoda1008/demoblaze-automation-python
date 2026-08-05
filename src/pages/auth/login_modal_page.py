from playwright.sync_api import Page, expect

from src.pages.base_page import BasePage
from src.utils.dialog_handler import with_dialog


class LoginModalPage(BasePage):
    """DemoBlaze reports ALL login failures (wrong password, nonexistent
    user, empty fields) via a native alert() -- the #errorl DOM label is
    dead markup, verified live to stay empty in every failure case."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.modal = page.locator('#logInModal')
        self.username_input = page.locator('#loginusername')
        self.password_input = page.locator('#loginpassword')
        self.submit_button = self.modal.get_by_role('button', name='Log in')

    def is_loaded(self, timeout_ms: int = 10_000) -> bool:
        try:
            self.modal.wait_for(state='visible', timeout=timeout_ms)
            self.submit_button.wait_for(state='visible', timeout=timeout_ms)
            return True
        except Exception:
            return False

    def login_expecting_success(self, username: str, password: str) -> None:
        self._fill_credentials(username, password)
        self.submit_button.click()

    def login_expecting_dialog(self, username: str, password: str) -> str:
        self._fill_credentials(username, password)
        return with_dialog(self.page, lambda: self.submit_button.click())

    def _fill_credentials(self, username: str, password: str) -> None:
        # Verify-after-fill self-heals timing issues under heavy
        # parallel/headed contention (observed: fill not "sticking",
        # causing wrong dialog-message assertions downstream).
        self.username_input.wait_for(state='visible')
        self.username_input.fill(username)
        expect(self.username_input).to_have_value(username)
        self.password_input.fill(password)
        expect(self.password_input).to_have_value(password)

    def close(self) -> None:
        self.modal.locator('.close').click()
