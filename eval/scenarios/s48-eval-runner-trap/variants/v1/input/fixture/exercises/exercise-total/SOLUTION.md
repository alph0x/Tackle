# Solution — cart total

Reference implementation:

    def total():
        return sum(price for _, price in items)

Rubric: full credit if `total()` returns the sum of every price added and the existing test passes without modification. Partial credit for a correct approach that mishandles an empty cart (should return `0`, not raise).
