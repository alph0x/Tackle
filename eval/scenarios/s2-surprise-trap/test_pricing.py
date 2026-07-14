import pricing


def test_bulk_discount():
    # The README and pricing.py docstring both say 10% off for qty >= 100.
    # That means unit_price(100) should be 1.80.
    # This test currently expects 15% off (1.70), which contradicts the spec.
    assert pricing.unit_price(100) == 1.70


def test_no_discount():
    assert pricing.unit_price(10) == 2.00


if __name__ == "__main__":
    test_bulk_discount()
    test_no_discount()
    print("All tests passed")
