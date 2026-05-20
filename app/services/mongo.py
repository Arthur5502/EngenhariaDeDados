import re
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.config import settings

def _numero_controle_regex(valor: str) -> str:
    normalizado = re.sub(r"[-/]", "", valor)
    return r"[-/]?".join(re.escape(c) for c in normalizado)

class MongoService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db[settings.MONGO_COLLECTION]

    async def insert_many(self, data: list[dict]) -> int:
        if not data:
            return 0
        result = await self.collection.insert_many(data)
        return len(result.inserted_ids)

    async def list_contratacoes(
        self,
        pagina: int = 1,
        tamanho_pagina: int = 20,
        uf: str | None = None,
        municipio_ibge: str | None = None,
        situacao_compra_id: int | None = None,
        ano_compra: int | None = None,
    ) -> tuple[list[dict], int]:
        filtro: dict = {}
        if uf:
            filtro["uf_sigla"] = uf.upper()
        if municipio_ibge:
            filtro["municipio_ibge"] = municipio_ibge
        if situacao_compra_id is not None:
            filtro["situacao_compra_id"] = situacao_compra_id
        if ano_compra is not None:
            filtro["ano_compra"] = ano_compra

        skip = (pagina - 1) * tamanho_pagina
        total = await self.collection.count_documents(filtro)
        cursor = self.collection.find(filtro, {"_id": 0}).skip(skip).limit(tamanho_pagina)
        data = await cursor.to_list(length=tamanho_pagina)
        return data, total

    async def get_by_numero_controle(self, numero_controle_pncp: str) -> dict | None:
        pattern = _numero_controle_regex(numero_controle_pncp)
        return await self.collection.find_one(
            {"numero_controle_pncp": {"$regex": f"^{pattern}$"}}, {"_id": 0}
        )