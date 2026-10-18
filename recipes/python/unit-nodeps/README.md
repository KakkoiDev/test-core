# unit-nodeps (Python)

A unit test with the standard library only (`unittest`), for a project that installs nothing. pytest reads the same
file, so it keeps working when the project grows.

- Kind: unit · Tool: stdlib `unittest` (`subTest` for table rows)
- Use for: a no-dependency starter or script. With pytest available, prefer `unit-table`.

## Copy
Copy, never retype: `recipes/python/unit-nodeps/test_slug_unittest.py` and, to see it run, `recipes/python/unit-nodeps/slug.py`.

## Fill
Change the import and the `cases` rows. Keep `with self.subTest(...)` so each row reports on its own.

## Run
`python3 -m unittest discover -s recipes/python/unit-nodeps` (or `pytest recipes/python/unit-nodeps`)
