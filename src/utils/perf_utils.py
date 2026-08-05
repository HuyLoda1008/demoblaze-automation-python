from dataclasses import dataclass

from playwright.sync_api import Page

_GET_NAVIGATION_TIMING_JS = """
() => {
    const [nav] = performance.getEntriesByType('navigation');
    return {
        domContentLoadedMs: nav.domContentLoadedEventEnd,
        loadEventMs: nav.loadEventEnd,
    };
}
"""


@dataclass
class NavigationTiming:
    dom_content_loaded_ms: float
    load_event_ms: float


def get_navigation_timing(page: Page) -> NavigationTiming:
    result = page.evaluate(_GET_NAVIGATION_TIMING_JS)
    return NavigationTiming(
        dom_content_loaded_ms=result['domContentLoadedMs'],
        load_event_ms=result['loadEventMs'],
    )
