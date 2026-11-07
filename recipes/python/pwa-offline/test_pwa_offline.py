"""Recipe pwa-offline: an installable app keeps working offline. Checks: its service worker takes control with the
app's own scope, CacheStorage holds exactly the app's files, a reload with the network cut is served by the worker and
still works, and full Chromium reports the app installable (and a page without a manifest not).
"""
import pytest
from playwright.sync_api import expect

from pwa.pwa import cache_contents, installability, reload_offline, service_worker_control

APP = "/pwa/index.html"
CHROMIUM_FLAGS = ["--use-mock-keychain", "--password-store=basic"]  # NOTES.md 1


def test_the_service_worker_takes_control_of_its_own_scope_and_caches_the_app(page, app_url):
    page.goto(app_url + APP)

    registration = service_worker_control(page)

    assert registration == {"scope": f"{app_url}/pwa/", "scriptURL": f"{app_url}/pwa/sw.js"}
    assert cache_contents(page) == {
        "tally-v1": ["/pwa/app.js", "/pwa/icon-192.png", "/pwa/icon-512.png", "/pwa/index.html", "/pwa/manifest.webmanifest"],
    }


def test_an_offline_reload_is_served_by_the_service_worker_and_the_app_still_works(page, app_url):
    page.goto(app_url + APP)
    service_worker_control(page)

    reload = reload_offline(page)

    assert reload == {"status": 200, "from_service_worker": True}
    expect(page.get_by_role("heading", name="Tally")).to_be_visible()
    page.get_by_role("button", name="Add one").click()  # app.js came from the cache too
    expect(page.locator("#count")).to_have_text("1")


def test_chromium_reports_the_app_installable_and_a_page_without_a_manifest_not(playwright, browser_type_launch_args,
                                                                                 app_url, tmp_path):
    # Full Chromium (the headless shell says "installable" to everything) on a persistent profile (a fresh context
    # would add "in-incognito").
    context = playwright.chromium.launch_persistent_context(
        tmp_path / "profile", **{**browser_type_launch_args, "args": CHROMIUM_FLAGS}, channel="chromium")
    try:
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(app_url + APP)
        service_worker_control(page)

        app = installability(page)
        page.goto(app_url + "/")
        plain = installability(page)

        assert app == {"errors": [], "manifest_url": f"{app_url}/pwa/manifest.webmanifest", "manifest_errors": []}
        assert "no-manifest" in plain["errors"]
    finally:
        context.close()


def test_the_installability_check_refuses_the_headless_shell_instead_of_passing(page, app_url):
    page.goto(app_url + "/")

    with pytest.raises(RuntimeError, match="headless shell"):
        installability(page)
