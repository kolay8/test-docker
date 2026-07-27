from django.contrib import admin
from .models import Category, Ingredient, Dish

admin.site.register(Category)
admin.site.register(Ingredient)
admin.site.register(Dish)
