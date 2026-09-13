from decimal import Decimal

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import CategoryForm, DeliveryAddressForm, DishForm, OrderForm, OrderStatusForm, RegisterForm
from .models import Category, Dish, Order, OrderItem, Profile

staff_required = user_passes_test(lambda u: u.is_authenticated and u.is_staff, login_url='home')
MAX_DISH_QUANTITY = 10
MAX_CART_QUANTITY = 50


def _get_cart(request):
    stored = request.session.get('cart', {})
    if isinstance(stored, list):
        return {str(pk): 1 for pk in stored}
    return {
        str(pk): int(qty)
        for pk, qty in stored.items()
        if str(qty).isdigit() and int(qty) > 0
    }


def _cart_count(cart):
    return sum(cart.values())


def _cart_data(cart, request):
    dishes = list(Dish.objects.filter(pk__in=cart).select_related('category'))
    dishes.sort(key=lambda dish: list(cart).index(str(dish.pk)))
    for dish in dishes:
        dish.quantity = cart[str(dish.pk)]
        dish.subtotal = dish.price * dish.quantity
    total = sum((d.subtotal for d in dishes), Decimal('0.00'))
    html = ''.join(
        render_to_string('cart_item.html', {'dish': dish}, request=request)
        for dish in dishes
    )
    return dishes, total, html


def index(request):
    return render(request, 'index.html')


def menu_page(request):
    categories = Category.objects.prefetch_related('dishes').all()
    cart = _get_cart(request)
    cart_dishes, cart_total, _ = _cart_data(cart, request)
    return render(request, 'menu.html', {
        'categories': categories,
        'cart_dishes': cart_dishes,
        'cart_total': cart_total,
    })


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
    form = CategoryForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('categories_manage')
    return render(request, 'category_form.html', {'form': form, 'title': 'Додати категорію'})


@staff_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=category)
    if form.is_valid():
        form.save()
        return redirect('categories_manage')
    return render(request, 'category_form.html', {'form': form, 'title': 'Редагувати категорію'})


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


def add_to_cart(request, pk):
    if request.method != 'POST':
        return redirect('detail', pk=pk)

    get_object_or_404(Dish, pk=pk)
    cart = _get_cart(request)
    dish_id = str(pk)
    if cart.get(dish_id, 0) < MAX_DISH_QUANTITY and _cart_count(cart) < MAX_CART_QUANTITY:
        cart[dish_id] = cart.get(dish_id, 0) + 1
    request.session['cart'] = cart
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        _, total, html = _cart_data(cart, request)
        return JsonResponse({
            'cart_count': _cart_count(cart),
            'quantity': cart.get(dish_id, 0),
            'total': str(total),
            'cart_html': html,
        })
    next_url = request.POST.get('next', '')
    if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
        return redirect(next_url)
    return redirect('cart')


def remove_from_cart(request, pk):
    if request.method == 'POST':
        cart = _get_cart(request)
        cart.pop(str(pk), None)
        request.session['cart'] = cart
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            _, total, html = _cart_data(cart, request)
            return JsonResponse({
                'cart_count': _cart_count(cart),
                'total': str(total),
                'cart_html': html,
            })
    return redirect('cart')


def update_cart(request, pk):
    dish = get_object_or_404(Dish, pk=pk)
    if request.method == 'POST':
        cart = _get_cart(request)
        dish_id = str(pk)
        try:
            quantity = int(request.POST.get('quantity', 0))
        except (TypeError, ValueError):
            quantity = 0

        if quantity <= 0:
            cart.pop(dish_id, None)
        else:
            other_items_count = _cart_count(cart) - cart.get(dish_id, 0)
            max_quantity = min(MAX_DISH_QUANTITY, MAX_CART_QUANTITY - other_items_count)
            if max_quantity > 0:
                cart[dish_id] = min(quantity, max_quantity)
        request.session['cart'] = cart
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            _, total, html = _cart_data(cart, request)
            actual_quantity = cart.get(dish_id, 0)
            return JsonResponse({
                'cart_count': _cart_count(cart),
                'quantity': actual_quantity,
                'subtotal': str(dish.price * actual_quantity),
                'total': str(total),
                'cart_html': html,
            })
    return redirect('cart')


def cart_page(request):
    cart = _get_cart(request)
    dishes, total, _ = _cart_data(cart, request)
    return render(request, 'cart.html', {'dishes': dishes, 'total': total})


@login_required(login_url='login')
def checkout(request):
    cart = _get_cart(request)
    dishes, subtotal, _ = _cart_data(cart, request)
    if not dishes:
        return redirect('cart')

    profile_obj, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            is_delivery = form.cleaned_data['delivery_method'] == Order.DELIVERY
            delivery_fee = Decimal('100.00') if is_delivery else Decimal('0.00')
            with transaction.atomic():
                order = form.save(commit=False)
                order.user = request.user
                order.subtotal = subtotal
                order.delivery_fee = delivery_fee
                order.total = subtotal + delivery_fee
                order.payment_method = 'При отриманні'
                order.save()
                OrderItem.objects.bulk_create([
                    OrderItem(
                        order=order,
                        dish=dish,
                        dish_name=dish.name,
                        price=dish.price,
                        quantity=dish.quantity,
                        subtotal=dish.subtotal,
                    )
                    for dish in dishes
                ])
                request.session['cart'] = {}
            return redirect('order_success', pk=order.pk)
    else:
        form = OrderForm(initial={
            'phone': profile_obj.phone,
            'delivery_address': profile_obj.delivery_address,
            'delivery_method': Order.DELIVERY,
        })
    return render(request, 'checkout.html', {
        'form': form,
        'dishes': dishes,
        'subtotal': subtotal,
        'delivery_total': subtotal + Decimal('100.00'),
        'pickup_total': subtotal,
    })


@login_required(login_url='login')
def order_success(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related('items'), pk=pk, user=request.user)
    return render(request, 'order_success.html', {'order': order})


@staff_required
def orders_manage(request):
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=request.POST.get('order_id'))
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
    orders = Order.objects.prefetch_related('items').select_related('user')
    return render(request, 'orders_manage.html', {'orders': orders})


@staff_required
def dish_create(request):
    form = DishForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        dish = form.save()
        return redirect('detail', pk=dish.pk)
    return render(request, 'dish_form.html', {'form': form, 'title': 'Додати страву', 'dish': None})


@staff_required
def dish_update(request, pk):
    dish = get_object_or_404(Dish, pk=pk)
    form = DishForm(request.POST or None, request.FILES or None, instance=dish)
    if form.is_valid():
        form.save()
        return redirect('detail', pk=dish.pk)
    return render(request, 'dish_form.html', {'form': form, 'title': 'Редагувати страву', 'dish': dish})


@staff_required
def dish_delete(request, pk):
    dish = get_object_or_404(Dish, pk=pk)
    if request.method == 'POST':
        dish.delete()
        return redirect('menu')
    return render(request, 'confirm_delete.html', {'title': 'Видалити страву', 'object_name': dish.name, 'cancel_url': reverse('detail', args=[dish.pk])})


def profile(request):
    profile_obj = Profile.objects.get_or_create(user=request.user)[0] if request.user.is_authenticated else None
    return render(request, 'profile.html', {'profile': profile_obj})


@login_required(login_url='login')
def profile_address(request):
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)
    form = DeliveryAddressForm(request.POST or None, instance=profile_obj)
    if form.is_valid():
        form.save()
        return redirect('profile')
    return render(request, 'profile_address.html', {'form': form})


def register(request):
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        user.profile.phone = form.cleaned_data['phone']
        user.profile.save()
        login(request, user, backend='menu.backends.PhoneOrUsernameBackend')
        return redirect('profile_address')
    return render(request, 'registration/register.html', {'form': form})
