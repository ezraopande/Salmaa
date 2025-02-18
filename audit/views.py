from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import AuditLog
from django.shortcuts import redirect


@login_required
def audit_logs(request):
    if request.user.role != "law_enforcement":
        return redirect('dashboard')

    logs = AuditLog.objects.all().order_by('-timestamp')
    return render(request, 'audit/logs.html', {'logs': logs})
