
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LiveClassSession
from .emails import send_session_invites

@receiver(post_save, sender=LiveClassSession)
def on_session_created(sender, instance: LiveClassSession, created, **kwargs):
    if created:
        send_session_invites(instance)