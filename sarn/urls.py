from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth.decorators import login_required
from users.views import admin_dashboard, dashboard, home_redirect, register, user_login, logout_user
from cases.views import (
    admin_summary_report, anonymous_report_case,case_detail, 
    case_statistics, export_case_report_excel, export_case_report_pdf, 
    report_case, case_list, AssignCaseView, ChangeCaseStatusView
)
from communication.views import send_message
from notifications.views import notifications_list, mark_notification_as_read
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
    path('admin-dashboard/', login_required(admin_dashboard), name='admin_dashboard'),

    # Case Management
    path('report-case/', login_required(report_case), name='report_case'),
    path('cases/', login_required(case_list), name='case_list'),
    path('cases/<int:case_id>/', login_required(case_detail), name='case_detail'),  # ✅ FIXED: Added case_detail route
    path('assign-case/<int:pk>/', login_required(AssignCaseView.as_view()), name='assign_case'),
    path('change_status/<int:pk>/', login_required(ChangeCaseStatusView.as_view()), name='change_status'),

    # Notifications
    path('notifications/', login_required(notifications_list), name='notifications_list'),
    path('notifications/read/<int:notification_id>/', login_required(mark_notification_as_read), name='mark_notification_as_read'),

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