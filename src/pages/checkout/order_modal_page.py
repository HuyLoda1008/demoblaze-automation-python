import re
from dataclasses import dataclass

from playwright.sync_api import Page, expect

from src.pages.base_page import BasePage


@dataclass
class OrderFormData:
    name: str
    country: str
    city: str
    card: str
    month: str
    year: str


@dataclass
class OrderConfirmation:
    id: str
    amount: str
    card_number: str
    name: str
    date: str


class OrderModalPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.modal = page.locator('#orderModal')
        self.name_input = page.locator('#name')
        self.country_input = page.locator('#country')
        self.city_input = page.locator('#city')
        self.card_input = page.locator('#card')
        self.month_input = page.locator('#month')
        self.year_input = page.locator('#year')
        self.total_label = page.locator('#totalm')
        self.purchase_button = self.modal.get_by_role('button', name='Purchase')
        self.confirmation = page.locator('.sweet-alert')

    def is_loaded(self, timeout_ms: int = 10_000) -> bool:
        try:
            self.modal.wait_for(state='visible', timeout=timeout_ms)
            self.name_input.wait_for(state='visible', timeout=timeout_ms)
            return True
        except Exception:
            return False

    def fill_order_form(self, data: OrderFormData) -> None:
        # Verify-after-fill pinpoints which field silently failed to take a
        # value, rather than surfacing as a wrong confirmation/no-op later.
        self.name_input.fill(data.name)
        expect(self.name_input).to_have_value(data.name)
        self.country_input.fill(data.country)
        expect(self.country_input).to_have_value(data.country)
        self.city_input.fill(data.city)
        expect(self.city_input).to_have_value(data.city)
        self.card_input.fill(data.card)
        expect(self.card_input).to_have_value(data.card)
        self.month_input.fill(data.month)
        expect(self.month_input).to_have_value(data.month)
        self.year_input.fill(data.year)
        expect(self.year_input).to_have_value(data.year)

    def purchase(self) -> None:
        # Submitting with empty fields produces NEITHER a confirmation
        # dialog NOR a visible error -- a silent no-op, verified live.
        # Callers testing that path must assert confirmation never becomes
        # visible, not look for a validation message.
        self.purchase_button.click()

    def get_confirmation(self) -> OrderConfirmation:
        self.confirmation.wait_for(state='visible')
        text = self.confirmation.inner_text()

        def extract(pattern: str) -> str:
            match = re.search(pattern, text)
            if not match:
                return ''
            return match.group(1).split('\n')[0].strip()

        return OrderConfirmation(
            id=extract(r'Id:\s*(\S+)'),
            amount=extract(r'Amount:\s*([\d.]+\s*USD)'),
            card_number=extract(r'Card Number:\s*(\S+)'),
            name=extract(r'Name:\s*(.+)'),
            date=extract(r'Date:\s*(.+)'),
        )

    def close_confirmation(self) -> None:
        self.confirmation.get_by_role('button', name='OK').click()
