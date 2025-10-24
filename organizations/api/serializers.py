from rest_framework import serializers
from organizations.models import (
    OrganizationTask, TaskApplication, TaskSubmission, StudentAchievement
)

class OrganizationTaskSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source="business.name", read_only=True)
    required_skills = serializers.SlugRelatedField(slug_field="name", many=True, read_only=True)
    class Meta:
        model = OrganizationTask
        fields = ("id", "title", "slug", "business", "business_name", "description", "difficulty", "points", "deadline", "status", "required_skills")

class TaskApplicationCreateSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    motivation = serializers.CharField(required=False, allow_blank=True)

class TaskApplicationSerializer(serializers.ModelSerializer):
    task = OrganizationTaskSerializer(read_only=True)
    class Meta:
        model = TaskApplication
        fields = ("id", "task", "status", "motivation", "created_at")

class TaskSubmissionCreateSerializer(serializers.Serializer):
    url = serializers.URLField(required=False, allow_blank=True)
    content = serializers.CharField(required=False, allow_blank=True)
    # attachment handled via multipart in a different endpoint if needed

class TaskSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskSubmission
        fields = ("id", "application", "url", "content", "status", "feedback", "reviewed_by", "reviewed_at", "created_at")

class StudentAchievementSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source="business.name", read_only=True)
    class Meta:
        model = StudentAchievement
        fields = ("id", "title", "points", "business", "business_name", "task", "issued_at")