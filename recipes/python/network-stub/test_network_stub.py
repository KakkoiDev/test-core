"""Recipe network-stub: tests never reach the network. Stub it where the call is made.

- In the browser: page.route() answers the page's request with fixed data, or with an error.
- In Python code: httpx.MockTransport answers the client's request.
"""
import httpx
from playwright.sync_api import expect

from tips import fetch_tip


def test_the_page_shows_the_stubbed_tip(signed_in_page):
    signed_in_page.route("**/api/tip", lambda route: route.fulfill(json={"text": "Stubbed tip"}))

    signed_in_page.reload()

    expect(signed_in_page.locator("#tip")).to_have_text("Stubbed tip")


def test_the_page_survives_a_failing_service(signed_in_page):
    signed_in_page.route("**/api/tip", lambda route: route.fulfill(status=503, json={"error": "down"}))

    signed_in_page.reload()

    expect(signed_in_page.locator("#tip")).to_have_text("Tip unavailable.")


def test_code_reads_the_stubbed_response():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"text": "Drink water"}))

    assert fetch_tip(httpx.Client(transport=transport)) == "Drink water"


def test_code_falls_back_when_the_service_fails():
    transport = httpx.MockTransport(lambda request: httpx.Response(500))

    assert fetch_tip(httpx.Client(transport=transport)) == "Tip unavailable."


def test_the_stub_sees_the_request_the_code_made():
    seen = []

    def answer(request):
        seen.append(str(request.url))
        return httpx.Response(200, json={"text": "ok"})

    fetch_tip(httpx.Client(transport=httpx.MockTransport(answer)))

    assert seen == ["https://tips.example.com/today"]
