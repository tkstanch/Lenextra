import os

def create_meeting():
    # Placeholder. Implement Zoom SDK/API here and return (join_url, meeting_code).
    # Env vars: ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET
    account_id = os.getenv("ZOOM_ACCOUNT_ID")
    client_id = os.getenv("ZOOM_CLIENT_ID")
    client_secret = os.getenv("ZOOM_CLIENT_SECRET")
    if not (account_id and client_id and client_secret):
        raise RuntimeError("Zoom not configured")
    # TODO: Create meeting via Zoom REST and return real URL/code.
    return "", None