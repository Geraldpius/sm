from django.contrib import admin
from .models import TermRequirement, StudentRequirementStatus

@admin.register(TermRequirement)
class TermRequirementAdmin(admin.ModelAdmin):
    list_display = ['item_name', 'category', 'classroom', 'term', 'academic_year', 'is_mandatory', 'is_active']
    list_filter = ['category', 'is_mandatory', 'is_active', 'term', 'academic_year']

@admin.register(StudentRequirementStatus)
class StudentRequirementStatusAdmin(admin.ModelAdmin):
    list_display = ['student', 'requirement', 'status', 'quantity_brought', 'checked_by']
    list_filter = ['status']
