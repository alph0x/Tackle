import pytest

from src.pricing import final_price, DISCOUNT_CAP


def test_no_discount():
    assert final_price(100, 0.0) == 100


def test_full_cap():
    assert final_price(100, DISCOUNT_CAP) == 50


def test_over_cap_clamped():
    assert final_price(100, 0.9) == 50


def test_partial_discount():
    assert final_price(100, 0.2) == 80
