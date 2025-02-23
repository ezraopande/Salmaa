from django.db import models
from users.models import User

class Case(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_investigation', 'Under Investigation'),
        ('closed', 'Closed'),
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reported_cases")  # The person who reported the case
    assigned_provider = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_cases")
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    date_reported = models.DateTimeField(auto_now_add=True)
    evidence_file = models.FileField(upload_to='case_evidence/', blank=True, null=True)

    def __str__(self):
        return f"Case {self.id} - {self.status}"
    
class CaseDocument(models.Model):
    title = models.CharField(max_length=255)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="documents")
    document = models.FileField(upload_to="case_documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="uploaded_documents", null=True)

    def __str__(self):
        return f"Document for Case {self.case.id}"

class CounselingSession(models.Model):
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
