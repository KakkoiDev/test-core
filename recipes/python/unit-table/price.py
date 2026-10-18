"""The function under test: a pure function (no files, no network, no clock). Replace it with yours."""


def total_with_tax(yen: int, rate: float = 0.10) -> int:
    """Price including consumption tax, rounded down to a whole yen. Negative prices are an error."""
    if yen < 0:
        raise ValueError("A price cannot be negative.")
    return int(yen * (1 + rate) // 1)
