## What changed and why

<!-- The problem/need this addresses, not just a restatement of the diff. -->

## Type of change

- [ ] New test coverage (spec, page object)
- [ ] Bug fix (existing test/page object was wrong)
- [ ] Framework/infra change (fixtures, config, CI)
- [ ] Docs only

## Verification

CI enforces `mypy .`, `ruff check .` (plus `scripts/check_pom_boundary.py`,
which blocks tests from driving the DOM directly instead of through a page
object), and `ruff format --check .` on every PR via the `lint` job -- see
`CODE_CONVENTIONS.md`. The `smoke` job enforces `pytest -m smoke` passing.
Both are required checks; a failing PR can't be merged. No need to
self-report these here.

What CI can't verify -- fill in what you actually observed, not just that a
command exited 0:

- [ ] Ran the specific spec(s) touched by this PR and confirmed the intended
      behavior (e.g. "ran test_login.py headed, watched the dialog fire and
      get handled correctly"):

- [ ] If this PR adds a test that mutates cart/account state, it tracks
      cleanup via `cart_cleanup` (or explains in this PR why it doesn't need
      to -- see "Teardown" in README.md)
- [ ] If this PR documents a new DemoBlaze quirk, it was verified live
      (network capture / manual repro), not assumed

## Known site quirks this PR interacts with

<!-- Check any that apply, so a reviewer knows what to watch for.
See README.md "Known site quirks" for the full writeups. -->

- [ ] Shared/global cart (presence-based assertions, not counts)
- [ ] Eventually-consistent `/addtocart` (polling required)
- [ ] Native `alert()` dialogs for login/signup errors
- [ ] Order form only validates the `Name` field
- [ ] Python sync-API dialog-polling gotcha (see `dialog_handler.py`)
- [ ] None of the above

## Screenshots / trace (if UI-visible change)

<!-- Optional but helpful: a screenshot from a headed run
(pytest --headed), or reports/html/index.html output. -->
