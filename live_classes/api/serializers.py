from rest_framework import serializers
from live_classes.models import LiveClassRequest, LiveClassSession

class LiveClassRequestCreateSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    topic = serializers.CharField(required=False, allow_blank=True)
    preferred_times = serializers.CharField(required=False, allow_blank=True)

class LiveClassRequestSerializer(serializers.ModelSerializer):
    course_title = serializers.SerializerMethodField()
    class Meta:
        model = LiveClassRequest
        fields = ("id", "course", "course_title", "topic", "preferred_times", "status", "created_at")
    def get_course_title(self, obj):
        return getattr(obj.course, "title", None) or getattr(obj.course, "name", None)

class LiveClassSessionSerializer(serializers.ModelSerializer):
    course_title = serializers.SerializerMethodField()
    class Meta:
        model = LiveClassSession
        fields = (
            "id", "course", "course_title", "start_at", "duration_minutes",
            "provider", "meeting_url", "meeting_code", "created_at",
        )
    def get_course_title(self, obj):
        return getattr(obj.course, "title", None) or getattr(obj.course, "name", None)