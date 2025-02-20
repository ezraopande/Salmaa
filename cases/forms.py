# forms.py
from django import forms
from .models import Case

class CaseAssignmentForm(forms.ModelForm):
    notes = forms.CharField(widget=forms.Textarea, required=False)
    
    class Meta:
        model = Case
        fields = ['assigned_provider']

class StatusChangeForm(forms.ModelForm):
    status_notes = forms.CharField(widget=forms.Textarea)
    notify_reporter = forms.BooleanField(required=False, initial=True)
    
    class Meta:
        model = Case
        fields = ['status']