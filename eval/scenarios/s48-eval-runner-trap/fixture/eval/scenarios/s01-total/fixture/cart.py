items = []


def add(item, price):
    items.append((item, price))


def total():
    return sum(price for _, price in items)
