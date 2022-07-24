from django.urls import path
from .views import (
    UserListView
)
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('users/', UserListView.as_view(), name='user-profiles'),
    path('register-admin/', views.register_admin, name='admin-register'),
    path('ban-user/<str:username>', views.ban_user, name='user-ban'),
    path('unban-user/<str:username>', views.unban_user, name='user-unban'),
]
