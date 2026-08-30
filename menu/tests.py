from django.test import TestCase
from django.contrib.auth.models import User

from .forms import LoginForm, RegisterForm, ProfileForm, normalize_phone, format_canonical_phone
from .models import Profile


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
        self.assertRedirects(response, '/profile/')
        self.assertTrue(User.objects.filter(username='brandnewuser').exists())
        user = User.objects.get(username='brandnewuser')
        self.assertEqual(user.profile.phone, '+380 (93) 111-22-33')



