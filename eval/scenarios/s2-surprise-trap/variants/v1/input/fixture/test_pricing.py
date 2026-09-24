import pricing


def test_bulk_discount():
    # 100+ units should be 15% off.
    assert pricing.unit_price(100) == 1.70


def test_no_discount():
    assert pricing.unit_price(10) == 2.00


if __name__ == "__main__":
    test_bulk_discount()
    test_no_discount()
    print("All tests passed")
