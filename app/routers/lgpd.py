from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.dependencies import get_current_user
from app.services.supabase import (
    delete_user_account,
    get_audit_log,
    get_profile,
    get_user_consents,
    log_audit,
    revoke_consent,
)
from app.schemas.lgpd import AuditLogOut, ConsentimentoOut, DadosPessoaisOut

router = APIRouter(prefix="/lgpd", tags=["LGPD"])

@router.get("/dados", response_model=DadosPessoaisOut, summary="Exportar dados pessoais", description="Retorna todos os dados pessoais do titular, incluindo consentimentos e log de auditoria. LGPD Art. 18, II e V.",)
async def exportar_dados(request: Request, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    ip = request.client.host if request.client else None

    profile = await get_profile(user_id)
    consents = await get_user_consents(user_id)
    audit = await get_audit_log(user_id)

    await log_audit(user_id, "exportacao_dados", None, ip)

    return DadosPessoaisOut(
        perfil=profile or {},
        consentimentos=[ConsentimentoOut(**c) for c in consents],
        log_auditoria=[AuditLogOut(**a) for a in audit],
    )

@router.get("/consentimentos", response_model=list[ConsentimentoOut], summary="Listar consentimentos", description="Lista todos os consentimentos registrados para o titular. LGPD Art. 18, I.",)
async def listar_consentimentos(current_user: dict = Depends(get_current_user)):
    consents = await get_user_consents(current_user["user_id"])
    return [ConsentimentoOut(**c) for c in consents]

@router.post("/revogar-consentimento/{consent_id}", status_code=status.HTTP_200_OK, summary="Revogar consentimento", description="Revoga um consentimento previamente concedido pelo titular. LGPD Art. 8, §5°.",)
async def revogar_consentimento(
    consent_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    result = await revoke_consent(user_id, consent_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consentimento não encontrado ou já revogado",
        )

    ip = request.client.host if request.client else None
    await log_audit(user_id, "revogacao_consentimento", {"consent_id": consent_id}, ip)

    return {"mensagem": "Consentimento revogado com sucesso", "revogado_em": result["revogado_em"]}

@router.delete("/conta", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir conta", description=("Remove permanentemente a conta e todos os dados pessoais do titular. Registros de auditoria são anonimizados. LGPD Art. 18, VI."),)
async def excluir_conta(request: Request, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    ip = request.client.host if request.client else None

    await log_audit(user_id, "exclusao_conta", None, ip)

    try:
        await delete_user_account(user_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))