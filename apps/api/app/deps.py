"""Auth + Supabase client per request.

Pattern: caller sends `Authorization: Bearer <jwt>`. We pass the JWT to
PostgREST so all queries run as the authenticated user — RLS enforces row
isolation. Supabase Auth validates the JWT for us via get_user.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException, status
from supabase import Client, create_client

from .config import get_settings


@dataclass
class AuthedUser:
    id: str
    email: str | None
    client: Client


def authed_user(authorization: str = Header(...)) -> AuthedUser:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    jwt = authorization.split(" ", 1)[1].strip()
    if not jwt:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "empty bearer token")

    settings = get_settings()
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    try:
        user_resp = client.auth.get_user(jwt)
    except Exception as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"invalid token: {e}") from e
    if user_resp is None or user_resp.user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "no user for token")

    client.postgrest.auth(jwt)
    return AuthedUser(id=user_resp.user.id, email=user_resp.user.email, client=client)
