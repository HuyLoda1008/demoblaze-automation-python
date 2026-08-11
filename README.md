# DemoBlaze Automation (Python)

E2E automation framework (Playwright + pytest) covering the **Login** and **Cart**
features of [demoblaze.com](https://www.demoblaze.com/).

This is a Python/pytest port of [`demoblaze-automation`](https://github.com/HuyLoda1008/demoblaze-automation)
(TypeScript/Playwright Test) — same architecture (Page Object Model, fixtures,
tagged tests, CI/CD, Docker, k8s), same live-verified DemoBlaze site behavior,
different language/tooling. See `CODE_CONVENTIONS.md` before adding a page
object or spec.

## Setup

```bash
make install
# or manually:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
playwright install --with-deps

cp config/env/prod.env.example config/env/prod.env
# fill in TEST_USER / TEST_PASSWORD -- see "Test account" below
```

Requires Python 3.9+ (pinned in `.python-version`; 3.11+ recommended if
available, but 3.9 is fully supported by every dependency here).

## Running

```bash
make test              # full suite, chromium/firefox/webkit
make test-smoke        # fast subset, marked @pytest.mark.smoke
make test-regression   # broader negative/edge coverage
make test-api          # API-only specs (no browser)
make test-unit         # pure-logic unit tests (pydantic schemas, env config)
make test-perf         # navigation-timing smoke checks
make test-a11y         # axe-core accessibility checks (Home/Product/Cart)
make test-headed       # any of the above with --headed for local debugging
make test-rerun-failed # re-run only what failed last run (reports/failed_tests.log)
make report            # open the last HTML report
make gen-testcases     # regenerate test-cases/test-cases.xlsx
make typecheck         # mypy --strict
make lint              # ruff check + POM-boundary enforcement
make format-check      # ruff format --check
```

Marker-based selection also works directly: `pytest -m auth`.

## Architecture

```
config/
  environments.py        # env registry (TEST_ENV picks a block); config/env/prod.env holds real creds
src/
  pages/                 # Page Object Model
    base_page.py         # thin base -- defers to Playwright's own auto-waiting expect()
    components/nav_bar.py  # site-wide header, composed into every page (self.nav_bar = NavBar(page))
    home_page.py           auth/login_modal_page.py   auth/signup_modal_page.py
    product/product_detail_page.py
    cart/cart_page.py      checkout/order_modal_page.py
  fixtures/cart_cleanup.py   # teardown collector for cart items (see "Teardown" below)
  utils/api_client.py        # DemoblazeApiClient -- every api.demoblaze.com call, named + typed
  utils/dialog_handler.py    # shared native-alert handling (see "Gotchas" below)
  utils/perf_utils.py        # navigation-timing helper
tests/
  conftest.py             # fixture wiring (equivalent of src/fixtures/test-options.ts)
  ui/auth/test_login.py           ui/cart/test_add_to_cart.py, test_checkout.py
  regression/test_cart_and_checkout.py
  api/test_demoblaze_api.py       (playwright.request, no browser)
  performance/test_page_load.py
  accessibility/test_a11y.py      (axe-core, allowlist-based)
  unit/test_api_client_schemas.py, test_environments.py   (pure logic, no browser/network)
test-cases/
  generate_xlsx.py        # typed source of truth -> test-cases.xlsx
scripts/check_pom_boundary.py    # AST check blocking page.click/fill/... in tests/**/test_*.py
.github/workflows/e2e.yml
```

## Test account

DemoBlaze has no account-provisioning REST API, so there is no safe way to
create-and-destroy a disposable account per test run. A single throwaway
account (shared with the TypeScript sibling project) is used; its credentials
live in `config/env/prod.env` (gitignored) and as GitHub Actions secrets in CI.

## Teardown

- **Cart items**: `src/fixtures/cart_cleanup.py`'s `CartCleanup` tracks cart-item
  ids created by a test (`cart_cleanup.track(id)`), and the `cart_cleanup`
  fixture deletes them after the test body runs, unconditionally (including on
  failure).
- **Purchased items** need no tracking — a successful `purchase()` triggers
  DemoBlaze's own `POST /deletecart` as a side effect.
- **Login session**: the `home_page` fixture logs out automatically in
  teardown if the test ends still authenticated.

## Re-running failures

Any run (local or CI) that has failures writes `reports/failed_tests.log` --
a `-k`-ready expression naming just the failed tests (via a
`pytest_terminal_summary` hook in `tests/conftest.py`). To re-run only those:

```bash
make test-rerun-failed
```

This is a flat file rather than pytest's built-in `--lf` cache because it
survives being pulled out of a CI artifact and reused on a different
machine/checkout -- e.g. copy `reports/failed_tests.log` out of a GitHub
Actions run's uploaded `reports/` artifact and run `make test-rerun-failed`
locally against the same failing subset.

## Known site quirks (see CODE_CONVENTIONS.md and inline comments)

Everything here mirrors the TypeScript sibling project's live-verified
findings: DemoBlaze reports login/signup errors via native `alert()` dialogs
(not inline text); the cart is a shared, non-session-isolated global bucket
(never assert absolute/baseline counts, only presence); `/addtocart` is
eventually consistent; the order form only validates the `Name` field; API
errors are mostly `200 { errorMessage }`, not real HTTP error codes.
