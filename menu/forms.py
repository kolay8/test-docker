from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Dish, Category, Order, Profile


def normalize_phone(value):
    digits = ''.join(filter(str.isdigit, value or ''))
    if digits.startswith('380') and len(digits) == 12:
        return digits[3:]
    if digits.startswith('0') and len(digits) == 10:
        return digits[1:]
    return digits if len(digits) == 9 else None


def format_canonical_phone(value):
    digits = normalize_phone(value)
    return f'+380 ({digits[:2]}) {digits[2:5]}-{digits[5:7]}-{digits[7:9]}' if digits else None


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
        fields = ['phone', 'delivery_address']
        labels = {
            'phone': 'Телефон',
            'delivery_address': 'Адреса доставки',
        }
        widgets = {
            'delivery_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Вулиця, будинок, квартира, місто',
                'autocomplete': 'street-address',
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            return ''
        normalized = format_canonical_phone(phone)
        if not normalized:
            raise forms.ValidationError('Введіть номер у форматі +380 (XX) XXX-XX-XX, 0XX XXX-XX-XX або 9 цифр.')
        query = Profile.objects.filter(phone=normalized)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise forms.ValidationError('Цей номер телефону вже використовується.')
        return normalized


class DeliveryAddressForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['delivery_address']
        labels = {
            'delivery_address': 'Адреса доставки',
        }
        widgets = {
            'delivery_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Вулиця, будинок, квартира, місто',
                'autocomplete': 'street-address',
            }),
        }


class OrderForm(forms.ModelForm):
    delivery_method = forms.ChoiceField(
        label='Спосіб отримання',
        choices=Order.DELIVERY_METHODS,
        widget=forms.RadioSelect,
    )

    class Meta:
        model = Order
        fields = ['phone', 'delivery_method', 'delivery_address']
        labels = {
            'phone': 'Номер телефону',
            'delivery_method': 'Спосіб отримання',
            'delivery_address': 'Адреса доставки',
        }
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'type': 'tel'}),
            'delivery_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Вулиця, будинок, квартира, місто',
                'autocomplete': 'street-address',
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        normalized = format_canonical_phone(phone)
        if not normalized:
            raise forms.ValidationError('Введіть коректний номер телефону.')
        return normalized

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('delivery_method') == Order.DELIVERY and not cleaned_data.get('delivery_address'):
            self.add_error('delivery_address', 'Вкажіть адресу доставки.')
        return cleaned_data


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']
        labels = {'status': 'Статус'}
        widgets = {'status': forms.Select(attrs={'class': 'form-select form-select-sm'})}


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Нікнейм або телефон',
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'placeholder': 'Нікнейм або +380 (XX) XXX-XX-XX',
        }),
    )


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
        normalized = format_canonical_phone(phone)
        if not normalized:
            raise forms.ValidationError('Введіть номер у форматі +380 (XX) XXX-XX-XX, 0XX XXX-XX-XX або 9 цифр.')
        if Profile.objects.filter(phone=normalized).exists():
            raise forms.ValidationError('Цей номер телефону вже використовується. Будь ласка, введіть унікальний номер.')
        return normalized

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'phone']
