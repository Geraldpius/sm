from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Sum, Count, Q
from django.http import HttpResponse
from django.utils import timezone
import json
from .models import Exam, ExamResult, StudentReport
from apps.students.models import Student
from apps.core.models import ClassRoom, Subject, SchoolSettings


def calculate_grade(percentage, school):
    grade, points, remarks = school.get_grade(percentage)
    return grade, points, remarks


def compute_student_report(student, exam, school):
    results = ExamResult.objects.filter(student=student, exam=exam).select_related('subject')
    if not results:
        return None
    
    total_marks = sum(float(r.marks) for r in results)
    total_possible = sum(r.max_marks for r in results)
    average = (total_marks / total_possible * 100) if total_possible > 0 else 0
    
    # Sort by points and take best 8 (UNEB O-level style)
    sorted_results = sorted(results, key=lambda r: r.points)
    best_8 = sorted_results[:8]
    aggregate = sum(r.points for r in best_8)
    
    report, _ = StudentReport.objects.get_or_create(
        student=student,
        exam=exam,
        defaults={'academic_year': exam.academic_year, 'term': exam.term}
    )
    report.total_marks = total_marks
    report.total_possible = total_possible
    report.average = average
    report.aggregate = aggregate
    report.academic_year = exam.academic_year
    report.term = exam.term
    report.save()
    return report


@login_required
def exam_list(request):
    school = SchoolSettings.get_settings()
    year = int(request.GET.get('year', school.current_year))
    term = int(request.GET.get('term', school.current_term))
    class_filter = request.GET.get('class_id', '')
    
    exams = Exam.objects.filter(academic_year=year, term=term).select_related('classroom')
    if class_filter:
        exams = exams.filter(classroom_id=class_filter)
    
    classes = ClassRoom.objects.filter(is_active=True, academic_year=year).order_by('name')
    context = {'exams': exams, 'classes': classes, 'year': year, 'term': term, 'class_filter': class_filter}
    return render(request, 'results/exam_list.html', context)


@login_required
def create_exam(request):
    school = SchoolSettings.get_settings()
    if request.method == 'POST':
        try:
            import datetime
            classroom = ClassRoom.objects.get(id=request.POST.get('classroom_id'))
            exam = Exam.objects.create(
                name=request.POST.get('name'),
                exam_type=request.POST.get('exam_type', 'eot'),
                classroom=classroom,
                academic_year=int(request.POST.get('academic_year', school.current_year)),
                term=int(request.POST.get('term', school.current_term)),
                start_date=datetime.date.fromisoformat(request.POST.get('start_date')),
                end_date=datetime.date.fromisoformat(request.POST.get('end_date')),
                max_marks=int(request.POST.get('max_marks', 100)),
                created_by=request.user.get_full_name() or request.user.username,
            )
            messages.success(request, f'Exam "{exam.name}" created!')
            return redirect('enter_marks', exam_id=exam.pk)
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    classes = ClassRoom.objects.filter(is_active=True, academic_year=school.current_year).order_by('name')
    return render(request, 'results/create_exam.html', {'classes': classes})


@login_required
def enter_marks(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    school = SchoolSettings.get_settings()
    
    # Check class access
    session_key = f'class_access_{exam.classroom_id}'
    if not request.user.is_staff and not request.session.get(session_key):
        return redirect('class_access', class_id=exam.classroom_id)
    
    students = Student.objects.filter(
        current_class=exam.classroom, is_active=True
    ).order_by('last_name', 'first_name')
    subjects = exam.classroom.subjects.filter(is_active=True).order_by('name')
    
    if request.method == 'POST':
        saved_count = 0
        for student in students:
            for subject in subjects:
                key = f'marks_{student.pk}_{subject.pk}'
                marks_str = request.POST.get(key, '').strip()
                if marks_str:
                    try:
                        marks = float(marks_str)
                        marks = max(0, min(marks, exam.max_marks))
                        percentage = (marks / exam.max_marks) * 100
                        grade, points, remarks = calculate_grade(percentage, school)
                        
                        result, created = ExamResult.objects.update_or_create(
                            student=student, exam=exam, subject=subject,
                            defaults={
                                'marks': marks,
                                'max_marks': exam.max_marks,
                                'grade': grade,
                                'points': int(points),
                                'remarks': remarks,
                                'academic_year': exam.academic_year,
                                'term': exam.term,
                                'entered_by': request.user.get_full_name() or request.user.username,
                            }
                        )
                        saved_count += 1
                    except ValueError:
                        pass
        
        # Compute reports
        for student in students:
            compute_student_report(student, exam, school)
        
        messages.success(request, f'{saved_count} marks saved successfully!')
        return redirect('enter_marks', exam_id=exam_id)
    
    # Load existing marks
    existing = {}
    for result in ExamResult.objects.filter(exam=exam):
        existing[(result.student_id, result.subject_id)] = result
    
    context = {
        'exam': exam, 'students': students, 'subjects': subjects, 'existing': existing,
    }
    return render(request, 'results/enter_marks.html', context)


@login_required
def class_results(request, class_id):
    classroom = get_object_or_404(ClassRoom, pk=class_id)
    school = SchoolSettings.get_settings()
    
    # Check class access
    session_key = f'class_access_{class_id}'
    if not request.user.is_staff and not request.session.get(session_key):
        return redirect('class_access', class_id=class_id)
    
    year = int(request.GET.get('year', school.current_year))
    term = int(request.GET.get('term', school.current_term))
    exam_id = request.GET.get('exam_id')
    
    exams = Exam.objects.filter(classroom=classroom, academic_year=year, term=term)
    selected_exam = None
    if exam_id:
        selected_exam = get_object_or_404(Exam, pk=exam_id)
    elif exams.exists():
        selected_exam = exams.last()
    
    students = Student.objects.filter(current_class=classroom, is_active=True).order_by('last_name')
    subjects = classroom.subjects.filter(is_active=True).order_by('name')
    
    results_table = []
    if selected_exam:
        reports = {r.student_id: r for r in StudentReport.objects.filter(exam=selected_exam)}
        
        # Rank students
        student_data = []
        for student in students:
            s_results = {r.subject_id: r for r in ExamResult.objects.filter(student=student, exam=selected_exam)}
            report = reports.get(student.pk)
            student_data.append({'student': student, 'results': s_results, 'report': report})
        
        # Sort by average descending
        student_data.sort(key=lambda x: float(x['report'].average) if x['report'] else 0, reverse=True)
        for i, sd in enumerate(student_data, 1):
            if sd['report']:
                sd['report'].position = i
                sd['report'].out_of = len(student_data)
                sd['report'].save()
        results_table = student_data
    
    context = {
        'classroom': classroom, 'exams': exams, 'selected_exam': selected_exam,
        'students': students, 'subjects': subjects, 'results_table': results_table,
        'year': year, 'term': term,
    }
    return render(request, 'results/class_results.html', context)


@login_required
def student_report(request, student_id, exam_id):
    student = get_object_or_404(Student, pk=student_id)
    exam = get_object_or_404(Exam, pk=exam_id)
    school = SchoolSettings.get_settings()
    
    results = ExamResult.objects.filter(student=student, exam=exam).select_related('subject').order_by('subject__name')
    report = StudentReport.objects.filter(student=student, exam=exam).first()
    
    if request.method == 'POST':
        if report:
            report.class_teacher_comment = request.POST.get('class_teacher_comment', report.class_teacher_comment)
            report.head_teacher_comment = request.POST.get('head_teacher_comment', report.head_teacher_comment)
            report.dos_comment = request.POST.get('dos_comment', report.dos_comment)
            date_str = request.POST.get('next_term_opening')
            if date_str:
                import datetime
                report.next_term_opening = datetime.date.fromisoformat(date_str)
            report.is_promoted = request.POST.get('is_promoted') == 'on'
            report.save()
            messages.success(request, 'Report comments saved!')
        return redirect('student_report', student_id=student_id, exam_id=exam_id)
    
    context = {
        'student': student, 'exam': exam, 'results': results,
        'report': report, 'school': school,
    }
    return render(request, 'results/student_report.html', context)


@login_required
def publish_exam(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    exam.is_published = not exam.is_published
    exam.save()
    status = 'published' if exam.is_published else 'unpublished'
    messages.success(request, f'Exam results {status}!')
    return redirect('class_results', class_id=exam.classroom_id)


@login_required
def subject_analysis(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    school = SchoolSettings.get_settings()
    subjects = exam.classroom.subjects.filter(is_active=True)
    
    analysis = []
    for subject in subjects:
        results = ExamResult.objects.filter(exam=exam, subject=subject)
        if results.exists():
            marks = [float(r.marks) for r in results]
            total = results.count()
            passed = results.filter(marks__gte=exam.max_marks * school.grade_d_min / 100).count()
            analysis.append({
                'subject': subject,
                'count': total,
                'highest': max(marks),
                'lowest': min(marks),
                'average': round(sum(marks) / total, 2),
                'passed': passed,
                'failed': total - passed,
                'pass_rate': round(passed / total * 100, 1),
                'grade_dist': {
                    'A': results.filter(grade='A').count(),
                    'B': results.filter(grade='B').count(),
                    'C': results.filter(grade='C').count(),
                    'D': results.filter(grade='D').count(),
                    'E': results.filter(grade='E').count(),
                    'F': results.filter(grade='F').count(),
                    'U': results.filter(grade='U').count(),
                }
            })
    
    context = {'exam': exam, 'analysis': analysis}
    return render(request, 'results/subject_analysis.html', context)
