// Recipe japanese-text (code half): compare and store Japanese after Unicode normalization (NFC).
import { expect, test } from 'vitest';
import { cleanTitle } from '../../../sample_app/server.js';

const DECOMPOSED_GA = 'が'; // how some keyboards and copied PDFs send が

test('decomposed input is composed and trimmed', () => {
  expect(cleanTitle(`　${DECOMPOSED_GA}っこう `)).toBe('がっこう'); // the full-width space is trimmed too
  expect(cleanTitle(DECOMPOSED_GA)).toHaveLength(1);
});

test('the two forms look alike but are not equal until normalized', () => {
  expect(DECOMPOSED_GA === 'が').toBe(false);
  expect(DECOMPOSED_GA.normalize('NFC') === 'が').toBe(true);
});

test('Japanese sorts in gojūon order with Intl.Collator', () => {
  const sorted = ['さくら', 'あめ', 'かさ'].sort(new Intl.Collator('ja').compare);
  expect(sorted).toEqual(['あめ', 'かさ', 'さくら']);
});
