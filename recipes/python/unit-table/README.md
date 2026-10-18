# unit-table (Python)

Test a pure function with a table of cases: one row per behaviour, one test function for all rows.

- Kind: unit · Tool: pytest `parametrize`
- Use for: calculations, parsing, formatting, validation: anything with input → output and no side effects.

## Copy
Copy, never retype: `recipes/python/unit-table/test_price_table.py` (the test) and, to see it run,
`recipes/python/unit-table/price.py` (the function under test).

## Fill
1. Change `from price import total_with_tax` to your function.
2. One `pytest.param(..., id="what this row proves")` per behaviour. The `id` is the name a failure prints.
3. Errors get their own test with `pytest.raises(..., match=...)`.

## Run
`pytest recipes/python/unit-table -q`

## Don't
- Don't loop over cases inside one test: the first failure hides the others. Use rows.
- Don't call the network, the clock or random numbers: pass them in as arguments.
