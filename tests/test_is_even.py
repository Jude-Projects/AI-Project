import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from is_even import is_even


def test_is_even_with_even_number():
    assert is_even(4) is True


def test_is_even_with_odd_number():
    assert is_even(3) is False


def test_is_even_with_zero():
    assert is_even(0) is True


def test_is_even_with_negative_even_number():
    assert is_even(-4) is True


def test_is_even_with_negative_odd_number():
    assert is_even(-3) is False
