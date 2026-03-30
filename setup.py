#!/usr/bin/env python
"""
setup.py — Run this ONCE after installing dependencies to initialize the database.
Usage:  python setup.py
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_mgmt.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User
from apps.core.models import SchoolSettings, Subject, ClassRoom, UserProfile


def run():
    print("\n" + "="*60)
    print("  UGANDA SCHOOL MANAGEMENT SYSTEM — SETUP")
    print("="*60)

    # ── 0. Migrations ────────────────────────────────────────────
    print("\n[0/5] Running database migrations...")
    try:
        call_command('makemigrations', '--no-input', verbosity=0)
        call_command('migrate', '--no-input', verbosity=0)
        print("   ✓ Database tables created")
    except Exception as e:
        print(f"   ✗ Migration error: {e}")
        sys.exit(1)

    # ── 1. School Settings ───────────────────────────────────────
    print("\n[1/6] Creating school settings...")
    school, created = SchoolSettings.objects.get_or_create(pk=1, defaults={
        'name': 'Uganda Secondary School',
        'motto': 'Excellence Through Education',
        'address': 'P.O. Box 1, Kampala, Uganda',
        'phone': '+256 700 000 000',
        'email': 'info@school.ac.ug',
        'district': 'Kampala',
        'current_year': 2024,
        'current_term': 1,
        'currency': 'UGX',
        'grade_a_min': 80,
        'grade_b_min': 70,
        'grade_c_min': 60,
        'grade_d_min': 50,
        'grade_e_min': 40,
        'grade_f_min': 30,
    })
    if created:
        print("   ✓ School settings created")
    else:
        print("   • School settings already exist")

    # ── 2. Subjects ──────────────────────────────────────────────
    print("\n[2/6] Creating subjects...")
    subjects_data = [
        # O-Level subjects
        ('ENG',  'English Language',   'O', True,  100, 50),
        ('MATH', 'Mathematics',        'O', True,  100, 50),
        ('BIO',  'Biology',            'O', False, 100, 50),
        ('CHEM', 'Chemistry',          'O', False, 100, 50),
        ('PHY',  'Physics',            'O', False, 100, 50),
        ('HIST', 'History',            'O', False, 100, 50),
        ('GEO',  'Geography',          'O', False, 100, 50),
        ('CRE',  'CRE',                'O', False, 100, 50),
        ('AGR',  'Agriculture',        'O', False, 100, 50),
        ('ICT',  'ICT',                'O', False, 100, 50),
        ('FART', 'Fine Art',           'O', False, 100, 50),
        ('LUG',  'Luganda',            'O', False, 100, 50),
        ('KIS',  'Kiswahili',          'O', False, 100, 50),
        ('FN',   'Food & Nutrition',   'O', False, 100, 50),
        ('LIT',  'Literature',         'O', False, 100, 50),
        # A-Level subjects
        ('ECON', 'Economics',          'A', False, 100, 50),
        ('ACC',  'Accounting',         'A', False, 100, 50),
        ('ENT',  'Entrepreneurship',   'A', False, 100, 50),
        ('GP',   'General Paper',      'A', True,  100, 50),
        ('SUBS', 'Subsidiary ICT',     'A', False, 100, 50),
    ]
    created_count = 0
    for code, name, level, is_core, max_marks, pass_mark in subjects_data:
        _, c = Subject.objects.get_or_create(
            code=code,
            defaults={
                'name': name, 'level': level, 'is_core': is_core,
                'max_marks': max_marks, 'pass_mark': pass_mark,
            }
        )
        if c:
            created_count += 1
    print(f"   ✓ {created_count} new subjects created ({Subject.objects.count()} total)")

    # ── 3. Classes ───────────────────────────────────────────────
    print("\n[3/6] Creating classes...")
    o_level_classes = ['S1', 'S2', 'S3', 'S4']
    a_level_classes = ['S5', 'S6']

    o_subjects = list(Subject.objects.filter(level='O', is_active=True))
    a_subjects = list(Subject.objects.filter(level='A', is_active=True))
    # A-level also uses some O-level subjects
    a_combined = a_subjects + list(Subject.objects.filter(code__in=['ENG','MATH','PHY','CHEM','BIO','ECON','ACC']))

    cls_created = 0
    year = 2024
    for name in o_level_classes:
        cls, c = ClassRoom.objects.get_or_create(
            name=name, stream='', academic_year=year,
            defaults={'level': 'O', 'password': f'{name.lower()}2024', 'capacity': 45}
        )
        if c:
            cls.subjects.set(o_subjects)
            cls_created += 1

    for name in a_level_classes:
        cls, c = ClassRoom.objects.get_or_create(
            name=name, stream='', academic_year=year,
            defaults={'level': 'A', 'password': f'{name.lower()}2024', 'capacity': 35}
        )
        if c:
            cls.subjects.set(a_combined)
            cls_created += 1

    print(f"   ✓ {cls_created} new classes created ({ClassRoom.objects.count()} total)")
    print("   ℹ Class passwords: s1→s12024, s2→s22024, ... s6→s62024")

    # ── 4. Superuser / Admin ─────────────────────────────────────
    print("\n[4/6] Creating admin user...")
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser(
            username='admin',
            password='admin@2024',
            email='admin@school.ac.ug',
            first_name='System',
            last_name='Administrator',
        )
        UserProfile.objects.create(user=admin, role='admin')
        print("   ✓ Admin user created — username: admin | password: admin@2024")
    else:
        print("   • Admin user already exists")

    # Default staff accounts
    staff = [
        ('bursar',      'bursar@2024',     'Bursar',      'Office', 'bursar'),
        ('dos',         'dos@2024',        'Director',    'Studies', 'dos'),
        ('headteacher', 'head@2024',       'Head',        'Teacher', 'headteacher'),
        ('teacher1',    'teacher@2024',    'Class',       'Teacher', 'teacher'),
    ]
    for uname, pwd, fname, lname, role in staff:
        if not User.objects.filter(username=uname).exists():
            u = User.objects.create_user(
                username=uname, password=pwd,
                first_name=fname, last_name=lname,
            )
            UserProfile.objects.create(user=u, role=role)
            print(f"   ✓ {role.title()} created — username: {uname} | password: {pwd}")

    # ── 5. Sample Fee Structures ─────────────────────────────────
    print("\n[5/6] Creating sample fee structures...")
    from apps.fees.models import FeeStructure

    fee_amounts = {
        'S1': 450000, 'S2': 450000, 'S3': 500000,
        'S4': 550000, 'S5': 650000, 'S6': 650000,
    }
    boarding_amounts = {
        'S1': 350000, 'S2': 350000, 'S3': 350000,
        'S4': 350000, 'S5': 400000, 'S6': 400000,
    }
    fee_created = 0
    for cls in ClassRoom.objects.filter(academic_year=year):
        class_name = cls.name
        for term in [1, 2, 3]:
            # Tuition
            _, c = FeeStructure.objects.get_or_create(
                classroom=cls, fee_type='tuition', academic_year=year, term=term,
                defaults={
                    'amount': fee_amounts.get(class_name, 500000),
                    'is_mandatory': True,
                    'description': f'{cls} Tuition Fees Term {term}',
                }
            )
            if c: fee_created += 1
            # Boarding
            _, c = FeeStructure.objects.get_or_create(
                classroom=cls, fee_type='boarding', academic_year=year, term=term,
                defaults={
                    'amount': boarding_amounts.get(class_name, 350000),
                    'is_mandatory': False,
                    'description': f'{cls} Boarding Fees Term {term}',
                }
            )
            if c: fee_created += 1
    print(f"   ✓ {fee_created} fee structures created")

    # ── Done ─────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("  SETUP COMPLETE!")
    print("="*60)
    print("\n  LOGIN CREDENTIALS:")
    print("  ┌─────────────────┬──────────────┬──────────────┐")
    print("  │ Role            │ Username     │ Password     │")
    print("  ├─────────────────┼──────────────┼──────────────┤")
    print("  │ Administrator   │ admin        │ admin@2024   │")
    print("  │ Bursar          │ bursar       │ bursar@2024  │")
    print("  │ Dir. of Studies │ dos          │ dos@2024     │")
    print("  │ Head Teacher    │ headteacher  │ head@2024    │")
    print("  │ Teacher         │ teacher1     │ teacher@2024 │")
    print("  └─────────────────┴──────────────┴──────────────┘")
    print("\n  CLASS PASSWORDS (for results access):")
    print("  S1=s12024  S2=s22024  S3=s32024")
    print("  S4=s42024  S5=s52024  S6=s62024")
    print("\n  Start server:  python manage.py runserver")
    print("  Then open:     http://127.0.0.1:8000/")
    print("="*60 + "\n")


if __name__ == '__main__':
    run()
