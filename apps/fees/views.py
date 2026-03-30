from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, Count
from django.http import HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
import datetime, uuid, csv
from .models import FeePayment, FeeStructure, FeeWaiver
from apps.students.models import Student
from apps.core.models import SchoolSettings, ClassRoom


def generate_receipt_number():
    from django.utils import timezone
    prefix = timezone.now().strftime('%Y%m%d')
    last = FeePayment.objects.filter(receipt_number__startswith=prefix).order_by('receipt_number').last()
    if last:
        try:
            num = int(last.receipt_number[-4:]) + 1
        except:
            num = 1
    else:
        num = 1
    return f"{prefix}{num:04d}"


@login_required
def fees_dashboard(request):
    school = SchoolSettings.get_settings()
    year = int(request.GET.get('year', school.current_year))
    term = int(request.GET.get('term', school.current_term))
    
    # Collection summary per class
    classes = ClassRoom.objects.filter(is_active=True, academic_year=year).annotate(
        student_count=Count('student', filter=Q(student__is_active=True))
    ).order_by('name')
    
    summary = []
    total_expected = 0
    total_collected = 0
    
    for cls in classes:
        expected = FeeStructure.objects.filter(
            classroom=cls, academic_year=year, term=term
        ).aggregate(t=Sum('amount'))['t'] or 0
        expected_total = expected * cls.student_count
        
        collected = FeePayment.objects.filter(
            student__current_class=cls,
            academic_year=year, term=term,
            status__in=['paid', 'partial']
        ).aggregate(t=Sum('amount_paid'))['t'] or 0
        
        total_expected += expected_total
        total_collected += collected
        
        summary.append({
            'class': cls,
            'students': cls.student_count,
            'expected': expected_total,
            'collected': collected,
            'balance': expected_total - collected,
            'rate': round((collected / expected_total * 100) if expected_total > 0 else 0, 1),
        })
    
    recent = FeePayment.objects.filter(
        academic_year=year, term=term
    ).select_related('student').order_by('-payment_date')[:15]
    
    context = {
        'summary': summary,
        'total_expected': total_expected,
        'total_collected': total_collected,
        'total_balance': total_expected - total_collected,
        'collection_rate': round((total_collected / total_expected * 100) if total_expected > 0 else 0, 1),
        'recent_payments': recent,
        'year': year,
        'term': term,
    }
    return render(request, 'fees/dashboard.html', context)


@login_required
def record_payment(request):
    school = SchoolSettings.get_settings()
    student = None
    student_id = request.GET.get('student_id') or request.POST.get('student_id')
    
    if student_id:
        student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST' and request.POST.get('action') == 'pay':
        student = get_object_or_404(Student, id=request.POST.get('student_id'))
        try:
            fee_structure_id = request.POST.get('fee_structure_id')
            fee_structure = FeeStructure.objects.get(id=fee_structure_id) if fee_structure_id else None
            
            amount_expected = float(request.POST.get('amount_expected', 0))
            amount_paid = float(request.POST.get('amount_paid', 0))
            discount = float(request.POST.get('discount', 0))
            
            payment_date_str = request.POST.get('payment_date')
            payment_date = datetime.date.fromisoformat(payment_date_str) if payment_date_str else timezone.now().date()
            
            payment = FeePayment.objects.create(
                student=student,
                fee_structure=fee_structure,
                academic_year=int(request.POST.get('academic_year', school.current_year)),
                term=int(request.POST.get('term', school.current_term)),
                fee_type=request.POST.get('fee_type', 'tuition'),
                amount_expected=amount_expected,
                amount_paid=amount_paid,
                discount=discount,
                payment_method=request.POST.get('payment_method', 'cash'),
                payment_date=payment_date,
                receipt_number=generate_receipt_number(),
                transaction_reference=request.POST.get('transaction_reference', ''),
                bank_name=request.POST.get('bank_name', ''),
                received_by=request.user.get_full_name() or request.user.username,
                remarks=request.POST.get('remarks', ''),
            )
            messages.success(request, f'Payment recorded! Receipt #{payment.receipt_number}')
            return redirect('view_receipt', pk=payment.pk)
        except Exception as e:
            messages.error(request, f'Error recording payment: {str(e)}')
    
    fee_structures = []
    if student and student.current_class:
        fee_structures = FeeStructure.objects.filter(
            classroom=student.current_class,
            academic_year=school.current_year,
            term=school.current_term
        )
    
    students = Student.objects.filter(is_active=True).select_related('current_class').order_by('last_name')
    context = {
        'student': student,
        'students': students,
        'fee_structures': fee_structures,
        'today': timezone.now().date(),
    }
    return render(request, 'fees/record_payment.html', context)


@login_required
def view_receipt(request, pk):
    payment = get_object_or_404(FeePayment, pk=pk)
    school = SchoolSettings.get_settings()
    
    # All payments for this student this term
    term_payments = FeePayment.objects.filter(
        student=payment.student,
        academic_year=payment.academic_year,
        term=payment.term,
        status__in=['paid', 'partial']
    ).aggregate(total=Sum('amount_paid'))['total'] or 0
    
    context = {
        'payment': payment,
        'school': school,
        'term_total_paid': term_payments,
    }
    return render(request, 'fees/receipt.html', context)


@login_required
def fee_defaulters(request):
    school = SchoolSettings.get_settings()
    year = int(request.GET.get('year', school.current_year))
    term = int(request.GET.get('term', school.current_term))
    class_filter = request.GET.get('class_id', '')
    
    students_qs = Student.objects.filter(is_active=True).select_related('current_class')
    if class_filter:
        students_qs = students_qs.filter(current_class_id=class_filter)
    
    defaulters = []
    for student in students_qs:
        if not student.current_class:
            continue
        fee_struct = FeeStructure.objects.filter(
            classroom=student.current_class,
            academic_year=year, term=term
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        if fee_struct == 0:
            continue
        
        paid = FeePayment.objects.filter(
            student=student, academic_year=year, term=term,
            status__in=['paid', 'partial']
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        
        balance = fee_struct - paid
        if balance > 0:
            defaulters.append({
                'student': student,
                'expected': fee_struct,
                'paid': paid,
                'balance': balance,
                'percentage_paid': round((paid / fee_struct * 100) if fee_struct > 0 else 0, 1),
            })
    
    defaulters.sort(key=lambda x: x['balance'], reverse=True)
    total_balance = sum(d['balance'] for d in defaulters)
    
    classes = ClassRoom.objects.filter(is_active=True, academic_year=year).order_by('name')
    context = {
        'defaulters': defaulters,
        'total_defaulters': len(defaulters),
        'total_balance': total_balance,
        'classes': classes,
        'year': year, 'term': term, 'class_filter': class_filter,
    }
    return render(request, 'fees/defaulters.html', context)


@login_required
def payment_history(request):
    school = SchoolSettings.get_settings()
    qs = FeePayment.objects.select_related('student', 'student__current_class').order_by('-payment_date')
    
    q = request.GET.get('q', '')
    year = request.GET.get('year', '')
    term = request.GET.get('term', '')
    method = request.GET.get('method', '')
    
    if q:
        qs = qs.filter(
            Q(student__first_name__icontains=q) | Q(student__last_name__icontains=q) |
            Q(receipt_number__icontains=q) | Q(student__student_id__icontains=q)
        )
    if year:
        qs = qs.filter(academic_year=year)
    if term:
        qs = qs.filter(term=term)
    if method:
        qs = qs.filter(payment_method=method)
    
    total = qs.aggregate(total=Sum('amount_paid'))['total'] or 0
    paginator = Paginator(qs, 50)
    page = paginator.get_page(request.GET.get('page', 1))
    
    context = {'payments': page, 'total_collected': total, 'q': q}
    return render(request, 'fees/history.html', context)


@login_required
def fee_structure_list(request):
    school = SchoolSettings.get_settings()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            try:
                classroom = ClassRoom.objects.get(id=request.POST.get('classroom_id'))
                FeeStructure.objects.create(
                    classroom=classroom,
                    fee_type=request.POST.get('fee_type', 'tuition'),
                    amount=float(request.POST.get('amount', 0)),
                    academic_year=int(request.POST.get('academic_year', school.current_year)),
                    term=int(request.POST.get('term', school.current_term)),
                    description=request.POST.get('description', ''),
                    is_mandatory=request.POST.get('is_mandatory') == 'on',
                )
                messages.success(request, 'Fee structure added!')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        elif action == 'delete':
            FeeStructure.objects.filter(id=request.POST.get('fee_id')).delete()
            messages.success(request, 'Fee structure deleted.')
        return redirect('fee_structure_list')
    
    year = int(request.GET.get('year', school.current_year))
    term = int(request.GET.get('term', school.current_term))
    structures = FeeStructure.objects.filter(
        academic_year=year, term=term
    ).select_related('classroom').order_by('classroom__name', 'fee_type')
    classes = ClassRoom.objects.filter(is_active=True, academic_year=year).order_by('name')
    
    context = {'structures': structures, 'classes': classes, 'year': year, 'term': term}
    return render(request, 'fees/structure.html', context)


@login_required
def export_defaulters_csv(request):
    school = SchoolSettings.get_settings()
    year = int(request.GET.get('year', school.current_year))
    term = int(request.GET.get('term', school.current_term))
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="defaulters_term{term}_{year}.csv"'
    writer = csv.writer(response)
    writer.writerow(['#', 'Student ID', 'Student Name', 'Class', 'Expected', 'Paid', 'Balance', 'Guardian Phone'])
    
    students = Student.objects.filter(is_active=True).select_related('current_class')
    count = 1
    for student in students:
        if not student.current_class:
            continue
        fee_struct = FeeStructure.objects.filter(
            classroom=student.current_class, academic_year=year, term=term
        ).aggregate(total=Sum('amount'))['total'] or 0
        paid = FeePayment.objects.filter(
            student=student, academic_year=year, term=term, status__in=['paid', 'partial']
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        balance = fee_struct - paid
        if balance > 0:
            writer.writerow([
                count, student.student_id, student.full_name,
                str(student.current_class), fee_struct, paid, balance,
                student.guardian_phone or student.father_phone
            ])
            count += 1
    return response
