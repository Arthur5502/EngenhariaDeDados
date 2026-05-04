from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.services.auth import hash_password
from app.schemas.user import UserCreate


def _mascarar_cpf(cpf: str) -> str:
    return f"***.***.{cpf[6:9]}-**"


class UserService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["users"]

    async def create(self, data: UserCreate) -> dict | None:
        if await self.collection.find_one({"email": data.email}):
            return None

        doc = {
            "nome": data.nome,
            "cpf": data.cpf,
            "email": data.email,
            "telefone": data.telefone,
            "hashed_password": hash_password(data.password),
            "cnpj_mei": data.cnpj_mei,
            "razao_social": data.razao_social,
            "cnae_principal": data.cnae_principal,
            "uf": data.uf,
            "municipio": data.municipio,
            "ativo": True,
            "criado_em": datetime.now(timezone.utc).isoformat(),
        }
        result = await self.collection.insert_one(doc)
        doc["id"] = str(result.inserted_id)
        doc["cpf_mascarado"] = _mascarar_cpf(doc["cpf"])
        return doc

    async def get_by_email(self, email: str) -> dict | None:
        doc = await self.collection.find_one({"email": email})
        if doc:
            doc["id"] = str(doc.pop("_id"))
            doc["cpf_mascarado"] = _mascarar_cpf(doc["cpf"])
        return doc

    async def get_by_cnpj(self, cnpj: str) -> dict | None:
        import re
        digits = re.sub(r"\D", "", cnpj)
        doc = await self.collection.find_one({"cnpj_mei": digits})
        if doc:
            doc["id"] = str(doc.pop("_id"))
            doc["cpf_mascarado"] = _mascarar_cpf(doc["cpf"])
        return doc
