# Documento Técnico — Requisito 1: Autenticação e Segurança da Informação

**Projeto:** Projeto Integrador — Backend de Dados PNCP  
**Requisito:** Segurança da Informação — Requisito 1  
**Tema:** Sistema de Autenticação e Controle de Acesso  
**Data:** 2026-05-06  
**Responsável:** Arthur Campos  

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Arquitetura do Sistema de Autenticação](#2-arquitetura-do-sistema-de-autenticação)
3. [Componentes e Responsabilidades](#3-componentes-e-responsabilidades)
4. [Proteção de Credenciais](#4-proteção-de-credenciais)
5. [Fluxos de Autenticação](#5-fluxos-de-autenticação)
6. [Especificação das APIs de Autenticação](#6-especificação-das-apis-de-autenticação)
7. [Validação e Sanitização de Entrada](#7-validação-e-sanitização-de-entrada)
8. [Controle de Acesso por Rota](#8-controle-de-acesso-por-rota)
9. [Mascaramento e Proteção de Dados](#9-mascaramento-e-proteção-de-dados)
10. [Modelo de Dados do Usuário](#10-modelo-de-dados-do-usuário)
11. [Respostas de Erro](#11-respostas-de-erro)
12. [Dependências Utilizadas](#12-dependências-utilizadas)

---

## 1. Visão Geral

O sistema de autenticação do backend foi projetado seguindo o padrão **OAuth2 com tokens Bearer (JWT — JSON Web Token)**. O objetivo é garantir que apenas usuários com credenciais válidas possam acessar os dados do PNCP e executar os pipelines ETL armazenados no banco de dados.

### Princípios Adotados

| Princípio | Implementação |
|---|---|
| Senhas nunca em texto plano | Hash Bcrypt com pré-hashing SHA-256 |
| Sessão sem estado (Stateless) | JWT com expiração curta (30 min) |
| Dados sensíveis protegidos na resposta | CPF mascarado, senha removida |
| Validação de identidade brasileira | Validação de dígito verificador CPF e CNPJ |
| Separação entre rotas públicas e privadas | Dependency Injection via `get_current_user` |
| Conformidade com LGPD | Minimização e mascaramento de dados pessoais |

---

## 2. Arquitetura do Sistema de Autenticação

```
┌────────────────────────────────────────────────────────────┐
│                         CLIENTE                            │
│  (Browser / Aplicação Front-end / Ferramenta de API)       │
└────────────────────┬───────────────────────────────────────┘
                     │  HTTP Request
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    FASTAPI APPLICATION                      │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               ROUTERS (app/routers/)                │   │
│  │                                                     │   │
│  │  ┌──────────────────┐    ┌────────────────────────┐ │   │
│  │  │  auth.py         │    │  Rotas Protegidas       │ │   │
│  │  │  POST /register  │    │  /contratacoes/*        │ │   │
│  │  │  POST /login     │    │  /etl/run               │ │   │
│  │  │  GET  /me  ──────┼────▶  /auth/me               │ │   │
│  │  └────────┬─────────┘    └──────────┬─────────────┘ │   │
│  └───────────┼──────────────────────────┼───────────────┘   │
│              │                          │                    │
│              ▼                          ▼                    │
│  ┌─────────────────────┐   ┌────────────────────────────┐   │
│  │  SERVICES           │   │  DEPENDENCY INJECTION      │   │
│  │  (app/services/)    │   │  (app/dependencies.py)     │   │
│  │                     │   │                            │   │
│  │  auth.py            │   │  get_current_user()        │   │
│  │  - hash_password    │   │  - Extrai token Bearer     │   │
│  │  - verify_password  │   │  - Valida assinatura JWT   │   │
│  │  - create_token     │   │  - Verifica expiração      │   │
│  │  - decode_token     │   │  - Busca usuário ativo     │   │
│  │                     │   │                            │   │
│  │  user.py            │   └────────────────────────────┘   │
│  │  - create           │                                    │
│  │  - get_by_cnpj      │                                    │
│  │  - get_by_email     │                                    │
│  └──────────┬──────────┘                                    │
│             │                                               │
│             ▼                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  DATABASE (app/database.py)                           │  │
│  │  MongoDB — Coleção: users (AsyncIOMotorClient)        │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

---

## 3. Componentes e Responsabilidades

### `app/config.py` — Configurações de Segurança

Gerencia as variáveis sensíveis lidas do arquivo `.env` via **Pydantic Settings**:

```python
class Settings(BaseSettings):
    SECRET_KEY: str               # Chave HMAC para assinar os tokens JWT
    ALGORITHM: str = "HS256"      # Algoritmo de assinatura do JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Tempo de vida do token
```

> A `SECRET_KEY` é uma string aleatória de 64 caracteres hexadecimais gerada fora do código e injetada via variável de ambiente. Nunca deve ser versionada em repositórios públicos.

---

### `app/services/auth.py` — Lógica de Criptografia e JWT

Centraliza todas as operações de criptografia de senha e geração/validação de tokens.

**Funções:**

| Função | Responsabilidade |
|---|---|
| `_prehash(password)` | Aplica SHA-256 na senha antes do Bcrypt |
| `hash_password(password)` | Gera hash Bcrypt final para armazenamento |
| `verify_password(plain, hashed)` | Verifica senha fornecida contra hash armazenado |
| `create_access_token(data, expires_delta)` | Cria JWT assinado com CNPJ e expiração |
| `decode_token(token)` | Decodifica e valida assinatura e expiração do JWT |

---

### `app/dependencies.py` — Proteção das Rotas

Implementa o fluxo de autorização como uma dependência reutilizável do FastAPI:

```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db = Depends(get_database)
) -> dict:
    token = credentials.credentials
    payload = decode_token(token)          # Valida assinatura e exp
    cnpj = payload.get("sub")             # Extrai identidade
    user = await get_by_cnpj(cnpj, db)    # Verifica existência no banco
    if not user or not user.get("ativo"):
        raise HTTPException(status_code=401)
    return user
```

Qualquer rota que declare `user = Depends(get_current_user)` automaticamente exige token válido.

---

### `app/schemas/user.py` — Validação de Entrada

Schemas Pydantic que definem e validam os dados de entrada e saída:

| Schema | Uso | Campos Principais |
|---|---|---|
| `UserCreate` | Corpo do `POST /auth/register` | nome, cpf, email, telefone, password, cnpj_mei, razao_social, cnae_principal, uf, municipio |
| `UserOut` | Resposta de `/register` e `/me` | Todos os campos do usuário exceto senha; CPF mascarado |
| `TokenOut` | Resposta do `POST /auth/login` | access_token, token_type |

---

### `app/services/user.py` — Operações no Banco de Dados

| Método | Descrição |
|---|---|
| `create(data)` | Verifica unicidade do e-mail, hasheia senha, persiste usuário |
| `get_by_cnpj(cnpj, db)` | Busca usuário removendo caracteres não numéricos do CNPJ |
| `get_by_email(email, db)` | Usado para checar duplicidade no cadastro |

---

## 4. Proteção de Credenciais

### 4.1 Hashing com Bcrypt

Senhas são armazenadas exclusivamente como hash. O algoritmo escolhido é o **Bcrypt**, padrão da indústria para proteção de senhas, pelos seguintes motivos:

- **Work factor ajustável:** O custo computacional pode ser aumentado conforme o hardware evoluir, mantendo a resistência a força bruta ao longo do tempo.
- **Salt automático:** O Bcrypt incorpora um salt único e aleatório a cada hash gerado via `bcrypt.gensalt()`, tornando inviáveis ataques por *rainbow tables*.

### 4.2 Pré-hashing com SHA-256

O Bcrypt possui uma limitação técnica de **72 bytes de entrada**. Senhas maiores que isso seriam truncadas silenciosamente, comprometendo a segurança de senhas longas sem que o sistema ou o usuário percebessem.

A solução adotada é o **pré-hashing**:

```
Senha do usuário (qualquer tamanho)
        │
        ▼
  SHA-256 (hashlib)
        │
        ▼
  String hexadecimal de 64 caracteres (sempre dentro do limite de 72 bytes)
        │
        ▼
  Bcrypt (com salt aleatório)
        │
        ▼
  Hash final armazenado no banco (campo: hashed_password)
```

**Implementação (`app/services/auth.py`):**

```python
def _prehash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def hash_password(password: str) -> str:
    return _pwd_context.hash(_prehash(password))

def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(_prehash(plain), hashed)
```

> Este padrão é amplamente documentado pela comunidade de segurança como mitigação eficaz para o limite do Bcrypt. A saída SHA-256 tem tamanho fixo de 64 caracteres hexadecimais, sempre abaixo do limite de 72 bytes.

---

## 5. Fluxos de Autenticação

### 5.1 Fluxo de Cadastro (`POST /auth/register`)

```
Cliente                          API                          MongoDB
   │                              │                              │
   │─── POST /auth/register ──────▶                              │
   │    {nome, cpf, email,        │                              │
   │     password, cnpj_mei, ...} │                              │
   │                              │                              │
   │                              │── Valida campos Pydantic ──▶ │
   │                              │   (CPF, CNPJ, Email)         │
   │                              │                              │
   │                              │── Busca e-mail no banco ─────▶
   │                              │◀─ Resposta: existe? ─────────│
   │                              │                              │
   │         ◀── 400 Bad Request ─│ (se e-mail já cadastrado)    │
   │                              │                              │
   │                              │── SHA-256(senha) ──▶ Bcrypt ▶ hash
   │                              │                              │
   │                              │── Insere usuário ────────────▶
   │                              │   {nome, cpf, email,         │
   │                              │    hashed_password,          │
   │                              │    ativo: true,              │
   │                              │    criado_em: now()}         │
   │                              │◀─ {_id: ObjectId} ───────────│
   │                              │                              │
   │◀── 201 Created ──────────────│                              │
   │    {id, nome,                │                              │
   │     cpf_mascarado,           │                              │
   │     email, ...}              │                              │
```

### 5.2 Fluxo de Login (`POST /auth/login`)

```
Cliente                          API                          MongoDB
   │                              │                              │
   │─── POST /auth/login ─────────▶                              │
   │    username=cnpj             │                              │
   │    password=senha            │                              │
   │    (form-data, OAuth2)       │                              │
   │                              │                              │
   │                              │── Busca usuário por CNPJ ────▶
   │                              │◀─ Documento do usuário ──────│
   │                              │                              │
   │         ◀── 401 Unauthorized ─│ (se CNPJ não encontrado)    │
   │                              │                              │
   │                              │── verify_password() ─────────│
   │                              │   SHA-256(senha_input) vs    │
   │                              │   hashed_password            │
   │                              │                              │
   │         ◀── 401 Unauthorized ─│ (se senha incorreta)        │
   │                              │                              │
   │                              │── create_access_token() ─────│
   │                              │   payload: {sub: cnpj,       │
   │                              │             exp: now+30min}  │
   │                              │   assinado com SECRET_KEY    │
   │                              │                              │
   │◀── 200 OK ───────────────────│                              │
   │    {access_token: "eyJ...",  │                              │
   │     token_type: "bearer"}    │                              │
```

### 5.3 Fluxo de Acesso a Rota Protegida (`GET /auth/me` e demais)

```
Cliente                          API                          MongoDB
   │                              │                              │
   │─── GET /auth/me ─────────────▶                              │
   │    Authorization:            │                              │
   │    Bearer eyJhbGci...        │                              │
   │                              │                              │
   │                              │── HTTPBearer extrai token ───│
   │                              │                              │
   │                              │── decode_token() ────────────│
   │                              │   Valida assinatura HMAC-256 │
   │                              │   Verifica campo "exp"       │
   │                              │                              │
   │     ◀── 401 Unauthorized ────│ (token inválido ou expirado) │
   │                              │                              │
   │                              │── Extrai CNPJ de payload.sub │
   │                              │                              │
   │                              │── Busca usuário por CNPJ ────▶
   │                              │◀─ Documento do usuário ──────│
   │                              │                              │
   │     ◀── 401 Unauthorized ────│ (usuário não existe ou       │
   │                              │  ativo=false)                │
   │                              │                              │
   │◀── 200 OK ───────────────────│                              │
   │    {id, nome,                │                              │
   │     cpf_mascarado, ...}      │                              │
```

---

## 6. Especificação das APIs de Autenticação

### 6.1 `POST /auth/register` — Cadastro de Usuário

| Atributo | Valor |
|---|---|
| Método | `POST` |
| Autenticação | Não necessária |
| Content-Type | `application/json` |
| Status de Sucesso | `201 Created` |

**Request Body:**

```json
{
  "nome": "João da Silva",
  "cpf": "123.456.789-09",
  "email": "joao@email.com",
  "telefone": "(81) 99999-0000",
  "password": "minhaS3nh@Segura",
  "cnpj_mei": "12.345.678/0001-90",
  "razao_social": "João da Silva Consultoria MEI",
  "cnae_principal": "7490-1/04",
  "uf": "PE",
  "municipio": "Recife"
}
```

**Response (201 Created):**

```json
{
  "id": "6638a2f0e12b4a001c8d4321",
  "nome": "João da Silva",
  "cpf_mascarado": "***.456.789-**",
  "email": "joao@email.com",
  "telefone": "(81) 99999-0000",
  "cnpj_mei": "12345678000190",
  "razao_social": "João da Silva Consultoria MEI",
  "cnae_principal": "7490-1/04",
  "uf": "PE",
  "municipio": "Recife",
  "ativo": true,
  "criado_em": "2026-05-06T19:15:00Z"
}
```

**Erros possíveis:**

| Status | Condição |
|---|---|
| `400 Bad Request` | E-mail já cadastrado |
| `422 Unprocessable Entity` | CPF inválido, CNPJ inválido, formato incorreto |

---

### 6.2 `POST /auth/login` — Autenticação e Emissão de Token

| Atributo | Valor |
|---|---|
| Método | `POST` |
| Autenticação | Não necessária |
| Content-Type | `application/x-www-form-urlencoded` (padrão OAuth2) |
| Status de Sucesso | `200 OK` |

**Request Body (Form-Data):**

```
username=12345678000190
password=minhaS3nh@Segura
```

> O campo `username` segue a convenção do padrão OAuth2 `password flow`, mas na prática contém o **CNPJ** da empresa MEI.

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODAwMDE5MCIsImV4cCI6MTcxNTAxMjIwMH0.abc123...",
  "token_type": "bearer"
}
```

**Estrutura do JWT (payload decodificado):**

```json
{
  "sub": "12345678000190",
  "exp": 1715012200
}
```

**Erros possíveis:**

| Status | Condição |
|---|---|
| `401 Unauthorized` | CNPJ não encontrado ou senha incorreta |

---

### 6.3 `GET /auth/me` — Dados do Usuário Autenticado

| Atributo | Valor |
|---|---|
| Método | `GET` |
| Autenticação | **Obrigatória** — `Authorization: Bearer <token>` |
| Status de Sucesso | `200 OK` |

**Response (200 OK):**

```json
{
  "id": "6638a2f0e12b4a001c8d4321",
  "nome": "João da Silva",
  "cpf_mascarado": "***.456.789-**",
  "email": "joao@email.com",
  "telefone": "(81) 99999-0000",
  "cnpj_mei": "12345678000190",
  "razao_social": "João da Silva Consultoria MEI",
  "cnae_principal": "7490-1/04",
  "uf": "PE",
  "municipio": "Recife",
  "ativo": true,
  "criado_em": "2026-05-06T19:15:00Z"
}
```

**Erros possíveis:**

| Status | Condição |
|---|---|
| `401 Unauthorized` | Token ausente, assinatura inválida, token expirado |
| `401 Unauthorized` | Usuário não encontrado ou desativado no banco |

---

## 7. Validação e Sanitização de Entrada

A camada de validação é implementada via **Pydantic** (`app/schemas/user.py`) e executada antes de qualquer lógica de negócio.

### 7.1 Validação do CPF

```python
@field_validator("cpf")
def validate_cpf(cls, v):
    digits = re.sub(r"\D", "", v)
    # Bloqueia sequências repetidas (ex: 111.111.111-11)
    if len(set(digits)) == 1:
        raise ValueError("CPF inválido")
    # Algoritmo mod-11 para verificar os dois dígitos verificadores
    ...
```

- Remove caracteres não numéricos (`re.sub(r"\D", "", v)`) — evita injeção de scripts via campos de documento
- Valida comprimento: exatamente 11 dígitos
- Rejeita sequências idênticas (e.g., `000.000.000-00`)
- Verifica os dígitos verificadores pelo algoritmo mod-11 oficial

### 7.2 Validação do CNPJ

Mesma lógica do CPF, adaptada para 14 dígitos e o algoritmo mod-11 com pesos específicos do CNPJ. Aceita formatos com ou sem pontuação (`12.345.678/0001-90` ou `12345678000190`).

### 7.3 Validação de E-mail

Utiliza o tipo `EmailStr` do Pydantic, que aplica validação conforme a RFC 5322. Aceita apenas endereços de e-mail válidos (`usuario@dominio.com`).

### 7.4 Normalização de UF

```python
@field_validator("uf")
def normalize_uf(cls, v):
    return v.upper()
```

Garante consistência no banco, independente da forma como o usuário informou a UF.

### 7.5 Sanitização no Login

No login, o CNPJ é normalizado antes da consulta ao banco:

```python
def get_by_cnpj(cnpj: str):
    cnpj_digits = re.sub(r"\D", "", cnpj)
    # Consulta MongoDB com o CNPJ apenas com dígitos
```

Isso previne ataques de injeção NoSQL por meio de operadores MongoDB embutidos em strings de identificadores.

---

## 8. Controle de Acesso por Rota

| Rota | Método | Acesso | Mecanismo |
|---|---|---|---|
| `/auth/register` | `POST` | Público | Nenhum |
| `/auth/login` | `POST` | Público | Nenhum |
| `/auth/me` | `GET` | Privado | `Depends(get_current_user)` |
| `/contratacoes/` | `GET` | Privado | `Depends(get_current_user)` |
| `/contratacoes/{id}` | `GET` | Privado | `Depends(get_current_user)` |
| `/etl/run` | `POST` | Privado | `Depends(get_current_user)` |
| `/health` | `GET` | Público | Nenhum |

**Justificativa para proteção do `/etl/run`:**  
A rota de ETL realiza requisições externas à API do PNCP e operações de escrita em massa no MongoDB. Sem autenticação, qualquer agente externo poderia disparar processamentos arbitrários, causando consumo excessivo de recursos (DoS) e sobrecarga no banco de dados.

---

## 9. Mascaramento e Proteção de Dados

Em conformidade com o princípio de **Privacy by Design** e as diretrizes da **LGPD (Lei Geral de Proteção de Dados — Lei nº 13.709/2018)**:

### 9.1 Remoção da Senha nas Respostas

O campo `hashed_password` **nunca** é retornado em nenhum endpoint. O schema `UserOut` não inclui esse campo, e o FastAPI serializa apenas os campos definidos no schema de resposta.

### 9.2 Mascaramento do CPF

O CPF, dado pessoal sensível, é retornado mascarado em todas as respostas:

```
CPF armazenado:  12345678909
CPF na resposta: "***.456.789-**"
```

**Implementação:**

```python
@computed_field
@property
def cpf_mascarado(self) -> str:
    d = self.cpf  # string com 11 dígitos
    return f"***.{d[3:6]}.{d[6:9]}-**"
```

O dado bruto permanece no banco para fins de identificação interna, mas **jamais trafega em respostas de API**.

---

## 10. Modelo de Dados do Usuário

Documento armazenado na coleção `users` do MongoDB:

```json
{
  "_id": "ObjectId('6638a2f0e12b4a001c8d4321')",
  "nome": "João da Silva",
  "cpf": "12345678909",
  "email": "joao@email.com",
  "telefone": "(81) 99999-0000",
  "hashed_password": "$2b$12$eImiTXuWVxfM37uY4JANjQ...",
  "cnpj_mei": "12345678000190",
  "razao_social": "João da Silva Consultoria MEI",
  "cnae_principal": "7490-1/04",
  "uf": "PE",
  "municipio": "Recife",
  "ativo": true,
  "criado_em": "2026-05-06T19:15:00.000Z"
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `_id` | ObjectId | Identificador único do MongoDB |
| `nome` | String | Nome completo do usuário |
| `cpf` | String (11 dígitos) | CPF (apenas dígitos, armazenamento interno) |
| `email` | String | E-mail único, usado para verificar duplicidade |
| `telefone` | String | Telefone de contato |
| `hashed_password` | String | Hash Bcrypt (SHA-256 + Bcrypt) |
| `cnpj_mei` | String (14 dígitos) | CNPJ MEI — identificador principal para login |
| `razao_social` | String | Nome da empresa |
| `cnae_principal` | String | Código de atividade econômica |
| `uf` | String (2 chars) | Unidade Federativa, sempre maiúsculo |
| `municipio` | String | Nome do município |
| `ativo` | Boolean | Indica se o usuário pode realizar login |
| `criado_em` | String ISO 8601 | Timestamp de criação do registro |

---

## 11. Respostas de Erro

O FastAPI é configurado em `app/main.py` para retornar erros de validação com formato padronizado.

### Erro de Validação (422)

```json
{
  "detail": [
    {
      "loc": ["body", "cpf"],
      "msg": "CPF inválido",
      "type": "value_error"
    }
  ]
}
```

### Erro de Autenticação (401)

```json
{
  "detail": "Token inválido ou expirado"
}
```

### Erro de Conflito no Cadastro (400)

```json
{
  "detail": "E-mail já cadastrado"
}
```

---

## 12. Dependências Utilizadas

| Biblioteca | Versão | Papel na Autenticação |
|---|---|---|
| `fastapi` | ≥ 0.115.0 | Framework web, roteamento e Dependency Injection |
| `python-jose[cryptography]` | ≥ 3.3.0 | Geração e validação de tokens JWT (HS256) |
| `bcrypt` | ≥ 4.0.0 | Hashing de senhas com salt automático |
| `passlib[bcrypt]` | — | Abstração sobre bcrypt para `CryptContext` |
| `pydantic` | ≥ 2.7.0 | Validação e sanitização de esquemas de entrada |
| `pydantic[email]` | ≥ 2.7.0 | Validação de formato de e-mail (RFC 5322) |
| `pydantic-settings` | ≥ 2.3.0 | Leitura segura de variáveis de ambiente |
| `python-multipart` | ≥ 0.0.9 | Suporte a `application/x-www-form-urlencoded` (OAuth2 login) |
| `motor` | ≥ 3.5.0 | Driver async MongoDB para operações de usuário |
