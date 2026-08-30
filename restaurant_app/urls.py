"""
URL configuration for restaurant_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from menu import views as menu_views
from menu.forms import LoginForm
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', menu_views.index, name='home'),
    path('menu/', menu_views.menu_page, name='menu'),
    path('manage-dishes/', menu_views.dishes_manage, name='dishes_manage'),
    path('manage-categories/', menu_views.categories_manage, name='categories_manage'),
    path('categories/new/', menu_views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', menu_views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', menu_views.category_delete, name='category_delete'),
    path('about/', menu_views.about_page, name='about'),
    path('profile/', menu_views.profile, name='profile'),
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

