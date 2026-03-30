from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile


def login_view(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(request.GET.get('next', '/dashboard/'))
        messages.error(request, 'Invalid username or password.')
    return render(request, 'auth/login.html')


def logout_view(request):
    logout(request)
    return redirect('/auth/login/')


@login_required
def manage_users(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            username   = request.POST.get('username', '').strip()
            first_name = request.POST.get('first_name', '').strip()
            last_name  = request.POST.get('last_name', '').strip()
            email      = request.POST.get('email', '').strip()
            password   = request.POST.get('password', '')
            role       = request.POST.get('role', 'teacher')
            phone      = request.POST.get('phone', '').strip()

            if not username or not password:
                messages.error(request, 'Username and password are required.')
            elif User.objects.filter(username=username).exists():
                messages.error(request, f'Username "{username}" is already taken.')
            else:
                user = User.objects.create_user(
                    username=username, password=password,
                    first_name=first_name, last_name=last_name, email=email,
                )
                # Use get_or_create so the signal-created profile isn't duplicated
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.role  = role
                profile.phone = phone
                profile.save()
                messages.success(request, f'User {user.get_full_name() or username} created successfully!')

        elif action == 'edit':
            user_id    = request.POST.get('user_id')
            u          = get_object_or_404(User, id=user_id)
            u.first_name = request.POST.get('first_name', u.first_name).strip()
            u.last_name  = request.POST.get('last_name',  u.last_name).strip()
            u.email      = request.POST.get('email',      u.email).strip()
            u.save()
            profile, _ = UserProfile.objects.get_or_create(user=u)
            profile.role  = request.POST.get('role', profile.role)
            profile.phone = request.POST.get('phone', profile.phone).strip()
            profile.save()
            messages.success(request, f'User {u.get_full_name()} updated.')

        elif action == 'toggle':
            u = get_object_or_404(User, id=request.POST.get('user_id'))
            if u == request.user:
                messages.error(request, 'You cannot deactivate your own account.')
            else:
                u.is_active = not u.is_active
                u.save()
                status = 'activated' if u.is_active else 'deactivated'
                messages.success(request, f'{u.get_full_name() or u.username} has been {status}.')

        elif action == 'reset_password':
            u        = get_object_or_404(User, id=request.POST.get('user_id'))
            new_pass = request.POST.get('new_password', '').strip()
            if len(new_pass) < 6:
                messages.error(request, 'New password must be at least 6 characters.')
            else:
                u.set_password(new_pass)
                u.save()
                messages.success(request, f'Password for {u.get_full_name() or u.username} reset successfully.')

        elif action == 'delete':
            u = get_object_or_404(User, id=request.POST.get('user_id'))
            if u == request.user:
                messages.error(request, 'You cannot delete your own account.')
            elif u.is_superuser:
                messages.error(request, 'Cannot delete a superuser account.')
            else:
                name = u.get_full_name() or u.username
                u.delete()
                messages.success(request, f'User {name} deleted.')

        return redirect('manage_users')

    users = User.objects.all().select_related('profile').order_by('first_name', 'last_name')
    return render(request, 'auth/users.html', {'users': users})


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', request.user.first_name).strip()
        request.user.last_name  = request.POST.get('last_name',  request.user.last_name).strip()
        request.user.email      = request.POST.get('email',      request.user.email).strip()
        request.user.save()

        profile.phone = request.POST.get('phone', profile.phone).strip()
        if 'photo' in request.FILES:
            profile.photo = request.FILES['photo']
        profile.save()

        old_pass = request.POST.get('old_password', '')
        new_pass = request.POST.get('new_password', '')
        if old_pass and new_pass:
            if request.user.check_password(old_pass):
                if len(new_pass) < 6:
                    messages.error(request, 'New password must be at least 6 characters.')
                    return redirect('profile')
                request.user.set_password(new_pass)
                request.user.save()
                messages.success(request, 'Password changed. Please log in again.')
                return redirect('/auth/login/')
            else:
                messages.error(request, 'Current password is incorrect.')
                return redirect('profile')

        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    return render(request, 'auth/profile.html', {'profile': profile})
