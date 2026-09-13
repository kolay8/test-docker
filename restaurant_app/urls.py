from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from menu import views as menu_views
from menu.forms import LoginForm

urlpatterns = [
    path('', menu_views.index, name='home'),
    path('menu/', menu_views.menu_page, name='menu'),
    path('cart/', menu_views.cart_page, name='cart'),
    path('cart/add/<int:pk>/', menu_views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:pk>/', menu_views.update_cart, name='update_cart'),
    path('cart/remove/<int:pk>/', menu_views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', menu_views.checkout, name='checkout'),
    path('order/<int:pk>/success/', menu_views.order_success, name='order_success'),
    path('manage-orders/', menu_views.orders_manage, name='orders_manage'),
    path('manage-dishes/', menu_views.dishes_manage, name='dishes_manage'),
    path('manage-categories/', menu_views.categories_manage, name='categories_manage'),
    path('categories/new/', menu_views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', menu_views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', menu_views.category_delete, name='category_delete'),
    path('about/', menu_views.about_page, name='about'),
    path('profile/', menu_views.profile, name='profile'),
    path('profile/address/', menu_views.profile_address, name='profile_address'),
    path('login/', auth_views.LoginView.as_view(authentication_form=LoginForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', menu_views.register, name='register'),
    path('accounts/login/', auth_views.LoginView.as_view(authentication_form=LoginForm)),
    path('accounts/', include('django.contrib.auth.urls')),
    path('dish/<int:pk>/', menu_views.detail, name='detail'),
    path('dish/new/', menu_views.dish_create, name='dish_create'),
    path('dish/<int:pk>/edit/', menu_views.dish_update, name='dish_update'),
    path('dish/<int:pk>/delete/', menu_views.dish_delete, name='dish_delete'),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
