from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import Notification

@login_required
def notifications_list(request):
    # Get base queryset
    queryset = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Get filters from request
    status = request.GET.get('status')
    date_range = request.GET.get('date_range')
    case_id = request.GET.get('case_id')
    
    # Apply status filter
    if status == 'unread':
        queryset = queryset.filter(is_read=False)
    elif status == 'read':
        queryset = queryset.filter(is_read=True)
    
    # Apply date range filter
    if date_range == 'today':
        queryset = queryset.filter(created_at__date=timezone.now().date())
    elif date_range == 'week':
        week_ago = timezone.now() - timedelta(days=7)
        queryset = queryset.filter(created_at__gte=week_ago)
    elif date_range == 'month':
        month_ago = timezone.now() - timedelta(days=30)
        queryset = queryset.filter(created_at__gte=month_ago)
    
    # Apply case filter
    if case_id:
        queryset = queryset.filter(case__id=case_id)
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(queryset, 10)  # Show 10 notifications per page
    
    try:
        notifications = paginator.page(page)
    except PageNotAnInteger:
        notifications = paginator.page(1)
    except EmptyPage:
        notifications = paginator.page(paginator.num_pages)
    
    # Get unread count for badge
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
        'status': status,
        'date_range': date_range,
        'case_id': case_id,
    }
    
    return render(request, 'notifications/list.html', context)

@login_required
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    messages.success(request, 'Notification marked as read.')
    return redirect('notifications_list')

@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('notifications_list')

@login_required
def clear_all_notifications(request):
    Notification.objects.filter(user=request.user).delete()
    messages.success(request, 'All notifications cleared.')
    return redirect('notifications_list')