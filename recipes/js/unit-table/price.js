// The function under test: a pure function (no files, no network, no clock). Replace it with yours.
export function totalWithTax(yen, rate = 0.1) {
  if (yen < 0) throw new RangeError('A price cannot be negative.');
  return Math.floor(yen * (1 + rate));
}
