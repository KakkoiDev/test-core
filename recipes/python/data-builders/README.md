# data-builders (Python)

Make test records with one function per kind of record: valid, unique defaults, and keyword overrides for what the test
is about.

- Kind: fixture data · Tool: plain Python (no library)
- Use for: any test that needs a user, a task, an order. Stops copy-pasted dictionaries from drifting.

## Copy
Copy, never retype: `recipes/python/data-builders/builders.py` (put it next to your `conftest.py`). Its own tests:
`recipes/python/data-builders/test_builders.py`.

## Fill
- One `build_<record>(**overrides)` per record. Defaults must be valid and unique (a counter, not random).
- In a test, write only the field that matters: `build_task(done=True)`.
- A new required field: add its default in the builder once.

## Run
`pytest recipes/python/data-builders -q`

## Don't
- Don't use random data without a seed: a failure must happen again on the next run.
- Don't use real people's names, emails or addresses: use `example.com` and obvious test values.
