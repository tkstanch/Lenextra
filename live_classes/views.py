from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from .models import LiveClassSession

def _user_enrolled(user, course) -> bool:
    try:
        return hasattr(course, "students") and course.students.filter(id=user.id).exists()
    except Exception:
        return False

@login_required
def join_session(request, pk: int):
    session = get_object_or_404(LiveClassSession, pk=pk)
    if not session.meeting_url:
        return HttpResponseBadRequest("Session not ready.")
    if request.user.is_staff or request.user == session.assigned_tutor:
        return HttpResponseRedirect(session.meeting_url)
    if _user_enrolled(request.user, session.course):
        # Optionally auto-invite joining student:
        session.invited_students.add(request.user)
        return HttpResponseRedirect(session.meeting_url)
    return HttpResponseForbidden("You do not have access to this live class.")
