from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth.decorators import login_required
from users.views import dashboard, home_redirect, register, user_login, logout_user
from cases.views import (
    admin_summary_report, anonymous_report_case,case_detail, 
    case_statistics, export_case_report_excel, export_case_report_pdf, 
    report_case, case_list, AssignCaseView, ChangeCaseStatusView, 
    add_counseling_session, add_court_case, add_police_followup, upload_case_document,
    court_cases, counseling_sessions, police_followups, case_documents, delete_document
)
from communication.views import send_message
from notifications.views import notifications_list, mark_notification_as_read, mark_all_notifications_read, clear_all_notifications
from audit.views import audit_logs, export_audit_logs_excel, export_audit_logs_pdf

handler403 = 'sarn.views.custom_permission_denied'



urlpatterns = [
    path('admin/', admin.site.urls),

    # Publicly Accessible Paths
    path('', home_redirect, name='home'),
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', logout_user, name='logout'),

    # Dashboards
    path('dashboard/', login_required(dashboard), name='dashboard'),

    # Case Management
    path('report-case/', login_required(report_case), name='report_case'),
    path('cases/', login_required(case_list), name='case_list'),
    path('cases/<int:case_id>/', login_required(case_detail), name='case_detail'),  # ✅ FIXED: Added case_detail route
    path('assign-case/<int:pk>/', login_required(AssignCaseView.as_view()), name='assign_case'),
    path('change_status/<int:pk>/', login_required(ChangeCaseStatusView.as_view()), name='change_status'),
    path('add-counseling-session/<int:case_id>/', login_required(add_counseling_session), name='add_counseling_session'),
    path('add-court-case/<int:case_id>/', login_required(add_court_case), name='add_court_case'),
    path('add-police-followup/<int:case_id>/', login_required(add_police_followup), name='add_police_followup'),
    path('upload-case-document/<int:case_id>/', login_required(upload_case_document), name='upload_case_document'),
    path('court-cases/', login_required(court_cases), name='court_cases'),
    path('counseling-sessions/', login_required(counseling_sessions), name='counseling_sessions'),
    path('police-followups/', login_required(police_followups), name='police_followups'),
    path('case-documents/', login_required(case_documents), name='case_documents'),
    path('delete-document/<int:id>/', login_required(delete_document), name='delete-document'),

    # Notifications
    path('notifications/', login_required(notifications_list), name='notifications_list'),
    path('notifications/read/<int:notification_id>/', login_required(mark_notification_as_read), name='mark_notification_as_read'),
    path('notifications/read/all/', login_required(mark_all_notifications_read), name='mark_all_notifications_read'),
    path('notifications/clear/all/', login_required(clear_all_notifications), name='clear_all_notifications'),

    # Messaging
    path('send-message/', login_required(send_message), name='send_message'),

    # Reports & Audit Logs
    path('audit-logs/', login_required(audit_logs), name='audit_logs'),
    path('audit-logs/export/excel/', export_audit_logs_excel, name='export_audit_logs_excel'),
    path('audit-logs/export/pdf/', export_audit_logs_pdf, name='export_audit_logs_pdf'),
    path('admin-summary/', login_required(admin_summary_report), name='admin_summary_report'),
    path('case-statistics/', login_required(case_statistics), name='case_statistics'),

    # Report Exports
    path('export/pdf/', login_required(export_case_report_pdf), name='export_case_report_pdf'),
    path('export/excel/', login_required(export_case_report_excel), name='export_case_report_excel'),

    # Anonymous Reports
    path('anonymous-report/', login_required(anonymous_report_case), name='anonymous_report_case'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)