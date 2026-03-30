from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
import csv, json
from .models import Student, StudentPromotion, StudentLeave
from apps.core.models import ClassRoom, SchoolSettings


def generate_student_id(year):
    last = Student.objects.filter(student_id__startswith=f"S{year}").order_by('student_id').last()
    if last:
        try:
            num = int(last.student_id[-4:]) + 1
        except:
            num = 1
    else:
        num = 1
    return f"S{year}{num:04d}"


@login_required
def student_list(request):
    school = SchoolSettings.get_settings()
    qs = Student.objects.filter(is_active=True).select_related('current_class')
    
    q = request.GET.get('q', '')
    class_filter = request.GET.get('class_id', '')
    gender_filter = request.GET.get('gender', '')
    boarder_filter = request.GET.get('boarder', '')
    
    if q:
        qs = qs.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) |
            Q(student_id__icontains=q) | Q(admission_number__icontains=q) |
            Q(other_names__icontains=q)
        )
    if class_filter:
        qs = qs.filter(current_class_id=class_filter)
    if gender_filter:
        qs = qs.filter(gender=gender_filter)
    if boarder_filter:
        qs = qs.filter(is_boarder=boarder_filter == 'true')
    
    paginator = Paginator(qs, 50)
    page = paginator.get_page(request.GET.get('page', 1))
    classes = ClassRoom.objects.filter(is_active=True, academic_year=school.current_year).order_by('name')
    
    context = {
        'students': page,
        'classes': classes,
        'total': qs.count(),
        'q': q,
        'class_filter': class_filter,
    }
    return render(request, 'students/list.html', context)


@login_required
def student_register(request):
    school = SchoolSettings.get_settings()
    if request.method == 'POST':
        year = school.current_year
        student_id = generate_student_id(str(year)[2:])
        
        try:
            class_id = request.POST.get('current_class')
            classroom = ClassRoom.objects.get(id=class_id) if class_id else None
            
            dob_str = request.POST.get('date_of_birth')
            adm_str = request.POST.get('admission_date')
            from datetime import datetime
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
            adm = datetime.strptime(adm_str, '%Y-%m-%d').date() if adm_str else timezone.now().date()
            
            student = Student.objects.create(
                student_id=student_id,
                first_name=request.POST.get('first_name', ''),
                last_name=request.POST.get('last_name', ''),
                other_names=request.POST.get('other_names', ''),
                gender=request.POST.get('gender', 'M'),
                date_of_birth=dob,
                current_class=classroom,
                admission_date=adm,
                admission_number=request.POST.get('admission_number', ''),
                lin_number=request.POST.get('lin_number', ''),
                index_number=request.POST.get('index_number', ''),
                previous_school=request.POST.get('previous_school', ''),
                religion=request.POST.get('religion', ''),
                nationality=request.POST.get('nationality', 'Ugandan'),
                district_of_origin=request.POST.get('district_of_origin', ''),
                blood_group=request.POST.get('blood_group', ''),
                medical_conditions=request.POST.get('medical_conditions', ''),
                home_address=request.POST.get('home_address', ''),
                phone=request.POST.get('phone', ''),
                email=request.POST.get('email', ''),
                father_name=request.POST.get('father_name', ''),
                father_phone=request.POST.get('father_phone', ''),
                father_occupation=request.POST.get('father_occupation', ''),
                mother_name=request.POST.get('mother_name', ''),
                mother_phone=request.POST.get('mother_phone', ''),
                mother_occupation=request.POST.get('mother_occupation', ''),
                guardian_name=request.POST.get('guardian_name', ''),
                guardian_phone=request.POST.get('guardian_phone', ''),
                guardian_relationship=request.POST.get('guardian_relationship', ''),
                guardian_address=request.POST.get('guardian_address', ''),
                is_boarder=request.POST.get('is_boarder') == 'on',
                is_sponsored=request.POST.get('is_sponsored') == 'on',
                sponsor_name=request.POST.get('sponsor_name', ''),
            )
            if 'photo' in request.FILES:
                student.photo = request.FILES['photo']
                student.save()
            
            messages.success(request, f'Student {student.full_name} registered with ID: {student.student_id}')
            return redirect('student_detail', pk=student.pk)
        except Exception as e:
            messages.error(request, f'Error registering student: {str(e)}')
    
    classes = ClassRoom.objects.filter(is_active=True, academic_year=school.current_year).order_by('name')
    return render(request, 'students/register.html', {'classes': classes})


@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    from apps.fees.models import FeePayment
    from apps.results.models import ExamResult
    school = SchoolSettings.get_settings()
    
    fee_payments = FeePayment.objects.filter(student=student).order_by('-payment_date')
    results = ExamResult.objects.filter(student=student).order_by('-academic_year', '-term')
    promotions = StudentPromotion.objects.filter(student=student).order_by('-promotion_date')
    leaves = StudentLeave.objects.filter(student=student).order_by('-created_at')
    
    # Fee balance for current term
    from apps.fees.models import FeeStructure
    from django.db.models import Sum
    fee_structure = FeeStructure.objects.filter(
        classroom=student.current_class,
        academic_year=school.current_year,
        term=school.current_term
    ).first()
    
    paid_this_term = FeePayment.objects.filter(
        student=student,
        academic_year=school.current_year,
        term=school.current_term,
        status__in=['paid', 'partial']
    ).aggregate(total=Sum('amount_paid'))['total'] or 0
    
    balance = (fee_structure.amount if fee_structure else 0) - paid_this_term
    
    context = {
        'student': student,
        'fee_payments': fee_payments,
        'results': results,
        'promotions': promotions,
        'leaves': leaves,
        'fee_balance': balance,
        'paid_this_term': paid_this_term,
        'fee_structure': fee_structure,
    }
    return render(request, 'students/detail.html', context)


@login_required
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    school = SchoolSettings.get_settings()
    if request.method == 'POST':
        try:
            from datetime import datetime
            dob_str = request.POST.get('date_of_birth')
            if dob_str:
                student.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
            
            class_id = request.POST.get('current_class')
            student.current_class = ClassRoom.objects.get(id=class_id) if class_id else None
            
            for field in ['first_name','last_name','other_names','gender','religion','nationality',
                         'district_of_origin','blood_group','medical_conditions','home_address',
                         'phone','email','father_name','father_phone','father_occupation',
                         'mother_name','mother_phone','mother_occupation','guardian_name',
                         'guardian_phone','guardian_relationship','guardian_address',
                         'previous_school','admission_number','lin_number','index_number','sponsor_name']:
                val = request.POST.get(field)
                if val is not None:
                    setattr(student, field, val)
            
            student.is_boarder = request.POST.get('is_boarder') == 'on'
            student.is_sponsored = request.POST.get('is_sponsored') == 'on'
            if 'photo' in request.FILES:
                student.photo = request.FILES['photo']
            student.save()
            messages.success(request, 'Student updated successfully!')
            return redirect('student_detail', pk=pk)
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    classes = ClassRoom.objects.filter(is_active=True, academic_year=school.current_year).order_by('name')
    return render(request, 'students/edit.html', {'student': student, 'classes': classes})


@login_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        student.is_active = False
        student.save()
        messages.success(request, f'Student {student.full_name} has been deactivated.')
        return redirect('student_list')
    return render(request, 'students/confirm_delete.html', {'student': student})


@login_required
def promote_students(request):
    school = SchoolSettings.get_settings()
    if request.method == 'POST':
        student_ids = request.POST.getlist('student_ids')
        to_class_id = request.POST.get('to_class')
        to_class = ClassRoom.objects.get(id=to_class_id)
        
        promoted = 0
        for sid in student_ids:
            try:
                student = Student.objects.get(id=sid)
                from_class = student.current_class
                StudentPromotion.objects.create(
                    student=student,
                    from_class=from_class,
                    to_class=to_class,
                    academic_year=school.current_year,
                    promoted_by=request.user.get_full_name()
                )
                student.current_class = to_class
                student.save()
                promoted += 1
            except Exception:
                continue
        messages.success(request, f'{promoted} students promoted to {to_class}!')
        return redirect('student_list')
    
    classes = ClassRoom.objects.filter(is_active=True, academic_year=school.current_year).order_by('name')
    students = Student.objects.filter(is_active=True).select_related('current_class')
    from_class_id = request.GET.get('class_id')
    if from_class_id:
        students = students.filter(current_class_id=from_class_id)
    return render(request, 'students/promote.html', {
        'classes': classes, 'students': students, 'from_class_id': from_class_id
    })


@login_required
def export_students_csv(request):
    school = SchoolSettings.get_settings()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="students_{school.current_year}.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'Student ID', 'Full Name', 'Gender', 'Class', 'Date of Birth',
        'Admission Date', 'Phone', 'Guardian', 'Guardian Phone', 'Boarder'
    ])
    students = Student.objects.filter(is_active=True).select_related('current_class')
    for s in students:
        writer.writerow([
            s.student_id, s.full_name, s.get_gender_display(),
            str(s.current_class) if s.current_class else '',
            s.date_of_birth, s.admission_date, s.phone,
            s.guardian_name or s.father_name, s.guardian_phone or s.father_phone,
            'Yes' if s.is_boarder else 'No'
        ])
    return response


@login_required
def student_id_card(request, pk):
    student = get_object_or_404(Student, pk=pk)
    school = SchoolSettings.get_settings()
    return render(request, 'students/id_card.html', {
        'student': student, 'school': school
    })
