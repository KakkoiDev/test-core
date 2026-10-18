"""tools/e2e_coverage.py: controls are found by role+name, label and data-testid; removing a control while its test
stays fails; a control no test uses fails unless --allow-untested; the repository itself passes."""
import json

import pytest

from tools_path import ROOT
import e2e_coverage

PAGE = """<!doctype html><html lang="en"><body>
<h1>Shop</h1>
<form>
  <label for="q">Search</label><input id="q" type="search">
  <label>Quantity <input name="n" type="number"></label>
  <input type="email" aria-label="Your email">
  <input type="hidden" name="csrf" value="x">
  <select id="size" aria-labelledby="size-label"></select><span id="size-label">Size</span>
  <textarea placeholder="Notes"></textarea>
  <button type="submit">Buy now</button>
  <input type="submit" value="Save">
</form>
<a href="/help">Help</a><a>not a link</a>
<button data-testid="close-dialog"><img src="x.svg" alt="Close"></button>
<div role="tab">Details</div><div role="status">Saved</div>
<button aria-label="Delete {{ item.name }}">x</button>
<button data-e2e-ignore="decorative, covered by a unit test">Shine</button>
<template><li><label><input type="checkbox"> <span></span></label></li></template>
</body></html>"""


def write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return str(path)


def controls_of(tmp_path, page=PAGE, messages=None):
    return e2e_coverage.parse_page(write(tmp_path, "page.html", page), messages or {}, "data-text")


def test_controls_are_found_with_their_roles_and_names(tmp_path):
    found = {(c.role, c.names[0].text) for c in controls_of(tmp_path)}

    assert found >= {("searchbox", "Search"), ("spinbutton", "Quantity"), ("textbox", "Your email"),
                     ("combobox", "Size"), ("textbox", "Notes"), ("button", "Buy now"), ("button", "Save"),
                     ("link", "Help"), ("button", "Close"), ("tab", "Details"), ("button", "Delete …"), ("checkbox", "")}
    assert not any(c.role == "status" for c in controls_of(tmp_path))
    assert len([c for c in controls_of(tmp_path) if c.role == "link"]) == 1  # <a> without href is not a link
    assert not any(c.tag == "input" and c.role is None for c in controls_of(tmp_path))  # hidden input skipped


def run(tmp_path, tests, page=PAGE, extra=()):
    page_file = write(tmp_path, "page.html", page)
    test_files = [write(tmp_path, name, text) for name, text in tests.items()]
    code = e2e_coverage.main(["--pages", page_file, "--tests", *test_files, "--json", *extra])
    return code


ALL_PY = '''
def test_shop(page):
    page.get_by_label("Search").fill("hat")
    page.get_by_role("spinbutton", name="Quantity").fill("2")
    page.get_by_label("Your email").fill("a@example.com")
    page.get_by_role("combobox", name="Size").select_option("M")
    page.get_by_placeholder("Notes").fill("gift")
    page.get_by_role("button", name="Buy now").click()
    page.get_by_role("button", name="Save").click()
    page.get_by_role("link", name="Help").click()
    page.get_by_test_id("close-dialog").click()
    page.get_by_role("tab", name="Details").click()
    page.get_by_role("button", name=f"Delete {name}").click()
    page.get_by_role("checkbox").check()
'''


def test_every_control_used_passes(tmp_path, capsys):
    assert run(tmp_path, {"test_shop.py": ALL_PY}) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["ok"] and report["untested"] == [] and report["orphans"] == []


def test_a_removed_control_whose_test_stays_fails(tmp_path, capsys):
    page = PAGE.replace('<button type="submit">Buy now</button>', "")

    assert run(tmp_path, {"test_shop.py": ALL_PY}, page=page) == 1
    report = json.loads(capsys.readouterr().out)
    assert [o["test"] for o in report["orphans"]] == ["test_shop"]
    assert 'name="Buy now"' in report["orphans"][0]["reference"]


def test_removing_the_control_and_its_test_together_passes(tmp_path):
    page = PAGE.replace('<button type="submit">Buy now</button>', "")
    tests = ALL_PY.replace('    page.get_by_role("button", name="Buy now").click()\n', "")

    assert run(tmp_path, {"test_shop.py": tests}, page=page) == 0


def test_a_control_no_test_uses_fails_unless_allowed(tmp_path, capsys):
    tests = ALL_PY.replace('    page.get_by_role("link", name="Help").click()\n', "")

    assert run(tmp_path, {"test_shop.py": tests}) == 1
    assert [u["control"] for u in json.loads(capsys.readouterr().out)["untested"]] == ['link "Help"']
    assert run(tmp_path, {"test_shop.py": tests}, extra=["--allow-untested"]) == 0


def test_javascript_locators_count(tmp_path):
    js = '''
test('shop', async ({ page }) => {
  await page.getByLabel('Search').fill('hat');
  await page.getByRole('spinbutton', { name: 'Quantity' }).fill('2');
  await page.getByLabel(/your email/i).fill('a@example.com');
  await page.getByRole('combobox', { name: 'Size' }).selectOption('M');
  await page.getByPlaceholder('Notes').fill('gift');
  await page.getByRole('button', { name: 'Buy now', exact: true }).click();
  await page.getByRole('button', { name: 'Save' }).click();
  await page.getByRole('link', { name: 'Help' }).click();
  await page.locator('[data-testid="close-dialog"]').click();
  await page.getByRole('tab', { name: 'Details' }).click();
  await page.getByRole('button', { name: `Delete ${item}` }).click();
  await page.getByRole('checkbox').check();
});
'''
    assert run(tmp_path, {"shop.spec.js": js}) == 0


def test_exact_names_must_match_exactly(tmp_path, capsys):
    tests = ALL_PY + '    page.get_by_role("button", name="Buy", exact=True).click()\n'

    assert run(tmp_path, {"test_shop.py": tests}) == 1
    assert "Buy" in json.loads(capsys.readouterr().out)["orphans"][0]["reference"]


def test_a_wildcard_name_never_hides_a_removed_label(tmp_path, capsys):
    tests = ALL_PY + '    page.get_by_label("Coupon code").fill("X")\n'

    assert run(tmp_path, {"test_shop.py": tests}) == 1
    assert "Coupon code" in json.loads(capsys.readouterr().out)["orphans"][0]["reference"]


def test_non_control_roles_and_text_are_never_orphans(tmp_path):
    tests = ALL_PY + ('    page.get_by_role("heading", name="Gone").click()\n'
                      '    page.get_by_text("Some paragraph").click()\n')

    assert run(tmp_path, {"test_shop.py": tests}) == 0


def test_an_ignore_comment_keeps_a_reference_out(tmp_path):
    tests = ALL_PY + '    page.get_by_role("button", name="Old").click()  # e2e-coverage: ignore, removed in task 12\n'

    assert run(tmp_path, {"test_shop.py": tests}) == 0


def test_messages_give_every_language_name(tmp_path):
    page = '<html lang="en"><label for="t" data-text="newTask">New task</label><input id="t">' \
           '<button data-text="add">Add</button></html>'
    messages = {"newTask": ["New task", "新しいタスク"], "add": ["Add", "追加"]}
    controls = controls_of(tmp_path, page, messages)

    names = {n.text for c in controls for n in c.names}
    assert {"New task", "新しいタスク", "Add", "追加"} <= names


def test_the_repository_follows_the_e2e_rule(capsys):
    code = e2e_coverage.main([
        "--pages", str(ROOT / "sample_app/static/index.html"),
        "--messages", str(ROOT / "sample_app/static/messages/en.json"), str(ROOT / "sample_app/static/messages/ja.json"),
        "--tests", str(ROOT / "recipes/python/**/*.py"), str(ROOT / "recipes/js/**/*.spec.js"),
        str(ROOT / "recipes/js/e2e-journey/tasks-page.js"), "--json"])

    report = json.loads(capsys.readouterr().out)
    assert code == 0, report
    assert len(report["controls"]) == 9


def test_nothing_to_check_is_not_a_pass(tmp_path):
    assert e2e_coverage.main(["--pages", str(tmp_path / "none*.html"), "--tests", str(tmp_path / "none*.py")]) == 2
