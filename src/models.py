from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class OrgaoEntidade(BaseModel):
    model_config = ConfigDict(extra='allow')
    
    cnpj: str
    razaoSocial: str
    poderId: str
    esferaId: str

class UnidadeOrgao(BaseModel):
    model_config = ConfigDict(extra='allow')
    
    codigoUnidade: str
    nomeUnidade: str
    ufSigla: str
    municipioNome: str
    codigoIbge: str

class AmparoLegal(BaseModel):
    model_config = ConfigDict(extra='allow')
    
    codigo: int
    nome: str

class PNCPContractModel(BaseModel):
    model_config = ConfigDict(extra='allow')

    numeroControlePNCP: str
    
    anoCompra: int
    numeroCompra: Optional[str] = None
    processo: Optional[str] = None
    objetoCompra: Optional[str] = None
    
    valorTotalEstimado: Optional[float] = 0.0
    valorTotalHomologado: Optional[float] = None
    
    dataPublicacaoPncp: Optional[str] = None
    dataAberturaProposta: Optional[str] = None
    dataEncerramentoProposta: Optional[str] = None
    
    orgaoEntidade: OrgaoEntidade
    unidadeOrgao: UnidadeOrgao
    amparoLegal: Optional[AmparoLegal] = None
    
    situacaoCompraId: Optional[int] = None
    situacaoCompraNome: Optional[str] = None
