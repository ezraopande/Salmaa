from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from django.contrib import messages
from django.db import transaction
from .forms import CaseAssignmentForm, CounselingSessionForm, CourtCaseForm, PoliceFollowUpForm, StatusChangeForm
from users.models import User
from .models import Case, CaseDocument, CounselingSession, CourtCase, PoliceFollowUp
from django.shortcuts import render, redirect, get_object_or_404
from notifications.models import Notification
from audit.models import AuditLog  # Import the AuditLog model
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from audit.models import AuditLog 
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db.models import Q
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
        '''send_mail(
            "New GBV Case Reported",
            f"A new case has been reported by {request.user.username}. Please check the system for details.",
            "admin@sarn-gbv.org",
            list(recipients),
            fail_silently=False,
        )'''
        messages.success(request, "Case reported successfully.")
        return redirect('case_list')

    return render(request, 'cases/report_case.html')



@login_required
def case_list(request):
    # Determine the cases based on the user's role
    if request.user.role == "law_enforcement":
        cases = Case.objects.all()
    elif request.user.role == "provider":
        cases = Case.objects.filter(assigned_provider=request.user)
    else:
        cases = Case.objects.filter(reporter=request.user)
        
    # Filter cases based on the query parameters
    status_filter = request.GET.get('status')  
    if status_filter:
        cases = cases.filter(status=status_filter)

    # Pagination
    paginator = Paginator(cases, 10)  # Show 10 cases per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Context to be passed to the template
    context = {
        'cases': page_obj,
        'status_choices': Case.STATUS_CHOICES,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }

    return render(request, 'cases/case_list.html', context)


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

class AssignCaseView(LoginRequiredMixin, UpdateView):
    model = Case
    form_class = CaseAssignmentForm
    template_name = 'cases/assign_case.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get all providers who can be assigned cases
        context['providers'] = self.get_available_providers()
        context['case'] = self.get_object()
        return context
    
    def get_available_providers(self):
        return User.objects.filter(role='provider', is_active=True)
    
    def form_valid(self, form):
        case = self.get_object()
        provider = form.cleaned_data['assigned_provider']
        notes = form.cleaned_data.get('notes', '')
        
        with transaction.atomic():
            # Update case assignment
            case.assigned_provider = provider
            if case.status == 'pending':
                case.status = 'under_investigation'
            case.save()
            
            # Create assignment record
            '''CaseAssignment.objects.create(
                case=case,
                provider=provider,
                assigned_by=self.request.user,
                notes=notes
            )'''
            
            # Optionally notify the provider
            self.notify_provider(case, provider)
        
        messages.success(self.request, f'Case #{case.id} has been assigned to {provider.get_full_name()}')
        return redirect('case_detail', case_id=case.id)
    
    def notify_provider(self, case, provider):
        Notification.objects.create(
            user=case.reporter,
            case=case,
            message=f"Your case has been assigned to {provider.username}."
        )
        
        Notification.objects.create(
            user=provider,
            case=case,
            message=f"You have been assigned to case #{case.id}."
        )
        
        AuditLog.objects.create(
            user=self.request.user,
            action=f"assigned case {case.id} to {provider.username}"
        )

class ChangeCaseStatusView(LoginRequiredMixin, UpdateView):
    model = Case
    form_class = StatusChangeForm
    template_name = 'cases/update_case_status.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['case'] = self.get_object()
        context['status_choices'] = Case.STATUS_CHOICES
        # context['status_history'] = self.get_status_history()
        return context
    
    def form_valid(self, form):
        case = self.get_object()
        new_status = form.cleaned_data['status']
        notes = form.cleaned_data['status_notes']
        notify_reporter = form.cleaned_data.get('notify_reporter', False)
        
        with transaction.atomic():
            
            # Update case status
            case.status = new_status
            case.save()
            
            if notify_reporter:
                self.notify_reporter(case, new_status, notes)
        
        messages.success(self.request, f'Status for Case #{case.id} has been updated to {case.get_status_display()}')
        return redirect('case_detail', case_id=case.id)
    
    def notify_reporter(self, case, new_status, notes):
        Notification.objects.create(
            user=case.reporter,
            case=case,
            message=f"Your case status has been updated to '{new_status}'."
        )
        
        AuditLog.objects.create(
            user=self.request.user,
            action=f"changed case {case.id} status to {case.status}"
        )


@login_required
def case_detail(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    context = {
        'case': case,
        'counseling_sessions': CounselingSession.objects.filter(survivor=case.reporter).order_by('-session_date'),
        'court_cases': CourtCase.objects.filter(case=case).order_by('-hearing_date'),
        'documents': CaseDocument.objects.filter(case=case).order_by('-uploaded_at'),
        'follow_ups': PoliceFollowUp.objects.filter(case=case).order_by('-date_updated'),
    }
    return render(request, 'cases/case_detail.html', context)

@login_required
def add_counseling_session(request, case_id):
    if request.user.role != 'provider':
        raise PermissionDenied("Only providers can add counseling sessions")
    
    case = get_object_or_404(Case, id=case_id)
    
    if request.method == 'POST':
        form = CounselingSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.counselor = request.user
            session.survivor = case.reporter
            session.save()
            Notification.objects.create(
                case = case,
                user = case.reporter,
                message = f"A counseling session has been scheduled for you on {session.session_date} by {request.user.get_username()}."
            )
            AuditLog.objects.create(
                user = request.user,
                action = f"added counseling session for case {case.id}"
            )
            messages.success(request, 'Counseling session added successfully')
            return redirect('case_detail', case_id=case_id)
    else:
        form = CounselingSessionForm()
    
    return render(request, 'cases/add_counseling_session.html', {'form': form, 'case': case})

@login_required
def add_court_case(request, case_id):
    if request.user.role != 'law_enforcement':
        raise PermissionDenied("Only law enforcement can add court cases")
    
    case = get_object_or_404(Case, id=case_id)
    
    if request.method == 'POST':
        form = CourtCaseForm(request.POST)
        if form.is_valid():
            court_case = form.save(commit=False)
            court_case.case = case
            court_case.save()
            Notification.objects.create(
                case = case,
                user = case.reporter,
                message = f"A court case has been scheduled for you on {court_case.hearing_date} by {request.user.get_username()}."
            )
            AuditLog.objects.create(    
                user = request.user,
                action = f"added court case for case {case.id}"
            )
            messages.success(request, 'Court case added successfully')
            return redirect('case_detail', case_id=case_id)
    else:
        form = CourtCaseForm()
    
    return render(request, 'cases/add_court_case.html', {'form': form, 'case': case})

@login_required
def add_police_followup(request, case_id):
    if request.user.role != 'law_enforcement':
        messages.error(request, "Only law enforcement")
        raise PermissionDenied("Only law enforcement can add follow-ups")
    
    case = get_object_or_404(Case, id=case_id)
    
    if request.method == 'POST':
        form = PoliceFollowUpForm(request.POST)
        if form.is_valid():
            followup = form.save(commit=False)
            followup.case = case
            followup.officer = request.user
            followup.save()
            Notification.objects.create(
                case = case,
                user = case.reporter,
                message = f"A follow-up has been scheduled for you on {followup.date_updated} by {request.user.get_username()}."
            )
            AuditLog.objects.create(
                user = request.user,
                action = f"added follow-up for case {case.id}"
            )
            messages.success(request, 'Follow-up added successfully')
            return redirect('case_detail', case_id=case_id)
    else:
        form = PoliceFollowUpForm()
    
    return render(request, 'cases/add_followup.html', {'form': form, 'case': case})

@login_required
def upload_case_document(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    
    if request.method == 'POST' and request.FILES.get('document'):
        document = CaseDocument(
            case=case,
            document=request.FILES['document'],
            title = request.POST['title'],
            uploaded_by = request.user
        )
        document.save()
        AuditLog.objects.create(
            user = request.user,
            action = f"uploaded document for case {case.id}"
        )
        messages.success(request, 'Document uploaded successfully')
        return redirect('case_detail', case_id=case_id)
    
    return render(request, 'cases/upload_document.html', {'case': case})

@login_required
def court_cases(request):
    court_cases = CourtCase.objects.all()
    return render(request, 'cases/court_cases.html', {'court_cases': court_cases})

@login_required
def counseling_sessions(request):
    if request.user.role == 'provider':
        sessions = CounselingSession.objects.filter(counselor=request.user).order_by('-session_date')
    elif request.user.role == 'survivor':
        sessions = CounselingSession.objects.filter(survivor=request.user).order_by('-session_date')
    else:
        sessions = []
    
    paginator = Paginator(sessions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'cases/counseling_sessions.html', {'page_obj': page_obj, 'now' : now()})

@login_required
def police_followups(request):
    now = timezone.now()
    
    # Filter based on user role
    if request.user.role == 'law_enforcement':
        # Police officers see followups they created
        followups = PoliceFollowUp.objects.filter(
            officer=request.user
        ).select_related('case', 'officer').order_by('-date_updated')
    elif request.user.role == 'survivor':
        # Survivors see followups related to their cases
        followups = PoliceFollowUp.objects.filter(
            case__survivor=request.user
        ).select_related('case', 'officer').order_by('-date_updated')
    elif request.user.role == 'provider':
        # Service providers see followups for cases they're involved with
        followups = PoliceFollowUp.objects.filter(
            case__counseling_sessions__counselor=request.user
        ).distinct().select_related('case', 'officer').order_by('-date_updated')
    else:
        followups = PoliceFollowUp.objects.none()

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        followups = followups.filter(
            Q(case__id__icontains=search_query) |
            Q(update_details__icontains=search_query) |
            Q(officer__username__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(followups, 9)  # Show 9 followups per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'now': now,
    }
    
    return render(request, 'cases/police_followups.html', context)

@login_required
def case_documents(request):
    # Filter based on user role
    if request.user.role == 'law_enforcement':
        # Police officers see all documents for cases they're involved with
        documents = CaseDocument.objects.filter(
            Q(case__follow_ups__officer=request.user)
        ).distinct()
    elif request.user.role == 'survivor':
        # Survivors see documents from their cases
        documents = CaseDocument.objects.filter(
            case__survivor=request.user
        )
    elif request.user.role == 'provider':
        # Service providers see documents for cases they're counseling
        documents = CaseDocument.objects.filter(
            case__assigned_provider=request.user
        ).distinct()
    else:
        documents = CaseDocument.objects.none()

    # Filter by document type
    doc_type = request.GET.get('type')
    if doc_type:
        documents = documents.filter(document_type=doc_type)

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        documents = documents.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(case__id__icontains=search_query)
        )

    # Sort functionality
    sort_by = request.GET.get('sort', '-uploaded_at')
    documents = documents.order_by(sort_by)

    # Pagination
    paginator = Paginator(documents, 12)  # Show 12 documents per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'current_type': doc_type,
        'sort_by': sort_by
    }
    
    return render(request, 'cases/case_documents.html', context)

def delete_document(request, id):
    case_document = get_object_or_404(CaseDocument,id = id)
    case_document.delete()
    messages.success(request, "The document was deleted successfully")
    AuditLog.objects.create(
        user = request.user,
        action = f"deleted document for case {case_document.case.id}"
    )
    return redirect('/case-documents/')