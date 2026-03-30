from django.db import models
from django.contrib.auth.models import User


class SchoolSettings(models.Model):
    name = models.CharField(max_length=200, default="Uganda Secondary School")
    motto = models.CharField(max_length=300, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='school/', blank=True, null=True)
    founded_year = models.IntegerField(default=2000)
    district = models.CharField(max_length=100, blank=True)
    
    # Grading scale (Uganda UNEB style)
    grade_a_min = models.IntegerField(default=80, help_text="Min % for A (Distinction 1)")
    grade_b_min = models.IntegerField(default=70, help_text="Min % for B (Merit 2)")
    grade_c_min = models.IntegerField(default=60, help_text="Min % for C (Credit 3)")
    grade_d_min = models.IntegerField(default=50, help_text="Min % for D (Pass 4)")
    grade_e_min = models.IntegerField(default=40, help_text="Min % for E (Pass 5)")
    grade_f_min = models.IntegerField(default=30, help_text="Min % for F (Fail 6)")
    # Below grade_f_min = U (Ungraded/Fail 9)

    # Fees structure
    currency = models.CharField(max_length=10, default="UGX")
    current_term = models.IntegerField(default=1, choices=[(1,'Term 1'),(2,'Term 2'),(3,'Term 3')])
    current_year = models.IntegerField(default=2024)
    
    class Meta:
        verbose_name = "School Settings"
        
    def __str__(self):
        return self.name
    
    def get_grade(self, percentage):
        if percentage >= self.grade_a_min:
            return 'A', '1', 'Distinction'
        elif percentage >= self.grade_b_min:
            return 'B', '2', 'Merit'
        elif percentage >= self.grade_c_min:
            return 'C', '3', 'Credit'
        elif percentage >= self.grade_d_min:
            return 'D', '4', 'Pass'
        elif percentage >= self.grade_e_min:
            return 'E', '5', 'Pass'
        elif percentage >= self.grade_f_min:
            return 'F', '6', 'Fail'
        else:
            return 'U', '9', 'Ungraded'

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


LEVEL_CHOICES = [
    ('O', 'O-Level'),
    ('A', 'A-Level'),
]

CLASS_CHOICES = [
    ('S1', 'Senior 1'),
    ('S2', 'Senior 2'),
    ('S3', 'Senior 3'),
    ('S4', 'Senior 4'),
    ('S5', 'Senior 5'),
    ('S6', 'Senior 6'),
]

SUBJECT_CHOICES = [
    ('HIST', 'History'),
    ('CHEM', 'Chemistry'),
    ('BIO', 'Biology'),
    ('FART', 'Fine Art'),
    ('GEO', 'Geography'),
    ('MATH', 'Mathematics'),
    ('ENG', 'English'),
    ('ICT', 'ICT'),
    ('LUG', 'Luganda'),
    ('KIS', 'Kiswahili'),
    ('PHY', 'Physics'),
    ('AGR', 'Agriculture'),
    ('CRE', 'CRE'),
    ('FN', 'Food & Nutrition'),
    ('LIT', 'Literature'),
    ('ECON', 'Economics'),
    ('ACC', 'Accounting'),
    ('ENT', 'Entrepreneurship'),
    ('PED', 'Physical Education'),
    ('SUBS', 'Subsidiary ICT'),
    ('GP', 'General Paper'),
]

TERM_CHOICES = [(1, 'Term 1'), (2, 'Term 2'), (3, 'Term 3')]


class Subject(models.Model):
    code = models.CharField(max_length=10, unique=True, choices=SUBJECT_CHOICES)
    name = models.CharField(max_length=100)
    level = models.CharField(max_length=1, choices=LEVEL_CHOICES, default='O')
    is_core = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    max_marks = models.IntegerField(default=100)
    pass_mark = models.IntegerField(default=50)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['name']


class ClassRoom(models.Model):
    name = models.CharField(max_length=5, choices=CLASS_CHOICES)
    level = models.CharField(max_length=1, choices=LEVEL_CHOICES, default='O')
    stream = models.CharField(max_length=20, blank=True, help_text="e.g., Arts, Science, None")
    class_teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='class_teacher_of')
    password = models.CharField(max_length=100, default='class123',
                                 help_text="Password to access this class results")
    capacity = models.IntegerField(default=45)
    subjects = models.ManyToManyField(Subject, blank=True)
    academic_year = models.IntegerField(default=2024)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        stream = f" {self.stream}" if self.stream else ""
        return f"{self.name}{stream} ({self.academic_year})"

    def display_name(self):
        stream = f" {self.stream}" if self.stream else ""
        return f"{self.name}{stream}"

    class Meta:
        ordering = ['name', 'stream']
        unique_together = ['name', 'stream', 'academic_year']


class AcademicYear(models.Model):
    year = models.IntegerField(unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return str(self.year)

    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicYear.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('headteacher', 'Head Teacher'),
        ('teacher', 'Teacher'),
        ('bursar', 'Bursar'),
        ('dos', 'Director of Studies'),
        ('receptionist', 'Receptionist'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='teacher')
    phone = models.CharField(max_length=20, blank=True)
    classes = models.ManyToManyField(ClassRoom, blank=True, help_text="Classes this user manages")
    photo = models.ImageField(upload_to='staff/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.role})"
