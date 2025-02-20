from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from cases.models import Case
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

    if request.user.role == "survivor":
        # Get survivor's cases
        user_cases = Case.objects.filter(reporter=request.user)
        
        context.update({
            'pending_count': user_cases.filter(status='pending').count(),
            'investigation_count': user_cases.filter(status='under_investigation').count(),
            'closed_count': user_cases.filter(status='closed').count(),
            'recent_cases': user_cases.order_by('-date_reported')[:5],
            'user_role': 'survivor',
            'total_cases': user_cases.count(),
            
            # Additional survivor-specific statistics
            'latest_case_status': user_cases.order_by('-date_reported').first().get_status_display() if user_cases.exists() else None,
            'cases_this_month': user_cases.filter(
                date_reported__month=timezone.now().month,
                date_reported__year=timezone.now().year
            ).count()
        })

    elif request.user.role == "provider":
        # Get cases assigned to provider
        assigned_cases = Case.objects.filter(assigned_provider=request.user)
        
        context.update({
            'pending_count': assigned_cases.filter(status='pending').count(),
            'investigation_count': assigned_cases.filter(status='under_investigation').count(),
            'closed_count': assigned_cases.filter(status='closed').count(),
            'recent_cases': assigned_cases.order_by('-date_reported')[:5],
            'user_role': 'provider',
            'total_cases': assigned_cases.count(),
            
            # Additional provider-specific statistics
            'cases_requiring_attention': assigned_cases.filter(
                status='under_investigation',
                date_reported__lte=timezone.now() - timedelta(days=7)
            ).count(),
            'cases_closed_this_month': assigned_cases.filter(
                status='closed',
                date_reported__month=timezone.now().month,
                date_reported__year=timezone.now().year
            ).count()
        })

    elif request.user.role == "law_enforcement":
        # Get all cases for law enforcement
        all_cases = Case.objects.all()
        
        context.update({
            'pending_count': all_cases.filter(status='pending').count(),
            'investigation_count': all_cases.filter(status='under_investigation').count(),
            'closed_count': all_cases.filter(status='closed').count(),
            'recent_cases': all_cases.order_by('-date_reported')[:5],
            'user_role': 'law_enforcement',
            'total_cases': all_cases.count(),
            
            # Additional law enforcement-specific statistics
            'cases_by_status': all_cases.values('status').annotate(count=Count('status')),
            'cases_by_provider': Case.objects.exclude(assigned_provider=None)
                .values('assigned_provider__username')
                .annotate(count=Count('id')),
            'unassigned_cases': all_cases.filter(assigned_provider=None).count()
        })
    else:
        context.update({
            'error': "Invalid role.",
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
        role = request.POST["role"]
        phone = request.POST.get("phone", "")
        address = request.POST.get("address", "")
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]

        # Check if passwords match
        if password1 != password2:
            return render(request, 'users/register.html', {'error': "Passwords do not match"})

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return render(request, 'users/register.html', {'error': "Username already taken. Choose another."})

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return render(request, 'users/register.html', {'error': "Email already registered. Use a different email."})

        # Create the user and hash the password
        user = User(username=username, email=email, role=role, phone=phone, address=address)
        user.set_password(password1)  # Correctly hash the password
        user.save()
        print('--------------------saved---------------')

        # Authenticate and log in the user
        user = authenticate(request, username=username, password=password1)
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Redirect to dashboard

    return render(request, 'users/register.html')


def user_login(request):

    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            # Redirect to the next page if available, otherwise go to dashboard
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            return render(request, 'users/login.html', {'error': "Invalid username or password"})

    return render(request, 'users/login.html')

def logout_user(request):
    logout(request) 
    return redirect('login')

@login_required
def admin_dashboard(request):
    if request.user.role != "law_enforcement":
        return redirect('dashboard')  # Only allow law enforcement access

    total_cases = Case.objects.count()
    resolved_cases = Case.objects.filter(status="closed").count()
    pending_cases = Case.objects.filter(status="pending").count()

    # Cases grouped by status for chart display
    cases_by_status = list(
        Case.objects.values('status')
        .annotate(count=Count('id'))
    )

    return render(request, 'users/admin_dashboard.html', {
        "total_cases": total_cases,
        "resolved_cases": resolved_cases,
        "pending_cases": pending_cases,
        "cases_by_status": cases_by_status,
        "cases": Case.objects.all()  # Show all cases to law enforcement
    })

    if request.user.role != "law_enforcement":
        return redirect('dashboard')  # Only law enforcement can access

    total_cases = Case.objects.count()
    resolved_cases = Case.objects.filter(status="closed").count()
    pending_cases = Case.objects.filter(status="pending").count()

    # Cases grouped by status for the chart
    cases_by_status = list(
        Case.objects.values('status')
        .annotate(count=Count('id'))
    )

    return render(request, 'users/admin_dashboard.html', {
        "total_cases": total_cases,
        "resolved_cases": resolved_cases,
        "pending_cases": pending_cases,
        "cases_by_status": cases_by_status
    })