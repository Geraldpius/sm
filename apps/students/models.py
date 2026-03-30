from django.db import models
from apps.core.models import ClassRoom


GENDER_CHOICES = [('M', 'Male'), ('F', 'Female')]

RELIGION_CHOICES = [
    ('Christian', 'Christian'),
    ('Muslim', 'Muslim'),
    ('Other', 'Other'),
]

BLOOD_GROUP_CHOICES = [
    ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
    ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
]


class Student(models.Model):
    # Identification
    student_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    other_names = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    photo = models.ImageField(upload_to='students/', blank=True, null=True)
    
    # Academic
    current_class = models.ForeignKey(ClassRoom, on_delete=models.SET_NULL, null=True, blank=True)
    admission_date = models.DateField()
    admission_number = models.CharField(max_length=50, blank=True)
    lin_number = models.CharField(max_length=50, blank=True, help_text="UNEB LIN Number")
    index_number = models.CharField(max_length=50, blank=True, help_text="UNEB Index Number")
    previous_school = models.CharField(max_length=200, blank=True)
    
    # Personal
    religion = models.CharField(max_length=20, choices=RELIGION_CHOICES, blank=True)
    nationality = models.CharField(max_length=50, default='Ugandan')
    district_of_origin = models.CharField(max_length=100, blank=True)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)
    medical_conditions = models.TextField(blank=True)
    
    # Contact
    home_address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # Parent/Guardian
    father_name = models.CharField(max_length=200, blank=True)
    father_phone = models.CharField(max_length=20, blank=True)
    father_occupation = models.CharField(max_length=100, blank=True)
    mother_name = models.CharField(max_length=200, blank=True)
    mother_phone = models.CharField(max_length=20, blank=True)
    mother_occupation = models.CharField(max_length=100, blank=True)
    guardian_name = models.CharField(max_length=200, blank=True)
    guardian_phone = models.CharField(max_length=20, blank=True)
    guardian_relationship = models.CharField(max_length=100, blank=True)
    guardian_address = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_boarder = models.BooleanField(default=False)
    is_sponsored = models.BooleanField(default=False)
    sponsor_name = models.CharField(max_length=200, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student_id} - {self.full_name}"

    @property
    def full_name(self):
        names = [self.first_name, self.other_names, self.last_name]
        return ' '.join([n for n in names if n])

    def get_age(self):
        from django.utils import timezone
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    class Meta:
        ordering = ['last_name', 'first_name']


class StudentPromotion(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='promotions')
    from_class = models.ForeignKey(ClassRoom, on_delete=models.SET_NULL, null=True, related_name='promoted_from')
    to_class = models.ForeignKey(ClassRoom, on_delete=models.SET_NULL, null=True, related_name='promoted_to')
    academic_year = models.IntegerField()
    promotion_date = models.DateField(auto_now_add=True)
    remarks = models.TextField(blank=True)
    promoted_by = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.student} promoted from {self.from_class} to {self.to_class}"


class StudentLeave(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('returned', 'Returned'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='leaves')
    reason = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.CharField(max_length=200, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.full_name} - Leave {self.start_date} to {self.end_date}"
