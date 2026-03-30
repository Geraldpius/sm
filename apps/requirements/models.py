from django.db import models
from apps.students.models import Student
from apps.core.models import ClassRoom, TERM_CHOICES


class TermRequirement(models.Model):
    """Items required at the beginning of each term"""
    CATEGORY_CHOICES = [
        ('stationery', 'Stationery'),
        ('uniform', 'Uniform'),
        ('books', 'Books & Textbooks'),
        ('bedding', 'Bedding & Linen'),
        ('toiletries', 'Toiletries'),
        ('sports', 'Sports Equipment'),
        ('other', 'Other'),
    ]
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='requirements',
                                   null=True, blank=True, help_text="Leave blank for all classes")
    item_name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='stationery')
    description = models.TextField(blank=True)
    quantity = models.IntegerField(default=1)
    unit = models.CharField(max_length=50, default='piece')
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_mandatory = models.BooleanField(default=True)
    academic_year = models.IntegerField()
    term = models.IntegerField(choices=TERM_CHOICES)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        cls = f" ({self.classroom})" if self.classroom else " (All Classes)"
        return f"{self.item_name}{cls} - Term {self.term} {self.academic_year}"

    class Meta:
        ordering = ['category', 'item_name']


class StudentRequirementStatus(models.Model):
    """Track whether a student has brought required items"""
    STATUS_CHOICES = [
        ('brought', 'Brought'),
        ('partial', 'Partially Brought'),
        ('missing', 'Missing'),
        ('waived', 'Waived'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='requirement_status')
    requirement = models.ForeignKey(TermRequirement, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='missing')
    quantity_brought = models.IntegerField(default=0)
    remarks = models.CharField(max_length=300, blank=True)
    checked_by = models.CharField(max_length=200, blank=True)
    checked_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.full_name} - {self.requirement.item_name}: {self.status}"

    class Meta:
        unique_together = ['student', 'requirement']
