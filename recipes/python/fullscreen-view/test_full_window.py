"""Recipe fullscreen-view (fallback half): where the Fullscreen API is missing (iPhone Safari), the view fills the
window instead. Every test in this file runs on a phone-sized context with touch and no Fullscreen API.
"""
import pytest
from playwright.sync_api import expect

PHONE = {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 3, "is_mobile": True, "has_touch": True}
NO_FULLSCREEN_API = "Object.defineProperty(Document.prototype, 'fullscreenEnabled', { get: () => false })"


@pytest.fixture
def browser_context_args(browser_context_args):
    return {**browser_context_args, **PHONE}


@pytest.fixture
def context(context):
    context.add_init_script(NO_FULLSCREEN_API)
    return context


def test_without_the_fullscreen_api_the_view_fills_the_window_and_escape_leaves_it(signed_in_page):
    page = signed_in_page
    page.get_by_label("New task").fill("Half-typed task")
    board = page.locator("#board")
    opener = page.get_by_role("button", name="Full screen")

    opener.tap()

    expect(board).to_have_attribute("data-view", "full-window")
    assert board.bounding_box() == {"x": 0, "y": 0, "width": 390, "height": 844}
    assert page.evaluate("getComputedStyle(document.body).overflow") == "hidden"  # the page behind stays still
    exit_button = page.get_by_role("button", name="Exit full screen")
    expect(exit_button).to_be_focused()
    assert exit_button.bounding_box()["height"] >= 44
    page.keyboard.press("Escape")
    expect(board).to_have_attribute("data-view", "inline")
    expect(page.get_by_label("New task")).to_have_value("Half-typed task")
    expect(opener).to_be_focused()
