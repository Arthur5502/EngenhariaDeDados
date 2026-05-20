# SDD — Requisito 3: Atendimento a Requisitos de LGPD

**Base URL:** `https://projeto-integrador-backend-six.vercel.app`  
**Content-Type:** `application/json`

> Este documento descreve as mudanças introduzidas pelo Requisito 3 de Segurança da Informação: conformidade com a Lei Geral de Proteção de Dados (LGPD). O frontend deve atualizar o formulário de cadastro e implementar uma seção de privacidade para o usuário autenticado.

---

## Sumário

- [O que mudou no contrato da API](#o-que-mudou-no-contrato-da-api)
- [POST /auth/register — campo novo](#post-authregister--campo-novo)
- [GET /lgpd/dados](#get-lgpddados)
- [GET /lgpd/consentimentos](#get-lgpdconsentimentos)
- [POST /lgpd/revogar-consentimento/{consent_id}](#post-lgpdrevogar-consentimentoconsent_id)
- [DELETE /lgpd/conta](#delete-lgpdconta)
- [Schemas LGPD](#schemas-lgpd)
- [Fluxo Recomendado no Frontend](#fluxo-recomendado-no-frontend)
- [Erros e Exceções](#erros-e-exceções)

---

## O que mudou no contrato da API

### Cadastro — novo campo obrigatório

O formulário de cadastro agora exige o aceite explícito dos termos de uso e política de privacidade (LGPD Art. 7).

| Campo novo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `aceite_termos` | `boolean` | Sim | Deve ser `true`. Enviar `false` retorna erro `422`. |

### Novas rotas

Todas as rotas `/lgpd/*` são **autenticadas** — exigem `Authorization: Bearer <access_token>`.

| Método | Rota | Direito LGPD |
|---|---|---|
| `GET` | `/lgpd/dados` | Acesso e portabilidade — Art. 18, II e V |
| `GET` | `/lgpd/consentimentos` | Informação sobre tratamento — Art. 18, I |
| `POST` | `/lgpd/revogar-consentimento/{id}` | Revogação do consentimento — Art. 8, §5° |
| `DELETE` | `/lgpd/conta` | Esquecimento e exclusão — Art. 18, VI |

---

## POST /auth/register — campo novo

O endpoint continua no mesmo endereço. A única mudança é a adição do campo `aceite_termos`.

**Endpoint:** `POST /auth/register`  
**Autenticação:** não necessária.

### Exemplo de requisição (atualizado)

```json
{
  "nome": "Arthur Campos",
  "cpf": "123.456.789-09",
  "email": "arthur@dogship.com.br",
  "password": "minhasenha123",
  "telefone": "81999990000",
  "aceite_termos": true,
  "cnpj_mei": "12.345.678/0001-95",
  "razao_social": "Arthur Campos MEI",
  "cnae_principal": "6201-5/01",
  "uf": "PE",
  "municipio": "Recife"
}
```

> O backend registra automaticamente o consentimento com timestamp e IP de origem. O frontend **não precisa** chamar nenhum endpoint adicional.

### Erros possíveis (novos)

| Status | `detail` | Causa |
|--------|----------|-------|
| `422` | `"É necessário aceitar os termos de uso e política de privacidade..."` | `aceite_termos` enviado como `false` |
| `422` | Array de erros | Campo `aceite_termos` ausente no body |

---

## GET /lgpd/dados

Exporta todos os dados pessoais do titular: perfil, histórico de consentimentos e log de auditoria de acessos. Use para exibir uma página de "Meus Dados" ou permitir download.

**Endpoint:** `GET /lgpd/dados`  
**Autenticação:** obrigatória — `Authorization: Bearer <access_token>`

### Exemplo de requisição

```http
GET /lgpd/dados HTTP/1.1
Host: projeto-integrador-backend-six.vercel.app
Authorization: Bearer eyJhbGciOiJFUzI1NiIs...
```

### Resposta de sucesso — `200 OK`

```json
{
  "perfil": {
    "id": "c7629cde-a5d3-4c31-9250-a36e4538d989",
    "nome": "Arthur Campos",
    "cpf": "12345678909",
    "email": "arthur@dogship.com.br",
    "telefone": "81999990000",
    "cnpj": "12345678000195",
    "razao_social": "Arthur Campos MEI",
    "cnae_principal": "6201-5/01",
    "uf": "PE",
    "municipio": "Recife",
    "ativo": true,
    "created_at": "2026-05-07T20:41:17.523453+00:00"
  },
  "consentimentos": [
    {
      "id": "06d4fd61-3644-4f2b-9790-9d55c3c88a76",
      "versao_politica": "1.0",
      "finalidade": "Tratamento de dados pessoais para cadastro e uso da plataforma PNCP Integrador.",
      "aceito": true,
      "concedido_em": "2026-05-07T20:41:17.523453+00:00",
      "revogado_em": null
    }
  ],
  "log_auditoria": [
    {
      "id": "a1b2c3d4-...",
      "acao": "login",
      "detalhes": null,
      "realizado_em": "2026-05-20T13:00:00+00:00"
    },
    {
      "id": "e5f6g7h8-...",
      "acao": "cadastro",
      "detalhes": { "cnpj": "12345678000195" },
      "realizado_em": "2026-05-07T20:41:17+00:00"
    }
  ]
}
```

> **Atenção:** o campo `perfil.cpf` aqui retorna o valor descriptografado (dado real). Use essa rota apenas em contextos explícitos de exportação de dados, nunca como substituto de `/auth/me` para exibição rotineira.

### Ações registradas no `log_auditoria`

| `acao` | Quando ocorre |
|---|---|
| `cadastro` | Criação da conta |
| `login` | Login bem-sucedido |
| `acesso_perfil` | Chamada ao `GET /auth/me` |
| `exportacao_dados` | Chamada ao `GET /lgpd/dados` |
| `revogacao_consentimento` | Revogação de um consentimento |
| `exclusao_conta` | Exclusão da conta |

### Erros possíveis

| Status | `detail` | Causa |
|--------|----------|-------|
| `401` | `"Token inválido ou expirado"` | Token ausente ou expirado |

---

## GET /lgpd/consentimentos

Lista todos os consentimentos do titular, indicando quais estão ativos e quais foram revogados.

**Endpoint:** `GET /lgpd/consentimentos`  
**Autenticação:** obrigatória — `Authorization: Bearer <access_token>`

### Exemplo de requisição

```http
GET /lgpd/consentimentos HTTP/1.1
Host: projeto-integrador-backend-six.vercel.app
Authorization: Bearer eyJhbGciOiJFUzI1NiIs...
```

### Resposta de sucesso — `200 OK`

```json
[
  {
    "id": "06d4fd61-3644-4f2b-9790-9d55c3c88a76",
    "versao_politica": "1.0",
    "finalidade": "Tratamento de dados pessoais para cadastro e uso da plataforma PNCP Integrador.",
    "aceito": true,
    "concedido_em": "2026-05-07T20:41:17.523453+00:00",
    "revogado_em": null
  }
]
```

> Um consentimento está **ativo** quando `revogado_em` é `null`. Use isso para indicar visualmente ao usuário o status de cada consentimento.

---

## POST /lgpd/revogar-consentimento/{consent_id}

Revoga um consentimento ativo pelo seu `id`. Após revogado, o consentimento não pode ser reativado — um novo cadastro seria necessário para gerar um novo.

**Endpoint:** `POST /lgpd/revogar-consentimento/{consent_id}`  
**Autenticação:** obrigatória — `Authorization: Bearer <access_token>`

### Exemplo de requisição

```http
POST /lgpd/revogar-consentimento/06d4fd61-3644-4f2b-9790-9d55c3c88a76 HTTP/1.1
Host: projeto-integrador-backend-six.vercel.app
Authorization: Bearer eyJhbGciOiJFUzI1NiIs...
```

> O body da requisição deve estar **vazio** — o `consent_id` vai na URL.

### Resposta de sucesso — `200 OK`

```json
{
  "mensagem": "Consentimento revogado com sucesso",
  "revogado_em": "2026-05-20T14:30:00.000000+00:00"
}
```

### Erros possíveis

| Status | `detail` | Causa |
|--------|----------|-------|
| `401` | `"Token inválido ou expirado"` | Token ausente ou expirado |
| `404` | `"Consentimento não encontrado ou já revogado"` | `consent_id` inexistente ou já revogado |

---

## DELETE /lgpd/conta

Remove **permanentemente** a conta do titular e todos os seus dados pessoais (perfil, consentimentos). Registros de auditoria são anonimizados (o `user_id` se torna `null`). A ação é **irreversível**.

**Endpoint:** `DELETE /lgpd/conta`  
**Autenticação:** obrigatória — `Authorization: Bearer <access_token>`

### Exemplo de requisição

```http
DELETE /lgpd/conta HTTP/1.1
Host: projeto-integrador-backend-six.vercel.app
Authorization: Bearer eyJhbGciOiJFUzI1NiIs...
```

### Resposta de sucesso — `204 No Content`

Sem body. Após receber `204`, o frontend deve:
1. Limpar o `access_token` e `refresh_token` do armazenamento local.
2. Redirecionar para a tela de cadastro ou landing page.

### Erros possíveis

| Status | `detail` | Causa |
|--------|----------|-------|
| `401` | `"Token inválido ou expirado"` | Token ausente ou expirado |
| `500` | Mensagem de erro interno | Falha na exclusão no Supabase Auth |

---

## Schemas LGPD

### ConsentimentoOut

```json
{
  "id":              "string — UUID do consentimento",
  "versao_politica": "string — ex: \"1.0\"",
  "finalidade":      "string — descrição da finalidade de tratamento",
  "aceito":          "boolean — sempre true (apenas consentimentos positivos são registrados)",
  "concedido_em":    "string — ISO 8601",
  "revogado_em":     "string | null — ISO 8601 se revogado, null se ativo"
}
```

### AuditLogOut

```json
{
  "id":           "string — UUID do registro",
  "acao":         "string — tipo da operação (ex: \"login\", \"cadastro\")",
  "detalhes":     "object | null — dados extras dependendo da ação",
  "realizado_em": "string — ISO 8601"
}
```

### DadosPessoaisOut

```json
{
  "perfil":        "object — todos os campos da tabela users (com cpf e telefone descriptografados)",
  "consentimentos": "ConsentimentoOut[]",
  "log_auditoria":  "AuditLogOut[]"
}
```

---

## Fluxo Recomendado no Frontend

### 1. Cadastro — checkbox de aceite obrigatório

```
Formulário de cadastro
└─ Adicionar checkbox: "Li e aceito os Termos de Uso e a Política de Privacidade"
   ├─ Desabilitado por padrão
   ├─ Botão "Cadastrar" fica desabilitado enquanto checkbox não for marcado
   └─ Enviar aceite_termos: true no body ao submeter
```

### 2. Seção "Privacidade" na área logada

Criar uma página de privacidade/configurações acessível pelo menu do usuário:

```
/privacidade
├─ GET /lgpd/consentimentos → listar consentimentos ativos e revogados
├─ POST /lgpd/revogar-consentimento/{id} → botão "Revogar" por consentimento ativo
├─ GET /lgpd/dados → botão "Exportar meus dados" (download JSON)
└─ DELETE /lgpd/conta → botão "Excluir minha conta" (com confirmação modal)
```

### 3. Exclusão de conta — fluxo com confirmação

```
1. Usuário clica em "Excluir minha conta"
2. Exibir modal de confirmação: "Esta ação é irreversível. Todos os seus dados serão excluídos."
3. Usuário confirma → DELETE /lgpd/conta
4. Resposta 204 → limpar tokens → redirecionar para /
```

### Exemplo com fetch (JavaScript)

```js
const API = 'https://projeto-integrador-backend-six.vercel.app'
const token = localStorage.getItem('token')
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${token}`,
}

// Listar consentimentos
const consentimentos = await fetch(`${API}/lgpd/consentimentos`, { headers })
  .then(r => r.json())

// Exportar dados
const dados = await fetch(`${API}/lgpd/dados`, { headers })
  .then(r => r.json())

// Revogar consentimento
await fetch(`${API}/lgpd/revogar-consentimento/${consentimentos[0].id}`, {
  method: 'POST',
  headers,
})

// Excluir conta
const res = await fetch(`${API}/lgpd/conta`, { method: 'DELETE', headers })
if (res.status === 204) {
  localStorage.removeItem('token')
  localStorage.removeItem('refresh_token')
  window.location.href = '/'
}
```

---

## Erros e Exceções

### Formato padrão de erro

```json
{ "detail": "mensagem de erro" }
```

### Erros de validação — `422 Unprocessable Entity`

```json
{
  "detail": [
    {
      "campo": "aceite_termos",
      "erro": "Value error, É necessário aceitar os termos de uso e política de privacidade para criar uma conta"
    }
  ]
}
```
