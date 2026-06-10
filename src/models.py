from pydantic import BaseModel, ConfigDict
from typing import Optional, List


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


class FonteOrcamentaria(BaseModel):
    model_config = ConfigDict(extra='allow')


class OrgaoSubRogado(BaseModel):
    model_config = ConfigDict(extra='allow')


class UnidadeSubRogada(BaseModel):
    model_config = ConfigDict(extra='allow')


class PNCPContractModel(BaseModel):
    model_config = ConfigDict(extra='allow')

    numeroControlePNCP: str

    anoCompra: int
    sequencialCompra: Optional[int] = None
    numeroCompra: Optional[str] = None
    processo: Optional[str] = None
    objetoCompra: Optional[str] = None

    valorTotalEstimado: Optional[float] = 0.0
    valorTotalHomologado: Optional[float] = None

    dataInclusao: Optional[str] = None
    dataPublicacaoPncp: Optional[str] = None
    dataAberturaProposta: Optional[str] = None
    dataEncerramentoProposta: Optional[str] = None
    dataAtualizacao: Optional[str] = None
    dataAtualizacaoGlobal: Optional[str] = None

    modalidadeId: Optional[int] = None
    modalidadeNome: Optional[str] = None
    modoDisputaId: Optional[int] = None
    modoDisputaNome: Optional[str] = None

    tipoInstrumentoConvocatorioCodigo: Optional[int] = None
    tipoInstrumentoConvocatorioNome: Optional[str] = None

    situacaoCompraId: Optional[int] = None
    situacaoCompraNome: Optional[str] = None

    srp: Optional[bool] = None
    usuarioNome: Optional[str] = None

    linkSistemaOrigem: Optional[str] = None
    linkProcessoEletronico: Optional[str] = None
    informacaoComplementar: Optional[str] = None
    justificativaPresencial: Optional[str] = None

    orgaoEntidade: OrgaoEntidade
    unidadeOrgao: UnidadeOrgao
    amparoLegal: Optional[AmparoLegal] = None
    orgaoSubRogado: Optional[OrgaoSubRogado] = None
    unidadeSubRogada: Optional[UnidadeSubRogada] = None
    fontesOrcamentarias: Optional[List[FonteOrcamentaria]] = None
