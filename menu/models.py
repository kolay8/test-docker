from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Category(models.Model):
    name = models.CharField(max_length = 64)

    def __str__(self):
        return self.name

class Dish(models.Model):
    name = models.CharField(max_length = 64)
    image = models.ImageField(upload_to='dishes/', blank=True, null=True)
    weight = models.PositiveIntegerField(null=True, blank=True, verbose_name='Вага (г)')
    price = models.DecimalField(max_digits=7, decimal_places=2)
    description = models.TextField(null=True, blank=True, max_length=500)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, null=True, blank=True, related_name='dishes')
    likes = models.ManyToManyField('auth.User', related_name='liked_dishes', blank=True)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    delivery_address = models.CharField('Адреса доставки', max_length=255, blank=True)

    def __str__(self):
        return f"Profile for {self.user.username}"


class Order(models.Model):
    DELIVERY = 'delivery'
    PICKUP = 'pickup'
    DELIVERY_METHODS = (
        (DELIVERY, 'Доставка'),
        (PICKUP, 'Самовивіз'),
    )
    STATUS_NEW = 'new'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUSES = (
        (STATUS_NEW, 'Нове'),
        (STATUS_PROCESSING, 'В роботі'),
        (STATUS_COMPLETED, 'Виконано'),
        (STATUS_CANCELLED, 'Скасовано'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    phone = models.CharField('Телефон', max_length=20)
    delivery_address = models.CharField('Адреса доставки', max_length=255, blank=True)
    delivery_method = models.CharField('Спосіб отримання', max_length=20, choices=DELIVERY_METHODS)
    subtotal = models.DecimalField('Сума страв', max_digits=9, decimal_places=2)
    delivery_fee = models.DecimalField('Доставка', max_digits=7, decimal_places=2, default=0)
    total = models.DecimalField('Разом', max_digits=9, decimal_places=2)
    payment_method = models.CharField('Оплата', max_length=50, default='При отриманні')
    status = models.CharField('Статус', max_length=20, choices=STATUSES, default=STATUS_NEW)
    created_at = models.DateTimeField('Створено', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Замовлення #{self.pk}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    dish = models.ForeignKey(Dish, on_delete=models.SET_NULL, null=True, blank=True)
    dish_name = models.CharField('Страва', max_length=64)
    price = models.DecimalField('Ціна', max_digits=7, decimal_places=2)
    quantity = models.PositiveIntegerField('Кількість')
    subtotal = models.DecimalField('Сума', max_digits=9, decimal_places=2)

    def __str__(self):
        return f'{self.dish_name} x {self.quantity}'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
