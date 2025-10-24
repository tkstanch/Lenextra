def create_meeting():
    # Jitsi needs no API; URL is enough.
    from ...models import generate_room_slug
    room = generate_room_slug()
    return f"https://meet.jit.si/{room}", room