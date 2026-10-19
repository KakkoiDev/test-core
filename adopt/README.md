# Adopt test-core in another repository

One command copies test-core into a repository, pinned to a commit:

```sh
python3 adopt/adopt.py ../coding-core            # first time
python3 adopt/adopt.py ../coding-core --update   # later, to move to this commit
python3 ../coding-core/test-core/adopt.py --verify ../coding-core/test-core   # what its CI runs
```

It writes `test-core/` (the tools, the `functional` library with the generated test blocks, `package.json` marking the
JavaScript as ES modules, `MANIFEST.json` with the commit and a sha256 per file, and `adopt.py` for `--verify`), plus
the project's own starting files: `test-core/README.md`, `test-core/vocabulary.json`, `test-core/scenarios-template.md`
and `.github/workflows/test-core.yml` (skip it with `--no-workflow`). Library files are replaced only with `--update`;
the project's files are never overwritten. `--dry-run` prints what would change.

After adopting:
1. Python: add `test-core` to pytest's `pythonpath`; JavaScript: import from `test-core/functional/js/index.js`.
2. Set the workflow's `env` (task files, pages, e2e tests, test folders).
3. Write scenarios from `scenarios-template.md`; grow `vocabulary.json`; register the steps (recipe `scenario-steps`).
