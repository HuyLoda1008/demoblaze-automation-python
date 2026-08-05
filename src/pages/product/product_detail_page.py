from playwright.sync_api import Page, expect

from src.pages.base_page import BasePage
from src.utils.dialog_handler import with_dialog


class ProductDetailPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.add_to_cart_link = page.get_by_role('link', name='Add to cart')
        self.product_title = page.locator('.product-content h2.name')
        self.product_price = page.locator('.product-content h3.price-container')

    def open(self, product_id: 'int | str') -> None:
        # Navigate directly by id since no reliable link-based nav exists
        # from every context.
        self.goto(f'/prod.html?idp_={product_id}')
        expect(self.product_title).to_be_visible()
        expect(self.add_to_cart_link).to_be_visible()

    def is_loaded(self, timeout_ms: int = 10_000) -> bool:
        try:
            self.product_title.wait_for(state='visible', timeout=timeout_ms)
            return True
        except Exception:
            return False

    def get_product_title(self) -> str:
        return self.product_title.inner_text().strip()

    def add_to_cart(self) -> str:
        # Fires native alert 'Product added'; dialog handler must be armed
        # before the click or the click hangs until timeout (verified live).
        return with_dialog(self.page, lambda: self.add_to_cart_link.click())
