from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_list, name='student_list'),
    path('register/', views.student_register, name='student_register'),
    path('<int:pk>/', views.student_detail, name='student_detail'),
    path('<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('<int:pk>/delete/', views.student_delete, name='student_delete'),
    path('<int:pk>/id-card/', views.student_id_card, name='student_id_card'),
    path('promote/', views.promote_students, name='promote_students'),
    path('export/csv/', views.export_students_csv, name='export_students_csv'),
]
