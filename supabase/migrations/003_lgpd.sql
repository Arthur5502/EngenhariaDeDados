-- Requisito 3: Atendimento a requisitos de LGPD
-- Tabelas para registro de consentimento e log de auditoria de operações sobre dados pessoais.

-- LGPD Art. 7 — o consentimento é uma das bases legais para tratamento de dados pessoais.
CREATE TABLE IF NOT EXISTS public.user_consents (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    versao_politica text        NOT NULL DEFAULT '1.0',
    finalidade      text        NOT NULL,
    aceito          boolean     NOT NULL,
    ip_origem       text,
    concedido_em    timestamptz NOT NULL DEFAULT now(),
    revogado_em     timestamptz
);

ALTER TABLE public.user_consents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "usuario_le_proprios_consentimentos"
    ON public.user_consents FOR SELECT
    USING (auth.uid() = user_id);

COMMENT ON TABLE  public.user_consents              IS 'LGPD Art. 7 — registra o consentimento do titular para cada finalidade de tratamento.';
COMMENT ON COLUMN public.user_consents.finalidade   IS 'Descrição da finalidade para a qual os dados são tratados.';
COMMENT ON COLUMN public.user_consents.versao_politica IS 'Versão da política de privacidade vigente no momento do consentimento.';
COMMENT ON COLUMN public.user_consents.revogado_em  IS 'Preenchido quando o titular revoga o consentimento (LGPD Art. 8 §5°).';

-- LGPD Art. 37 — o controlador deve manter registro das operações de tratamento de dados pessoais.
CREATE TABLE IF NOT EXISTS public.audit_log (
    id           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      uuid        REFERENCES auth.users(id) ON DELETE SET NULL,
    acao         text        NOT NULL,
    detalhes     jsonb,
    ip_origem    text,
    realizado_em timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "usuario_le_proprio_log"
    ON public.audit_log FOR SELECT
    USING (auth.uid() = user_id);

COMMENT ON TABLE  public.audit_log         IS 'LGPD Art. 37 — registro das operações de tratamento de dados pessoais realizadas pela aplicação.';
COMMENT ON COLUMN public.audit_log.user_id IS 'Definido como NULL após exclusão da conta (anonimização do registro histórico).';
COMMENT ON COLUMN public.audit_log.acao    IS 'Tipo de operação: cadastro, login, acesso_perfil, exportacao_dados, exclusao_conta, revogacao_consentimento.';
