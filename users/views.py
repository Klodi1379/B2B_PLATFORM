from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import login, authenticate, update_session_auth_hash, logout
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import User
from .forms import UserRegistrationForm, UserProfileForm

@login_required
def dashboard(request):
    """
    Main dashboard view - redirects to the appropriate dashboard based on user type
    """
    user = request.user

    if user.is_supplier:
        return redirect('suppliers:dashboard')
    elif user.is_shop:
        return redirect('shops:dashboard')
    elif user.is_driver:
        return redirect('delivery:driver_today')
    else:
        # Default to admin dashboard or handle other user types
        return render(request, 'users/dashboard.html')

@login_required
def profile(request):
    """
    Display user profile information
    """
    return render(request, 'users/profile.html')

@login_required
def profile_edit(request):
    """
    Edit user profile information
    """
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Your profile has been updated successfully.'))
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'users/profile_edit.html', {'form': form})

def register(request):
    """
    Main registration page where user selects account type
    """
    return render(request, 'users/register.html')

def register_user_type(request, user_type):
    """
    Register a new user with a specific user type
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = user_type.upper()
            user.save()

            # Log the user in
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)

            messages.success(request, _('Your account has been created successfully.'))
            return redirect('users:dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'users/register_form.html', {
        'form': form,
        'user_type': user_type
    })

def activate(request, uidb64, token):
    """
    Activate a user account using the activation link
    """
    # Placeholder for account activation logic
    return redirect('users:dashboard')

@login_required
def password_change(request):
    """
    Change user password
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, _('Your password has been changed successfully.'))
            return redirect('users:profile')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'users/password_change.html', {'form': form})

def password_reset(request):
    """
    Request password reset
    """
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            # Process password reset
            messages.success(request, _('Password reset instructions have been sent to your email.'))
            return redirect('users:password_reset_done')
    else:
        form = PasswordResetForm()

    return render(request, 'users/password_reset.html', {'form': form})

def password_reset_done(request):
    """
    Password reset request confirmation
    """
    return render(request, 'users/password_reset_done.html')

def password_reset_confirm(request, uidb64, token):
    """
    Confirm password reset and set new password
    """
    # Placeholder for password reset confirmation logic
    return render(request, 'users/password_reset_confirm.html')

def password_reset_complete(request):
    """
    Password reset completion
    """
    return render(request, 'users/password_reset_complete.html')

def logout_view(request):
    """
    Custom logout view that accepts both GET and POST requests
    """
    logout(request)
    messages.success(request, _('You have been logged out successfully.'))
    return HttpResponseRedirect(reverse('common:home'))

@login_required
def admin_dashboard(request):
    """
    Admin dashboard view with overview of system
    """
    # Check if user is admin or staff
    if not (request.user.is_admin or request.user.is_staff):
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('users:dashboard')

    # Get counts for dashboard
    from suppliers.models import Supplier
    from shops.models import Shop
    from products.models import Product, Category
    from orders.models import Order

    context = {
        'user_count': User.objects.count(),
        'supplier_count': Supplier.objects.count(),
        'shop_count': Shop.objects.count(),
        'product_count': Product.objects.count(),
        'category_count': Category.objects.count(),
        'order_count': Order.objects.count(),

        # Recent users
        'recent_users': User.objects.all().order_by('-date_joined')[:10],

        # Recent orders
        'recent_orders': Order.objects.all().order_by('-created_at')[:10],
    }

    return render(request, 'users/admin_dashboard.html', context)
