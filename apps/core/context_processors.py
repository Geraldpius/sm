from django.db import connection
from .models import SchoolSettings


def school_settings(request):
    # Guard against missing table (before migrations run)
    try:
        if 'core_schoolsettings' not in connection.introspection.table_names():
            return {}
        school = SchoolSettings.get_settings()
    except Exception:
        return {}

    user_role = 'admin'
    if request.user.is_authenticated:
        if request.user.is_superuser:
            user_role = 'admin'
        else:
            try:
                user_role = request.user.profile.role
            except Exception:
                user_role = 'teacher'

    return {
        'school': school,
        'school_name': school.name,
        'school_motto': school.motto,
        'current_term': school.current_term,
        'current_year': school.current_year,
        'currency': school.currency,
        'user_role': user_role,
    }
```
