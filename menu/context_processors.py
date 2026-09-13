from .views import _cart_count, _get_cart


def cart(request):
    return {'cart_count': _cart_count(_get_cart(request))}