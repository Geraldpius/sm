from django.contrib import admin
from .models import Exam, ExamResult, StudentReport

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['name', 'exam_type', 'classroom', 'academic_year', 'term', 'is_published']
    list_filter = ['exam_type', 'academic_year', 'term', 'is_published']

@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'subject', 'marks', 'grade', 'points']
    list_filter = ['grade', 'academic_year', 'term']
    search_fields = ['student__first_name', 'student__last_name']

@admin.register(StudentReport)
class StudentReportAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'average', 'aggregate', 'position']
