from django.contrib.auth.decorators import login_required

from users.models import User
from .models import Case
from django.shortcuts import render, redirect, get_object_or_404
from notifications.models import Notification
from audit.models import AuditLog  # Import the AuditLog model

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from audit.models import AuditLog  # Track assignments
from datetime import datetime
import calendar
from django.utils.dateparse import parse_date

from django.http import HttpResponse
from reportlab.pdfgen import canvas
import pandas as pd
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail

@login_required
def report_case(request):
    if request.method == "POST":
        description = request.POST["description"]
        evidence_file = request.FILES.get("evidence_file")

        case = Case.objects.create(reporter=request.user, description=description, evidence_file=evidence_file)

        # Notify law enforcement and providers
        recipients = User.objects.filter(role__in=["law_enforcement", "provider"]).values_list("email", flat=True)
        send_mail(
            "New GBV Case Reported",
            f"A new case has been reported by {request.user.username}. Please check the system for details.",
            "admin@sarn-gbv.org",
            list(recipients),
            fail_silently=False,
        )

        return redirect('case_list')

    return render(request, 'cases/report_case.html')



@login_required
def case_list(request):
    if request.user.role == "law_enforcement":
        cases = Case.objects.all()
    elif request.user.role == "provider":
        cases = Case.objects.filter(assigned_provider=request.user)
    else:
        cases = Case.objects.filter(reporter=request.user)
    return render(request, 'cases/case_list.html', {'cases': cases})

@login_required
def update_case_status(request, case_id):
    if request.user.role not in ["provider", "law_enforcement"]:
        return redirect('dashboard')

    case = get_object_or_404(Case, id=case_id)

    if request.method == "POST":
        new_status = request.POST["status"]
        case.status = new_status
        case.save()

        # Send notification to the case reporter
        Notification.objects.create(
            user=case.reporter,
            case=case,
            message=f"Your case status has been updated to '{new_status}'."
        )

        return redirect('case_list')

    return render(request, 'cases/update_case_status.html', {'case': case})



@login_required
def assign_case(request, case_id):
    if request.user.role != "law_enforcement":
        return redirect('dashboard')  # Restrict to law enforcement only

    case = get_object_or_404(Case, id=case_id)
    providers = User.objects.filter(role="provider")  # Fetch service providers

    if request.method == "POST":
        provider_id = request.POST["provider"]
        case.assigned_provider = get_object_or_404(User, id=provider_id)
        case.status = "under_investigation"
        case.save()

        # Log the assignment
        AuditLog.objects.create(
            user=request.user,
            action=f"Assigned case {case.id} to {case.assigned_provider.username}"
        )

        return redirect('case_list')

    return render(request, 'cases/assign_case.html', {'case': case, 'providers': providers})

def anonymous_report_case(request):
    if request.method == "POST":
        description = request.POST["description"]
        Case.objects.create(description=description, is_anonymous=True)
        return redirect('case_list')

    return render(request, 'cases/anonymous_report.html')






def case_statistics(request):
    if request.user.role not in ["law_enforcement", "provider"]:
        raise PermissionDenied("You are not authorized to view this report.")
    
    total_cases = Case.objects.count()
    return render(request, 'cases/statistics.html', {"total_cases": total_cases})




@login_required
def case_detail(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    return render(request, 'cases/case_detail.html', {'case': case})


@login_required
def export_case_report_pdf(request):
    if request.user.role not in ["law_enforcement", "provider"]:
        return redirect('dashboard')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="case_report.pdf"'
    p = canvas.Canvas(response)
    
    cases = Case.objects.all()
    
    y = 800
    p.drawString(100, y, "SARN GBV Case Report")
    y -= 30
    for case in cases:
        p.drawString(100, y, f"ID: {case.id}, Status: {case.status}, Date: {case.date_reported}")
        y -= 20
    
    p.showPage()
    p.save()
    return response

@login_required
def export_case_report_excel(request):
    if request.user.role not in ["law_enforcement", "provider"]:
        return redirect('dashboard')

    cases = Case.objects.values("id", "status", "date_reported")
    df = pd.DataFrame(list(cases))

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="case_report.xlsx"'
    df.to_excel(response, index=False)
    
    return response


@login_required
def admin_summary_report(request):
    if request.user.role != "law_enforcement":
        return redirect('dashboard')

    total_cases = Case.objects.count()
    total_survivors = User.objects.filter(role="survivor").count()
    total_providers = User.objects.filter(role="provider").count()

    resolved_cases = Case.objects.filter(status="closed").count()
    pending_cases = total_cases - resolved_cases

    return render(request, 'cases/admin_summary.html', {
        "total_cases": total_cases,
        "total_survivors": total_survivors,
        "total_providers": total_providers,
        "resolved_cases": resolved_cases,
        "pending_cases": pending_cases,
    })
