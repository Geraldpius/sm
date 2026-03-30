from django.urls import path
from . import views

urlpatterns = [
    path('', views.exam_list, name='exam_list'),
    path('create/', views.create_exam, name='create_exam'),
    path('exam/<int:exam_id>/marks/', views.enter_marks, name='enter_marks'),
    path('exam/<int:exam_id>/publish/', views.publish_exam, name='publish_exam'),
    path('exam/<int:exam_id>/analysis/', views.subject_analysis, name='subject_analysis'),
    path('class/<int:class_id>/', views.class_results, name='class_results'),
    path('student/<int:student_id>/exam/<int:exam_id>/', views.student_report, name='student_report'),
]
