from rest_framework import generics, permissions
from .models import Lab, LabStep, UserLabProgress
from .serializers import LabSerializer, LabStepSerializer, UserLabProgressSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import LabStep
import requests
import openai
from django.conf import settings

class LabListAPI(generics.ListAPIView):
    queryset = Lab.objects.all()
    serializer_class = LabSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class LabStepDetailAPI(generics.RetrieveAPIView):
    queryset = LabStep.objects.all()
    serializer_class = LabStepSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class UserLabProgressAPI(generics.ListCreateAPIView):
    queryset = UserLabProgress.objects.all()
    serializer_class = UserLabProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

class StepCodeCheckAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, step_id):
        user_code = request.data.get('code')
        step = LabStep.objects.get(pk=step_id)
        expected_code = step.expected_code
        instruction = step.instruction

        # Example: Judge0 API for code execution (replace with your API key and endpoint)
        judge0_url = "https://judge0-ce.p.rapidapi.com/submissions"
        payload = {
            "source_code": user_code,
            "language_id": self.get_language_id(step.lab.language),
        }
        headers = {
            "content-type": "application/json",
            "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
            "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com"
        }
        r = requests.post(judge0_url, json=payload, headers=headers)
        result = r.json()

        # Example: AI feedback (OpenAI, etc.)
        ai_hint = self.get_ai_hint(user_code, instruction)

        # Simple code match check
        correct = user_code.strip() == expected_code.strip()

        return Response({
            "correct": correct,
            "judge0_result": result,
            "ai_hint": ai_hint,
        }, status=status.HTTP_200_OK)

    def get_language_id(self, language):
        # Map your lab language to Judge0 language_id
        mapping = {
            "python": 71,
            "javascript": 63,
            "c": 50,
            "cpp": 54,
            # Add more as needed
        }
        return mapping.get(language.lower(), 71)

    def get_ai_hint(self, user_code, instruction):
        openai.api_key = settings.OPENAI_API_KEY
        prompt = (
            f"You are a coding assistant. The user is working on this step: '{instruction}'.\n"
            f"Their code:\n{user_code}\n"
            "Give a helpful hint or feedback to guide them to the correct solution."
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7,
        )
        return response.choices[0].message['content']