/* localStorage mirrors the cart UI for convenience; Django session data remains authoritative. */
(() => {
  const STORAGE_KEY = "saffronStoneCart";
  const readCart = () => {
    try {
      const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
      return value && typeof value === "object" && !Array.isArray(value) ? value : {};
    } catch (_) {
      return {};
    }
  };
  const writeCart = (cart) => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(cart)); } catch (_) { /* storage may be disabled */ }
  };

  // Record add-to-cart interactions for a responsive client-side cart mirror.
  document.querySelectorAll(".add-form").forEach((form) => {
    form.addEventListener("submit", () => {
      const match = form.action.match(/add\/(\d+)\//);
      if (!match) return;
      const cart = readCart();
      const id = match[1];
      cart[id] = Math.min(50, (Number.parseInt(cart[id], 10) || 0) + 1);
      writeCart(cart);
    });
  });

  // Keep the mirror aligned when quantities are changed or items removed on the cart page.
  document.querySelectorAll(".quantity-form").forEach((form) => {
    form.addEventListener("submit", () => {
      const match = form.action.match(/update\/(\d+)\//);
      if (!match) return;
      const input = form.querySelector('input[name="quantity"]');
      const quantity = Number.parseInt(input?.value, 10);
      if (quantity >= 1 && quantity <= 50) {
        const cart = readCart();
        cart[match[1]] = quantity;
        writeCart(cart);
      }
    });
  });
  document.querySelectorAll('form[action*="/cart/remove/"]').forEach((form) => {
    form.addEventListener("submit", () => {
      const match = form.action.match(/remove\/(\d+)\//);
      if (!match) return;
      const cart = readCart();
      delete cart[match[1]];
      writeCart(cart);
    });
  });
  const checkout = document.getElementById("checkout-form");
  if (checkout) checkout.addEventListener("submit", () => writeCart({}));
})();
