from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import TermRequirement, StudentRequirementStatus
from apps.students.models import Student
from apps.core.models import ClassRoom, SchoolSettings
import csv


@login_required
def requirements_list(request):
    school = SchoolSettings.get_settings()
    year = int(request.GET.get('year', school.current_year))
    term = int(request.GET.get('term', school.current_term))
    class_filter = request.GET.get('class_id', '')
    
    reqs = TermRequirement.objects.filter(academic_year=year, term=term, is_active=True)
    if class_filter:
        reqs = reqs.filter(models.Q(classroom_id=class_filter) | models.Q(classroom__isnull=True))
    
    classes = ClassRoom.objects.filter(is_active=True, academic_year=year).order_by('name')
    context = {'requirements': reqs, 'classes': classes, 'year': year, 'term': term, 'class_filter': class_filter}
    return render(request, 'requirements/list.html', context)


@login_required
def add_requirement(request):
    school = SchoolSettings.get_settings()
    if request.method == 'POST':
        try:
            class_id = request.POST.get('classroom_id')
            classroom = ClassRoom.objects.get(id=class_id) if class_id else None
            TermRequirement.objects.create(
                classroom=classroom,
                item_name=request.POST.get('item_name'),
                category=request.POST.get('category', 'stationery'),
                description=request.POST.get('description', ''),
                quantity=int(request.POST.get('quantity', 1)),
                unit=request.POST.get('unit', 'piece'),
                estimated_cost=float(request.POST.get('estimated_cost', 0)),
                is_mandatory=request.POST.get('is_mandatory') == 'on',
                academic_year=int(request.POST.get('academic_year', school.current_year)),
                term=int(request.POST.get('term', school.current_term)),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Requirement added!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    return redirect('requirements_list')


@login_required
def check_requirements(request, class_id):
    classroom = get_object_or_404(ClassRoom, pk=class_id)
    school = SchoolSettings.get_settings()
    students = Student.objects.filter(current_class=classroom, is_active=True).order_by('last_name')
    requirements = TermRequirement.objects.filter(
        academic_year=school.current_year, term=school.current_term, is_active=True
    ).filter(
        __import__('django.db.models', fromlist=['Q']).Q(classroom=classroom) | 
        __import__('django.db.models', fromlist=['Q']).Q(classroom__isnull=True)
    )
    
    if request.method == 'POST':
        for student in students:
            for req in requirements:
                key_status = f'status_{student.pk}_{req.pk}'
                key_qty = f'qty_{student.pk}_{req.pk}'
                status = request.POST.get(key_status, 'missing')
                qty = int(request.POST.get(key_qty, 0))
                StudentRequirementStatus.objects.update_or_create(
                    student=student, requirement=req,
                    defaults={
                        'status': status,
                        'quantity_brought': qty,
                        'checked_by': request.user.get_full_name() or request.user.username,
                    }
                )
        messages.success(request, 'Requirements status updated!')
        return redirect('check_requirements', class_id=class_id)
    
    status_map = {}
    for s in StudentRequirementStatus.objects.filter(
        student__in=students, requirement__in=requirements
    ):
        status_map[(s.student_id, s.requirement_id)] = s
    
    context = {
        'classroom': classroom, 'students': students, 'requirements': requirements,
        'status_map': status_map,
    }
    return render(request, 'requirements/check.html', context)


@login_required
def requirements_report(request):
    school = SchoolSettings.get_settings()
    year = int(request.GET.get('year', school.current_year))
    term = int(request.GET.get('term', school.current_term))
    class_id = request.GET.get('class_id')
    
    classroom = get_object_or_404(ClassRoom, pk=class_id) if class_id else None
    students = Student.objects.filter(
        current_class=classroom if classroom else __import__('django.db.models', fromlist=['Q']).Q(),
        is_active=True
    ).order_by('last_name') if classroom else Student.objects.filter(is_active=True).order_by('last_name')
    
    requirements = TermRequirement.objects.filter(
        academic_year=year, term=term, is_active=True
    )
    if classroom:
        from django.db.models import Q
        requirements = requirements.filter(Q(classroom=classroom) | Q(classroom__isnull=True))
    
    data = []
    for student in students:
        statuses = StudentRequirementStatus.objects.filter(student=student, requirement__in=requirements)
        total = requirements.count()
        brought = statuses.filter(status='brought').count()
        data.append({'student': student, 'total': total, 'brought': brought, 'missing': total - brought,
                     'percentage': round(brought/total*100 if total > 0 else 0, 1)})
    
    context = {'data': data, 'classroom': classroom, 'year': year, 'term': term, 'requirements': requirements}
    return render(request, 'requirements/report.html', context)


# URLs
from django.urls import path

urlpatterns = [
    path('', requirements_list, name='requirements_list'),
    path('add/', add_requirement, name='add_requirement'),
    path('class/<int:class_id>/check/', check_requirements, name='check_requirements'),
    path('report/', requirements_report, name='requirements_report'),
]
