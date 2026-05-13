from fastapi import APIRouter, Depends, HTTPException, status
from app.services.supabase import sign_up, sign_in, create_profile, get_profile, get_email_by_cnpj
from app.schemas.user import UserCreate, UserOut, TokenOut, LoginBody, mascarar_cpf, mascarar_email, mascarar_telefone
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate):
    try:
        response = await sign_up(body.email, body.password)
    except Exception as e:
        detail = str(e)
        if "already registered" in detail or "already been registered" in detail:
            detail = "E-mail já cadastrado"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    user = response.user
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Erro ao criar usuário")

    profile = await create_profile(str(user.id), {
        "nome": body.nome,
        "cpf": body.cpf,
        "cnpj": body.cnpj_mei,
        "email": body.email,
        "telefone": body.telefone,
        "razao_social": body.razao_social,
        "cnae_principal": body.cnae_principal,
        "uf": body.uf,
        "municipio": body.municipio,
    })

    return UserOut(
        id=str(user.id),
        nome=profile["nome"],
        cpf_mascarado=mascarar_cpf(profile["cpf"]),
        email_mascarado=mascarar_email(str(user.email)),
        telefone_mascarado=mascarar_telefone(profile.get("telefone", "")),
        cnpj_mei=profile["cnpj"],
        razao_social=profile.get("razao_social", ""),
        cnae_principal=profile.get("cnae_principal", ""),
        uf=profile.get("uf", ""),
        municipio=profile.get("municipio", ""),
        ativo=profile.get("ativo", True),
        criado_em=str(user.created_at),
    )

@router.post("/login", response_model=TokenOut)
async def login(body: LoginBody):
    email = await get_email_by_cnpj(body.cnpj)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CNPJ ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        response = await sign_in(email, body.password)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CNPJ ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    session = response.session
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão não iniciada")

    return TokenOut(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
    )

@router.get("/me", response_model=UserOut)
async def me(current_user: dict = Depends(get_current_user)):
    profile = await get_profile(current_user["user_id"])
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado")

    return UserOut(
        id=current_user["user_id"],
        nome=profile["nome"],
        cpf_mascarado=mascarar_cpf(profile["cpf"]),
        email_mascarado=mascarar_email(current_user["email"]),
        telefone_mascarado=mascarar_telefone(profile.get("telefone", "")),
        cnpj_mei=profile["cnpj"],
        razao_social=profile.get("razao_social", ""),
        cnae_principal=profile.get("cnae_principal", ""),
        uf=profile.get("uf", ""),
        municipio=profile.get("municipio", ""),
        ativo=profile.get("ativo", True),
        criado_em=str(profile.get("created_at", "")),
    )