"""Checkout order total calculation."""


def calculate_order(lines, discount_bps, tax_bps):
    subtotal = sum(line["unit_price_cents"] for line in lines)
    discount = 0
    taxable = subtotal
    tax = taxable * tax_bps // 10000
    return {
        "subtotal_cents": subtotal,
        "discount_cents": discount,
        "tax_cents": tax,
        "total_cents": subtotal + tax,
    }
