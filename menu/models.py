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

    def __str__(self):
        return f"Profile for {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
