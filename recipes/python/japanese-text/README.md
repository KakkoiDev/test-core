# japanese-text (Python)

Test Japanese in the page, in input and in storage.

- Kind: e2e and unit · Tools: pytest-playwright, `unicodedata`
- Use for: any app with Japanese texts or Japanese input (日本語の画面・入力・保存のテスト).

## Copy
Copy, never retype: `recipes/python/japanese-text/test_japanese_text.py`.

## Fill
- Switch the language the way a person does (a button, a setting), then find controls by their Japanese names:
  `get_by_role("button", name="追加")`, `get_by_label("新しいタスク")`. Check `<html lang="ja">`.
- Type with `fill("牛乳を買う")`: it commits the text like an IME. `press_sequentially` is only for testing
  per-key handlers.
- Normalize before comparing or storing: `unicodedata.normalize("NFC", text)`. 'か' + U+3099 and 'が' look the same.
- `str.strip()` also trims the full-width space `　` (U+3000).

## Run
`pytest recipes/python/japanese-text -q`

## Don't
- Don't count characters with bytes (`len(text.encode())`); count after NFC.
- Don't hard-code only English names in the page object of a bilingual app; test both languages.
