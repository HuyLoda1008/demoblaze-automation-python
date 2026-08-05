import logging

from src.pages.cart.cart_page import CartPage

logger = logging.getLogger(__name__)


class CartCleanup:
    """Teardown collector: tracks cart-item ids created during a test and
    deletes them afterward.

    NOT needed for tests completing a real purchase, since a successful
    purchase() triggers DemoBlaze's own POST /deletecart server-side as a
    side effect (verified live) -- only track ids from adds that are NOT
    followed by a successful purchase.
    """

    def __init__(self, cart_page: CartPage) -> None:
        self._cart_page = cart_page
        self._ids: list[str] = []

    def track(self, *ids: str) -> None:
        self._ids.extend(ids)

    def cleanup(self) -> None:
        if not self._ids:
            return

        # Negative checkout tests leave #orderModal open (purchase never
        # succeeds so nothing dismisses it); without navigating back to a
        # clean cart page first, the still-open modal intercepts pointer
        # events on rows underneath and every delete click below silently
        # no-ops.
        self._cart_page.open()

        for item_id in self._ids:
            try:
                self._cart_page.delete_row_by_id(item_id)
            except Exception as err:
                logger.warning('Cart teardown: failed to delete cart item %s: %s', item_id, err)
