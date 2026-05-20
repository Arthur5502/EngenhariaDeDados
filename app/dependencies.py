import asyncio
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.supabase import _get_client

_bearer = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        response = await asyncio.to_thread(
            _get_client().auth.get_user,
            credentials.credentials,
        )
        user = response.user
        if not user:
            raise unauthorized
        return {"user_id": str(user.id), "email": user.email}
    except Exception:
        raise unauthorized
