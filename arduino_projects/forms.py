from django import forms
from .models import ArduinoProject

class ArduinoProjectForm(forms.ModelForm):
    class Meta:
        model = ArduinoProject
        fields = ['name', 'code', 'board_fqbn']