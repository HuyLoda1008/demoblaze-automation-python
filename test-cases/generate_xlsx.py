"""Generates test-cases.xlsx from the typed data below. Source of truth is
this file (reviewable/diffable in git); run `make gen-testcases` to
regenerate the actual .xlsx deliverable.

Scenario coverage reflects behavior VERIFIED live against demoblaze.com
while building the automation (see README "Known site quirks"), not
generic boilerplate -- e.g. the duplicate-add-to-cart and empty-order-form
rows document the site's *actual* observed behavior, not an assumed one.
Content is carried over verbatim from the TypeScript sibling project's
test-cases/generate-xlsx.ts, the original source of truth.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import openpyxl
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.worksheet import Worksheet

Priority = Literal['High', 'Medium', 'Low']
CaseType = Literal['Functional', 'Edge', 'Negative']


@dataclass
class TestCase:
    id: str
    scenario: str
    type: CaseType
    priority: Priority
    preconditions: str
    steps: str
    test_data: str
    expected_result: str
    notes: str


LOGIN_CASES: list[TestCase] = [
    TestCase(
        id='LOGIN-001',
        scenario='Log in with valid credentials',
        type='Functional',
        priority='High',
        preconditions='A registered account exists',
        steps=(
            '1. Open Home page\n2. Click "Log in"\n3. Enter valid username/password\n'
            '4. Click "Log in" button'
        ),
        test_data='Registered username + correct password',
        expected_result=(
            'Nav bar shows "Welcome <username>"; "Log out" link becomes visible; '
            '"Log in"/"Sign up" links hide'
        ),
        notes='',
    ),
    TestCase(
        id='LOGIN-002',
        scenario='Log in with wrong password',
        type='Negative',
        priority='High',
        preconditions='A registered account exists',
        steps=(
            '1. Open Home page\n2. Click "Log in"\n3. Enter valid username + wrong password\n'
            '4. Click "Log in"'
        ),
        test_data='Registered username + incorrect password',
        expected_result='A native browser alert reads "Wrong password."; user remains logged out',
        notes=(
            'Verified live: the error is a native alert() dialog, NOT the #errorl label visible '
            'in the DOM (that label is dead markup and stays empty in every failure case).'
        ),
    ),
    TestCase(
        id='LOGIN-003',
        scenario='Log in with a nonexistent username',
        type='Negative',
        priority='High',
        preconditions='None',
        steps=(
            '1. Open Home page\n2. Click "Log in"\n3. Enter a username that has never been registered\n'
            '4. Click "Log in"'
        ),
        test_data='e.g. nonexistent_user_zzz_999 / any password',
        expected_result='A native browser alert reads "User does not exist."',
        notes='Verified live (native alert, same as LOGIN-002).',
    ),
    TestCase(
        id='LOGIN-004',
        scenario='Log in with both fields empty',
        type='Negative',
        priority='Medium',
        preconditions='None',
        steps='1. Open Home page\n2. Click "Log in"\n3. Leave Username and Password empty\n4. Click "Log in"',
        test_data='username="", password=""',
        expected_result='A native browser alert reads "Please fill out Username and Password."',
        notes='Verified live. This check is client-side (no network round-trip before the alert fires).',
    ),
    TestCase(
        id='LOGIN-005',
        scenario='Sign up with a username that already exists',
        type='Negative',
        priority='Medium',
        preconditions='The username is already registered',
        steps=(
            '1. Open Home page\n2. Click "Sign up"\n3. Enter the already-registered username + any password\n'
            '4. Click "Sign up"'
        ),
        test_data='An existing username',
        expected_result='A native browser alert reads "This user already exist."',
        notes=(
            'Verified live. Same native-alert pattern as login errors; the #errors label is '
            'likewise dead markup.'
        ),
    ),
    TestCase(
        id='LOGIN-006',
        scenario='Log out returns the nav bar to the logged-out state',
        type='Functional',
        priority='Medium',
        preconditions='User is currently logged in',
        steps='1. Click "Log out" in the nav bar',
        test_data='N/A',
        expected_result='"Log in"/"Sign up" links reappear; "Log out" and the welcome label hide',
        notes='',
    ),
    TestCase(
        id='LOGIN-007',
        scenario='Username with leading/trailing whitespace',
        type='Edge',
        priority='Low',
        preconditions='A registered account exists',
        steps='1. Log in with "  username  " (extra spaces) and the correct password',
        test_data='Registered username padded with spaces',
        expected_result=(
            'A native browser alert reads "User does not exist." -- the value is NOT trimmed server-side'
        ),
        notes='Verified live: whitespace padding is treated as a literally different (nonexistent) username.',
    ),
]

CART_CASES: list[TestCase] = [
    TestCase(
        id='CART-001',
        scenario='Add a single product to the cart',
        type='Functional',
        priority='High',
        preconditions='None (works for guest/anonymous users)',
        steps='1. Open a product detail page\n2. Click "Add to cart"\n3. Open the Cart page',
        test_data='e.g. "Samsung galaxy s6"',
        expected_result=(
            'A native alert reads "Product added"; the product\'s name subsequently appears as a '
            'row in the cart table'
        ),
        notes=(
            "Verified live: DemoBlaze's cart backend is shared across concurrent real-world visitors "
            'of this public practice site AND eventually-consistent (row count observed growing '
            '0 -> 275 within one test run, and the add can take several seconds to become visible). '
            "Assertions must check for the product's presence with polling, never an exact/immediate "
            'row count.'
        ),
    ),
    TestCase(
        id='CART-002',
        scenario='Add the same product to the cart twice',
        type='Edge',
        priority='Medium',
        preconditions='None',
        steps=(
            '1. Add a product to the cart\n2. Navigate back to the same product\n'
            '3. Add it to the cart again'
        ),
        test_data='"Samsung galaxy s6", added twice',
        expected_result='Two separate rows appear for the product -- NOT a single row with quantity = 2',
        notes=(
            'Verified live via the /viewcart API response: two distinct cart-item ids with the same '
            'prod_id are created, confirming "add" always appends rather than merging/incrementing '
            'quantity.'
        ),
    ),
    TestCase(
        id='CART-003',
        scenario='Delete an item from the cart',
        type='Functional',
        priority='Medium',
        preconditions='None (test adds the item itself, then deletes it)',
        steps=(
            '1. Open a product detail page and add it to the cart\n2. Open the Cart page\n'
            '3. Click "Delete" on that row'
        ),
        test_data='"Nexus 6"',
        expected_result='The row is removed from the table without a page reload',
        notes='',
    ),
    TestCase(
        id='CART-004',
        scenario='Place an order with all fields filled correctly',
        type='Functional',
        priority='High',
        preconditions='None (test adds the item itself)',
        steps=(
            '1. Open a product detail page and add it to the cart\n2. Open the Cart page\n'
            '3. Click "Place Order"\n4. Fill Name, Country, City, Credit card, Month, Year\n'
            '5. Click "Purchase"'
        ),
        test_data=(
            'Product="Nokia lumia 1520"; Name="QA Automation", Country="Vietnam", '
            'City="Ho Chi Minh City", Card="4111111111111111", Month="12", Year="2030"'
        ),
        expected_result=(
            'A confirmation dialog reads "Thank you for your purchase!" and shows an Id, Amount, '
            'Card Number, Name and Date matching the input'
        ),
        notes=(
            'Verified live. Selector note: the "Place Order" button must be matched by role/exact '
            "text, not a bare substring locator -- it otherwise ambiguously matches the order modal's "
            'own heading, "Place order".'
        ),
    ),
    TestCase(
        id='CART-005',
        scenario='Submit the order form with every field left empty',
        type='Negative',
        priority='High',
        preconditions='None (test adds the item itself)',
        steps=(
            '1. Open a product detail page and add it to the cart\n2. Open the Cart page and click '
            '"Place Order"\n3. Leave every field empty\n4. Click "Purchase"'
        ),
        test_data='Product="Nokia lumia 1520"; all order-form fields = ""',
        expected_result='No confirmation dialog appears',
        notes=(
            'Verified live: this is a SILENT no-op -- there is no visible validation error either '
            '(the #errors label never populates). Do not write an assertion expecting an error '
            'message; assert only that the confirmation never appears.'
        ),
    ),
    TestCase(
        id='CART-006',
        scenario='Submit the order form with only the Name field filled',
        type='Negative',
        priority='Medium',
        preconditions='None (test adds the item itself)',
        steps=(
            '1. Open a product detail page and add it to the cart\n2. Open the Cart page and click '
            '"Place Order"\n3. Fill only the Name field\n4. Click "Purchase"'
        ),
        test_data='Product="Nexus 6"; Name="Only Name Filled"; all other fields empty',
        expected_result='No confirmation dialog appears (same silent no-op as CART-005)',
        notes='Verified live.',
    ),
    TestCase(
        id='CART-007',
        scenario='Submit the order form with only the Name field left empty',
        type='Negative',
        priority='Medium',
        preconditions='None (test adds the item itself)',
        steps=(
            '1. Open a product detail page and add it to the cart\n2. Open the Cart page and click '
            '"Place Order"\n3. Fill Country, City, Card, Month, Year but leave Name empty\n'
            '4. Click "Purchase"'
        ),
        test_data=(
            'Product="Nexus 6"; Name=""; Country="Vietnam", City="Ho Chi Minh City", '
            'Card="4111111111111111", Month="12", Year="2030"'
        ),
        expected_result='No confirmation dialog appears -- Name specifically is required',
        notes='Verified live: confirms Name is checked even when every other field is valid.',
    ),
    TestCase(
        id='CART-008',
        scenario='Attempt to place an order with a non-numeric credit card value',
        type='Negative',
        priority='Low',
        preconditions='None (test adds the item itself)',
        steps=(
            '1. Open a product detail page and add it to the cart\n2. Open the Cart page and click '
            '"Place Order"\n3. Fill Card with a non-numeric string (e.g. "abcd")\n'
            '4. Fill remaining fields\n5. Click "Purchase"'
        ),
        test_data=(
            'Product="Nokia lumia 1520"; Name="QA Automation", Country="Vietnam", '
            'City="Ho Chi Minh City", Card="abcd", Month="12", Year="2030"'
        ),
        expected_result=(
            'Purchase SUCCEEDS regardless -- the confirmation dialog shows "Card Number: abcd" '
            'verbatim. There is no card-format validation at all.'
        ),
        notes=(
            'Verified live. Consistent with CART-005/006/007: the only field DemoBlaze validates '
            'before allowing purchase is Name; every other field (including Card) accepts '
            'arbitrary input.'
        ),
    ),
]

COLUMNS = [
    ('Test Case ID', 14),
    ('Scenario Title', 42),
    ('Type', 12),
    ('Priority', 10),
    ('Preconditions', 30),
    ('Test Steps', 50),
    ('Test Data', 28),
    ('Expected Result', 50),
    ('Notes', 55),
]


def build_sheet(workbook: openpyxl.Workbook, name: str, cases: list[TestCase]) -> Worksheet:
    sheet = workbook.create_sheet(name)
    for col_idx, (header, width) in enumerate(COLUMNS, start=1):
        cell = sheet.cell(row=1, column=col_idx, value=header)
        cell.font = Font(bold=True)
        sheet.column_dimensions[cell.column_letter].width = width
    sheet.freeze_panes = 'A2'

    for row_idx, tc in enumerate(cases, start=2):
        values = [
            tc.id,
            tc.scenario,
            tc.type,
            tc.priority,
            tc.preconditions,
            tc.steps,
            tc.test_data,
            tc.expected_result,
            tc.notes,
        ]
        for col_idx, value in enumerate(values, start=1):
            cell = sheet.cell(row=row_idx, column=col_idx, value=value)
            cell.alignment = Alignment(vertical='top', wrap_text=True)
    return sheet


def generate() -> Path:
    workbook = openpyxl.Workbook()
    workbook.properties.creator = 'QA Automation (DemoBlaze take-home)'
    workbook.remove(workbook.active)  # drop openpyxl's default "Sheet"

    build_sheet(workbook, 'Login', LOGIN_CASES)
    build_sheet(workbook, 'Cart', CART_CASES)

    out_path = Path(__file__).parent / 'test-cases.xlsx'
    workbook.save(out_path)
    return out_path


if __name__ == '__main__':
    path = generate()
    print(f'Wrote {path}')
