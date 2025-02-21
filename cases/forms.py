# forms.py
from django import forms
from .models import Case, PoliceFollowUp, CounselingSession, CaseDocument, CourtCase

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
        
class PoliceFollowUpForm(forms.ModelForm):
    class Meta:
        model = PoliceFollowUp
        fields = ['update_details']
        
class CounselingSessionForm(forms.ModelForm):
    class Meta:
        model = CounselingSession
        fields = ['session_date', 'notes']
        
class CaseDocumentForm(forms.ModelForm):
    class Meta:
        model = CaseDocument
        fields = ['document']
        
class CourtCaseForm(forms.ModelForm):
    class Meta:
        model = CourtCase
        fields = ['court_name', 'hearing_date', 'verdict']