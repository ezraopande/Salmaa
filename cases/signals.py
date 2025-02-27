from django.db.models.signals import post_save, post_init
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import (
    Case, 
    LawEnforcementAssignment, 
    CaseDocument, 
    CounselingSession,
    CourtCase,
    PoliceFollowUp,
)
from users.models import User
from notifications.models import Notification
from audit.models import AuditLog


# Helper function to send email notifications
def send_notification_email(subject, message, recipient_list):
    """
    Helper function to send email notifications
    """
    from_email = settings.DEFAULT_FROM_EMAIL
    
    # send_mail(
    #     subject=subject,
    #     message=message,
    #     from_email=from_email,
    #     recipient_list=recipient_list,
    #     fail_silently=False,
    # )

# Helper function to create notifications
def create_notification(user, case, message):
    """
    Create a notification record in the database
    """
    Notification.objects.create(
        user=user,
        case=case,
        message=message
    )

# Helper function to create audit logs
def create_audit_log(user, action):
    """
    Create an audit log entry
    """
    AuditLog.objects.create(
        user=user,
        action=action
    )

# Track original status for Case model
@receiver(post_init, sender=Case)
def store_original_status(sender, instance, **kwargs):
    """
    Store the original status when a Case instance is loaded
    """
    instance._original_status = instance.status if instance.pk else None

# Case Creation Signal
@receiver(post_save, sender=Case)
def case_post_save(sender, instance, created, **kwargs):
    """
    Signal to handle actions after a Case is created or updated
    """
    # When a new case is created
    if created:
        # Create audit log for case creation
        create_audit_log(
            user=instance.survivor,
            action=f"Created new case #{instance.case_number} of type {instance.get_incident_type_display()}"
        )
        
        # Notify law enforcement officers
        law_enforcement_users = User.objects.filter(role='law_enforcement')
        
        # Create notifications for each officer
        for officer in law_enforcement_users:
            message = f"New case #{instance.case_number} has been reported. Incident type: {instance.get_incident_type_display()}"
            create_notification(
                user=officer,
                case=instance,
                message=message
            )
            
            # Send email notifications to officers
            subject = f"New SGBV Case Reported - #{instance.case_number}"
            email_message = f"""
            Dear {officer.get_full_name() or officer.username},
            
            A new SGBV case has been reported and requires attention.
            
            Case Number: {instance.case_number}
            Incident Type: {instance.get_incident_type_display()}
            Date Reported: {timezone.now().strftime('%Y-%m-%d %H:%M')}
            
            Please log in to the system to view more details and take appropriate action.
            
            This is an automated message. Please do not reply.
            """
            
            send_notification_email(
                subject=subject,
                message=email_message,
                recipient_list=[officer.email]
            )
    
    # Check if status has changed
    if hasattr(instance, '_original_status') and instance._original_status != instance.status:
        # Create audit log for status change
        create_audit_log(
            user=instance.assigned_officer or instance.survivor,  # Use assigned officer if available, otherwise use survivor
            action=f"Changed case #{instance.case_number} status from {dict(Case.STATUS_CHOICES).get(instance._original_status)} to {dict(Case.STATUS_CHOICES).get(instance.status)}"
        )
        
        # Notify the survivor of the status change
        message = f"Your case #{instance.case_number} status has been updated to {dict(Case.STATUS_CHOICES).get(instance.status)}"
        create_notification(
            user=instance.survivor,
            case=instance,
            message=message
        )
        
        # Send email notification to survivor
        subject = f"Update on Your Case - #{instance.case_number}"
        email_message = f"""
        Dear {instance.survivor.get_full_name() or instance.survivor.username},
        
        There has been an update to your case.
        
        Case Number: {instance.case_number}
        New Status: {dict(Case.STATUS_CHOICES).get(instance.status)}
        
        Please log in to the system for more details.
        
        This is an automated message. Please do not reply.
        """
        
        send_notification_email(
            subject=subject,
            message=email_message,
            recipient_list=[instance.survivor.email]
        )
    
    # Update the original status
    instance._original_status = instance.status

# Law Enforcement Assignment Signal
@receiver(post_save, sender=LawEnforcementAssignment)
def law_enforcement_assignment_post_save(sender, instance, created, **kwargs):
    """
    Signal to handle actions after a LawEnforcementAssignment is created or updated
    """
    case = instance.case
    officer = instance.officer
    
    if created:
        # Create audit log for assignment
        create_audit_log(
            user=officer,
            action=f"Officer {officer.get_full_name() or officer.username} assigned to case #{case.case_number}"
        )
        
        # Notify the survivor
        message = f"Officer {officer.get_full_name() or officer.username} has been assigned to your case #{case.case_number}"
        create_notification(
            user=case.survivor,
            case=case,
            message=message
        )
        
        # Send email notification to survivor
        subject = f"Officer Assigned to Your Case - #{case.case_number}"
        email_message = f"""
        Dear {case.survivor.get_full_name() or case.survivor.username},
        
        An officer has been assigned to your case.
        
        Case Number: {case.case_number}
        Officer: {officer.get_full_name() or officer.username}
        
        Please log in to the system for more details.
        
        This is an automated message. Please do not reply.
        """
        
        send_notification_email(
            subject=subject,
            message=email_message,
            recipient_list=[case.survivor.email]
        )
    else:
        # Create audit log for status update
        create_audit_log(
            user=officer,
            action=f"Updated law enforcement assignment status for case #{case.case_number} to {dict(LawEnforcementAssignment.STATUS_CHOICES).get(instance.status)}"
        )
        
        # Notify the survivor
        message = f"Your case #{case.case_number} investigation status has been updated to {dict(LawEnforcementAssignment.STATUS_CHOICES).get(instance.status)}"
        create_notification(
            user=case.survivor,
            case=case,
            message=message
        )
        
        # Send email notification to survivor
        subject = f"Investigation Update on Your Case - #{case.case_number}"
        email_message = f"""
        Dear {case.survivor.get_full_name() or case.survivor.username},
        
        There has been an update to the investigation of your case.
        
        Case Number: {case.case_number}
        Investigation Status: {dict(LawEnforcementAssignment.STATUS_CHOICES).get(instance.status)}
        
        Please log in to the system for more details.
        
        This is an automated message. Please do not reply.
        """
        
        send_notification_email(
            subject=subject,
            message=email_message,
            recipient_list=[case.survivor.email]
        )

# Case Document Signal
@receiver(post_save, sender=CaseDocument)
def case_document_post_save(sender, instance, created, **kwargs):
    """
    Signal to handle actions after a CaseDocument is created
    """
    if created:
        case = instance.case
        uploader = instance.uploaded_by
        
        # Create audit log
        create_audit_log(
            user=uploader,
            action=f"Added document '{instance.title}' to case #{case.case_number}"
        )
        
        # 1. Notify the survivor
        message = f"New document '{instance.title}' has been added to your case #{case.case_number}"
        create_notification(
            user=case.survivor,
            case=case,
            message=message
        )
        
        # Send email to survivor
        subject = f"New Document Added to Your Case - #{case.case_number}"
        email_message = f"""
        Dear {case.survivor.get_full_name() or case.survivor.username},
        
        A new document has been added to your case.
        
        Case Number: {case.case_number}
        Document Title: {instance.title}
        Uploaded By: {uploader.get_full_name() or uploader.username}
        
        Please log in to the system to view this document.
        
        This is an automated message. Please do not reply.
        """
        
        send_notification_email(
            subject=subject,
            message=email_message,
            recipient_list=[case.survivor.email]
        )
        
        # 2. Notify assigned officer if any
        if case.assigned_officer:
            # Skip if the uploader is the assigned officer
            if case.assigned_officer != uploader:
                message = f"New document '{instance.title}' has been added to case #{case.case_number}"
                create_notification(
                    user=case.assigned_officer,
                    case=case,
                    message=message
                )
                
                # Send email to assigned officer
                subject = f"New Document Added to Case - #{case.case_number}"
                email_message = f"""
                Dear {case.assigned_officer.get_full_name() or case.assigned_officer.username},
                
                A new document has been added to a case assigned to you.
                
                Case Number: {case.case_number}
                Document Title: {instance.title}
                Uploaded By: {uploader.get_full_name() or uploader.username}
                
                Please log in to the system to view this document.
                
                This is an automated message. Please do not reply.
                """
                
                send_notification_email(
                    subject=subject,
                    message=email_message,
                    recipient_list=[case.assigned_officer.email]
                )

# Counseling Session Signal
@receiver(post_save, sender=CounselingSession)
def counseling_session_post_save(sender, instance, created, **kwargs):
    """
    Signal to handle actions after a CounselingSession is created
    """
    if created:
        case = instance.case
        counselor = instance.counselor
        
        # Create audit log
        create_audit_log(
            user=counselor,
            action=f"Scheduled counseling session for case #{case.case_number} on {instance.session_date.strftime('%Y-%m-%d %H:%M')}"
        )
        
        # Notify the survivor
        message = f"A counseling session has been scheduled for your case #{case.case_number} on {instance.session_date.strftime('%Y-%m-%d %H:%M')}"
        create_notification(
            user=instance.survivor,
            case=case,
            message=message
        )
        
        # Send email notification to survivor
        subject = f"Counseling Session Scheduled - Case #{case.case_number}"
        email_message = f"""
        Dear {instance.survivor.get_full_name() or instance.survivor.username},
        
        A counseling session has been scheduled for your case.
        
        Case Number: {case.case_number}
        Counselor: {counselor.get_full_name() or counselor.username}
        Date & Time: {instance.session_date.strftime('%Y-%m-%d %H:%M')}
        
        Please log in to the system for more details.
        
        This is an automated message. Please do not reply.
        """
        
        send_notification_email(
            subject=subject,
            message=email_message,
            recipient_list=[instance.survivor.email]
        )

# Track original assigned officer for Case model
@receiver(post_init, sender=Case)
def store_original_assigned_officer(sender, instance, **kwargs):
    """
    Store the original assigned officer when a Case instance is loaded
    """
    instance._original_assigned_officer_id = instance.assigned_officer_id if instance.pk else None

# Signal to handle officer assignment in Case model
@receiver(post_save, sender=Case)
def case_officer_assignment(sender, instance, **kwargs):
    """
    Signal to handle officer assignment changes in the Case model
    """
    # Skip if this is a new case (already handled in case_post_save)
    if not instance.pk:
        return
    
    # Check if assigned officer has changed
    if hasattr(instance, '_original_assigned_officer_id') and instance._original_assigned_officer_id != instance.assigned_officer_id:
        # Get the new officer
        if instance.assigned_officer:
            # Create audit log for officer assignment
            create_audit_log(
                user=instance.assigned_officer,
                action=f"Officer {instance.assigned_officer.get_full_name() or instance.assigned_officer.username} assigned to case #{instance.case_number}"
            )
            
            # 1. Notify the assigned officer
            message = f"You have been assigned to case #{instance.case_number} - {instance.get_incident_type_display()}"
            create_notification(
                user=instance.assigned_officer,
                case=instance,
                message=message
            )
            
            # Send email to assigned officer
            subject = f"You Have Been Assigned to Case #{instance.case_number}"
            email_message = f"""
            Dear {instance.assigned_officer.get_full_name() or instance.assigned_officer.username},
            
            You have been assigned to the following case:
            
            Case Number: {instance.case_number}
            Incident Type: {instance.get_incident_type_display()}
            Status: {instance.get_status_display()}
            
            Please log in to the system to view case details and take appropriate action.
            
            This is an automated message. Please do not reply.
            """
            
            send_notification_email(
                subject=subject,
                message=email_message,
                recipient_list=[instance.assigned_officer.email]
            )
            
            # 2. Notify the survivor
            message = f"Officer {instance.assigned_officer.get_full_name() or instance.assigned_officer.username} has been assigned to your case #{instance.case_number}"
            create_notification(
                user=instance.survivor,
                case=instance,
                message=message
            )
            
            # Send email to survivor
            subject = f"Officer Assigned to Your Case - #{instance.case_number}"
            email_message = f"""
            Dear {instance.survivor.get_full_name() or instance.survivor.username},
            
            An officer has been assigned to your case.
            
            Case Number: {instance.case_number}
            Officer: {instance.assigned_officer.get_full_name() or instance.assigned_officer.username}
            
            Please log in to the system for more details.
            
            This is an automated message. Please do not reply.
            """
            
            send_notification_email(
                subject=subject,
                message=email_message,
                recipient_list=[instance.survivor.email]
            )
        
        # Update the original assigned officer
        instance._original_assigned_officer_id = instance.assigned_officer_id

# Court Case Signal
@receiver(post_save, sender=CourtCase)
def court_case_post_save(sender, instance, created, **kwargs):
    """
    Signal to handle actions after a CourtCase is created or updated
    """
    case = instance.case
    
    # Create the appropriate audit log based on whether it's a new court case or an update
    if created:
        # Determine the user who created the court case (fallback to assigned officer)
        user = case.assigned_officer or case.survivor
        
        # Create audit log for new court case
        create_audit_log(
            user=user,
            action=f"Created court case for case #{case.case_number} at {instance.court_name}"
        )
        
        # Notify the survivor
        message = f"A court case has been filed for your case #{case.case_number} at {instance.court_name}"
        create_notification(
            user=case.survivor,
            case=case,
            message=message
        )
        
        # Send email notification to survivor
        subject = f"Court Case Filed - Case #{case.case_number}"
        email_message = f"""
        Dear {case.survivor.get_full_name() or case.survivor.username},
        
        A court case has been filed for your case.
        
        Case Number: {case.case_number}
        Court: {instance.court_name}
        Hearing Date: {instance.hearing_date.strftime('%Y-%m-%d')}
        
        Please log in to the system for more details.
        
        This is an automated message. Please do not reply.
        """
        
        send_notification_email(
            subject=subject,
            message=email_message,
            recipient_list=[case.survivor.email]
        )
    else:
        # If verdict is updated
        if instance.verdict:
            # Determine the user who updated the verdict (fallback to assigned officer)
            user = case.assigned_officer or case.survivor
            
            # Create audit log for verdict update
            create_audit_log(
                user=user,
                action=f"Updated verdict for court case #{instance.id} related to case #{case.case_number}"
            )
            
            # Notify the survivor
            message = f"A verdict has been recorded for your court case related to case #{case.case_number}"
            create_notification(
                user=case.survivor,
                case=case,
                message=message
            )
            
            # Send email notification to survivor
            subject = f"Court Verdict Recorded - Case #{case.case_number}"
            email_message = f"""
            Dear {case.survivor.get_full_name() or case.survivor.username},
            
            A verdict has been recorded for your court case.
            
            Case Number: {case.case_number}
            Court: {instance.court_name}
            
            Please log in to the system to view the verdict details.
            
            This is an automated message. Please do not reply.
            """
            
            send_notification_email(
                subject=subject,
                message=email_message,
                recipient_list=[case.survivor.email]
            )

# Police Follow-up Signal
@receiver(post_save, sender=PoliceFollowUp)
def police_followup_post_save(sender, instance, created, **kwargs):
    """
    Signal to handle actions after a PoliceFollowUp is created
    """
    if created:
        case = instance.case
        officer = instance.officer
        
        # Create audit log
        create_audit_log(
            user=officer,
            action=f"Added follow-up for case #{case.case_number}"
        )
        
        # Notify the survivor
        message = f"Officer {officer.get_full_name() or officer.username} has provided an update on your case #{case.case_number}"
        create_notification(
            user=case.survivor,
            case=case,
            message=message
        )
        
        # Send email notification to survivor
        subject = f"New Police Follow-up - Case #{case.case_number}"
        email_message = f"""
        Dear {case.survivor.get_full_name() or case.survivor.username},
        
        A police officer has provided an update on your case.
        
        Case Number: {case.case_number}
        Officer: {officer.get_full_name() or officer.username}
        Date: {instance.date_updated.strftime('%Y-%m-%d %H:%M')}
        
        Please log in to the system to view the update details.
        
        This is an automated message. Please do not reply.
        """
        
        send_notification_email(
            subject=subject,
            message=email_message,
            recipient_list=[case.survivor.email]
        )