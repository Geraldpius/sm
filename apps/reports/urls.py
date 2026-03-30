from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_home, name='reports_home'),
    path('enrollment/', views.enrollment_report, name='enrollment_report'),
    path('fees/', views.fees_report, name='fees_report'),
    path('academic/', views.academic_report, name='academic_report'),
    path('export/<str:report_type>/', views.export_report_csv, name='export_report_csv'),
]
