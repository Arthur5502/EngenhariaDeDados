-- Requisito 2: Gerenciamento de dados em repouso — criptografia de campos sensíveis
--
-- CPF e telefone passam a ser armazenados criptografados (Fernet/AES-128-CBC, camada de aplicação).
-- cpf_hash guarda SHA-256 do CPF em dígitos: mantém a restrição de unicidade sem expor o dado.

ALTER TABLE public.users
    DROP CONSTRAINT IF EXISTS users_cpf_key;

ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS cpf_hash text UNIQUE;

COMMENT ON COLUMN public.users.cpf      IS 'CPF criptografado com Fernet (AES-128-CBC). Só descriptografável pela aplicação com DATA_ENCRYPTION_KEY.';
COMMENT ON COLUMN public.users.cpf_hash IS 'SHA-256 do CPF (somente dígitos) — garante unicidade sem expor o dado em claro.';
COMMENT ON COLUMN public.users.telefone IS 'Telefone criptografado com Fernet (AES-128-CBC). Só descriptografável pela aplicação com DATA_ENCRYPTION_KEY.';
