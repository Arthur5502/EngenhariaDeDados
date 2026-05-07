# SDD — Integração Frontend: Módulo de Autenticação

**Base URL:** `https://projeto-integrador-backend-six.vercel.app`  
**Content-Type:** `application/json` (todas as requisições e respostas)

---

## Sumário

- [Schemas](#schemas)
- [POST /auth/register](#post-authregister)
- [POST /auth/login](#post-authlogin)
- [GET /auth/me](#get-authme)
- [Erros e Exceções](#erros-e-exceções)
- [Fluxo Recomendado no Frontend](#fluxo-recomendado-no-frontend)

---

## Schemas

### Requisição — Cadastro

```json
{
  "nome":          "string — nome completo do usuário",
  "cpf":           "string — apenas dígitos ou formatado (ex: 123.456.789-09)",
  "email":         "string — e-mail válido",
  "password":      "string — senha",
  "telefone":      "string — telefone",
  "cnpj_mei":      "string — apenas dígitos ou formatado (ex: 12.345.678/0001-95)",
  "razao_social":  "string — razão social da empresa",
  "cnae_principal":"string — código CNAE principal",
  "uf":            "string — sigla do estado (ex: PE) — convertido para maiúsculo automaticamente",
  "municipio":     "string — nome do município"
}
```

### Requisição — Login

```json
{
  "cnpj":     "string — apenas dígitos ou formatado",
  "password": "string — senha"
}
```

### Resposta — Token (login bem-sucedido)

```json
{
  "access_token":  "string — JWT para usar nas requisições autenticadas",
  "refresh_token": "string — JWT para renovar a sessão",
  "token_type":    "bearer"
}
```

### Resposta — Usuário (cadastro e /me)

```json
{
  "id":             "string — UUID do usuário",
  "nome":           "string",
  "cpf_mascarado":  "string — formato: ***.***. XXX-** (apenas dígitos 6-8 visíveis)",
  "email":          "string",
  "telefone":       "string",
  "cnpj_mei":       "string — 14 dígitos sem formatação",
  "razao_social":   "string",
  "cnae_principal": "string",
  "uf":             "string — sigla em maiúsculo",
  "municipio":      "string",
  "ativo":          "boolean",
  "criado_em":      "string — ISO 8601 (ex: 2026-05-07T20:00:00+00:00)"
}
```

---

## POST /auth/register

Cria um novo usuário e retorna o perfil criado.

**Endpoint:** `POST /auth/register`

### Exemplo de requisição

```json
{
  "nome": "Arthur Campos",
  "cpf": "123.456.789-09",
  "email": "arthur@exemplo.com",
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
  "email": "arthur@exemplo.com",
  "telefone": "81999990000",
  "cnpj_mei": "12345678000195",
  "razao_social": "Arthur Campos MEI",
  "cnae_principal": "6201-5/01",
  "uf": "PE",
  "municipio": "Recife",
  "ativo": true,
  "criado_em": "2026-05-07 20:00:00+00:00"
}
```

### Erros possíveis

| Status | `detail` | Causa |
|--------|----------|-------|
| `400` | `"E-mail já cadastrado"` | E-mail já existe no sistema |
| `400` | `"Erro ao criar usuário"` | Falha interna ao criar no Supabase Auth |
| `422` | Array de erros (ver abaixo) | Campo inválido ou ausente |

---

## POST /auth/login

Autentica o usuário com CNPJ e senha. Retorna tokens de sessão.

**Endpoint:** `POST /auth/login`

### Exemplo de requisição

```json
{
  "cnpj": "12.345.678/0001-95",
  "password": "minhasenha123"
}
```

### Resposta de sucesso — `200 OK`

```json
{
  "access_token": "eyJhbGciOiJFUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

> Guarde o `access_token` (ex: `localStorage` ou estado global). Ele é necessário para todas as rotas autenticadas.

### Erros possíveis

| Status | `detail` | Causa |
|--------|----------|-------|
| `401` | `"CNPJ ou senha incorretos"` | CNPJ não cadastrado ou senha errada |
| `401` | `"Sessão não iniciada"` | Supabase não retornou sessão válida |
| `422` | Array de erros (ver abaixo) | CNPJ inválido ou campo ausente |

---

## GET /auth/me

Retorna o perfil do usuário autenticado.

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
  "email": "arthur@exemplo.com",
  "telefone": "81999990000",
  "cnpj_mei": "12345678000195",
  "razao_social": "Arthur Campos MEI",
  "cnae_principal": "6201-5/01",
  "uf": "PE",
  "municipio": "Recife",
  "ativo": true,
  "criado_em": "2026-05-07 20:00:00+00:00"
}
```

### Erros possíveis

| Status | `detail` | Causa |
|--------|----------|-------|
| `401` | `"Token inválido ou expirado"` | Token ausente, mal-formado ou expirado |
| `403` | — | Header `Authorization` não enviado |
| `404` | `"Perfil não encontrado"` | Token válido mas perfil não existe no banco |

---

## Erros e Exceções

### Formato padrão de erro

Todos os erros retornam JSON com o campo `detail`:

```json
{ "detail": "mensagem de erro" }
```

### Erros de validação — `422 Unprocessable Entity`

Quando um campo está ausente ou inválido, o formato é diferente:

```json
{
  "detail": [
    { "campo": "cpf",      "erro": "Value error, CPF inválido" },
    { "campo": "cnpj_mei", "erro": "Value error, CNPJ inválido" }
  ]
}
```

O campo `campo` indica qual field falhou. Use isso para exibir erros inline no formulário.

### Validações aplicadas automaticamente pelo backend

| Campo | Validação |
|-------|-----------|
| `cpf` | Dígitos verificadores do CPF (aceita formatado ou só dígitos) |
| `cnpj_mei` / `cnpj` | Dígitos verificadores do CNPJ (aceita formatado ou só dígitos) |
| `email` | Formato de e-mail válido |
| `uf` | Convertido para maiúsculo automaticamente |

---

## Fluxo Recomendado no Frontend

```
1. Cadastro
   POST /auth/register
   → sucesso (201): redirecionar para login ou logar automaticamente
   → erro (400/422): exibir mensagem inline no formulário

2. Login
   POST /auth/login
   → sucesso (200): salvar access_token (localStorage / context / cookie httpOnly)
   → erro (401/422): exibir "CNPJ ou senha incorretos"

3. Rotas protegidas
   Adicionar header em toda requisição autenticada:
   Authorization: Bearer <access_token>

4. Token expirado
   → receber 401 em qualquer rota protegida
   → redirecionar para /login e limpar o token salvo
```

### Exemplo com fetch (JavaScript)

```js
// Login
const res = await fetch('https://projeto-integrador-backend-six.vercel.app/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ cnpj: '12345678000195', password: 'minhasenha123' }),
})
const { access_token } = await res.json()
localStorage.setItem('token', access_token)

// Rota autenticada
const me = await fetch('https://projeto-integrador-backend-six.vercel.app/auth/me', {
  headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
})
const user = await me.json()
```
