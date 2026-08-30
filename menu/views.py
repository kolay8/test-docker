from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import user_passes_test, login_required
from django.urls import reverse
from django.contrib.auth import login

from .forms import DishForm, CategoryForm, RegisterForm
from .models import Category, Dish, Profile

staff_required = user_passes_test(lambda u: u.is_authenticated and u.is_staff, login_url='home')


def index(request):
    return render(request, 'index.html')


def menu_page(request):
    categories = Category.objects.prefetch_related('dishes').all()
    menu_items = Dish.objects.select_related('category').all()
    return render(request, 'menu.html', {'menu_items': menu_items, 'categories': categories})


@staff_required
def dishes_manage(request):
    dishes = Dish.objects.select_related('category').all()
    return render(request, 'dishes_manage.html', {'dishes': dishes})


@staff_required
def categories_manage(request):
    categories = Category.objects.all()
    return render(request, 'categories_manage.html', {'categories': categories})


@staff_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('categories_manage')
    return render(request, 'category_form.html', {'form': CategoryForm(), 'title': 'Додати категорію'})


@staff_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('categories_manage')
    return render(request, 'category_form.html', {'form': CategoryForm(instance=category), 'title': 'Редагувати категорію'})


@staff_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        return redirect('categories_manage')
    return render(request, 'confirm_delete.html', {'title': 'Видалити категорію', 'object_name': category.name, 'cancel_url': reverse('categories_manage')})


def about_page(request):
    return render(request, 'about.html')


def detail(request, pk):
    item = get_object_or_404(Dish, pk=pk)
    return render(request, 'details.html', {'item': item})


@staff_required
def dish_create(request):
    if request.method == 'POST':
        form = DishForm(request.POST, request.FILES)
        if form.is_valid():
            dish = form.save()
            return redirect('detail', pk=dish.pk)
    return render(request, 'dish_form.html', {'form': DishForm(), 'title': 'Додати страву', 'dish': None})


@staff_required
def dish_update(request, pk):
    dish = get_object_or_404(Dish, pk=pk)
    if request.method == 'POST':
        form = DishForm(request.POST, request.FILES, instance=dish)
        if form.is_valid():
            form.save()
            return redirect('detail', pk=dish.pk)
    return render(request, 'dish_form.html', {'form': DishForm(instance=dish), 'title': 'Редагувати страву', 'dish': dish})


@staff_required
def dish_delete(request, pk):
    dish = get_object_or_404(Dish, pk=pk)
    if request.method == 'POST':
        dish.delete()
        return redirect('menu')
    return render(request, 'confirm_delete.html', {'title': 'Видалити страву', 'object_name': dish.name, 'cancel_url': reverse('detail', args=[dish.pk])})


def profile(request):
    profile_obj = None
    if request.user.is_authenticated:
        profile_obj, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, 'profile.html', {'profile': profile_obj})


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.phone = form.cleaned_data['phone']
            profile.save()
            login(request, user, backend='menu.backends.PhoneOrUsernameBackend')
            return redirect('profile')
    return render(request, 'registration/register.html', {'form': RegisterForm()})
