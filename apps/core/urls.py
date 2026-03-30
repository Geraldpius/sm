from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('settings/', views.school_settings_view, name='school_settings'),
    path('classes/', views.manage_classes, name='manage_classes'),
    path('subjects/', views.manage_subjects, name='manage_subjects'),
    path('class/<int:class_id>/access/', views.class_access, name='class_access'),
]
