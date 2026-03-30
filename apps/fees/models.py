from django.db import models
from apps.students.models import Student
from apps.core.models import ClassRoom, TERM_CHOICES


PAYMENT_METHOD_CHOICES = [
    ('cash', 'Cash'),
    ('bank', 'Bank Transfer'),
    ('mobile_money', 'Mobile Money'),
    ('cheque', 'Cheque'),
    ('online', 'Online'),
]

PAYMENT_STATUS_CHOICES = [
    ('paid', 'Fully Paid'),
    ('partial', 'Partially Paid'),
    ('unpaid', 'Unpaid'),
    ('waived', 'Waived'),
]

FEE_TYPE_CHOICES = [
    ('tuition', 'Tuition Fees'),
    ('boarding', 'Boarding Fees'),
    ('uniform', 'Uniform'),
    ('sports', 'Sports Fees'),
    ('exams', 'Examination Fees'),
    ('development', 'Development Fund'),
    ('library', 'Library Fees'),
    ('ict', 'ICT Fees'),
    ('medical', 'Medical Fees'),
    ('other', 'Other'),
]


class FeeStructure(models.Model):
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='fee_structures')
    fee_type = models.CharField(max_length=20, choices=FEE_TYPE_CHOICES, default='tuition')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    academic_year = models.IntegerField()
    term = models.IntegerField(choices=TERM_CHOICES)
    description = models.CharField(max_length=300, blank=True)
    is_mandatory = models.BooleanField(default=True)
    due_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.classroom} - {self.get_fee_type_display()} - Term {self.term} {self.academic_year}"

    class Meta:
        ordering = ['academic_year', 'term', 'classroom__name']
        unique_together = ['classroom', 'fee_type', 'academic_year', 'term']


class FeePayment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='feepayment')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.SET_NULL, null=True, blank=True)
    academic_year = models.IntegerField()
    term = models.IntegerField(choices=TERM_CHOICES)
    fee_type = models.CharField(max_length=20, choices=FEE_TYPE_CHOICES, default='tuition')
    
    amount_expected = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    payment_date = models.DateField()
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='paid')
    
    receipt_number = models.CharField(max_length=50, unique=True)
    transaction_reference = models.CharField(max_length=200, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    
    received_by = models.CharField(max_length=200)
    remarks = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Receipt #{self.receipt_number} - {self.student.full_name}"

    def save(self, *args, **kwargs):
        self.balance = self.amount_expected - self.amount_paid - self.discount
        if self.balance <= 0:
            self.status = 'paid'
        elif self.amount_paid > 0:
            self.status = 'partial'
        else:
            self.status = 'unpaid'
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-payment_date', '-created_at']


class FeeWaiver(models.Model):
    WAIVER_TYPE_CHOICES = [
        ('full', 'Full Waiver'),
        ('partial', 'Partial Waiver'),
        ('scholarship', 'Scholarship'),
        ('bursary', 'Bursary'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='waivers')
    academic_year = models.IntegerField()
    term = models.IntegerField(choices=TERM_CHOICES)
    waiver_type = models.CharField(max_length=20, choices=WAIVER_TYPE_CHOICES)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reason = models.TextField()
    approved_by = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.full_name} - {self.waiver_type} waiver"
