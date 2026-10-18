"""Recipe unit-table: one table of cases, one test function. Copy this file, then change the import and the rows."""
import pytest

from price import total_with_tax

CASES = [
    # (id: what the row proves, input, rate, expected)
    pytest.param(1000, 0.10, 1100, id="standard rate"),
    pytest.param(1000, 0.08, 1080, id="reduced rate for food"),
    pytest.param(0, 0.10, 0, id="zero stays zero"),
    pytest.param(999, 0.10, 1098, id="rounds down, never up"),
]


@pytest.mark.parametrize(("yen", "rate", "expected"), CASES)
def test_total_with_tax(yen, rate, expected):
    assert total_with_tax(yen, rate) == expected


def test_a_negative_price_is_an_error():
    with pytest.raises(ValueError, match="cannot be negative"):
        total_with_tax(-1)
