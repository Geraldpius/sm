from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Avg, Count, Q, Max, Min
from apps.core.models import SchoolSettings, ClassRoom
from apps.students.models import Student
from apps.fees.models import FeePayment, FeeStructure
from apps.results.models import Exam, ExamResult, StudentReport
import csv, io
from datetime import datetime


@login_required
def reports_home(request):
    return render(request, 'reports/home.html')


@login_required
def enrollment_report(request):
    school = SchoolSettings.get_settings()
    year = int(request.GET.get('year', school.current_year))
    
    classes = ClassRoom.objects.filter(is_active=True, academic_year=year).order_by('name')
    data = []
    total_boys = total_girls = total_boarders = total_all = 0
    
    for cls in classes:
        students = Student.objects.filter(current_class=cls, is_active=True)
        boys = students.filter(gender='M').count()
        girls = students.filter(gender='F').count()
        boarders = students.filter(is_boarder=True).count()
        total = students.count()
        data.append({'class': cls, 'boys': boys, 'girls': girls, 'boarders': boarders, 'total': total})
        total_boys += boys; total_girls += girls; total_boarders += boarders; total_all += total
    
    context = {
        'data': data, 'total_boys': total_boys, 'total_girls': total_girls,
        'total_boarders': total_boarders, 'total_all': total_all, 'year': year,
    }
    return render(request, 'reports/enrollment.html', context)


@login_required
def fees_report(request):
    school = SchoolSettings.get_settings()
    year = int(request.GET.get('year', school.current_year))
    term = int(request.GET.get('term', school.current_term))
    
    # Monthly breakdown
    payments = FeePayment.objects.filter(
        academic_year=year, term=term, status__in=['paid', 'partial']
    ).values('payment_date__month').annotate(
        total=Sum('amount_paid'), count=Count('id')
    ).order_by('payment_date__month')
    
    monthly = []
    month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    for p in payments:
        monthly.append({
            'month': month_names[p['payment_date__month'] - 1],
            'total': p['total'], 'count': p['count']
        })
    
    # By payment method
    by_method = FeePayment.objects.filter(
        academic_year=year, term=term, status__in=['paid', 'partial']
    ).values('payment_method').annotate(total=Sum('amount_paid'), count=Count('id'))
    
    # By class
    classes = ClassRoom.objects.filter(is_active=True, academic_year=year).order_by('name')
    by_class = []
    for cls in classes:
        collected = FeePayment.objects.filter(
            student__current_class=cls, academic_year=year, term=term,
            status__in=['paid', 'partial']
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        by_class.append({'class': cls, 'collected': collected})
    
    total_collected = FeePayment.objects.filter(
        academic_year=year, term=term, status__in=['paid', 'partial']
    ).aggregate(total=Sum('amount_paid'))['total'] or 0
    
    context = {
        'monthly': monthly, 'by_method': by_method, 'by_class': by_class,
        'total_collected': total_collected, 'year': year, 'term': term,
    }
    return render(request, 'reports/fees_report.html', context)


@login_required
def academic_report(request):
    school = SchoolSettings.get_settings()
    year = int(request.GET.get('year', school.current_year))
    term = int(request.GET.get('term', school.current_term))
    
    classes = ClassRoom.objects.filter(is_active=True, academic_year=year).order_by('name')
    data = []
    for cls in classes:
        exams = Exam.objects.filter(classroom=cls, academic_year=year, term=term, is_published=True)
        if not exams.exists():
            continue
        exam = exams.last()
        reports = StudentReport.objects.filter(exam=exam)
        if not reports.exists():
            continue
        avg = reports.aggregate(avg=Avg('average'))['avg'] or 0
        top = reports.order_by('-average').first()
        data.append({
            'class': cls, 'exam': exam, 'students': reports.count(),
            'class_average': round(avg, 2),
            'top_student': top.student if top else None,
            'top_average': round(float(top.average), 1) if top else 0,
        })
    
    context = {'data': data, 'year': year, 'term': term}
    return render(request, 'reports/academic.html', context)


@login_required
def export_report_csv(request, report_type):
    school = SchoolSettings.get_settings()
    year = int(request.GET.get('year', school.current_year))
    term = int(request.GET.get('term', school.current_term))
    
    response = HttpResponse(content_type='text/csv')
    
    if report_type == 'enrollment':
        response['Content-Disposition'] = f'attachment; filename="enrollment_{year}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Class', 'Boys', 'Girls', 'Total', 'Boarders'])
        for cls in ClassRoom.objects.filter(is_active=True, academic_year=year):
            students = Student.objects.filter(current_class=cls, is_active=True)
            writer.writerow([str(cls), students.filter(gender='M').count(),
                            students.filter(gender='F').count(), students.count(),
                            students.filter(is_boarder=True).count()])
    
    elif report_type == 'fees':
        response['Content-Disposition'] = f'attachment; filename="fees_term{term}_{year}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Date', 'Receipt #', 'Student', 'Class', 'Amount', 'Method', 'Received By'])
        for p in FeePayment.objects.filter(academic_year=year, term=term).select_related('student', 'student__current_class').order_by('-payment_date'):
            writer.writerow([p.payment_date, p.receipt_number, p.student.full_name,
                           str(p.student.current_class), p.amount_paid, p.get_payment_method_display(), p.received_by])
    
    return response
