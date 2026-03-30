from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda r: redirect('/dashboard/'), name='home'),
    path('auth/', include('apps.core.urls_auth')),
    path('dashboard/', include('apps.core.urls')),
    path('students/', include('apps.students.urls')),
    path('fees/', include('apps.fees.urls')),
    path('results/', include('apps.results.urls')),
    path('reports/', include('apps.reports.urls')),
    path('requirements/', include('apps.requirements.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
