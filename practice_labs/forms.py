from django import forms

class CodeSubmissionForm(forms.Form):
    code = forms.CharField(widget=forms.Textarea, label="Your Code")