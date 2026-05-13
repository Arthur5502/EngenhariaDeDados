# SDD — Requisito 2: Dados em Repouso e Anonimização

**Base URL:** `https://projeto-integrador-backend-six.vercel.app`  
**Content-Type:** `application/json`

> Este documento descreve as mudanças introduzidas pelo Requisito 2 de Segurança da Informação: criptografia de campos sensíveis no banco de dados e anonimização nas respostas da API. O frontend deve atualizar seus contratos para os novos nomes de campos.

---

## Sumário

- [O que mudou no contrato da API](#o-que-mudou-no-contrato-da-api)
- [Schema atualizado — Resposta de Usuário](#schema-atualizado--resposta-de-usuário)
- [POST /auth/register](#post-authregister)
- [GET /auth/me](#get-authme)
- [Comportamento interno de criptografia](#comportamento-interno-de-criptografia)
- [Schema do banco de dados (Supabase)](#schema-do-banco-de-dados-supabase)

---

## O que mudou no contrato da API

Os campos de dados pessoais na resposta `UserOut` foram renomeados para tornar explícito que são **sempre anonimizados**:

| Campo anterior | Campo atual | Exemplo de valor |
|---|---|---|
| `email` | `email_mascarado` | `ar***@dogship.com.br` |
| `telefone` | `telefone_mascarado` | `(*******0000)` |
| `cpf_mascarado` | `cpf_mascarado` (sem alteração) | `***.***.789-**` |

> O backend **nunca** retorna CPF, email ou telefone em texto claro, mesmo para o próprio usuário autenticado.

---

## Schema atualizado — Resposta de Usuário

Usado nas respostas de `POST /auth/register` e `GET /auth/me`.

```json
{
  "id":                "string — UUID do usuário",
  "nome":              "string",
  "cpf_mascarado":     "string — formato: ***.***.XXX-**",
  "email_mascarado":   "string — formato: XX***@dominio.com",
  "telefone_mascarado":"string — formato: (*******XXXX)",
  "cnpj_mei":          "string — 14 dígitos sem formatação",
  "razao_social":      "string",
  "cnae_principal":    "string",
  "uf":                "string — sigla em maiúsculo",
  "municipio":         "string",
  "ativo":             "boolean",
  "criado_em":         "string — ISO 8601"
}
```

---

## POST /auth/register

Cria um novo usuário. A requisição não muda — o frontend continua enviando os dados em texto claro. A criptografia é aplicada internamente pelo backend antes de gravar no banco.

**Endpoint:** `POST /auth/register`  
**Autenticação:** não necessária.

### Exemplo de requisição (sem alteração)

```json
{
  "nome": "Arthur Campos",
  "cpf": "123.456.789-09",
  "email": "arthur@dogship.com.br",
  "password": "minhasenha123",
  "telefone": "81999990000",
  "cnpj_mei": "12.345.678/0001-95",
  "razao_social": "Arthur Campos MEI",
  "cnae_principal": "6201-5/01",
  "uf": "PE",
  "municipio": "Recife"
}
```

### Resposta de sucesso — `201 Created`

```json
{
  "id": "c7629cde-a5d3-4c31-9250-a36e4538d989",
  "nome": "Arthur Campos",
  "cpf_mascarado": "***.***. 789-**",
  "email_mascarado": "ar***@dogship.com.br",
  "telefone_mascarado": "(*******0000)",
  "cnpj_mei": "12345678000195",
  "razao_social": "Arthur Campos MEI",
  "cnae_principal": "6201-5/01",
  "uf": "PE",
  "municipio": "Recife",
  "ativo": true,
  "criado_em": "2026-05-13T17:00:00+00:00"
}
```

### Erros possíveis

| Status | `detail` | Causa |
|--------|----------|-------|
| `400` | `"E-mail já cadastrado"` | E-mail já existe no Supabase Auth |
| `400` | `"Erro ao criar usuário"` | Falha interna no Supabase |
| `422` | Array de erros | Campo inválido ou ausente |

---

## GET /auth/me

Retorna o perfil do usuário autenticado com os dados anonimizados.

**Endpoint:** `GET /auth/me`  
**Autenticação:** obrigatória — header `Authorization: Bearer <access_token>`

### Exemplo de requisição

```http
GET /auth/me HTTP/1.1
Host: projeto-integrador-backend-six.vercel.app
Authorization: Bearer eyJhbGciOiJFUzI1NiIs...
```

### Resposta de sucesso — `200 OK`

```json
{
  "id": "c7629cde-a5d3-4c31-9250-a36e4538d989",
  "nome": "Arthur Campos",
  "cpf_mascarado": "***.***. 789-**",
  "email_mascarado": "ar***@dogship.com.br",
  "telefone_mascarado": "(*******0000)",
  "cnpj_mei": "12345678000195",
  "razao_social": "Arthur Campos MEI",
  "cnae_principal": "6201-5/01",
  "uf": "PE",
  "municipio": "Recife",
  "ativo": true,
  "criado_em": "2026-05-13T17:00:00+00:00"
}
```

### Erros possíveis

| Status | `detail` | Causa |
|--------|----------|-------|
| `401` | `"Token inválido ou expirado"` | Token ausente, mal-formado ou expirado |
| `404` | `"Perfil não encontrado"` | Token válido mas perfil não existe no banco |

---

## Comportamento interno de criptografia

O frontend não precisa lidar com criptografia — ela é **totalmente transparente**. Este diagrama descreve o que acontece internamente:

```
CADASTRO — fluxo de dados
─────────────────────────────────────────────────────────
Frontend          →  [cpf: "12345678901", telefone: "81999990000"]
Pydantic          →  Valida dígitos verificadores do CPF e CNPJ
crypto.py         →  cpf_enc   = Fernet.encrypt("12345678901")
                     cpf_hash  = SHA-256("12345678901")   ← unicidade
                     tel_enc   = Fernet.encrypt("81999990000")
Supabase (banco)  →  Grava cpf_enc, cpf_hash, tel_enc
API (resposta)    →  cpf_mascarado, email_mascarado, telefone_mascarado

LEITURA — fluxo de dados
─────────────────────────────────────────────────────────
Supabase (banco)  →  Retorna cpf_enc, tel_enc (criptografados)
crypto.py         →  Fernet.decrypt(cpf_enc)  → "12345678901"
                     Fernet.decrypt(tel_enc)  → "81999990000"
schemas/user.py   →  mascarar_cpf()      → "***.***.789-**"
                     mascarar_email()    → "ar***@dogship.com.br"
                     mascarar_telefone() → "(*******0000)"
API (resposta)    →  Retorna apenas os valores mascarados
```

### Algoritmo de criptografia

| Aspecto | Detalhe |
|---|---|
| Algoritmo | **Fernet** (AES-128-CBC + HMAC-SHA256) |
| Campos criptografados | `cpf`, `telefone` (tabela `users` do Supabase) |
| Campos com hash | `cpf_hash` — SHA-256 do CPF, para garantir unicidade sem exposição |
| Chave | `DATA_ENCRYPTION_KEY` — variável de ambiente, nunca no código-fonte |
| IV | Aleatório a cada cifragem (proteção contra correlação de dados) |

---

## Schema do banco de dados (Supabase)

A tabela `public.users` após a migration `002_encrypt_sensitive_fields`:

```sql
CREATE TABLE public.users (
    id               uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    nome             text        NOT NULL,
    cpf              text        NOT NULL,         -- Fernet-encrypted
    cpf_hash         text        UNIQUE,           -- SHA-256 para unicidade
    cnpj             text        NOT NULL UNIQUE,  -- texto claro (usado em lookup de login)
    email            text        NOT NULL,
    telefone         text        NOT NULL,         -- Fernet-encrypted
    razao_social     text        NOT NULL,
    cnae_principal   text        NOT NULL,
    uf               char(2)     NOT NULL,
    municipio        text        NOT NULL,
    ativo            boolean     NOT NULL DEFAULT true,
    created_at       timestamptz NOT NULL DEFAULT now()
);
```

> **Por que o CNPJ não é criptografado?** O CNPJ é utilizado como chave de busca no login (`GET users WHERE cnpj = ?`). Criptografar com IV aleatório tornaria a busca inviável. Como o CNPJ é um dado público (Receita Federal), o risco residual é aceito e documentado.
