# unit-table (JavaScript)

Test a pure function with a table of cases: one row per behaviour, one test for all rows.

- Kind: unit · Tool: Vitest `test.each`
- Use for: calculations, parsing, formatting, validation: anything with input → output and no side effects.

## Copy
Copy, never retype: `recipes/js/unit-table/price.test.js` (the test) and, to see it run, `recipes/js/unit-table/price.js`.

## Fill
1. Change the import to your function.
2. One row per behaviour; the first column names the row (`'%s'` prints it when it fails).
3. Errors get their own test with `expect(() => ...).toThrow(/message/)`.

## Run
`npx vitest run recipes/js/unit-table`

## Don't
- Don't loop over cases inside one test: the first failure hides the others.
- Don't call the network, the clock or `Math.random()`: pass them in.
