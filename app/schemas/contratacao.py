from pydantic import BaseModel, Field
from typing import Optional

class ContratacaoOut(BaseModel):
    numero_controle_pncp: Optional[str] = None
    ano_compra: Optional[int] = None
    numero_compra: Optional[str] = None
    processo: Optional[str] = None
    objeto_compra: Optional[str] = None
    modalidade_id: Optional[int] = None
    modalidade_nome: Optional[str] = None
    modo_disputa_nome: Optional[str] = None
    situacao_compra_id: Optional[int] = None
    situacao_compra_nome: Optional[str] = None
    tipo_instrumento_convocatorio: Optional[str] = None
    valor_total_estimado: Optional[float] = None
    valor_total_homologado: Optional[float] = None
    srp: Optional[bool] = None
    orgao_cnpj: Optional[str] = None
    orgao_razao_social: Optional[str] = None
    orgao_poder_id: Optional[str] = None
    orgao_esfera_id: Optional[str] = None
    unidade_codigo: Optional[str] = None
    unidade_nome: Optional[str] = None
    municipio_nome: Optional[str] = None
    municipio_ibge: Optional[str] = None
    uf_sigla: Optional[str] = None
    uf_nome: Optional[str] = None
    amparo_legal_codigo: Optional[int] = None
    amparo_legal_nome: Optional[str] = None
    data_inclusao: Optional[str] = None
    data_atualizacao: Optional[str] = None
    data_publicacao_pncp: Optional[str] = None
    data_abertura_proposta: Optional[str] = None
    data_encerramento_proposta: Optional[str] = None
    link_sistema_origem: Optional[str] = None
    data_extracao: Optional[str] = None

    model_config = {"from_attributes": True}

class ContratacoesPaginadas(BaseModel):
    total: int
    pagina: int
    tamanho_pagina: int
    data: list[ContratacaoOut]

class ETLParams(BaseModel):
    data_final: str = Field(
        default="20260331",
        description="Data final no formato YYYYMMDD",
        examples=["20260331"],
    )
    uf: str = Field(default="pe", description="Sigla do estado")
    codigo_municipio_ibge: str = Field(default="2611606", description="Código IBGE do município")
    codigo_modalidade: str = Field(default="8", description="Código da modalidade de contratação")

class ETLResult(BaseModel):
    extraidos: int
    transformados: int
    inseridos: int
    mensagem: str