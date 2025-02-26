from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from cases.models import Case, LawEnforcementAssignment
from django.contrib import messages
from notifications.models import Notification
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .models import User


@login_required
def dashboard(request):
    # Common context for all users
    context = {
        'unread_notifications_count': Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
    }
    
    print(request.user.role)
    
    if request.user.role == "survivor":
        # Get survivor's incidents
        user_incidents = Case.objects.filter(survivor=request.user)
        context.update({
            'pending_count': user_incidents.filter(status='reported').count(),
            'investigation_count': user_incidents.filter(status__in=['under_investigation', 'medical_examination', 'legal_proceedings']).count(),
            'closed_count': user_incidents.filter(status='closed').count(),
            'recent_cases': user_incidents.order_by('-report_date')[:5],
            'user_role': 'survivor',
            'total_cases': user_incidents.count(),
            # Additional survivor-specific statistics
            'latest_case_status': user_incidents.order_by('-report_date').first().get_status_display() if user_incidents.exists() else None,
            'cases_this_month': user_incidents.filter(
                report_date__month=timezone.now().month,
                report_date__year=timezone.now().year
            ).count()
        })
    elif request.user.role == "law_enforcement":
        # Get cases where the officer is assigned
        assigned_cases = Case.objects.filter(assigned_officer=request.user)
        law_assignments = LawEnforcementAssignment.objects.filter(officer=request.user)
        context.update({
            'pending_count': assigned_cases.filter(status='reported').count(),
            'investigation_count': assigned_cases.filter(status__in=['under_investigation', 'medical_examination', 'legal_proceedings']).count(),
            'closed_count': assigned_cases.filter(status='closed').count(),
            'recent_cases': assigned_cases.order_by('-report_date')[:5],
            'user_role': 'provider',  # Keep 'provider' for template compatibility
            'total_cases': assigned_cases.count(),
            # Additional provider-specific statistics
            'cases_requiring_attention': assigned_cases.filter(
                status__in=['reported', 'under_investigation'],
                report_date__lte=timezone.now() - timedelta(days=7)
            ).count(),
            'cases_closed_this_month': assigned_cases.filter(
                status='closed',
                updated_at__month=timezone.now().month,
                updated_at__year=timezone.now().year
            ).count(),
            'assigned_to_me_count': law_assignments.count()
        })
    elif request.user.role == "officer":
        # Get all incidents for law enforcement
        all_incidents = Case.objects.all()
        
        context.update({
            'pending_count': all_incidents.filter(status='reported').count(),
            'investigation_count': all_incidents.filter(status__in=['under_investigation', 'medical_examination', 'legal_proceedings']).count(),
            'closed_count': all_incidents.filter(status='closed').count(),
            'recent_cases': all_incidents.order_by('-report_date')[:5],
            'user_role': 'sgbv_officer',
            'total_cases': all_incidents.count(),
            # Additional law enforcement-specific statistics
            'cases_by_status': all_incidents.values('status').annotate(count=Count('status')),
            'cases_by_provider': Case.objects.exclude(assigned_officer=None)
                .values('assigned_officer__username')
                .annotate(count=Count('id')),
            'unassigned_cases': all_incidents.filter(assigned_officer=None).count()
        })
    elif request.user.role == "medical_examiner":
        # Get cases for medical examiner (cases in medical examination status)
        medical_cases = Case.objects.filter(status='medical_examination')
        context.update({
            'pending_count': medical_cases.filter(status='reported').count(),
            'investigation_count': medical_cases.count(),
            'closed_count': Case.objects.filter(status='closed').count(),
            'recent_cases': medical_cases.order_by('-report_date')[:5],
            'user_role': 'medical_examiner',
            'total_cases': medical_cases.count()
        })
    else:
        context.update({
            'error': "Invalid user type.",
            'user_role': 'unknown'
        })
    
    return render(request, 'users/dashboard.html', context)
def home_redirect(request):
  
    if request.user.is_authenticated:
        return redirect('dashboard')  # Redirect to dashboard if logged in
    else:
        return redirect('login')  # Redirect to login if not logged in

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        phone = request.POST.get("phone", "")
        address = request.POST.get("address", "")
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]

        # Check if passwords match
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'users/register.html')

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'users/register.html')

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return render(request, 'users/register.html')

        # Create the user and hash the password
        user = User(username=username, email=email, phone=phone, address=address)
        user.set_password(password1)
        user.save()
        
        messages.success(request, "Account created successfully.")

        # Authenticate and log in the user
        user = authenticate(request, username=username, password=password1)
        if user is not None:
            login(request, user)
            return redirect('dashboard')

    return render(request, 'users/register.html')


def user_login(request):

    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Logged in successfully.")
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, 'users/login.html')

    return render(request, 'users/login.html')

def logout_user(request):
    logout(request) 
    return redirect('login')
