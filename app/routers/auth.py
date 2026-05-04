from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.database import get_db
from app.services.user import UserService
from app.services.auth import verify_password, create_access_token
from app.schemas.user import UserCreate, UserOut, TokenOut
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticação"])

def get_user_service():
    return UserService(get_db())

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    body: UserCreate,
    service: UserService = Depends(get_user_service),
):
    user = await service.create(body)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail já cadastrado",
        )
    return UserOut(**user)

@router.post("/login", response_model=TokenOut)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service),
):
    user = await service.get_by_cnpj(form.username)
    if not user or not verify_password(form.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CNPJ ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": user["cnpj_mei"]})
    return TokenOut(access_token=token)

@router.get("/me", response_model=UserOut)
async def me(current_user: dict = Depends(get_current_user)):
    return UserOut(**current_user)