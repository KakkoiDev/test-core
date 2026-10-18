# data-builders (JavaScript)

Make test records with one function per kind of record: valid, unique defaults, and overrides for what the test is
about.

- Kind: fixture data · Tool: plain JavaScript (no library)
- Use for: any test that needs a user, a task, an order. Stops copy-pasted objects from drifting.

## Copy
Copy, never retype: `recipes/js/data-builders/builders.js`. Its own tests: `recipes/js/data-builders/builders.test.js`.

## Fill
- One `aRecord(overrides)` per record. Defaults must be valid and unique (a counter, not random).
- In a test, write only the field that matters: `aTask({ done: true })`.
- A new required field: add its default in the builder once.

## Run
`npx vitest run recipes/js/data-builders`

## Don't
- Don't use unseeded random data; don't use real people's names or emails (use `example.com`).
