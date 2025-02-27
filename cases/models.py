from django.db import models
from users.models import User

class Case(models.Model):
    """
    Model to store SGBV incident reports
    """
    INCIDENT_TYPE_CHOICES = (
        ('physical', 'Physical Violence'),
        ('sexual', 'Sexual Violence'),
        ('emotional', 'Emotional/Psychological Violence'),
        ('economic', 'Economic Violence'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('reported', 'Reported'),
        ('under_investigation', 'Under Investigation'),
        ('medical_examination', 'Medical Examination'),
        ('legal_proceedings', 'Legal Proceedings'),
        ('closed', 'Closed'),
    )
    
    survivor = models.ForeignKey(User, on_delete=models.PROTECT, related_name='reported_incidents')
    incident_type = models.CharField(max_length=20, choices=INCIDENT_TYPE_CHOICES)
    incident_date = models.DateTimeField()
    incident_location = models.CharField(max_length=255)
    description = models.TextField()
    perpetrator_name = models.CharField(max_length=255, blank=True, null=True)
    perpetrator_details = models.TextField(blank=True, null=True)
    
    # Case management fields
    case_number = models.CharField(max_length=50)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='reported')
    report_date = models.DateTimeField(auto_now_add=True)
    assigned_officer = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_cases',
        limit_choices_to={'role': 'law_enforcement'}
    )
    assigned_medic = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_medic',
        limit_choices_to={'role': 'medical_officer'}
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Case #{self.case_number} - {self.get_incident_type_display()}"


class LawEnforcementAssignment(models.Model):
    """
    Model to track law enforcement assignments and investigation progress
    """
    STATUS_CHOICES = (
        ('assigned', 'Assigned'),
        ('investigating', 'Investigating'),
        ('suspect_apprehended', 'Suspect Apprehended'),
        ('case_filed', 'Case Filed with Court'),
        ('closed', 'Closed'),
    )
    
    incident = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='law_enforcement_assignments')
    officer = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='law_enforcement_cases',
        limit_choices_to={'role': 'law_enforcement'}
    )
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='assigned')
    assigned_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"LE Assignment for Case #{self.incident.case_number}"
class CaseDocument(models.Model):
    title = models.CharField(max_length=255)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="documents")
    document = models.FileField(upload_to="case_documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="uploaded_documents", null=True)

    def __str__(self):
        return f"Document for Case {self.case.id}"

class CounselingSession(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="counseling_sessions")
    survivor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="counseling_sessions")
    counselor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions_conducted")
    session_date = models.DateTimeField()
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Counseling Session {self.id} - {self.survivor.username}"

class CourtCase(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="court_cases")
    court_name = models.CharField(max_length=255)
    hearing_date = models.DateField()
    verdict = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Court Case for {self.case.id} - {self.court_name}"

class PoliceFollowUp(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="follow_ups")
    officer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="police_followups")
    update_details = models.TextField()
    date_updated = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Follow-up on Case {self.case.id}"
