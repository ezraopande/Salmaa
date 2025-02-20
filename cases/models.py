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
