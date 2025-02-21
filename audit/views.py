from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import csv
from datetime import datetime
from .models import AuditLog
from users.models import User

@login_required
def audit_logs(request):
    if request.user.role != "law_enforcement":
        return redirect('dashboard')

    # Get all users for the filter dropdown
    users = User.objects.all().order_by('username')

    # Initialize the queryset
    queryset = AuditLog.objects.all().order_by('-timestamp')

    # Apply filters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    user_filter = request.GET.get('user')

    if date_from:
        date_from = parse_date(date_from)
        queryset = queryset.filter(timestamp__date__gte=date_from)

    if date_to:
        date_to = parse_date(date_to)
        queryset = queryset.filter(timestamp__date__lte=date_to)

    if user_filter:
        queryset = queryset.filter(user_id=user_filter)

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(queryset, 10)  # Show 10 logs per page

    try:
        audit_logs = paginator.page(page)
    except PageNotAnInteger:
        audit_logs = paginator.page(1)
    except EmptyPage:
        audit_logs = paginator.page(paginator.num_pages)

    context = {
        'audit_logs': audit_logs,
        'users': users,
        'selected_user': user_filter,
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'audit/logs.html', context)

@login_required
def export_audit_logs_excel(request):
    if request.user.role != "law_enforcement":
        return redirect('dashboard')

    # Apply the same filters as the main view
    queryset = AuditLog.objects.all().order_by('-timestamp')
    
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    user_filter = request.GET.get('user')

    if date_from:
        date_from = parse_date(date_from)
        queryset = queryset.filter(timestamp__date__gte=date_from)

    if date_to:
        date_to = parse_date(date_to)
        queryset = queryset.filter(timestamp__date__lte=date_to)

    if user_filter:
        queryset = queryset.filter(user_id=user_filter)

    # Create the HttpResponse object with Excel headers
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'

    # Create the CSV writer
    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'User', 'Role', 'Action'])

    # Write the data
    for log in queryset:
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.user.username,
            log.user.role,
            log.action
        ])

    return response

# Define custom colors matching your system theme
PRIMARY_COLOR = colors.HexColor('#6c63ff')  # Your primary color
SECONDARY_COLOR = colors.HexColor('#5a52cc')  # Darker shade for accents
LIGHT_PRIMARY = colors.HexColor('#8c85ff')  # Lighter shade for backgrounds

@login_required
def export_audit_logs_pdf(request):
    if request.user.role != "law_enforcement":
        return redirect('dashboard')

    # Apply filters (same as before)
    queryset = AuditLog.objects.all().order_by('-timestamp')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    user_filter = request.GET.get('user')

    if date_from:
        date_from = parse_date(date_from)
        queryset = queryset.filter(timestamp__date__gte=date_from)
    if date_to:
        date_to = parse_date(date_to)
        queryset = queryset.filter(timestamp__date__lte=date_to)
    if user_filter:
        queryset = queryset.filter(user_id=user_filter)

    # Create response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="SARN_GBV_audit_logs_{datetime.now().strftime("%Y%m%d")}.pdf"'

    # Create the PDF document
    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    # Create story to hold the elements
    elements = []

    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=PRIMARY_COLOR,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Custom subtitle style
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=SECONDARY_COLOR,
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    # Date style
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.grey,
        alignment=TA_RIGHT,
        spaceAfter=20
    )

    # Create and add logo
    # Using a placeholder SVG logo
    logo_svg = '''
    <svg width="100" height="100" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="45" fill="#6c63ff" opacity="0.2"/>
        <circle cx="50" cy="50" r="35" fill="#6c63ff" opacity="0.4"/>
        <circle cx="50" cy="50" r="25" fill="#6c63ff"/>
        <text x="50" y="55" font-family="Arial" font-size="16" fill="white" text-anchor="middle">SARN</text>
    </svg>
    '''
    
    # Add logo as SVG
    elements.append(Paragraph(f'<svg>{logo_svg}</svg>', ParagraphStyle('Logo', alignment=TA_CENTER)))
    elements.append(Spacer(1, 20))

    # Add title
    elements.append(Paragraph("SARN GBV Management System", title_style))
    elements.append(Paragraph("Audit Log Report", subtitle_style))
    
    # Add date
    elements.append(Paragraph(
        f"Generated on: {datetime.now().strftime('%B %d, %Y %H:%M')}",
        date_style
    ))

    # Add filter information if filters are applied
    if date_from or date_to or user_filter:
        filter_text = "Filters applied: "
        if date_from:
            filter_text += f"From {date_from.strftime('%Y-%m-%d')} "
        if date_to:
            filter_text += f"To {date_to.strftime('%Y-%m-%d')} "
        if user_filter:
            user = User.objects.get(id=user_filter)
            filter_text += f"User: {user.username}"
        
        elements.append(Paragraph(filter_text, styles['Italic']))
        elements.append(Spacer(1, 20))

    # Prepare table data
    data = [['Timestamp', 'User', 'Role', 'Action']]
    for log in queryset:
        data.append([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.user.username,
            log.user.role.title(),
            log.action
        ])

    # Create table
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Row styling
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        
        # Grid styling
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LINEBEFORE', (0, 0), (0, -1), 1, colors.black),
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.grey),
        
        # Alternate row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_PRIMARY]),
        
        # Column widths
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    elements.append(table)

    # Build PDF
    doc.build(elements)
    return response