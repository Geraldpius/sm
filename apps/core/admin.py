from django.contrib import admin
from .models import SchoolSettings, Subject, ClassRoom, AcademicYear, UserProfile

@admin.register(SchoolSettings)
class SchoolSettingsAdmin(admin.ModelAdmin):
    list_display = ['name', 'current_year', 'current_term']

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'level', 'is_core', 'is_active']
    list_filter = ['level', 'is_core', 'is_active']

@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'stream', 'level', 'academic_year', 'capacity', 'is_active']
    list_filter = ['level', 'academic_year', 'is_active']

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['year', 'start_date', 'end_date', 'is_current']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'is_active']
    list_filter = ['role', 'is_active']
