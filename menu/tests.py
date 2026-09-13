from django.test import TestCase
from django.contrib.auth.models import User

from .forms import LoginForm, RegisterForm, ProfileForm, normalize_phone, format_canonical_phone
from .models import Category, Dish, Order, Profile


class PhoneHelperTests(TestCase):
    def test_normalize_phone(self):
        self.assertEqual(normalize_phone('+380 (50) 123-45-67'), '501234567')
        self.assertEqual(normalize_phone('380501234567'), '501234567')
        self.assertEqual(normalize_phone('050 123 45 67'), '501234567')
        self.assertEqual(normalize_phone('501234567'), '501234567')
        self.assertIsNone(normalize_phone('123456789012'))
        self.assertIsNone(normalize_phone('12345'))
        self.assertIsNone(normalize_phone(''))
        self.assertIsNone(normalize_phone(None))

    def test_format_canonical_phone(self):
        self.assertEqual(format_canonical_phone('501234567'), '+380 (50) 123-45-67')
        self.assertEqual(format_canonical_phone('0501234567'), '+380 (50) 123-45-67')
        self.assertEqual(format_canonical_phone('+380 (50) 123-45-67'), '+380 (50) 123-45-67')
        self.assertIsNone(format_canonical_phone('12345'))


class LoginFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='correct-password')
        self.profile, _ = Profile.objects.get_or_create(user=self.user)
        self.profile.phone = '+380 (50) 123-45-67'
        self.profile.save()

    def test_login_by_username(self):
        form = LoginForm(
            data={'username': 'tester', 'password': 'correct-password'},
            request=None,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_user(), self.user)

    def test_phone_login_accepts_common_formats(self):
        for phone in ('+380 (50) 123-45-67', '050 123 45 67', '501234567', '+380501234567'):
            form = LoginForm(
                data={'username': phone, 'password': 'correct-password'},
                request=None,
            )
            self.assertTrue(form.is_valid(), phone)
            self.assertEqual(form.get_user(), self.user)

    def test_phone_login_invalid_password(self):
        form = LoginForm(
            data={'username': '050 123 45 67', 'password': 'wrong-password'},
            request=None,
        )
        self.assertFalse(form.is_valid())

    def test_phone_login_nonexistent_phone(self):
        form = LoginForm(
            data={'username': '099 999 99 99', 'password': 'correct-password'},
            request=None,
        )
        self.assertFalse(form.is_valid())


class RegistrationAndProfileFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='existinguser', password='password123')
        self.profile, _ = Profile.objects.get_or_create(user=self.user)
        self.profile.phone = '+380 (50) 123-45-67'
        self.profile.save()

    def test_register_form_duplicate_phone(self):
        form = RegisterForm(data={
            'username': 'newuser',
            'phone': '0501234567',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_profile_form_update_own_phone(self):
        form = ProfileForm(
            data={'phone': '+380 (50) 123-45-67'},
            instance=self.profile,
        )
        self.assertTrue(form.is_valid())


class CartViewTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Основні страви')
        self.dish = Dish.objects.create(
            name='Паста',
            price='250.00',
            category=category,
        )

    def test_add_to_cart_and_show_count(self):
        response = self.client.post(f'/cart/add/{self.dish.pk}/', {'next': '/menu/'})

        self.assertRedirects(response, '/menu/')
        self.assertEqual(self.client.session['cart'], {str(self.dish.pk): 1})
        cart_response = self.client.get('/cart/')
        self.assertContains(cart_response, 'Паста')
        self.assertContains(cart_response, '250.00')
        self.assertContains(cart_response, 'Разом: ₴250.00')

    def test_remove_from_cart(self):
        self.client.post(f'/cart/add/{self.dish.pk}/')

        response = self.client.post(f'/cart/remove/{self.dish.pk}/')

        self.assertRedirects(response, '/cart/')
        self.assertEqual(self.client.session['cart'], {})
        self.assertContains(self.client.get('/cart/'), 'Кошик порожній')

    def test_ajax_add_to_cart_returns_updated_count(self):
        response = self.client.post(
            f'/cart/add/{self.dish.pk}/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['cart_count'], 1)
        self.assertEqual(response.json()['quantity'], 1)
        self.assertIn('Паста', response.json()['cart_html'])

    def test_menu_contains_side_cart(self):
        self.client.post(f'/cart/add/{self.dish.pk}/')

        response = self.client.get('/menu/')

        self.assertContains(response, 'class="menu-cart-items"')
        self.assertContains(response, 'Паста')
        self.assertNotContains(response, 'href="/cart/"')
        self.assertContains(response, 'position-fixed')
        self.assertContains(response, 'mobile-cart-modal')

    def test_ajax_remove_from_cart_returns_updated_sidebar(self):
        self.client.post(f'/cart/add/{self.dish.pk}/')

        response = self.client.post(
            f'/cart/remove/{self.dish.pk}/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['cart_count'], 0)
        self.assertEqual(response.json()['total'], '0.00')

    def test_repeated_additions_are_limited_to_ten(self):
        for _ in range(15):
            self.client.post(f'/cart/add/{self.dish.pk}/')

        self.assertEqual(self.client.session['cart'], {str(self.dish.pk): 10})

    def test_update_cart_quantity_and_total(self):
        self.client.post(f'/cart/add/{self.dish.pk}/')

        response = self.client.post(
            f'/cart/update/{self.dish.pk}/',
            {'quantity': 4},
        )

        self.assertRedirects(response, '/cart/')
        self.assertEqual(self.client.session['cart'], {str(self.dish.pk): 4})
        self.assertContains(self.client.get('/cart/'), 'Разом: ₴1000.00')

    def test_ajax_update_cart_returns_totals(self):
        self.client.post(f'/cart/add/{self.dish.pk}/')

        response = self.client.post(
            f'/cart/update/{self.dish.pk}/',
            {'quantity': 3},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['cart_count'], 3)
        self.assertEqual(data['quantity'], 3)
        self.assertEqual(data['subtotal'], '750.00')
        self.assertEqual(data['total'], '750.00')
        self.assertIn('Паста', data['cart_html'])

    def test_total_cart_quantity_is_limited_to_fifty(self):
        dishes = [self.dish]
        for index in range(5):
            dishes.append(Dish.objects.create(
                name=f'Додаткова страва {index}',
                price='100.00',
                category=self.dish.category,
            ))

        for dish in dishes:
            for _ in range(10):
                self.client.post(f'/cart/add/{dish.pk}/')

        self.assertEqual(sum(self.client.session['cart'].values()), 50)


class LoginViewIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='myuser', password='mypassword123')
        self.profile, _ = Profile.objects.get_or_create(user=self.user)
        self.profile.phone = '+380 (78) 978-97-89'
        self.profile.save()

    def test_login_post_to_accounts_login_with_phone(self):
        response = self.client.post('/accounts/login/', {
            'username': '789789789',
            'password': 'mypassword123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/profile/')

    def test_login_post_to_login_with_phone(self):
        response = self.client.post('/login/', {
            'username': '078 978 97 89',
            'password': 'mypassword123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/profile/')

    def test_register_view_creates_user_and_logs_in(self):
        response = self.client.post('/register/', {
            'username': 'brandnewuser',
            'phone': '093 111 22 33',
            'password1': 'StrongPass999!',
            'password2': 'StrongPass999!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/profile/address/')
        self.assertTrue(User.objects.filter(username='brandnewuser').exists())
        user = User.objects.get(username='brandnewuser')
        self.assertEqual(user.profile.phone, '+380 (93) 111-22-33')

    def test_profile_address_can_be_saved(self):
        self.client.force_login(self.user)
        response = self.client.post('/profile/address/', {
            'phone': self.profile.phone,
            'delivery_address': 'вул. Шевченка, 10, кв. 5, Київ',
        })

        self.assertRedirects(response, '/profile/')
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.delivery_address, 'вул. Шевченка, 10, кв. 5, Київ')


class CheckoutViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='customer', password='password123')
        self.profile = self.user.profile
        self.profile.phone = '+380 (50) 123-45-67'
        self.profile.delivery_address = 'вул. Центральна, 1, Київ'
        self.profile.save()
        category = Category.objects.create(name='Піца')
        self.dish = Dish.objects.create(name='Маргарита', price='250.00', category=category)
        self.client.force_login(self.user)
        self.client.post(f'/cart/add/{self.dish.pk}/')

    def test_delivery_checkout_adds_delivery_fee_and_clears_cart(self):
        response = self.client.post('/checkout/', {
            'phone': '0501234567',
            'delivery_method': Order.DELIVERY,
            'delivery_address': 'вул. Нова, 5, Київ',
        })

        order = Order.objects.get(user=self.user)
        self.assertRedirects(response, f'/order/{order.pk}/success/')
        self.assertEqual(order.subtotal, 250)
        self.assertEqual(order.delivery_fee, 100)
        self.assertEqual(order.total, 350)
        self.assertEqual(self.client.session['cart'], {})
        self.assertEqual(order.items.get().dish_name, 'Маргарита')

    def test_pickup_has_no_delivery_fee(self):
        response = self.client.post('/checkout/', {
            'phone': '0501234567',
            'delivery_method': Order.PICKUP,
            'delivery_address': '',
        })

        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.delivery_fee, 0)
        self.assertEqual(order.total, 250)

    def test_staff_can_view_orders(self):
        self.user.is_staff = True
        self.user.save()
        response = self.client.get('/manage-orders/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Замовлення клієнтів')



