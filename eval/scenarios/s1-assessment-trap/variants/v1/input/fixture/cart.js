// Cart checkout module
//
// Intended behavior: apply the discount first, then tax the discounted amount.

function checkout(items, discountRate, taxRate) {
  let subtotal = 0;
  for (let i = 0; i < items.length; i++) {
    subtotal += items[i].price * items[i].qty;
  }

  const tax = subtotal * taxRate;
  const discount = subtotal * discountRate;

  return subtotal - discount + tax;
}

module.exports = { checkout };
