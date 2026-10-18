// Recipe unit-table: one table of cases, one test. Copy this file, then change the import and the rows.
import { describe, expect, test } from 'vitest';
import { totalWithTax } from './price.js';

describe('totalWithTax', () => {
  test.each([
    // [what the row proves, yen, rate, expected]
    ['standard rate', 1000, 0.1, 1100],
    ['reduced rate for food', 1000, 0.08, 1080],
    ['zero stays zero', 0, 0.1, 0],
    ['rounds down, never up', 999, 0.1, 1098],
  ])('%s', (_name, yen, rate, expected) => {
    expect(totalWithTax(yen, rate)).toBe(expected);
  });

  test('a negative price is an error', () => {
    expect(() => totalWithTax(-1)).toThrow(/cannot be negative/);
  });
});
