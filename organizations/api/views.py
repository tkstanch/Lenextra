from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.models import OrganizationTask, TaskApplication, TaskSubmission, StudentAchievement, StudentProfile, Business
from .serializers import (
    OrganizationTaskSerializer, TaskApplicationCreateSerializer, TaskApplicationSerializer,
    TaskSubmissionCreateSerializer, TaskSubmissionSerializer, StudentAchievementSerializer,
)

def get_student_profile(user) -> StudentProfile:
    return get_object_or_404(StudentProfile, user=user)

class PublicTasksListAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        qs = OrganizationTask.objects.filter(is_active=True, status="open").select_related("business")
        return Response({"results": OrganizationTaskSerializer(qs, many=True).data})

class BusinessTasksListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, business_id: int):
        # Basic auth: only staff or business admins should see drafts; else open only
        qs = OrganizationTask.objects.filter(business_id=business_id)
        if not request.user.is_staff:
            qs = qs.filter(is_active=True, status__in=["open", "closed"])
        return Response({"results": OrganizationTaskSerializer(qs, many=True).data})

class ApplyToTaskAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        ser = TaskApplicationCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        task = get_object_or_404(OrganizationTask, pk=ser.validated_data["task_id"], is_active=True, status="open")
        student = get_student_profile(request.user)
        app, created = TaskApplication.objects.get_or_create(task=task, student=student, defaults={
            "motivation": ser.validated_data.get("motivation") or "",
        })
        if not created and app.status in ("rejected", "withdrawn"):
            app.status = "pending"
            app.motivation = ser.validated_data.get("motivation") or app.motivation
            app.save(update_fields=["status", "motivation"])
        return Response(TaskApplicationSerializer(app).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class MyApplicationsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        student = get_student_profile(request.user)
        qs = TaskApplication.objects.filter(student=student).select_related("task", "task__business")
        return Response({"results": TaskApplicationSerializer(qs, many=True).data})

class SubmitWorkAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, application_id: int):
        app = get_object_or_404(TaskApplication, pk=application_id, student__user=request.user, status__in=["approved", "pending"])
        ser = TaskSubmissionCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        submission, created = TaskSubmission.objects.get_or_create(application=app, defaults={
            "url": ser.validated_data.get("url"), "content": ser.validated_data.get("content"),
        })
        if not created:
            submission.url = ser.validated_data.get("url") or submission.url
            submission.content = ser.validated_data.get("content") or submission.content
            submission.status = "submitted"
            submission.save(update_fields=["url", "content", "status"])
        return Response(TaskSubmissionSerializer(submission).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class ReviewSubmissionAPIView(APIView):
    # Organization staff approves/rejects and issues achievement
    permission_classes = [permissions.IsAdminUser]
    def post(self, request, submission_id: int):
        decision = request.data.get("decision")  # "approve" | "reject"
        points = int(request.data.get("points", 10))
        feedback = request.data.get("feedback", "")
        sub = get_object_or_404(TaskSubmission, pk=submission_id)
        if decision == "approve":
            sub.status = "approved"
            sub.feedback = feedback
            sub.reviewed_by = request.user
            sub.save(update_fields=["status", "feedback", "reviewed_by"])
            app = sub.application
            app.status = "completed"
            app.save(update_fields=["status"])
            StudentAchievement.objects.create(
                student=app.student, business=app.task.business, task=app.task, title=f"Completed: {app.task.title}", points=points
            )
            return Response(TaskSubmissionSerializer(sub).data)
        elif decision == "reject":
            sub.status = "rejected"
            sub.feedback = feedback
            sub.reviewed_by = request.user
            sub.save(update_fields=["status", "feedback", "reviewed_by"])
            return Response(TaskSubmissionSerializer(sub).data)
        return Response({"detail": "Invalid decision"}, status=status.HTTP_400_BAD_REQUEST)

class MyAchievementsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        student = get_student_profile(request.user)
        qs = StudentAchievement.objects.filter(student=student).select_related("business", "task")
        return Response({"results": StudentAchievementSerializer(qs, many=True).data})