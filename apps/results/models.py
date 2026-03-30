from django.db import models
from apps.students.models import Student
from apps.core.models import Subject, ClassRoom, TERM_CHOICES


EXAM_TYPE_CHOICES = [
    ('bot', 'Beginning of Term Test'),
    ('mid', 'Mid-Term Exam'),
    ('eot', 'End of Term Exam'),
    ('mock', 'Mock Exam'),
    ('uneb', 'UNEB Exam'),
    ('cat', 'Continuous Assessment'),
]


class Exam(models.Model):
    name = models.CharField(max_length=200)
    exam_type = models.CharField(max_length=10, choices=EXAM_TYPE_CHOICES)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='exams')
    academic_year = models.IntegerField()
    term = models.IntegerField(choices=TERM_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    max_marks = models.IntegerField(default=100)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.name} - {self.classroom} ({self.academic_year} T{self.term})"

    class Meta:
        ordering = ['-academic_year', '-term', 'classroom__name']


class ExamResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='results')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    academic_year = models.IntegerField()
    term = models.IntegerField(choices=TERM_CHOICES)
    
    marks = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    max_marks = models.IntegerField(default=100)
    
    grade = models.CharField(max_length=5, blank=True)
    points = models.IntegerField(default=9)
    remarks = models.CharField(max_length=100, blank=True)
    teacher_comment = models.CharField(max_length=300, blank=True)
    
    entered_by = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def percentage(self):
        if self.max_marks > 0:
            return round((float(self.marks) / self.max_marks) * 100, 1)
        return 0

    def __str__(self):
        return f"{self.student.full_name} - {self.subject.name}: {self.marks}"

    class Meta:
        unique_together = ['student', 'exam', 'subject']
        ordering = ['subject__name']


class StudentReport(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='reports')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='student_reports')
    academic_year = models.IntegerField()
    term = models.IntegerField(choices=TERM_CHOICES)
    
    total_marks = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_possible = models.IntegerField(default=0)
    aggregate = models.IntegerField(default=0, help_text="Sum of best 8 subject points (UNEB style)")
    average = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    position = models.IntegerField(default=0)
    out_of = models.IntegerField(default=0)
    
    class_teacher_comment = models.TextField(blank=True)
    head_teacher_comment = models.TextField(blank=True)
    dos_comment = models.TextField(blank=True)
    
    next_term_opening = models.DateField(null=True, blank=True)
    is_promoted = models.BooleanField(default=True)
    
    generated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Report: {self.student.full_name} - {self.exam.name}"

    class Meta:
        unique_together = ['student', 'exam']
