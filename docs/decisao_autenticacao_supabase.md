# Documento Técnico — Decisão Arquitetural: Migração para Supabase Auth

**Projeto:** Projeto Integrador — Backend de Dados PNCP  
**Requisito:** Segurança da Informação — Requisito 1 (Revisão)  
**Tema:** Substituição do sistema de autenticação próprio (bcrypt + JWT) por Supabase Auth  
**Data:** 2026-05-07  
**Responsável:** Arthur Campos  

---

## Sumário

1. [Contexto e Motivação](#1-contexto-e-motivação)
2. [Comparativo: Implementação Própria vs Supabase Auth](#2-comparativo-implementação-própria-vs-supabase-auth)
3. [Riscos da Implementação Própria](#3-riscos-da-implementação-própria)
4. [Por que o Supabase resolve esses riscos](#4-por-que-o-supabase-resolve-esses-riscos)
5. [Nova Arquitetura do Sistema](#5-nova-arquitetura-do-sistema)
6. [Separação de Responsabilidades: Supabase e MongoDB](#6-separação-de-responsabilidades-supabase-e-mongodb)
7. [Fluxos de Autenticação Revisados](#7-fluxos-de-autenticação-revisados)
8. [Validação do JWT do Supabase no FastAPI](#8-validação-do-jwt-do-supabase-no-fastapi)
9. [Modelo de Dados](#9-modelo-de-dados)
10. [Dependências Revisadas](#10-dependências-revisadas)
11. [Considerações sobre o Plano Gratuito](#11-considerações-sobre-o-plano-gratuito)

---

## 1. Contexto e Motivação

A versão inicial do sistema implementava autenticação inteiramente no próprio backend: hashing de senhas com **bcrypt** (com pré-hashing SHA-256), emissão de **JWT próprio** assinado com `python-jose`, e armazenamento de usuários na coleção `users` do **MongoDB Atlas**.

Essa abordagem, embora funcional, exige que a equipe de desenvolvimento assuma a responsabilidade integral pela corretude e segurança de cada etapa do fluxo de autenticação — uma responsabilidade que é crítica e, ao mesmo tempo, periférica ao objetivo central do projeto, que é a análise de dados do PNCP.

A decisão foi migrar a autenticação e o armazenamento de dados de usuários para o **Supabase**, mantendo o **MongoDB** com foco exclusivo na **arquitetura medalhão** (Bronze / Silver / Gold) para os dados do PNCP.

---

## 2. Comparativo: Implementação Própria vs Supabase Auth

| Critério | Bcrypt + JWT próprio | Supabase Auth |
|---|---|---|
| **Hashing de senha** | Implementado manualmente (SHA-256 + bcrypt) | Bcrypt gerenciado internamente pelo Supabase |
| **Emissão de JWT** | Gerado no próprio backend com `python-jose` | Gerado pelo Supabase com RS256 (chave assimétrica) |
| **Validação de JWT** | Verificação local com SECRET_KEY simétrica | Verificação local com JWT_SECRET do projeto |
| **Refresh token** | Não implementado (sessão expira em 30 min) | Implementado nativamente |
| **Reset de senha** | Não implementado | Nativo com envio de e-mail |
| **Confirmação de e-mail** | Não implementado | Nativo, configurável |
| **Bloqueio por tentativas falhas** | Não implementado | Configurável via dashboard |
| **Auditoria de login** | Não implementado | Logs nativos no dashboard |
| **Armazenamento de usuários** | MongoDB (coleção `users`) | Supabase (PostgreSQL — `auth.users` + tabela `public.users`) |
| **Manutenção de segurança** | Responsabilidade da equipe | Responsabilidade da Supabase |
| **Conformidade** | Manual | SOC 2 Type II certificado |

---

## 3. Riscos da Implementação Própria

### 3.1 Implementação manual de criptografia

O código original implementava um pipeline de hashing em duas etapas:

```python
def _prehash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def hash_password(password: str) -> str:
    return _pwd_context.hash(_prehash(password))
```

Embora tecnicamente correto para mitigar o limite de 72 bytes do bcrypt, qualquer alteração futura nessa lógica (ex: mudar o algoritmo de pré-hashing, mudar o work factor do bcrypt) exigiria uma migração cuidadosa de todos os hashes armazenados. **Esse tipo de migração é de alto risco e frequentemente negligenciado.**

### 3.2 Ausência de refresh token

O JWT emitido expirava em 30 minutos sem nenhum mecanismo de renovação. Na prática, isso significa que o usuário seria deslogado abruptamente no meio de uma sessão de uso, comprometendo a experiência de uso e incentivando contornos inseguros (como aumentar o tempo de expiração indefinidamente).

### 3.3 Sem proteção contra força bruta

Nenhum mecanismo de rate-limiting ou bloqueio por tentativas falhas estava implementado no endpoint `/auth/login`. Um atacante poderia realizar tentativas ilimitadas de senha sem qualquer obstáculo.

### 3.4 Rotação de SECRET_KEY

O JWT era assinado com uma chave simétrica (`SECRET_KEY`) armazenada em variável de ambiente. Rotacionar essa chave — operação de segurança recomendada periodicamente — invalidaria **todos os tokens ativos** simultaneamente, causando logout forçado de todos os usuários.

### 3.5 Ausência de auditoria

Não havia nenhum registro de tentativas de login, logins bem-sucedidos, ou eventos de segurança. Em caso de incidente, seria impossível rastrear o acesso indevido.

---

## 4. Por que o Supabase resolve esses riscos

O **Supabase Auth** é uma implementação de autenticação battle-tested, baseada no **GoTrue** (open source, mantido pela equipe do Supabase), que resolve estruturalmente todos os pontos acima:

### 4.1 Criptografia gerenciada

O Supabase cuida do hashing de senhas internamente usando bcrypt com work factor adequado. Atualizações de segurança no algoritmo são aplicadas pelo provedor, sem intervenção da equipe.

### 4.2 JWT com RS256 (chave assimétrica)

Ao contrário do HS256 (chave simétrica) usado na implementação anterior, o Supabase emite JWTs assinados com **RS256** (RSA + SHA-256, chave assimétrica). Isso significa:

- A chave privada que assina os tokens **nunca sai do Supabase**
- O backend valida usando apenas a chave pública (ou o `JWT_SECRET` disponível no dashboard)
- Rotacionar chaves não invalida tokens já emitidos durante a transição

### 4.3 Refresh token nativo

O Supabase emite um par `access_token` (JWT de curta duração) + `refresh_token` (opaco, de longa duração). O frontend renova o access token transparentemente, sem forçar o usuário a fazer novo login.

```
access_token  →  validade curta (1 hora por padrão)
refresh_token →  validade longa (configurável, padrão 60 dias)
```

### 4.4 Proteção nativa contra força bruta

O Supabase implementa rate-limiting automático nas tentativas de login, bloqueando temporariamente IPs com muitas tentativas falhas — sem nenhuma linha de código adicional.

### 4.5 Auditoria e observabilidade

O dashboard do Supabase oferece logs de todos os eventos de autenticação: logins, registros, tokens emitidos, falhas. Isso atende ao requisito de **rastreabilidade** da LGPD e de boas práticas de segurança.

---

## 5. Nova Arquitetura do Sistema

```
┌──────────────────────────────────────────────────────────────────────┐
│                              CLIENTE                                  │
│         (Browser / Aplicação Front-end / Ferramenta de API)           │
└───────────────────────┬──────────────────────────────────────────────┘
                        │  HTTP Request
                        ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        FASTAPI APPLICATION                            │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                       ROUTERS                                │    │
│  │                                                              │    │
│  │  ┌─────────────────┐   ┌──────────────┐   ┌──────────────┐  │    │
│  │  │   auth.py       │   │contratacoes  │   │   etl.py     │  │    │
│  │  │  POST /register │   │   .py        │   │  POST /run   │  │    │
│  │  │  POST /login    │   │  GET /       │   │              │  │    │
│  │  │  GET  /me       │   │  GET /{id}   │   │              │  │    │
│  │  └────────┬────────┘   └──────┬───────┘   └──────┬───────┘  │    │
│  └───────────┼────────────────────┼──────────────────┼──────────┘    │
│              │                    │                  │               │
│              ▼                    ▼                  ▼               │
│  ┌───────────────────┐   ┌──────────────────────────────────────┐   │
│  │  SUPABASE SERVICE │   │        DEPENDENCY INJECTION          │   │
│  │  (services/       │   │        (dependencies.py)             │   │
│  │   supabase.py)    │   │                                      │   │
│  │                   │   │  get_current_user()                  │   │
│  │  - register()     │   │  - Extrai Bearer token               │   │
│  │  - login()        │   │  - Valida JWT com JWT_SECRET local   │   │
│  │  - get_profile()  │   │  - Extrai user_id (sub do payload)   │   │
│  └────────┬──────────┘   └──────────────────────────────────────┘   │
│           │                                                          │
└───────────┼──────────────────────────────────────────────────────────┘
            │
    ┌───────┴────────────────────────────────────────┐
    │                                                │
    ▼                                                ▼
┌───────────────────────────┐      ┌─────────────────────────────────┐
│         SUPABASE           │      │            MONGODB ATLAS         │
│                            │      │                                  │
│  auth.users                │      │  bronze_contratacoes             │
│  ├─ id (uuid)              │      │  ├─ Dados brutos da API PNCP    │
│  ├─ email                  │      │  └─ Ingestão sem transformação   │
│  └─ encrypted_password     │      │                                  │
│                            │      │  silver_contratacoes             │
│  public.users              │      │  ├─ Dados limpos e normalizados  │
│  ├─ id (FK → auth.users)   │      │  └─ Tipos e formatos corretos    │
│  ├─ nome                   │      │                                  │
│  ├─ cpf                    │      │  gold_contratacoes               │
│  ├─ cnpj                   │      │  ├─ Dados agregados              │
│  └─ ativo                  │      │  └─ Prontos para análise         │
└───────────────────────────┘      └─────────────────────────────────┘
```

---

## 6. Separação de Responsabilidades: Supabase e MongoDB

A divisão entre os dois sistemas segue o princípio da **coesão de dados**: cada sistema armazena os dados que naturalmente pertencem ao seu domínio.

| Dado | Sistema | Justificativa |
|---|---|---|
| Credenciais (senha, e-mail de auth) | Supabase `auth.users` | Gerenciado pelo sistema de auth |
| Perfil do usuário (CPF, CNPJ, nome) | Supabase `public.users` | Dado relacional estruturado, vinculado ao auth user |
| Dados brutos da API PNCP | MongoDB `bronze_contratacoes` | Semi-estruturado, alto volume, esquema variável |
| Dados limpos do PNCP | MongoDB `silver_contratacoes` | Semi-estruturado, transformado mas flexível |
| Dados agregados do PNCP | MongoDB `gold_contratacoes` | Semi-estruturado, prontos para análise |

O MongoDB **não armazena mais nenhum dado de usuário**. Ele é dedicado exclusivamente à **arquitetura medalhão** para dados do PNCP.

### Arquitetura Medalhão no MongoDB

```
API PNCP
   │
   ▼
Bronze  →  Dados brutos, exatamente como vêm da API
   │       Sem transformação, sem remoção de campos
   ▼
Silver  →  Dados limpos: tipos corretos (datas, valores monetários),
   │       campos normalizados, registros inválidos removidos
   ▼
Gold    →  Dados prontos para consumo: agregações por UF, município,
           modalidade, faixa de valor, período
```

---

## 7. Fluxos de Autenticação Revisados

### 7.1 Fluxo de Cadastro (`POST /auth/register`)

```
Cliente                     FastAPI                      Supabase
   │                           │                             │
   │── POST /auth/register ────▶                             │
   │   {email, password,       │                             │
   │    nome, cpf, cnpj}       │                             │
   │                           │                             │
   │                           │── supabase.auth.sign_up() ──▶
   │                           │   {email, password}         │
   │                           │◀─ {user.id, session} ───────│
   │                           │                             │
   │                           │── INSERT INTO public.users ─▶
   │                           │   {id: user.id,             │
   │                           │    nome, cpf, cnpj, ativo}  │
   │                           │                             │
   │◀── 201 Created ───────────│                             │
   │    {id, nome,             │                             │
   │     cpf_mascarado, ...}   │                             │
```

### 7.2 Fluxo de Login (`POST /auth/login`)

```
Cliente                     FastAPI                      Supabase
   │                           │                             │
   │── POST /auth/login ────────▶                             │
   │   {email, password}        │                             │
   │                           │                             │
   │                           │── supabase.auth              │
   │                           │   .sign_in_with_password() ─▶
   │                           │                             │
   │                           │◀─ {access_token,            │
   │                           │    refresh_token,           │
   │                           │    expires_in} ─────────────│
   │                           │                             │
   │◀── 200 OK ────────────────│                             │
   │    {access_token,         │                             │
   │     refresh_token,        │                             │
   │     token_type: "bearer"} │                             │
```

### 7.3 Fluxo de Acesso a Rota Protegida

```
Cliente                     FastAPI                      Supabase
   │                           │                             │
   │── GET /contratacoes/ ─────▶                             │
   │   Authorization:          │                             │
   │   Bearer eyJhbGci...      │                             │
   │                           │                             │
   │                           │── Extrai token do header ───│
   │                           │                             │
   │                           │── Valida JWT localmente ─── │
   │                           │   (JWT_SECRET, sem          │
   │                           │    chamada de rede)         │
   │                           │                             │
   │    ◀── 401 Unauthorized ───│ (token inválido/expirado)  │
   │                           │                             │
   │                           │── Extrai user_id do         │
   │                           │   payload.sub               │
   │                           │                             │
   │◀── 200 OK ────────────────│                             │
   │    {dados...}             │                             │
```

> **Ponto importante:** A validação do JWT na rota protegida é feita **localmente** no FastAPI, sem nenhuma chamada de rede ao Supabase. O `JWT_SECRET` disponível no dashboard do Supabase é suficiente para verificar a assinatura criptográfica do token. Isso mantém a latência das rotas protegidas igual à da implementação anterior.

---

## 8. Validação do JWT do Supabase no FastAPI

O token emitido pelo Supabase é um JWT padrão. O payload contém:

```json
{
  "sub": "uuid-do-usuario-no-supabase",
  "email": "joao@email.com",
  "role": "authenticated",
  "exp": 1715012200,
  "iat": 1715008600
}
```

A dependency `get_current_user` em `app/dependencies.py` valida esse token usando `python-jose`:

```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"]
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token sem identificação de usuário")

    return {"user_id": user_id, "email": payload.get("email")}
```

O campo `sub` contém o UUID do usuário no Supabase. Se a rota precisar de dados do perfil (nome, CNPJ, etc.), uma consulta adicional ao Supabase (`public.users`) é feita com esse UUID.

---

## 9. Modelo de Dados

### 9.1 Supabase — `auth.users` (gerenciado automaticamente)

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID | Identificador único (referenciado em `public.users`) |
| `email` | Text | E-mail do usuário (usado para login) |
| `encrypted_password` | Text | Hash bcrypt gerenciado pelo Supabase |
| `created_at` | Timestamptz | Timestamp de criação |
| `last_sign_in_at` | Timestamptz | Último login (auditoria) |

### 9.2 Supabase — `public.users` (gerenciado pela aplicação)

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | UUID | FK para `auth.users.id` |
| `nome` | Text | Nome completo do usuário |
| `cpf` | Text | CPF (apenas dígitos, 11 chars) |
| `cnpj` | Text | CNPJ MEI (apenas dígitos, 14 chars) |
| `ativo` | Boolean | Flag de ativação da conta |
| `created_at` | Timestamptz | Timestamp de criação do perfil |

### 9.3 MongoDB — Coleções da Arquitetura Medalhão

**`bronze_contratacoes`** — Dados brutos da API PNCP
```json
{
  "_id": "ObjectId",
  "ingested_at": "2026-05-07T15:00:00Z",
  "source": "pncp_api",
  "raw_data": { /* payload exato da API, sem modificação */ }
}
```

**`silver_contratacoes`** — Dados limpos e normalizados
```json
{
  "_id": "ObjectId",
  "numero_controle_pncp": "12345678000190-1-000001-2026",
  "orgao_nome": "Prefeitura de Recife",
  "valor_total_estimado": 5000.00,
  "data_publicacao": "2026-01-15",
  "uf": "PE",
  "municipio_ibge": "2611606",
  "modalidade_id": 8,
  "processed_at": "2026-05-07T15:05:00Z"
}
```

**`gold_contratacoes`** — Dados agregados para análise
```json
{
  "_id": "ObjectId",
  "periodo": "2026-01",
  "uf": "PE",
  "municipio_ibge": "2611606",
  "total_contratos": 143,
  "valor_total": 2150000.00,
  "valor_medio": 15034.97,
  "aggregated_at": "2026-05-07T15:10:00Z"
}
```

---

## 10. Dependências Revisadas

### Adicionadas

| Biblioteca | Versão | Papel |
|---|---|---|
| `supabase` | ≥ 2.0.0 | SDK Python do Supabase para operações de auth e banco |

### Removidas

| Biblioteca | Motivo da Remoção |
|---|---|
| `bcrypt` | Hashing de senha passa a ser responsabilidade do Supabase |
| `python-multipart` | Login por `form-data` OAuth2 substituído por JSON via Supabase SDK |

### Mantidas

| Biblioteca | Papel |
|---|---|
| `python-jose[cryptography]` | Validação local do JWT emitido pelo Supabase |
| `motor` | Driver async para MongoDB (dados PNCP) |
| `pydantic` | Validação de schemas de entrada e saída |
| `fastapi` | Framework web e dependency injection |

---

## 11. Considerações sobre o Plano Gratuito

O projeto utiliza o **Supabase Free Tier**, suficiente para os volumes esperados:

| Recurso | Limite Free Tier | Uso Esperado |
|---|---|---|
| Usuários ativos por mês | 50.000 | < 100 |
| Requests de autenticação | Ilimitado | Baixo |
| Projetos simultâneos | 2 | 1 |

**Limitação relevante:** Projetos no plano gratuito são **pausados automaticamente após 7 dias sem atividade**. Enquanto pausado, os endpoints de autenticação retornam erro até que o projeto seja reativado manualmente via dashboard do Supabase.

Para um projeto acadêmico com uso esporádico, esse comportamento é esperado e administrável. Se o projeto evoluir para produção contínua, o upgrade para o plano Pro (US$ 25/mês) desabilita a pausa automática.
