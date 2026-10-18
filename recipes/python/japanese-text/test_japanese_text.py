"""Recipe japanese-text: Japanese in the page, in input and in storage.

- Switch the page to Japanese and find controls by their Japanese names.
- Type Japanese with fill() (it inserts the text the way an IME commits it).
- Compare text after Unicode normalization: 'か' + U+3099 (combining dakuten) and 'が' look the same but differ.
"""
import unicodedata

from playwright.sync_api import expect

from sample_app.app import clean_title

DECOMPOSED_GA = "が"  # how some keyboards and copied PDFs send が


def test_the_page_switches_to_japanese(signed_in_page):
    signed_in_page.get_by_role("button", name="日本語").click()

    expect(signed_in_page.get_by_role("heading", level=1)).to_have_text("タスク")
    expect(signed_in_page.locator("html")).to_have_attribute("lang", "ja")
    expect(signed_in_page.get_by_role("button", name="English")).to_be_visible()


def test_a_japanese_task_is_added_and_counted(signed_in_page):
    signed_in_page.get_by_role("button", name="日本語").click()

    signed_in_page.get_by_label("新しいタスク").fill("牛乳を買う")
    signed_in_page.get_by_role("button", name="追加").click()

    expect(signed_in_page.get_by_role("listitem").filter(has_text="牛乳を買う")).to_be_visible()
    expect(signed_in_page.locator("#count")).to_have_text("1 件のタスク")


def test_decomposed_input_is_stored_composed(signed_in_page, app_url):
    signed_in_page.get_by_label("New task").fill(f"{DECOMPOSED_GA}っこう")
    signed_in_page.get_by_role("button", name="Add").click()
    expect(signed_in_page.locator("#count")).to_have_text("1 task")

    stored = signed_in_page.request.get(f"{app_url}/api/tasks").json()[0]["title"]

    assert stored == "がっこう"
    assert len(stored) == 4


def test_clean_title_composes_and_trims():
    assert clean_title(f"　{DECOMPOSED_GA}っこう ") == "がっこう"  # full-width space trimmed too
    assert unicodedata.is_normalized("NFC", clean_title(DECOMPOSED_GA))
