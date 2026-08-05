# Code Conventions

These are the conventions this repo already follows, written down so new
code stays consistent. Not aspirational -- if you find code that violates
one of these, that's a bug to fix, not a convention to relax.

This is the Python/pytest twin of the TypeScript sibling project
(`demoblaze-automation`); the *reasons* behind these conventions are
language-agnostic (they're mostly about DemoBlaze's real behavior, not
Python vs TypeScript), only the naming/tooling sections differ.

Some of this is mechanically enforced by the `lint` Makefile target/CI job
(`ruff check` / `ruff format --check` / `mypy`), including one rule specific
to this repo: `scripts/check_pom_boundary.py` blocks `page.click/fill/...`
calls inside `tests/**/test_*.py` -- a custom AST-based check, since
Python's lint ecosystem has no equivalent to ESLint's pluggable
AST-selector rules. The rest (naming, teardown, comment style) isn't
mechanically checkable and still relies on review -- call it out if you see
it drift.

## File & folder naming

- Page objects: `snake_case_page.py`, one class per file, class name is
  `PascalCase` (`login_modal_page.py` -> `LoginModalPage`).
- Specs: `tests/<category>/test_<feature>.py`, where `<category>` is
  `ui/<feature>`, `api`, `regression`, `performance`, or `accessibility`.
  pytest requires the `test_` filename prefix for discovery -- keep the
  filename and the module's obvious "feature name" describing the same
  thing.
- Fixtures/utils: `snake_case.py` under `src/fixtures/` or `src/utils/`,
  named after what they provide (`cart_cleanup.py` exports `CartCleanup`),
  not after where they're used. The actual pytest fixture *wiring*
  (`@pytest.fixture` functions) lives in `tests/conftest.py`, not next to
  the classes themselves.

## Page Object Model

- Every page object builds `Locator` fields in `__init__`, not strings
  re-queried per method. Prefer `page.get_by_role(...)` over raw CSS when
  the element has a meaningful accessible role/name -- fall back to
  `page.locator('#id')`/attribute selectors only when there's no role to
  target, or when precision requires it (see "Locator precision" below).
- A page object's methods are the *actions and queries a user/tester would
  describe in plain language* (`login_expecting_success()`,
  `get_confirmation()`), not raw Playwright calls re-exposed 1:1. If a test
  needs `.click()` on something with no semantic meaning of its own, that's
  a sign the page object is missing a named method for it.
- Composition, not inheritance, for cross-page relationships: `CartPage`
  holds `self.order_modal = OrderModalPage(page)` as a field. Don't build a
  deep inheritance chain to share behavior between page objects that
  represent different UI regions.
- `BasePage` stays thin (`goto()` + whatever's genuinely shared). Prefer
  Playwright's own auto-waiting `expect(locator)` over hand-rolled polling
  helpers -- only write a custom wait when the condition is genuinely
  compound (e.g. `CartPage.wait_for_new_ids`, which polls a set difference,
  not a single locator state).

## Locator precision

Two failure modes to actively guard against, both hit for real during
development (see README "Known site quirks"):

1. **Ambiguous text locators.** A bare `text=Foo`-style locator matches
   case-insensitive substrings anywhere on the page, including in unrelated
   headings/modals. Scope with `get_by_role('button', name='Exact Text')` or
   a locator scoped to a parent (`self.modal.get_by_role(...)`), not a bare
   text match.
2. **Synchronous native dialogs deadlocking a click.** If an action can
   trigger `alert()`/`confirm()` synchronously inside its own event handler
   (no network round-trip first), don't use `page.expect_event('dialog')`
   wrapped around the click -- register a persistent
   `page.once('dialog', ...)` listener *before* the click instead. See
   `src/utils/dialog_handler.py` for the full explanation and use
   `with_dialog()` from there rather than re-implementing this per page
   object.
3. **Python-specific: the sync API only processes background events (like
   an incoming `dialog` notification) while the main thread is inside a
   genuine Playwright call.** A raw `time.sleep()`/`threading.Event.wait()`
   after the triggering action will NOT reliably observe an asynchronously
   fired dialog (verified live -- see `dialog_handler.py`'s docstring).
   Poll with a real Playwright call (`page.wait_for_timeout(...)`), not a
   bare Python primitive. This has no TypeScript/Playwright-Test
   equivalent concern.

## Assertions

- Prefer `expect(locator).to_x()` (auto-retrying, web-first) over reading a
  value and asserting on the plain value, *unless* the page object method
  already handles retrying/polling itself (e.g. `CartPage.wait_for_new_ids`)
  -- don't double up on retry logic.
- After filling a form field under conditions where the fill might not
  "stick" on the first attempt (see `LoginModalPage._fill_credentials`),
  verify with `expect(input).to_have_value(...)` before proceeding, rather
  than trusting `fill()`'s own await silently.
- **Never assert an absolute or relative-to-a-remembered-baseline count**
  against anything backed by DemoBlaze's shared cart. It swings in both
  directions under real concurrent traffic (verified live). Assert
  *presence*, never `len(rows) == N` or `count >= baseline + N`.

## Markers

Fixed vocabulary, applied via `@pytest.mark.<name>` and registered in
`pyproject.toml` (`--strict-markers` fails loudly on a typo), not free-text:

| Marker        | Meaning                                                              |
| ------------- | ---------------------------------------------------------------------|
| `smoke`       | Fast, must-pass-on-every-PR subset. One happy-path per feature area. |
| `regression`  | Broader negative/edge coverage, not required on every push.          |
| `auth`        | Touches login/signup/logout.                                        |
| `cart`        | Touches cart/checkout.                                              |
| `api`         | `tests/api/**`, uses the `api_client`/`api_request_context` fixtures, no browser. |
| `perf`        | `tests/performance/**`, navigation-timing checks.                   |
| `a11y`        | `tests/accessibility/**`, axe-core checks.                          |

Every test gets at least one of `smoke`/`regression`, plus a feature marker.
Don't invent a new marker for a one-off need -- add a row to this table
first (and to `pyproject.toml`'s `markers` list) so the vocabulary stays
enumerable and `-m` selections stay predictable.

## Teardown

Every test that mutates shared state cleans up after itself: a pytest
fixture teardown (the code after `yield`) that runs *unconditionally* after
the test body, including on failure, and treats individual cleanup failures
as best-effort (`logging.warning`, not a raised exception that masks the
real test result).

- **Cart items added but not purchased**: track the returned id(s) from
  `cart_page.wait_for_new_ids(...)` via the `cart_cleanup` fixture
  (`cart_cleanup.track(id)`); its teardown deletes them by id.
- **Cart items that ARE purchased**: don't track them. A successful
  `order_modal.purchase()` triggers DemoBlaze's own `POST /deletecart`
  (verified live via network capture), which clears the browser's cart as a
  side effect.
- **Login session**: the `home_page` fixture teardown logs out automatically
  if the test ends still authenticated. Tests don't need to call `logout()`
  themselves unless logout behavior is what's under test.
- If you add a new kind of mutation (a new entity, a new API side effect),
  add teardown for it in the same PR that introduces the mutation, not as a
  follow-up. Verify it actually cleans up (re-run the test, check the target
  state) before considering the PR done -- don't assume a teardown call
  "must have worked."

## Comments

Default to none. Add a comment only when it captures something a future
reader can't get from the code itself: a non-obvious constraint, a
workaround for specific verified-live site behavior, or the reasoning
behind an assertion strategy. Every "why" comment in this repo should be
traceable to something that was actually observed running the suite, not a
hypothetical.

## Test structure

- Related tests for one feature area grouped in a `class Test<Feature>:`
  (or plain module-level functions when there's no shared setup) per spec
  file.
- Arrange/act/assert with blank lines between phases, not comments labeling
  them -- the blank line is the signal.
- A test that needs a generous timeout because of DemoBlaze's
  shared-backend latency uses `@pytest.mark.timeout(N)` (on the class or
  function) with a comment explaining why N and not the default.

## Python

- `mypy --strict` stays on. Don't add a bare `Any`/`# type: ignore` to route
  around a type error -- fix the underlying type, or use `object` with a
  narrowing check if the value is genuinely dynamic (e.g. parsed API/DOM
  content).
- Prefer relative-to-repo-root absolute imports (`from src.pages.home_page
  import HomePage`), not package-relative dot imports -- keeps import paths
  identical whether a module is run directly, imported by pytest, or
  imported by another module.
- Run `make typecheck` before considering a change done. It's not part of
  the pytest run itself, so nothing else catches a type error for you.
