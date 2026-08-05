import time
from typing import Callable

from playwright.sync_api import Dialog, Page


def with_dialog(page: Page, action: Callable[[], None], timeout_ms: int = 10_000) -> str:
    """Capture the message of the next native dialog() triggered by `action`.

    Some DemoBlaze dialogs fire synchronously inside a click's own event
    handler (no network round-trip -- e.g. the empty-field login check). A
    `page.expect_event('dialog')` context manager wrapped tightly around the
    click can deadlock in that case: Chromium's own post-click actionability
    re-check blocks on the already-open native dialog, so the click never
    settles and `expect_event` never gets a turn to resolve. Registering a
    persistent `page.once('dialog', ...)` listener BEFORE calling `action()`
    avoids that deadlock.

    `action()` returning also does NOT guarantee the dialog has already
    fired for the asynchronous case (e.g. wrong-password login -- the click
    can resolve well before the /login response triggers the alert).

    Playwright Python's SYNC API only processes queued background events
    (like an incoming 'dialog' notification) as a side effect of the main
    thread being inside the sync wrapper's own blocking machinery (e.g.
    page.click(), page.wait_for_timeout()) -- a plain `time.sleep()` or
    `threading.Event.wait()` on the main thread does NOT pump it (verified
    live: an async dialog sat unprocessed for 15s+ under a raw
    threading.Event.wait(), then fired immediately once another Playwright
    call ran). So after the action, we must actively poll using a genuine
    Playwright call (`page.wait_for_timeout`), not a bare Python primitive.
    This has no JS/Playwright-Test equivalent concern -- it's a Python
    sync-API-specific gotcha.
    """
    message_holder: list[str] = []
    dialog_caught = {'value': False}

    def handle_dialog(dialog: Dialog) -> None:
        message_holder.append(dialog.message)
        dialog.accept()
        dialog_caught['value'] = True

    page.once('dialog', handle_dialog)

    action()

    deadline = time.monotonic() + timeout_ms / 1000
    while not dialog_caught['value']:
        if time.monotonic() > deadline:
            raise TimeoutError(f'Timed out after {timeout_ms}ms waiting for a dialog')
        page.wait_for_timeout(100)

    return message_holder[0]
