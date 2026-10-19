"""functional/primitives.py in a browser: find, act, read, stub the network, freeze time, and loud missing controls."""
import re
from pathlib import Path

import pytest
from playwright.sync_api import expect

from functional import Registry, StepFailed, parse_scenarios, run_scenario
from functional import primitives as p
from functional.blocks.python import data_table
from functional.blocks.selftest import self_test

KIT = Path(__file__).resolve().parents[1] / "fixtures" / "app-blocks"
FORM = """<form><label for="email">Email</label><input id="email" aria-describedby="email-help" aria-invalid="true">
<p id="email-help">Enter an email like name@example.com.</p>
<label><input type="checkbox" name="r"> Remember me</label>
<select aria-label="Subject"><option value="v">Vocabulary</option><option value="g">Grammar</option></select>
<button type="button" aria-busy="true" onclick="this.textContent='Saved'">Save</button>
<p data-testid="out" hidden>secret</p><canvas role="img" aria-label="Orders per day: Saturday is busiest"></canvas></form>"""


@pytest.fixture
def form_page(page):
    page.set_content(FORM)
    return page


def test_control_finds_by_role_label_text_test_id_and_css(form_page):
    page = form_page
    assert p.control(page, role="button", name="Save").count() == 1
    assert p.control(page, label="Email").count() == 1
    assert p.control(page, text="Remember me").count() == 1
    assert p.control(page, test_id="out").count() == 1  # hidden but there
    assert p.control(page, css="canvas").count() == 1


def test_a_missing_control_fails_loudly(form_page, monkeypatch):
    monkeypatch.setattr(p.settings, "timeout", 200)
    with pytest.raises(p.ControlMissing, match='Form: uses a control that no longer exists: button "Delete"'):
        p.control(form_page, role="button", name="Delete", block="Form")
    with pytest.raises(p.ControlMissing, match='field labelled "Password"'):
        p.control(form_page, label="Password")


def test_act_and_read(form_page):
    page = form_page
    p.fill(p.control(page, label="Email"), "aiko@example.com")
    p.expect_value(p.control(page, label="Email"), "aiko@example.com")
    p.check(p.control(page, role="checkbox", name="Remember me"))
    p.expect_checked(p.control(page, role="checkbox"))
    p.uncheck(p.control(page, role="checkbox"))
    p.expect_checked(p.control(page, role="checkbox"), checked=False)
    p.select(p.control(page, role="combobox", name="Subject"), "Grammar")
    p.expect_value(p.control(page, role="combobox"), "g")
    p.press(p.control(page, label="Email"), "End")
    p.expect_attribute(p.control(page, role="button"), "aria-busy", "true")
    p.click(p.control(page, role="button", name="Save"))
    p.expect_text(page, "Saved")
    p.expect_text(p.control(page, role="button"), "Saved", exact=True)
    p.expect_no_text(page, "secret")
    p.expect_hidden(p.control(page, test_id="out"))
    p.expect_visible(p.control(page, role="img"))
    p.expect_name(p.control(page, role="img"), "Saturday is busiest")
    p.expect_description(p.control(page, label="Email"), "name@example.com")
    p.expect_count(page.get_by_role("checkbox"), 1)
    assert "Saved" in p.seen_text(page) and p.seen_text(p.control(page, role="button")) == "Saved"


def test_stub_network_in_the_page_and_freeze_time(page, app_url):
    p.stub_network({"GET /api/tip": {"json": {"text": "A stubbed tip"}}}, page=page)
    p.freeze_time("2026-10-19T09:00:00", page=page)
    p.goto(page, app_url)
    assert page.evaluate("new Date().toISOString()") == "2026-10-19T09:00:00.000Z"
    response = page.evaluate("fetch('/api/tip').then(r => r.json())")
    assert response == {"text": "A stubbed tip"}
    assert page.evaluate("fetch('/api/me').then(r => r.status)") == 401  # not in the table: the real route answers


def test_a_block_step_fails_when_the_page_disagrees(page):
    """A self-test is not a formality: the same steps fail when what the page shows is different."""
    module = data_table
    steps = Registry(module.steps)
    original = module.SELF_TEST
    expect.set_options(timeout=500)
    try:
        module.SELF_TEST = ["Then the table shows 5 rows"]
        with pytest.raises(StepFailed, match=re.escape('step "Then the table shows 5 rows" failed')):
            self_test(page, module, kit=KIT, registry=steps)
    finally:
        module.SELF_TEST = original
        expect.set_options(timeout=5000)
