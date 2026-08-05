import time
from dataclasses import dataclass

from playwright.sync_api import Page, expect

from src.pages.base_page import BasePage
from src.pages.checkout.order_modal_page import OrderModalPage


@dataclass
class CartRow:
    id: str
    name: str


_GET_ROWS_JS = """
(trs) => trs.map((tr) => {
    const name = tr.children[1]?.textContent?.trim() ?? '';
    const deleteLink = tr.querySelector('a[onclick^="deleteItem"]');
    const match = deleteLink?.getAttribute('onclick')?.match(/deleteItem\\('([^']+)'\\)/);
    return { id: match?.[1] ?? '', name };
})
"""


class CartPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.rows = page.locator('#tbodyid tr')
        # Must be role-based -- a bare text=Place Order locator ambiguously
        # matches the order modal's own "Place order" heading (Playwright
        # text matching is case-insensitive) -> strict-mode violation,
        # verified live.
        self.place_order_button = page.get_by_role('button', name='Place Order')
        self.order_modal = OrderModalPage(page)

    def open(self) -> None:
        self.goto('/cart.html')
        # Present/visible even with 0 rows -- a reliable "page loaded" marker.
        expect(self.place_order_button).to_be_visible()
        # DemoBlaze populates rows asynchronously on a separate timer.
        self.page.wait_for_timeout(500)

    def is_loaded(self, timeout_ms: int = 10_000) -> bool:
        try:
            self.place_order_button.wait_for(state='visible', timeout=timeout_ms)
            return True
        except Exception:
            return False

    def get_row_count(self) -> int:
        return self.rows.count()

    def get_rows(self) -> list[CartRow]:
        raw = self.rows.evaluate_all(_GET_ROWS_JS)
        return [CartRow(id=r['id'], name=r['name']) for r in raw]

    def get_row_names(self) -> list[str]:
        return [row.name for row in self.get_rows()]

    def get_row_ids_by_name(self, product_name: str) -> list[str]:
        return [row.id for row in self.get_rows() if row.name == product_name]

    def wait_for_new_ids(
        self,
        product_name: str,
        ids_before: list[str],
        min_new: int = 1,
        timeout_ms: int = 30_000,
    ) -> list[str]:
        """DemoBlaze's cart is NOT session-isolated -- it's a live, shared,
        global bucket (verified live: row counts swing wildly both
        directions, e.g. 0 -> 274, 293 -> 49, from real concurrent public
        traffic). An earlier baseline-count assertion was unsafe even with
        polling and was replaced after failing on real local data. Fix: diff
        cart-item IDS (not names, not counts) against a before-snapshot to
        identify precisely which ids are new -- immune to unrelated rows
        appearing/disappearing.
        """
        before = set(ids_before)

        # Reload exactly ONCE up front. An earlier version reloaded on every
        # poll cycle, which re-triggered the /viewcart fetch each time;
        # under load that fetch could take longer than one poll interval,
        # so it never resolved and the row count livelocked at 0 forever.
        self.page.reload()

        deadline = time.monotonic() + timeout_ms / 1000
        new_ids: list[str] = []
        while len(new_ids) < min_new and time.monotonic() < deadline:
            rows = self.get_rows()
            new_ids = [r.id for r in rows if r.name == product_name and r.id not in before]
            if len(new_ids) < min_new:
                time.sleep(1)

        assert (
            len(new_ids) >= min_new
        ), f'Expected at least {min_new} new cart row(s) for {product_name!r}, found {len(new_ids)}'
        return new_ids

    def delete_row_by_id(self, item_id: str, timeout_ms: int = 5_000) -> None:
        # Deliberately SHORT timeout (not Playwright's default) -- runs
        # per-id inside teardown; the shared cart is volatile so a row may
        # already be gone, and one missing row shouldn't burn the whole
        # test's timeout budget.
        self.page.locator(f'a[onclick="deleteItem(\'{item_id}\')"]').click(timeout=timeout_ms)
        # Row removal is a client-side DOM splice, no navigation.
        self.page.wait_for_timeout(500)

    def delete_row_by_name(self, product_name: str) -> None:
        row = self.page.locator('#tbodyid tr', has=self.page.locator(f'td:has-text("{product_name}")')).first
        row.locator('a[onclick^="deleteItem"]').click()
        self.page.wait_for_timeout(500)

    def click_place_order(self) -> None:
        self.place_order_button.click()
        expect(self.order_modal.modal).to_be_visible()
        expect(self.order_modal.name_input).to_be_visible()
