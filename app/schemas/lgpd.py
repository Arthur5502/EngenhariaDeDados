from typing import Any
from pydantic import BaseModel

class ConsentimentoOut(BaseModel):
    id: str
    versao_politica: str
    finalidade: str
    aceito: bool
    concedido_em: str
    revogado_em: str | None = None

class AuditLogOut(BaseModel):
    id: str
    acao: str
    detalhes: dict[str, Any] | None = None
    realizado_em: str

class DadosPessoaisOut(BaseModel):
    """Exportação completa dos dados pessoais do titular — LGPD Art. 18, II e V."""
    perfil: dict[str, Any]
    consentimentos: list[ConsentimentoOut]
    log_auditoria: list[AuditLogOut]
