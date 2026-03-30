from django.urls import path
from . import views

urlpatterns = [
    path('', views.fees_dashboard, name='fees_dashboard'),
    path('pay/', views.record_payment, name='record_payment'),
    path('receipt/<int:pk>/', views.view_receipt, name='view_receipt'),
    path('defaulters/', views.fee_defaulters, name='fee_defaulters'),
    path('history/', views.payment_history, name='payment_history'),
    path('structure/', views.fee_structure_list, name='fee_structure_list'),
    path('defaulters/export/', views.export_defaulters_csv, name='export_defaulters_csv'),
]
