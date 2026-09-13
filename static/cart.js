document.addEventListener('DOMContentLoaded', () => {
    const postForm = async (form) => {
        const response = await fetch(form.action, {
            method: 'POST',
            body: new FormData(form),
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        if (!response.ok) throw new Error('Request failed');
        return response.json();
    };

    const updateCartUI = (data) => {
        document.querySelectorAll('.cart-count').forEach((el) => {
            el.textContent = data.cart_count;
        });
        document.querySelectorAll('.cart-total').forEach((el) => {
            el.textContent = `₴${data.total}`;
        });
        document.querySelectorAll('.menu-cart-items').forEach((items) => {
            items.innerHTML = data.cart_html || '<p class="text-muted small mb-0 cart-empty">Порожньо</p>';
        });
        bindQuantityForms();
    };

    const bindQuantityForms = () => {
        document.querySelectorAll('.cart-quantity-form').forEach((form) => {
            if (form.dataset.bound) return;
            form.dataset.bound = 'true';
            const input = form.querySelector('.cart-quantity-input');
            let timeout;

            input.addEventListener('input', () => {
                clearTimeout(timeout);
                timeout = setTimeout(async () => {
                    input.disabled = true;
                    try {
                        const data = await postForm(form);
                        const sidebar = document.querySelector('.menu-cart .menu-cart-items');
                        if (sidebar) {
                            updateCartUI(data);
                        } else {
                            document.querySelectorAll('.cart-count').forEach((el) => {
                                el.textContent = data.cart_count;
                            });
                            const item = form.closest('.cart-item');
                            input.value = data.quantity;
                            item.querySelector('.cart-item-subtotal').textContent = `₴${data.subtotal}`;
                            const details = item.querySelector('.cart-item-details');
                            details.textContent = `₴${details.textContent.split(' x ')[0].replace('₴', '')} x ${data.quantity}`;
                            document.querySelector('.cart-total').textContent = `Разом: ₴${data.total}`;
                            input.disabled = false;
                        }
                    } catch {
                        form.submit();
                    }
                }, 400);
            });
        });
    };

    document.addEventListener('submit', async (e) => {
        const removeForm = e.target.closest('.cart-remove-form');
        if (removeForm) {
            e.preventDefault();
            try {
                const data = await postForm(removeForm);
                updateCartUI(data);
            } catch {
                removeForm.submit();
            }
            return;
        }

        const addForm = e.target.closest('.add-to-cart-form');
        if (addForm) {
            e.preventDefault();
            const btn = addForm.querySelector('button[type="submit"]');
            const orig = btn.textContent;
            btn.disabled = true;
            try {
                const data = await postForm(addForm);
                updateCartUI(data);
                btn.textContent = 'Додано';
                setTimeout(() => {
                    btn.textContent = orig;
                    btn.disabled = false;
                }, 1200);
            } catch {
                addForm.submit();
            }
        }
    });

    bindQuantityForms();
});