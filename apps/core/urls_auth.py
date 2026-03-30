from django.urls import path
from . import auth_views

urlpatterns = [
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('users/', auth_views.manage_users, name='manage_users'),
    path('profile/', auth_views.profile_view, name='profile'),
]
