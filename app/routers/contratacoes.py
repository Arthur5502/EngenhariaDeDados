from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import get_db
from app.services.mongo import MongoService
from app.schemas.contratacao import ContratacaoOut, ContratacoesPaginadas
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/contratacoes",
    tags=["Contratações"],
    dependencies=[Depends(get_current_user)],
)


def get_mongo_service():
    return MongoService(get_db())


@router.get("/", response_model=ContratacoesPaginadas)
async def listar_contratacoes(
    pagina: int = Query(default=1, ge=1),
    tamanho_pagina: int = Query(default=20, ge=1, le=100),
    uf: str | None = Query(default=None, description="Sigla do estado (ex: PE)"),
    municipio_ibge: str | None = Query(default=None, description="Código IBGE do município"),
    situacao_compra_id: int | None = Query(default=None),
    ano_compra: int | None = Query(default=None),
    service: MongoService = Depends(get_mongo_service),
):
    data, total = await service.list_contratacoes(
        pagina=pagina,
        tamanho_pagina=tamanho_pagina,
        uf=uf,
        municipio_ibge=municipio_ibge,
        situacao_compra_id=situacao_compra_id,
        ano_compra=ano_compra,
    )
    return ContratacoesPaginadas(
        total=total,
        pagina=pagina,
        tamanho_pagina=tamanho_pagina,
        data=[ContratacaoOut(**item) for item in data],
    )


@router.get("/{numero_controle_pncp:path}", response_model=ContratacaoOut)
async def buscar_contratacao(
    numero_controle_pncp: str,
    service: MongoService = Depends(get_mongo_service),
):
    item = await service.get_by_numero_controle(numero_controle_pncp)
    if not item:
        raise HTTPException(status_code=404, detail="Contratação não encontrada")
    return ContratacaoOut(**item)
