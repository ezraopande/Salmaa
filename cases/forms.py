from django import forms
from .models import Case

class CaseReportForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = ['description']
