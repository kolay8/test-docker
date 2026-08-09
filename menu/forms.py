from django import forms

from .models import Dish, Ingredient


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['name', 'price', 'description']


class DishForm(forms.ModelForm):
    class Meta:
        model = Dish
        fields = ['name', 'ingredients', 'price', 'description', 'category']
