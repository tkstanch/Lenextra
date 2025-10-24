from django.forms.models import inlineformset_factory
from .models import Course, Module, InstructorProfile, Appointment

ModuleFormSet = inlineformset_factory(
    Course,
    Module,
    fields=['title', 'description'],
    extra=2,
    can_delete=True
)

AppointmentFormSet = inlineformset_factory(
    InstructorProfile,
    Appointment,
    fields=['student', 'scheduled_time', 'status'],
    extra=2,
    can_delete=True
)