from playwright.sync_api import Page


class NavBar:
    """Site-wide header, present on every page. Composed into a page object
    via `self.nav_bar = NavBar(page)` instead of being redefined per page --
    mirrors the reusable cross-page component pattern (e.g. pagination,
    calendar picker) that bumblebee keeps under `pages/module/`.
    """

    def __init__(self, page: Page) -> None:
        self.login_nav_link = page.locator('#login2')
        self.signup_nav_link = page.locator('#signin2')
        self.logout_nav_link = page.locator('#logout2')
        self.welcome_label = page.locator('#nameofuser')
        self.cart_nav_link = page.locator('#cartur')

    def is_logged_in(self) -> bool:
        if not self.logout_nav_link.is_visible():
            return False
        return self.welcome_label.inner_text().startswith('Welcome')

    def logout(self, timeout_ms: int = 5_000) -> None:
        # May be called from fixture teardown -- must not burn the test's timeout budget.
        self.logout_nav_link.click(timeout=timeout_ms)

    def go_to_cart(self) -> None:
        self.cart_nav_link.click()
