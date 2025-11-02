from rest_framework import serializers
from .models import Lab, LabStep, UserLabProgress

class LabSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lab
        fields = '__all__'

class LabStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabStep
        fields = '__all__'

class UserLabProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLabProgress
        fields = '__all__'