import stock


def test_add_units():
    assert stock.add_units(10, 5) == 15


def test_remove_units():
    assert stock.remove_units(10, 4) == 6


def test_is_low_stock():
    assert stock.is_low_stock(3, 5) is True


def test_total_value():
    assert stock.total_value(4, 12) == 48


def test_running_total_three_deliveries():
    assert stock.running_total([10, 20, 30]) == 60


def test_running_total_four_deliveries():
    assert stock.running_total([5, 5, 5, 5]) == 20


if __name__ == "__main__":
    test_add_units()
    test_remove_units()
    test_is_low_stock()
    test_total_value()
    test_running_total_three_deliveries()
    test_running_total_four_deliveries()
    print("All checks passed")
