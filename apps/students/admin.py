from django.contrib import admin
from .models import Student, StudentPromotion, StudentLeave

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'full_name', 'gender', 'current_class', 'is_active', 'is_boarder']
    list_filter = ['gender', 'current_class', 'is_active', 'is_boarder']
    search_fields = ['first_name', 'last_name', 'student_id', 'admission_number']

@admin.register(StudentPromotion)
class StudentPromotionAdmin(admin.ModelAdmin):
    list_display = ['student', 'from_class', 'to_class', 'academic_year', 'promotion_date']

@admin.register(StudentLeave)
class StudentLeaveAdmin(admin.ModelAdmin):
    list_display = ['student', 'start_date', 'end_date', 'status']
    list_filter = ['status']
