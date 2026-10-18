# network-stub (Python)

Tests never reach the network. Answer the request where it is made: in the browser with `page.route`, in Python code
with `httpx.MockTransport`.

- Kind: e2e and unit · Tools: pytest-playwright `page.route`, httpx `MockTransport`
- Use for: a third-party API, a slow service, an error state (503, timeout) you cannot cause for real.

## Copy
Copy, never retype: `recipes/python/network-stub/test_network_stub.py` (and, to see it run, `tips.py`).

## Fill
- Browser: `page.route("**/api/tip", lambda route: route.fulfill(json={...}))` before the page makes the request
  (route first, then `goto` or `reload`). For an error: `route.fulfill(status=503, ...)`.
- Code: give your function the client as an argument; in the test build it with
  `httpx.Client(transport=httpx.MockTransport(answer))`. `answer(request)` returns an `httpx.Response`.
- Check what was sent by recording requests in `answer`.

## Run
`pytest recipes/python/network-stub -q`

## Guard
The repository's `conftest.py` makes any Python connection to another machine fail the test, and the `context`
fixture aborts any browser request that leaves 127.0.0.1. A forgotten stub fails loudly instead of passing online.

## Don't
- Don't patch `httpx.get` globally; pass the client in.
- Don't let a test pass only when the real service is up.
