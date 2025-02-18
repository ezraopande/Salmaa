from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Notification
from django.shortcuts import redirect, get_object_or_404

@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    return render(request, 'notifications/list.html', {'notifications': notifications})




@login_required
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications_list')
