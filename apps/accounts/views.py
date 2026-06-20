"""
MAS Investment - Accounts Views
Authentication: Register, Login, Logout, Email Verify, Password Reset
"""
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from .models import User, CustomerProfile
from apps.vendors.models import Vendor
from apps.riders.models import Rider
from apps.staff.models import StaffProfile
from apps.orders.models import Cart


def get_dashboard_url(user):
    role_map = {
        User.SUPER_ADMIN: '/admin-panel/',
        User.STAFF: '/staff/',
        User.VENDOR: '/vendor/',
        User.RIDER: '/rider/',
        User.CUSTOMER: '/customer/',
    }
    return role_map.get(user.role, '/')


@csrf_protect
def register_view(request):
    if request.user.is_authenticated:
        return redirect(get_dashboard_url(request.user))

    ROLE_CHOICES = [
        (User.CUSTOMER, 'Customer'),
        (User.VENDOR, 'Vendor/Supplier'),
        (User.RIDER, 'Delivery Rider'),
    ]

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        role = request.POST.get('role', User.CUSTOMER)

        errors = []
        if not all([first_name, last_name, email, password]):
            errors.append('All required fields must be filled.')
        if password != password2:
            errors.append('Passwords do not match.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if User.objects.filter(email=email).exists():
            errors.append('An account with this email already exists.')
        if role not in [User.CUSTOMER, User.VENDOR, User.RIDER]:
            errors.append('Invalid account type.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'auth/register.html', {
                'role_choices': ROLE_CHOICES,
                'form_data': request.POST
            })

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=role,
            is_verified=False,
        )

        # Create role-specific profiles
        if role == User.CUSTOMER:
            CustomerProfile.objects.create(user=user)
            Cart.objects.create(user=user)
        elif role == User.VENDOR:
            business_name = request.POST.get('business_name', f"{first_name}'s Store")
            Vendor.objects.create(
                user=user,
                business_name=business_name,
                business_email=email,
                business_phone=phone,
                business_address=request.POST.get('business_address', ''),
                city=request.POST.get('city', ''),
                state=request.POST.get('state', ''),
            )
        elif role == User.RIDER:
            Rider.objects.create(
                user=user,
                vehicle_type=request.POST.get('vehicle_type', Rider.VEHICLE_MOTORCYCLE),
            )

        # Send verification email
        _send_verification_email(request, user)

        messages.success(request, 'Account created! Please check your email to verify your account.')
        return redirect('accounts:login')

    return render(request, 'auth/register.html', {'role_choices': ROLE_CHOICES})


def _send_verification_email(request, user):
    verify_url = request.build_absolute_uri(
        reverse('accounts:verify_email', args=[str(user.email_verification_token)])
    )
    try:
        send_mail(
            subject=f'Verify your {settings.PLATFORM_NAME} account',
            message=f'Hi {user.first_name},\n\nPlease verify your email by clicking:\n{verify_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=render_to_string('emails/verify_email.html', {
                'user': user,
                'verify_url': verify_url,
                'platform_name': settings.PLATFORM_NAME,
            }),
            fail_silently=True,
        )
    except Exception:
        pass


def verify_email_view(request, token):
    user = get_object_or_404(User, email_verification_token=token)
    if not user.is_verified:
        user.is_verified = True
        user.email_verification_token = uuid.uuid4()  # Invalidate token
        user.save(update_fields=['is_verified', 'email_verification_token'])
        messages.success(request, 'Email verified successfully! You can now log in.')
    else:
        messages.info(request, 'Email already verified.')
    return redirect('accounts:login')


@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect(get_dashboard_url(request.user))

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        remember = request.POST.get('remember_me')

        user = authenticate(request, username=email, password=password)

        if user is None:
            messages.error(request, 'Invalid email or password.')
            return render(request, 'auth/login.html', {'email': email})

        if not user.is_active:
            messages.error(request, 'Your account has been deactivated. Please contact support.')
            return render(request, 'auth/login.html', {'email': email})

        login(request, user)
        if not remember:
            request.session.set_expiry(0)

        next_url = request.GET.get('next', get_dashboard_url(user))
        messages.success(request, f'Welcome back, {user.first_name}!')
        return redirect(next_url)

    return render(request, 'auth/login.html')


@login_required
def logout_view(request):
    name = request.user.first_name
    logout(request)
    messages.success(request, f'Goodbye, {name}! You have been logged out.')
    return redirect('home:home')


@csrf_protect
def password_reset_request_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        try:
            user = User.objects.get(email=email)
            token = user.generate_password_reset_token()
            reset_url = request.build_absolute_uri(
                reverse('accounts:password_reset_confirm', args=[str(token)])
            )
            send_mail(
                subject=f'Password Reset - {settings.PLATFORM_NAME}',
                message=f'Hi {user.first_name},\n\nReset your password:\n{reset_url}\n\nThis link expires in 24 hours.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=render_to_string('emails/password_reset.html', {
                    'user': user,
                    'reset_url': reset_url,
                    'platform_name': settings.PLATFORM_NAME,
                }),
                fail_silently=True,
            )
        except User.DoesNotExist:
            pass  # Don't reveal whether email exists
        messages.success(request, 'If that email is registered, you will receive a password reset link shortly.')
        return redirect('accounts:login')
    return render(request, 'auth/password_reset_request.html')


@csrf_protect
def password_reset_confirm_view(request, token):
    user = get_object_or_404(User, password_reset_token=token)
    if not user.is_password_reset_token_valid():
        messages.error(request, 'This password reset link has expired. Please request a new one.')
        return redirect('accounts:password_reset_request')

    if request.method == 'POST':
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        elif password != password2:
            messages.error(request, 'Passwords do not match.')
        else:
            user.set_password(password)
            user.password_reset_token = None
            user.password_reset_expires = None
            user.save(update_fields=['password', 'password_reset_token', 'password_reset_expires'])
            messages.success(request, 'Password reset successfully! Please log in.')
            return redirect('accounts:login')

    return render(request, 'auth/password_reset_confirm.html', {'token': token})


@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name).strip()
        user.last_name = request.POST.get('last_name', user.last_name).strip()
        user.phone = request.POST.get('phone', user.phone).strip()
        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']
        user.save()

        if user.is_customer and hasattr(user, 'customer_profile'):
            profile = user.customer_profile
            profile.address = request.POST.get('address', '')
            profile.city = request.POST.get('city', '')
            profile.state = request.POST.get('state', '')
            profile.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('accounts:profile')

    return render(request, 'auth/profile.html', {'user': user})
