from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import Course
from live_classes.models import LiveClassRequest, LiveClassSession
from .serializers import (
    LiveClassRequestCreateSerializer,
    LiveClassRequestSerializer,
    LiveClassSessionSerializer,
)
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_datetime
from live_classes.services.scheduler import find_available_tutor

User = get_user_model()

def user_enrolled_in_course(user, course: Course) -> bool:
    try:
        return hasattr(course, "students") and course.students.filter(id=user.id).exists()
    except Exception:
        return False

class CreateLiveClassRequestAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        ser = LiveClassRequestCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        course = get_object_or_404(Course, pk=ser.validated_data["course_id"])
        if not user_enrolled_in_course(request.user, course):
            return Response({"detail": "Course not unlocked."}, status=status.HTTP_403_FORBIDDEN)
        obj = LiveClassRequest.objects.create(
            course=course,
            requested_by=request.user,
            topic=ser.validated_data.get("topic") or "",
            preferred_times=ser.validated_data.get("preferred_times") or "",
            status="pending",
        )
        return Response(LiveClassRequestSerializer(obj).data, status=status.HTTP_201_CREATED)

class MyLiveSessionsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        # Upcoming and recent sessions for the user
        now = timezone.now()
        qs = LiveClassSession.objects.filter(invited_students=request.user).order_by("start_at")
        data = LiveClassSessionSerializer(qs, many=True).data
        return Response({"results": data})

class ScheduleLiveClassAPIView(APIView):
    # Staff schedules a session from a request
    permission_classes = [permissions.IsAdminUser]
    def post(self, request):
        req_id = request.data.get("request_id")
        start_at_str = request.data.get("start_at")
        duration = int(request.data.get("duration_minutes", 60))
        provider = request.data.get("provider") or "jitsi"
        tutor_id = request.data.get("tutor_id")

        live_req = get_object_or_404(LiveClassRequest, pk=req_id)
        start_at = parse_datetime(start_at_str)
        if not start_at:
            return Response({"detail": "Invalid start_at"}, status=status.HTTP_400_BAD_REQUEST)

        tutor = None
        if tutor_id:
            tutor = get_object_or_404(User, pk=tutor_id)
        else:
            tutor = find_available_tutor(start_at)

        meeting_url, code = LiveClassSession.build_meeting_url(provider)
        session = LiveClassSession.objects.create(
            course=live_req.course,
            request=live_req,
            scheduled_by=request.user,
            assigned_tutor=tutor,
            start_at=start_at,
            duration_minutes=duration,
            provider=provider,
            meeting_url=meeting_url or "",
            meeting_code=code or "",
        )
        # Invite the requester by default
        session.invited_students.add(live_req.requested_by)
        live_req.status = "scheduled"
        live_req.save(update_fields=["status"])
        return Response(LiveClassSessionSerializer(session).data, status=status.HTTP_201_CREATED)