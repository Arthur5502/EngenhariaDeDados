from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from app.database import get_db
from app.services.auth import decode_token
from app.services.user import UserService

_bearer = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
        cnpj: str | None = payload.get("sub")
        if not cnpj:
            raise unauthorized
    except JWTError:
        raise unauthorized

    user = await UserService(get_db()).get_by_cnpj(cnpj)
    if not user or not user.get("ativo"):
        raise unauthorized
    return user
