from django.db import models
from django.contrib.auth import get_user_model

class ArduinoProject(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    code = models.TextField()
    board_fqbn = models.CharField(max_length=256, default='arduino:avr:uno')
    created_at = models.DateTimeField(auto_now_add=True)
