from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import StudentProgress, ParentProfile

User = get_user_model()

@receiver(post_save, sender=User)
def ensure_parent_profile(sender, instance: User, created, **kwargs):
    # Safely ensure a ParentProfile exists for the user when first accessed.
    # Comment out if you prefer manual creation.
    if created:
        ParentProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=StudentProgress)
def notify_parents_on_progress(sender, instance: StudentProgress, created, **kwargs):
    if not created:
        return
    student = instance.student
    parent_users = [p.user for p in student.parents.select_related('user').all()]
    if not parent_users:
        return

    subject = f"Daily progress update for {student}"
    body = (
        f"Date: {instance.date}\n"
        f"Completed lessons: {instance.completed_lessons}\n"
        f"Time spent: {instance.time_spent_minutes} minutes\n"
        f"Average score: {instance.average_score if instance.average_score is not None else 'N/A'}\n"
        f"Notes: {instance.notes or '-'}\n"
    )
    to_emails = [u.email for u in parent_users if u.email]
    if to_emails:
        send_mail(subject, body, None, to_emails, fail_silently=True)