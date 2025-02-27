# forms.py
from django import forms
from .models import Case, PoliceFollowUp, CounselingSession, CaseDocument, CourtCase


class CaseReportForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = [
            'incident_type', 
            'incident_date', 
            'incident_location', 
            'description',
            'perpetrator_name', 
            'perpetrator_details'
        ]
        widgets = {
            'incident_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 5}),
            'perpetrator_details': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'perpetrator_name': 'Name of Perpetrator (if known)',
            'perpetrator_details': 'Additional Details about Perpetrator',
        }
        help_texts = {
            'description': 'Please provide a detailed account of the incident',
        }

class CaseAssignmentForm(forms.ModelForm):
    notes = forms.CharField(widget=forms.Textarea, required=False)
    
    class Meta:
        model = Case
        fields = ['assigned_officer', 'assigned_medic']
        
    def clean(self):
        cleaned_data = super().clean()
        assigned_officer = cleaned_data.get('assigned_officer')
        assigned_medic = cleaned_data.get('assigned_medic')
        
        # Ensure at least one provider is assigned
        if not assigned_officer and not assigned_medic:
            raise forms.ValidationError("You must assign at least one officer or medical officer to the case.")
            
        return cleaned_data

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