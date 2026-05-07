import asyncio
from types import SimpleNamespace
import httpx
from supabase import create_client, Client
from app.config import settings

_client: Client | None = None

def _get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    # sign_up/sign_in atualizam a sessão interna do cliente para o JWT do usuário;
    # força a service key nas chamadas PostgREST para bypassar RLS corretamente.
    _client.postgrest.auth(settings.SUPABASE_SERVICE_KEY)
    return _client

async def sign_up(email: str, password: str):
    async with httpx.AsyncClient() as http:
        r = await http.post(
            f"{settings.SUPABASE_URL}/auth/v1/admin/users",
            headers={
                "apikey": settings.SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
            },
            json={"email": email, "password": password, "email_confirm": True},
        )
        if not r.is_success:
            raise Exception(r.json().get("msg", r.text))
        data = r.json()
        user = SimpleNamespace(
            id=data["id"],
            email=data["email"],
            created_at=data["created_at"],
        )
        return SimpleNamespace(user=user)

async def sign_in(email: str, password: str):
    return await asyncio.to_thread(
        _get_client().auth.sign_in_with_password,
        {"email": email, "password": password},
    )

async def create_profile(user_id: str, data: dict) -> dict:
    def _insert():
        return _get_client().table("users").insert({"id": user_id, **data}).execute()
    response = await asyncio.to_thread(_insert)
    return response.data[0]

async def get_profile(user_id: str) -> dict | None:
    def _select():
        return _get_client().table("users").select("*").eq("id", user_id).execute()
    response = await asyncio.to_thread(_select)
    return response.data[0] if response.data else None

async def get_email_by_cnpj(cnpj: str) -> str | None:
    def _select():
        return _get_client().table("users").select("email").eq("cnpj", cnpj).execute()
    response = await asyncio.to_thread(_select)
    return response.data[0]["email"] if response.data else None
