from django.db import models

class Category(models.Model):
    name = models.CharField(max_length = 64)

    def __str__(self):
        return self.name

class Ingredient(models.Model):
    name = models.CharField(max_length = 64)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    description = models.TextField(null=True, blank=True, max_length=500)

    def __str__(self):
        return self.name

class Dish(models.Model):
    name = models.CharField(max_length = 64)
    ingredients = models.ManyToManyField(Ingredient)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    description = models.TextField(null=True, blank=True, max_length=500)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, null=True, blank=True, related_name='dishes')
    likes = models.ManyToManyField('auth.User', related_name='liked_dishes', blank=True)

    def __str__(self):
        return self.name
