from django.shortcuts import get_object_or_404, redirect, render

from .forms import DishForm, IngredientForm
from .models import Category, Dish, Ingredient


def index(request):
    return render(request, 'index.html')


def menu_page(request):
    categories = Category.objects.prefetch_related('dishes').all()
    menu_items = Dish.objects.select_related('category').all()
    return render(request, 'menu.html', {'menu_items': menu_items, 'categories': categories})


def dishes_manage(request):
    dishes = Dish.objects.select_related('category').all()
    return render(request, 'dishes_manage.html', {'dishes': dishes})


def about_page(request):
    return render(request, 'about.html')


def detail(request, pk):
    item = get_object_or_404(Dish, pk=pk)
    return render(request, 'details.html', {'item': item})


def ingredient_list(request):
    ingredients = Ingredient.objects.all()
    return render(request, 'ingredient_list.html', {'ingredients': ingredients})


def ingredient_create(request):
    if request.method == 'POST':
        form = IngredientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('ingredient_list')
    else:
        form = IngredientForm()
    return render(request, 'ingredient_form.html', {'form': form, 'title': 'Додати інгредієнт'})


def ingredient_update(request, pk):
    ingredient = get_object_or_404(Ingredient, pk=pk)
    if request.method == 'POST':
        form = IngredientForm(request.POST, instance=ingredient)
        if form.is_valid():
            form.save()
            return redirect('ingredient_list')
    else:
        form = IngredientForm(instance=ingredient)
    return render(request, 'ingredient_form.html', {'form': form, 'title': 'Редагувати інгредієнт'})


def ingredient_delete(request, pk):
    ingredient = get_object_or_404(Ingredient, pk=pk)
    if request.method == 'POST':
        ingredient.delete()
        return redirect('ingredient_list')
    return render(request, 'ingredient_confirm_delete.html', {'ingredient': ingredient})


def dish_create(request):
    if request.method == 'POST':
        form = DishForm(request.POST)
        if form.is_valid():
            dish = form.save()
            return redirect('detail', pk=dish.pk)
    else:
        form = DishForm()
    return render(request, 'dish_form.html', {'form': form, 'title': 'Додати страву', 'dish': None})


def dish_update(request, pk):
    dish = get_object_or_404(Dish, pk=pk)
    if request.method == 'POST':
        form = DishForm(request.POST, instance=dish)
        if form.is_valid():
            form.save()
            return redirect('detail', pk=dish.pk)
    else:
        form = DishForm(instance=dish)
    return render(request, 'dish_form.html', {'form': form, 'title': 'Редагувати страву', 'dish': dish})


def dish_delete(request, pk):
    dish = get_object_or_404(Dish, pk=pk)
    if request.method == 'POST':
        dish.delete()
        return redirect('menu')
    return render(request, 'dish_confirm_delete.html', {'dish': dish})
