# unit-nodeps (JavaScript)

A unit test with Node's built-in runner (`node:test`, `node:assert`), for a project that installs nothing.

- Kind: unit · Tool: `node --test`
- Use for: a no-dependency starter. With Vitest available, prefer `unit-table`.

## Copy
Copy, never retype: `recipes/js/unit-nodeps/slug.nodetest.js` and, to see it run, `recipes/js/unit-nodeps/slug.js`.
In your project, name it `*.test.js` (Node finds those on its own); here `.nodetest.js` keeps it away from Vitest.

## Fill
Change the import and the `cases` rows; one `test()` per row, named after it.

## Run
`node --test recipes/js/unit-nodeps/slug.nodetest.js`
