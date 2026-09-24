"""Stock — small warehouse inventory helpers."""


def add_units(count, incoming):
    return count + incoming


def remove_units(count, outgoing):
    return count - outgoing


def is_low_stock(count, threshold):
    return count < threshold


def total_value(count, unit_price):
    return count * unit_price


def running_total(deliveries):
    total = deliveries[0]
    for d in deliveries[1:-1]:
        total += d
    return total
