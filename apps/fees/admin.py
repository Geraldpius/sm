from django.contrib import admin
from .models import FeeStructure, FeePayment, FeeWaiver

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ['classroom', 'fee_type', 'amount', 'term', 'academic_year', 'is_mandatory']
    list_filter = ['fee_type', 'term', 'academic_year', 'is_mandatory']

@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'student', 'amount_paid', 'payment_method', 'payment_date', 'status']
    list_filter = ['status', 'payment_method', 'academic_year', 'term']
    search_fields = ['receipt_number', 'student__first_name', 'student__last_name', 'student__student_id']

@admin.register(FeeWaiver)
class FeeWaiverAdmin(admin.ModelAdmin):
    list_display = ['student', 'waiver_type', 'percentage', 'academic_year', 'term']
