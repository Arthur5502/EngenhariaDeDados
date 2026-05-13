# Requisito 2: Gerenciamento de Dados em Repouso e Anonimização de Informações

Este documento descreve a implementação do segundo requisito de Segurança da Informação, focado na proteção de dados pessoais armazenados nos bancos de dados do sistema e na anonimização de informações sensíveis nas respostas da API.

## 1. Visão Geral

O sistema utiliza dois bancos de dados distintos:

| Banco | Finalidade | Dados Sensíveis |
|---|---|---|
| **Supabase (PostgreSQL)** | Perfis de usuários (MEIs) | CPF, telefone, email |
| **MongoDB Atlas** | Contratações públicas (PNCP) | Nenhum dado de PF |

A estratégia de proteção é aplicada onde há dados de pessoas físicas: o **Supabase**.

## 2. Criptografia de Campos Sensíveis em Repouso

### 2.1 Algoritmo: Fernet (AES-128-CBC + HMAC-SHA256)

Os campos **CPF** e **telefone** são criptografados na **camada de aplicação** antes de serem gravados no banco de dados, usando o algoritmo **Fernet** da biblioteca `cryptography`.

O Fernet garante:
- **Confidencialidade:** AES-128 no modo CBC impede leitura direta do dado.
- **Integridade:** HMAC-SHA256 detecta qualquer adulteração do valor criptografado.
- **IV aleatório:** Cada operação de cifração gera um vetor de inicialização único, impedindo ataques de correlação (dois CPFs idênticos geram cifertextos diferentes).

*Implementação (`app/utils/crypto.py`):*
```python
def encrypt_field(value: str) -> str:
    return _get_fernet().encrypt(value.encode()).decode()

def decrypt_field(value: str) -> str:
    return _get_fernet().decrypt(value.encode()).decode()
```

### 2.2 Gestão da Chave de Criptografia

A chave (`DATA_ENCRYPTION_KEY`) é uma chave Fernet de 256 bits (32 bytes codificados em base64 URL-safe). Ela:
- É armazenada **exclusivamente como variável de ambiente** (`.env` / secrets do Vercel).
- Nunca é comitada no repositório (`.gitignore` protege o `.env`).
- Deve ser rotacionada em caso de suspeita de comprometimento.

### 2.3 Unicidade do CPF sem Exposição

O Fernet é não-determinístico (IV aleatório), portanto dois valores idênticos geram cifertextos diferentes. Para manter a restrição de unicidade do CPF no banco sem expor o dado em claro, foi adotado um **hash determinístico separado**:

```python
def hash_field(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
```

- A coluna `cpf` armazena o dado **criptografado** (confidencial).
- A coluna `cpf_hash` armazena o **SHA-256 do CPF em dígitos** e possui `UNIQUE CONSTRAINT` — garante que nenhum CPF se repita sem revelar o seu valor.

### 2.4 Migration Aplicada

```sql
-- supabase/migrations/002_encrypt_sensitive_fields.sql
ALTER TABLE public.users DROP CONSTRAINT IF EXISTS users_cpf_key;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS cpf_hash text UNIQUE;
```

## 3. Anonimização nas Respostas da API

Mesmo com dados criptografados em repouso, as respostas da API aplicam **mascaramento adicional** para minimizar a exposição de dados pessoais ao frontend e integrações.

| Campo | Dado Real | Retorno da API |
|---|---|---|
| CPF | `12345678901` | `***.***.789-**` |
| Email | `arthur@dogship.com.br` | `ar***@dogship.com.br` |
| Telefone | `81999990000` | `(*******0000)` |

*Implementação (`app/schemas/user.py`):*
```python
def mascarar_cpf(cpf: str) -> str:
    return f"***.***.{cpf[6:9]}-**"

def mascarar_email(email: str) -> str:
    local, domain = email.split("@", 1)
    return f"{local[:2]}***@{domain}"

def mascarar_telefone(telefone: str) -> str:
    digits = re.sub(r"\D", "", telefone)
    return f"({'*' * (len(digits) - 4)}{digits[-4:]})"
```

O schema `UserOut` expõe apenas `cpf_mascarado`, `email_mascarado` e `telefone_mascarado` — nunca o dado bruto.

## 4. Fluxo Completo: Registro e Leitura

```
REGISTRO:
  Frontend → [CPF, telefone em texto claro]
       → Validação Pydantic (dígitos verificadores)
       → encrypt_field(cpf) + hash_field(cpf)
       → Supabase: salva cpf_encrypted, cpf_hash, telefone_encrypted

LEITURA (/auth/me):
  Token JWT → get_current_user
       → get_profile(user_id): SELECT * → _decrypt_profile()
       → mascarar_cpf() + mascarar_email() + mascarar_telefone()
       → UserOut: retorna somente dados mascarados
```

## 5. MongoDB: Ausência de Dados Pessoais

Os documentos armazenados no MongoDB (coleção `contratacoes`) são provenientes da API pública do PNCP e contêm exclusivamente dados de **pessoas jurídicas e órgãos públicos** (CNPJ de órgãos, razão social de entidades governamentais). Não há dados de pessoas físicas identificáveis, portanto criptografia em repouso não é aplicável a essa coleção.

## 6. Proteção Complementar em Repouso (Supabase)

Além da criptografia em nível de campo, o Supabase/PostgreSQL fornece:
- **Criptografia de disco** (AES-256) gerenciada pela infraestrutura AWS — proteção contra acesso físico aos volumes.
- **Row Level Security (RLS)** — garante que cada usuário acessa somente seus próprios registros, conforme definido na migration `001`.
- **TLS obrigatório** em todas as conexões com o banco — protege os dados em trânsito.
