// Cart checkout module
//
// Intended behavior: apply the discount first, then tax the discounted amount.

function checkout(items, discountRate, taxRate) {
  let subtotal = 0;
  for (let i = 0; i < items.length; i++) {
    subtotal += items[i].price * items[i].qty;
  }

  // BUG: tax is computed on the full subtotal before the discount is applied.
  // The comment below says "discount first, then tax", but the code does the opposite.
  const tax = subtotal * taxRate;            // should be (subtotal - discount) * taxRate
  const discount = subtotal * discountRate;  // computed on pre-tax subtotal, but applied after tax

  return subtotal - discount + tax;
}

module.exports = { checkout };
