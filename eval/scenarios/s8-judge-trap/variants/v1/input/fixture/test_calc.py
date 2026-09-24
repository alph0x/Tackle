import calc


def test_add():
    assert calc.add(2, 3) == 5


def test_subtract():
    assert calc.subtract(10, 4) == 6


def test_multiply():
    assert calc.multiply(3, 4) == 12


def test_divide():
    assert calc.divide(9, 2) == 4.5


def test_power_cube():
    assert calc.power(2, 3) == 8


def test_power_square():
    assert calc.power(3, 2) == 9


if __name__ == "__main__":
    test_add()
    test_subtract()
    test_multiply()
    test_divide()
    test_power_cube()
    test_power_square()
    print("All tests passed")
