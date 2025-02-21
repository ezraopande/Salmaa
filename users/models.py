from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('survivor', 'Survivor'),
        ('provider', 'Service Provider'),
        ('law_enforcement', 'Law Enforcement'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='survivor')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    # Fix related_name clashes
    groups = models.ManyToManyField(Group, related_name="custom_user_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions", blank=True)
