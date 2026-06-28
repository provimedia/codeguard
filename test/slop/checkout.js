// Simulated agent diff for the checkout flow.

export function submitCheckout(cart) {
  console.log('submitting cart', cart); // SLOP (debug-leftover): console.log left in.

  // Loop over each item in the cart.
  for (const item of cart.items) { // SLOP (redundant-comment): restates the next line.
    item.confirmed = true;
  }

  return { ok: true, count: cart.items.length };
}
