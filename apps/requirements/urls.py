from django.urls import path
from . import views

urlpatterns = [
    path('', views.requirements_list, name='requirements_list'),
    path('add/', views.add_requirement, name='add_requirement'),
    path('class/<int:class_id>/check/', views.check_requirements, name='check_requirements'),
    path('report/', views.requirements_report, name='requirements_report'),
]
