import asyncio
from types import SimpleNamespace
import httpx
from supabase import create_client, Client
from app.config import settings
from app.utils.crypto import encrypt_field, decrypt_field, hash_field

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
    encrypted = {**data}
    if "cpf" in encrypted:
        cpf_plain = encrypted["cpf"]
        encrypted["cpf"] = encrypt_field(cpf_plain)
        encrypted["cpf_hash"] = hash_field(cpf_plain)
    if "telefone" in encrypted:
        encrypted["telefone"] = encrypt_field(encrypted["telefone"])

    def _insert():
        return _get_client().table("users").insert({"id": user_id, **encrypted}).execute()
    response = await asyncio.to_thread(_insert)
    return _decrypt_profile(response.data[0])

async def get_profile(user_id: str) -> dict | None:
    def _select():
        return _get_client().table("users").select("*").eq("id", user_id).execute()
    response = await asyncio.to_thread(_select)
    if not response.data:
        return None
    return _decrypt_profile(response.data[0])

def _decrypt_profile(row: dict) -> dict:
    result = {**row}
    if result.get("cpf"):
        try:
            result["cpf"] = decrypt_field(result["cpf"])
        except Exception:
            pass  # registro legado com valor em texto plano
    if result.get("telefone"):
        try:
            result["telefone"] = decrypt_field(result["telefone"])
        except Exception:
            pass
    return result

async def get_email_by_cnpj(cnpj: str) -> str | None:
    def _select():
        return _get_client().table("users").select("email").eq("cnpj", cnpj).execute()
    response = await asyncio.to_thread(_select)
    return response.data[0]["email"] if response.data else None

async def register_consent(
    user_id: str,
    finalidade: str,
    aceito: bool,
    ip: str | None = None,
) -> dict:
    """Registra consentimento do titular — LGPD Art. 7."""
    def _insert():
        return (
            _get_client()
            .table("user_consents")
            .insert({"user_id": user_id, "finalidade": finalidade, "aceito": aceito, "ip_origem": ip})
            .execute()
        )
    response = await asyncio.to_thread(_insert)
    return response.data[0]

async def get_user_consents(user_id: str) -> list[dict]:
    def _select():
        return (
            _get_client()
            .table("user_consents")
            .select("*")
            .eq("user_id", user_id)
            .order("concedido_em", desc=True)
            .execute()
        )
    response = await asyncio.to_thread(_select)
    return response.data

async def revoke_consent(user_id: str, consent_id: str) -> dict | None:
    """Revoga um consentimento específico — LGPD Art. 8, §5°."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    def _update():
        return (
            _get_client()
            .table("user_consents")
            .update({"revogado_em": now})
            .eq("id", consent_id)
            .eq("user_id", user_id)
            .is_("revogado_em", "null")
            .execute()
        )
    response = await asyncio.to_thread(_update)
    return response.data[0] if response.data else None

async def log_audit(
    user_id: str,
    acao: str,
    detalhes: dict | None = None,
    ip: str | None = None,
) -> None:
    """Registra operação sobre dados pessoais — LGPD Art. 37."""
    def _insert():
        return (
            _get_client()
            .table("audit_log")
            .insert({"user_id": user_id, "acao": acao, "detalhes": detalhes, "ip_origem": ip})
            .execute()
        )
    try:
        await asyncio.to_thread(_insert)
    except Exception:
        pass  # falhas de auditoria não devem interromper o fluxo principal

async def get_audit_log(user_id: str) -> list[dict]:
    def _select():
        return (
            _get_client()
            .table("audit_log")
            .select("*")
            .eq("user_id", user_id)
            .order("realizado_em", desc=True)
            .execute()
        )
    response = await asyncio.to_thread(_select)
    return response.data

async def delete_user_account(user_id: str) -> None:
    """Remove a conta do titular — LGPD Art. 18, VI (direito ao esquecimento).

    A exclusão em auth.users propaga em cascata para public.users e user_consents.
    Entradas em audit_log têm user_id definido como NULL (anonimização).
    """
    async with httpx.AsyncClient() as http:
        r = await http.delete(
            f"{settings.SUPABASE_URL}/auth/v1/admin/users/{user_id}",
            headers={
                "apikey": settings.SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
            },
        )
        if not r.is_success:
            raise Exception(r.json().get("msg", r.text))