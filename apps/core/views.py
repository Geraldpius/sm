from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from .models import SchoolSettings, ClassRoom, Subject, UserProfile
from apps.students.models import Student
from apps.fees.models import FeePayment, FeeStructure
from apps.results.models import ExamResult, Exam, StudentReport


def get_user_role(user):
    """Return role string for a user."""
    if user.is_superuser:
        return 'admin'
    try:
        return user.profile.role
    except Exception:
        return 'teacher'


@login_required
def dashboard(request):
    role = get_user_role(request.user)
    school = SchoolSettings.get_settings()

    # ── Admin / Head Teacher — full dashboard ─────────────────
    if role in ('admin', 'headteacher'):
        return _dashboard_admin(request, school)

    # ── Bursar — finance only ──────────────────────────────────
    elif role == 'bursar':
        return _dashboard_bursar(request, school)

    # ── Director of Studies — academics only ───────────────────
    elif role == 'dos':
        return _dashboard_dos(request, school)

    # ── Teacher — their classes only ──────────────────────────
    elif role == 'teacher':
        return _dashboard_teacher(request, school)

    # ── Receptionist — students only ──────────────────────────
    elif role == 'receptionist':
        return _dashboard_receptionist(request, school)

    # fallback
    return _dashboard_admin(request, school)


# ─────────────────────────────────────────────────────────────
# ADMIN / HEAD TEACHER  — everything
# ─────────────────────────────────────────────────────────────
def _dashboard_admin(request, school):
    total_students = Student.objects.filter(is_active=True).count()
    total_classes  = ClassRoom.objects.filter(is_active=True, academic_year=school.current_year).count()

    total_collected = FeePayment.objects.filter(
        academic_year=school.current_year, term=school.current_term,
        status__in=['paid', 'partial']
    ).aggregate(t=Sum('amount_paid'))['t'] or 0

    total_expected = FeeStructure.objects.filter(
        academic_year=school.current_year, term=school.current_term
    ).aggregate(t=Sum('amount'))['t'] or 0

    defaulters_count = Student.objects.filter(is_active=True).annotate(
        paid=Sum('feepayment__amount_paid', filter=Q(
            feepayment__academic_year=school.current_year,
            feepayment__term=school.current_term,
            feepayment__status__in=['paid', 'partial']
        ))
    ).filter(Q(paid__isnull=True) | Q(paid=0)).count()

    recent_payments = FeePayment.objects.filter(
        status__in=['paid', 'partial']
    ).select_related('student').order_by('-payment_date')[:8]

    class_summary = ClassRoom.objects.filter(
        is_active=True, academic_year=school.current_year
    ).annotate(student_count=Count('student')).order_by('name')

    recent_exams = Exam.objects.filter(
        academic_year=school.current_year, term=school.current_term
    ).select_related('classroom').order_by('-created_at')[:5]

    # Gender breakdown
    boys  = Student.objects.filter(is_active=True, gender='M').count()
    girls = Student.objects.filter(is_active=True, gender='F').count()

    ctx = {
        'role': 'admin',
        'total_students': total_students,
        'total_classes': total_classes,
        'total_collected': total_collected,
        'total_expected': total_expected,
        'defaulters_count': defaulters_count,
        'collection_rate': round((total_collected / total_expected * 100) if total_expected > 0 else 0, 1),
        'recent_payments': recent_payments,
        'class_summary': class_summary,
        'recent_exams': recent_exams,
        'boys': boys,
        'girls': girls,
    }
    return render(request, 'dashboards/admin_dashboard.html', ctx)


# ─────────────────────────────────────────────────────────────
# BURSAR — finance only
# ─────────────────────────────────────────────────────────────
def _dashboard_bursar(request, school):
    total_collected = FeePayment.objects.filter(
        academic_year=school.current_year, term=school.current_term,
        status__in=['paid', 'partial']
    ).aggregate(t=Sum('amount_paid'))['t'] or 0

    total_expected_all = 0
    classes = ClassRoom.objects.filter(is_active=True, academic_year=school.current_year)
    for cls in classes:
        fs = FeeStructure.objects.filter(
            classroom=cls, academic_year=school.current_year, term=school.current_term
        ).aggregate(t=Sum('amount'))['t'] or 0
        count = Student.objects.filter(current_class=cls, is_active=True).count()
        total_expected_all += fs * count

    total_balance = total_expected_all - total_collected

    # Defaulters
    defaulters = []
    for student in Student.objects.filter(is_active=True).select_related('current_class'):
        if not student.current_class:
            continue
        fs = FeeStructure.objects.filter(
            classroom=student.current_class,
            academic_year=school.current_year, term=school.current_term
        ).aggregate(t=Sum('amount'))['t'] or 0
        paid = FeePayment.objects.filter(
            student=student, academic_year=school.current_year,
            term=school.current_term, status__in=['paid', 'partial']
        ).aggregate(t=Sum('amount_paid'))['t'] or 0
        if fs > 0 and paid < fs:
            defaulters.append({'student': student, 'balance': fs - paid, 'paid': paid, 'expected': fs})
    defaulters.sort(key=lambda x: x['balance'], reverse=True)

    # Today's collections
    today = timezone.now().date()
    today_collected = FeePayment.objects.filter(
        payment_date=today, status__in=['paid', 'partial']
    ).aggregate(t=Sum('amount_paid'))['t'] or 0
    today_count = FeePayment.objects.filter(payment_date=today).count()

    # By method breakdown
    by_method = FeePayment.objects.filter(
        academic_year=school.current_year, term=school.current_term,
        status__in=['paid', 'partial']
    ).values('payment_method').annotate(total=Sum('amount_paid'), count=Count('id')).order_by('-total')

    recent_payments = FeePayment.objects.filter(
        status__in=['paid', 'partial']
    ).select_related('student', 'student__current_class').order_by('-payment_date')[:15]

    # Per-class collection
    class_fees = []
    for cls in classes.annotate(student_count=Count('student')):
        collected = FeePayment.objects.filter(
            student__current_class=cls,
            academic_year=school.current_year, term=school.current_term,
            status__in=['paid', 'partial']
        ).aggregate(t=Sum('amount_paid'))['t'] or 0
        fs_amt = FeeStructure.objects.filter(
            classroom=cls, academic_year=school.current_year, term=school.current_term
        ).aggregate(t=Sum('amount'))['t'] or 0
        expected = fs_amt * cls.student_count
        class_fees.append({
            'class': cls, 'collected': collected,
            'expected': expected, 'balance': expected - collected,
            'rate': round((collected / expected * 100) if expected > 0 else 0, 1),
        })

    ctx = {
        'role': 'bursar',
        'total_collected': total_collected,
        'total_expected': total_expected_all,
        'total_balance': total_balance,
        'collection_rate': round((total_collected / total_expected_all * 100) if total_expected_all > 0 else 0, 1),
        'defaulters': defaulters[:10],
        'defaulters_count': len(defaulters),
        'today_collected': today_collected,
        'today_count': today_count,
        'by_method': by_method,
        'recent_payments': recent_payments,
        'class_fees': class_fees,
    }
    return render(request, 'dashboards/bursar_dashboard.html', ctx)


# ─────────────────────────────────────────────────────────────
# DIRECTOR OF STUDIES — academics only
# ─────────────────────────────────────────────────────────────
def _dashboard_dos(request, school):
    total_students = Student.objects.filter(is_active=True).count()
    total_classes  = ClassRoom.objects.filter(is_active=True, academic_year=school.current_year).count()

    exams = Exam.objects.filter(
        academic_year=school.current_year, term=school.current_term
    ).select_related('classroom').order_by('-created_at')

    # Performance per class
    class_performance = []
    for cls in ClassRoom.objects.filter(is_active=True, academic_year=school.current_year).order_by('name'):
        exam = Exam.objects.filter(
            classroom=cls, academic_year=school.current_year,
            term=school.current_term, is_published=True
        ).last()
        if exam:
            reports = StudentReport.objects.filter(exam=exam)
            avg = reports.aggregate(a=Avg('average'))['a'] or 0
            top = reports.order_by('-average').first()
            class_performance.append({
                'class': cls,
                'exam': exam,
                'students': reports.count(),
                'average': round(avg, 1),
                'top_student': top.student if top else None,
                'published': True,
            })
        else:
            class_performance.append({
                'class': cls, 'exam': None,
                'students': Student.objects.filter(current_class=cls, is_active=True).count(),
                'average': 0, 'top_student': None, 'published': False,
            })

    # Subject pass rates across all classes
    subject_stats = []
    for subj in Subject.objects.filter(is_active=True).order_by('name'):
        results = ExamResult.objects.filter(
            subject=subj,
            exam__academic_year=school.current_year,
            exam__term=school.current_term
        )
        if results.exists():
            total = results.count()
            passed = results.filter(grade__in=['A', 'B', 'C', 'D']).count()
            avg = results.aggregate(a=Avg('marks'))['a'] or 0
            subject_stats.append({
                'subject': subj, 'total': total,
                'passed': passed, 'failed': total - passed,
                'pass_rate': round(passed / total * 100, 1),
                'average': round(avg, 1),
            })

    recent_exams = exams[:8]
    unpublished = exams.filter(is_published=False).count()

    ctx = {
        'role': 'dos',
        'total_students': total_students,
        'total_classes': total_classes,
        'exams_count': exams.count(),
        'unpublished': unpublished,
        'class_performance': class_performance,
        'subject_stats': subject_stats[:10],
        'recent_exams': recent_exams,
    }
    return render(request, 'dashboards/dos_dashboard.html', ctx)


# ─────────────────────────────────────────────────────────────
# TEACHER — only their assigned classes
# ─────────────────────────────────────────────────────────────
def _dashboard_teacher(request, school):
    try:
        profile = request.user.profile
        my_classes = profile.classes.filter(is_active=True, academic_year=school.current_year)
    except Exception:
        my_classes = ClassRoom.objects.none()

    class_data = []
    for cls in my_classes.annotate(student_count=Count('student')):
        exams = Exam.objects.filter(
            classroom=cls, academic_year=school.current_year, term=school.current_term
        ).order_by('-created_at')
        latest_exam = exams.first()
        avg = 0
        if latest_exam:
            rep = StudentReport.objects.filter(exam=latest_exam)
            avg = rep.aggregate(a=Avg('average'))['a'] or 0
        class_data.append({
            'class': cls,
            'students': cls.student_count,
            'exams': exams.count(),
            'latest_exam': latest_exam,
            'average': round(avg, 1),
        })

    # My recent exams
    my_exams = Exam.objects.filter(
        classroom__in=my_classes,
        academic_year=school.current_year,
        term=school.current_term
    ).select_related('classroom').order_by('-created_at')[:10]

    ctx = {
        'role': 'teacher',
        'my_classes': my_classes,
        'class_data': class_data,
        'my_exams': my_exams,
        'total_students': sum(d['students'] for d in class_data),
    }
    return render(request, 'dashboards/teacher_dashboard.html', ctx)


# ─────────────────────────────────────────────────────────────
# RECEPTIONIST — student registration only
# ─────────────────────────────────────────────────────────────
def _dashboard_receptionist(request, school):
    total_students = Student.objects.filter(is_active=True).count()
    boys  = Student.objects.filter(is_active=True, gender='M').count()
    girls = Student.objects.filter(is_active=True, gender='F').count()

    recent_registrations = Student.objects.filter(
        is_active=True
    ).select_related('current_class').order_by('-created_at')[:15]

    # Today's registrations
    today = timezone.now().date()
    today_count = Student.objects.filter(admission_date=today).count()

    class_summary = ClassRoom.objects.filter(
        is_active=True, academic_year=school.current_year
    ).annotate(student_count=Count('student')).order_by('name')

    ctx = {
        'role': 'receptionist',
        'total_students': total_students,
        'boys': boys,
        'girls': girls,
        'today_count': today_count,
        'recent_registrations': recent_registrations,
        'class_summary': class_summary,
    }
    return render(request, 'dashboards/receptionist_dashboard.html', ctx)


# ─────────────────────────────────────────────────────────────
# OTHER VIEWS (unchanged)
# ─────────────────────────────────────────────────────────────
@login_required
def school_settings_view(request):
    school = SchoolSettings.get_settings()
    if request.method == 'POST':
        school.name        = request.POST.get('name', school.name)
        school.motto       = request.POST.get('motto', school.motto)
        school.address     = request.POST.get('address', school.address)
        school.phone       = request.POST.get('phone', school.phone)
        school.email       = request.POST.get('email', school.email)
        school.website     = request.POST.get('website', school.website)
        school.founded_year= int(request.POST.get('founded_year', school.founded_year))
        school.district    = request.POST.get('district', school.district)
        school.currency    = request.POST.get('currency', school.currency)
        school.current_term= int(request.POST.get('current_term', school.current_term))
        school.current_year= int(request.POST.get('current_year', school.current_year))
        school.grade_a_min = int(request.POST.get('grade_a_min', school.grade_a_min))
        school.grade_b_min = int(request.POST.get('grade_b_min', school.grade_b_min))
        school.grade_c_min = int(request.POST.get('grade_c_min', school.grade_c_min))
        school.grade_d_min = int(request.POST.get('grade_d_min', school.grade_d_min))
        school.grade_e_min = int(request.POST.get('grade_e_min', school.grade_e_min))
        school.grade_f_min = int(request.POST.get('grade_f_min', school.grade_f_min))
        if 'logo' in request.FILES:
            school.logo = request.FILES['logo']
        school.save()
        messages.success(request, 'School settings updated successfully!')
        return redirect('school_settings')
    return render(request, 'base/settings.html', {'school': school})


@login_required
def manage_classes(request):
    school = SchoolSettings.get_settings()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            name     = request.POST.get('name')
            stream   = request.POST.get('stream', '')
            level    = 'A' if name in ['S5', 'S6'] else 'O'
            year     = int(request.POST.get('academic_year', school.current_year))
            password = request.POST.get('password', 'class123')
            capacity = int(request.POST.get('capacity', 45))
            cls, created = ClassRoom.objects.get_or_create(
                name=name, stream=stream, academic_year=year,
                defaults={'level': level, 'password': password, 'capacity': capacity}
            )
            if created:
                messages.success(request, f'Class {cls} created successfully!')
            else:
                messages.warning(request, f'Class {cls} already exists!')
        elif action == 'delete':
            ClassRoom.objects.filter(id=request.POST.get('class_id')).delete()
            messages.success(request, 'Class deleted.')
        elif action == 'update_password':
            ClassRoom.objects.filter(id=request.POST.get('class_id')).update(
                password=request.POST.get('new_password')
            )
            messages.success(request, 'Class password updated.')
        return redirect('manage_classes')

    classes = ClassRoom.objects.filter(academic_year=school.current_year).annotate(
        student_count=Count('student')
    ).order_by('name', 'stream')
    return render(request, 'base/classes.html', {'classes': classes})


@login_required
def manage_subjects(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            Subject.objects.get_or_create(
                code=request.POST.get('code'),
                defaults={
                    'name':      request.POST.get('name'),
                    'level':     request.POST.get('level', 'O'),
                    'is_core':   request.POST.get('is_core') == 'on',
                    'max_marks': int(request.POST.get('max_marks', 100)),
                    'pass_mark': int(request.POST.get('pass_mark', 50)),
                }
            )
            messages.success(request, 'Subject created!')
        elif action == 'toggle':
            subj = Subject.objects.get(id=request.POST.get('subject_id'))
            subj.is_active = not subj.is_active
            subj.save()
        return redirect('manage_subjects')
    subjects = Subject.objects.all().order_by('level', 'name')
    return render(request, 'base/subjects.html', {'subjects': subjects})


@login_required
def class_access(request, class_id):
    classroom    = get_object_or_404(ClassRoom, id=class_id)
    session_key  = f'class_access_{class_id}'

    if request.session.get(session_key) or request.user.is_staff:
        return redirect('class_results', class_id=class_id)

    if request.method == 'POST':
        if request.POST.get('password') == classroom.password:
            request.session[session_key] = True
            return redirect('class_results', class_id=class_id)
        messages.error(request, 'Incorrect password!')

    return render(request, 'base/class_access.html', {'classroom': classroom})
