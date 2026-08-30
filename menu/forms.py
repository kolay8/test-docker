from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Dish, Category, Profile


def normalize_phone(value):
    digits = ''.join(filter(str.isdigit, value or ''))
    if digits.startswith('380') and len(digits) == 12:
        return digits[3:]
    if digits.startswith('0') and len(digits) == 10:
        return digits[1:]
    if len(digits) == 9:
        return digits
    return None


def format_canonical_phone(digits_or_value):
    digits = normalize_phone(digits_or_value) if (len(digits_or_value or '') != 9 or not digits_or_value.isdigit()) else digits_or_value
    if digits and len(digits) == 9:
        return f'+380 ({digits[:2]}) {digits[2:5]}-{digits[5:7]}-{digits[7:9]}'
    return None


class DishForm(forms.ModelForm):
    class Meta:
        model = Dish
        fields = ['name', 'image', 'weight', 'price', 'description', 'category']
        labels = {
            'name': 'Назва страви',
            'image': 'Фото страви',
            'weight': 'Вага (г)',
            'price': 'Ціна (грн)',
            'description': 'Опис',
            'category': 'Категорія',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введіть назву'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'напр. 350', 'min': '1'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Опис страви'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            return ''
        digits = normalize_phone(phone)
        if not digits:
            raise forms.ValidationError('Введіть номер у форматі +380 (XX) XXX-XX-XX, 0XX XXX-XX-XX або 9 цифр.')
        normalized = format_canonical_phone(digits)
        query = Profile.objects.filter(phone=normalized)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise forms.ValidationError('Цей номер телефону вже використовується.')
        return normalized


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Нікнейм або телефон',
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'placeholder': 'Нікнейм або +380 (XX) XXX-XX-XX',
        }),
    )

    def clean(self):
        identifier = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if identifier and password:
            self.user_cache = authenticate(
                self.request,
                username=identifier,
                password=password,
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)
        return self.cleaned_data


class RegisterForm(UserCreationForm):
    phone = forms.CharField(
        label='Телефон',
        max_length=19,
        widget=forms.TextInput(attrs={
            'class': 'form-control d-inline-block w-auto',
            'type': 'tel',
            'inputmode': 'numeric',
            'placeholder': '(XX) XXX-XX-XX',
            'autocomplete': 'tel',
            'required': True,
        }),
    )

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        digits = normalize_phone(phone)
        if not digits:
            raise forms.ValidationError('Введіть номер у форматі +380 (XX) XXX-XX-XX, 0XX XXX-XX-XX або 9 цифр.')
        normalized = format_canonical_phone(digits)
        if Profile.objects.filter(phone=normalized).exists():
            raise forms.ValidationError('Цей номер телефону вже використовується. Будь ласка, введіть унікальний номер.')
        return normalized

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'phone']
