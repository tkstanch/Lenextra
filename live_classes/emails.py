from datetime import timedelta
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone

def _build_ics(summary: str, starts, duration_minutes: int, description: str, url: str) -> str:
    dt_start = starts.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dt_end = (starts + timedelta(minutes=duration_minutes)).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return "\r\n".join([
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//lenextra//live//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:REQUEST",
        "BEGIN:VEVENT",
        f"UID:{starts.timestamp()}@lenextra",
        f"DTSTAMP:{dt_start}",
        f"DTSTART:{dt_start}",
        f"DTEND:{dt_end}",
        f"SUMMARY:{summary}",
        f"DESCRIPTION:{description}\\nJoin: {url}",
        f"URL:{url}",
        "END:VEVENT",
        "END:VCALENDAR",
        "",
    ])

def send_session_invites(session) -> None:
    course_title = getattr(session.course, "title", None) or getattr(session.course, "name", "Course")
    subject = f"Live class scheduled: {course_title}"
    text = f"A live class has been scheduled.\nCourse: {course_title}\nStarts: {session.start_at}\nJoin: {session.meeting_url or ''}"
    ics = _build_ics(subject, session.start_at, session.duration_minutes, text, session.meeting_url or "")
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@lenextra")

    recipients = set()
    # Invite requester, assigned tutor, and any invited students
    if session.request and session.request.requested_by and session.request.requested_by.email:
        recipients.add(session.request.requested_by.email)
    if session.assigned_tutor and session.assigned_tutor.email:
        recipients.add(session.assigned_tutor.email)
    for u in session.invited_students.all():
        if u.email:
            recipients.add(u.email)

    if not recipients:
        return

    msg = EmailMessage(subject=subject, body=text, from_email=from_email, to=list(recipients))
    msg.attach(filename="invite.ics", content=ics, mimetype="text/calendar; method=REQUEST; charset=UTF-8")
    try:
        msg.send(fail_silently=True)
    except Exception:
        pass