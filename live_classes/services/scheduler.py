from datetime import datetime
from django.contrib.auth import get_user_model
from django.db.models import Q
from ..models import TutorAvailability

User = get_user_model()

def find_available_tutor(start_at: datetime) -> User | None:
    # Very basic: pick any staff with availability matching the weekday/time.
    weekday = start_at.weekday()
    t = start_at.time()
    slot = TutorAvailability.objects.filter(
        active=True, weekday=weekday, start_time__lte=t, end_time__gte=t, tutor__is_staff=True
    ).select_related("tutor").order_by("tutor_id").first()
    return slot.tutor if slot else None