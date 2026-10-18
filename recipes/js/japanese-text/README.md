# japanese-text (JavaScript)

Test Japanese in the page, in input and in storage (日本語の画面・入力・保存のテスト).

- Kind: e2e and unit · Tools: @playwright/test, Vitest, `String.prototype.normalize`, `Intl.Collator`
- Use for: any app with Japanese texts or Japanese input.

## Copy
Copy, never retype: `recipes/js/japanese-text/japanese-text.spec.js` (browser) and
`recipes/js/japanese-text/clean-title.test.js` (code).

## Fill
- Switch the language the way a person does, then find controls by their Japanese names:
  `getByRole('button', { name: '追加' })`, `getByLabel('新しいタスク')`. Check `<html lang="ja">`.
- Type with `fill('牛乳を買う')`: it commits the text like an IME.
- Normalize before comparing or storing: `text.normalize('NFC')`. Sort with `new Intl.Collator('ja').compare`.
- `trim()` also removes the full-width space `　`.

## Run
`npx vitest run recipes/js/japanese-text` and `npx playwright test recipes/js/japanese-text`

## Don't
- Don't count characters with bytes; don't test only the English texts of a bilingual app.
