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
from django.urls import path
from menu import views as menu_views

urlpatterns = [
    path('', menu_views.index, name='home'),
    path('menu/', menu_views.menu_page, name='menu'),
    path('manage-dishes/', menu_views.dishes_manage, name='dishes_manage'),
    path('about/', menu_views.about_page, name='about'),
    path('dish/<int:pk>/', menu_views.detail, name='detail'),
    path('dish/new/', menu_views.dish_create, name='dish_create'),
    path('dish/<int:pk>/edit/', menu_views.dish_update, name='dish_update'),
    path('dish/<int:pk>/delete/', menu_views.dish_delete, name='dish_delete'),
    path('ingredients/', menu_views.ingredient_list, name='ingredient_list'),
    path('ingredients/new/', menu_views.ingredient_create, name='ingredient_create'),
    path('ingredients/<int:pk>/edit/', menu_views.ingredient_update, name='ingredient_update'),
    path('ingredients/<int:pk>/delete/', menu_views.ingredient_delete, name='ingredient_delete'),
    path('admin/', admin.site.urls),
]
