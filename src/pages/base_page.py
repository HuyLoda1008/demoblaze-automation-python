from playwright.sync_api import Page


class BasePage:
    """Deliberately thin -- Playwright's own locators/expect() auto-wait and
    retry, so no hand-rolled polling helpers are needed here."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def goto(self, path: str = '/') -> None:
        self.page.goto(path)
