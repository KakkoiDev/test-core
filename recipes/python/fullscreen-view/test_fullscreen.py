"""Recipe fullscreen-view (native half): a part of the page goes full screen with the Fullscreen API and comes back
unchanged. Checks: the same element went full screen (not a copy), Exit is visible and focused, the state survives,
and focus returns to the button that opened it.
"""
from playwright.sync_api import expect

FULLSCREEN_ID = "() => document.fullscreenElement ? document.fullscreenElement.id : null"


def test_full_screen_keeps_the_view_and_its_state_and_exit_returns_focus(signed_in_page):
    page = signed_in_page
    page.get_by_label("New task").fill("Half-typed task")
    board = page.locator("#board")
    board.evaluate("element => { element.dataset.probe = 'same-node'; }")  # a re-created view would lose this
    opener = page.get_by_role("button", name="Full screen")

    opener.click()

    page.wait_for_function("() => document.fullscreenElement?.id === 'board'")
    exit_button = page.get_by_role("button", name="Exit full screen")
    expect(exit_button).to_be_focused()
    exit_button.click()
    page.wait_for_function("() => document.fullscreenElement === null")
    assert page.evaluate(FULLSCREEN_ID) is None
    expect(board).to_have_attribute("data-view", "inline")
    expect(board).to_have_attribute("data-probe", "same-node")
    expect(page.get_by_label("New task")).to_have_value("Half-typed task")
    expect(opener).to_be_focused()
