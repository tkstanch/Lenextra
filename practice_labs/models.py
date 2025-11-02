from django.db import models
from django.contrib.auth import get_user_model

class Lab(models.Model):
    title = models.CharField(max_length=200)
    language = models.CharField(max_length=50)
    description = models.TextField()

class LabStep(models.Model):
    lab = models.ForeignKey(Lab, related_name='steps', on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    instruction = models.TextField()
    expected_code = models.TextField()

class UserLabProgress(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE)
    current_step = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)
