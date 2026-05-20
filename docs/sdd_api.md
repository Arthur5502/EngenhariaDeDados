# Software Design Document (SDD) - APIs do Projeto Integrador Backend

Este documento descreve as rotas de API disponíveis no projeto, com foco especial no fluxo de autenticação (cadastro, login e recuperação de dados do usuário logado), além das demais rotas do sistema (Contratações e ETL).

## Sumário
1. [Fluxo de Autenticação](#1-fluxo-de-autentica%C3%A7%C3%A3o)
    *   [Cadastro de Usuário (`/auth/register`)](#cadastro-de-usu%C3%A1rio-authregister)
    *   [Login (`/auth/login`)](#login-authlogin)
    *   [Informações do Usuário Logado (`/auth/me`)](#informa%C3%A7%C3%B5es-do-usu%C3%A1rio-logado-authme)
2. [APIs de Contratações](#2-apis-de-contrata%C3%A7%C3%B5es)
    *   [Listar Contratações (`/contratacoes/`)](#listar-contrata%C3%A7%C3%B5es-contratacoes)
    *   [Buscar Contratação Específica (`/contratacoes/{numero_controle_pncp}`)](#buscar-contrata%C3%A7%C3%A3o-espec%C3%ADfica-contratacoesnumero_controle_pncp)
3. [APIs de ETL](#3-apis-de-etl)
    *   [Executar Pipeline ETL (`/etl/run`)](#executar-pipeline-etl-etlrun)

---

## 1. Fluxo de Autenticação

O sistema utiliza autenticação baseada em tokens JWT (JSON Web Token). Rotas protegidas (como `/auth/me`, `/contratacoes` e `/etl`) exigem o envio do token no cabeçalho da requisição no formato `Authorization: Bearer <token>`.

### Cadastro de Usuário (`/auth/register`)

Endpoint utilizado para criar uma nova conta de usuário. 

*   **Método:** `POST`
*   **Autenticação:** Não necessária.
*   **Body (JSON):**
    ```json
    {
      "nome": "João da Silva",
      "cpf": "123.456.789-00",
      "email": "joao@email.com",
      "telefone": "(11) 98765-4321",
      "password": "senha_super_secreta",
      "cnpj_mei": "12.345.678/0001-90",
      "razao_social": "João da Silva Soluções MEI",
      "cnae_principal": "6204-0/00",
      "uf": "SP",
      "municipio": "São Paulo"
    }
    ```
    *Atenção: CPF e CNPJ passam por validação de formato e de dígito verificador. A senha não tem limite de caracteres devido ao uso prévio de hash SHA-256 antes do bcrypt.*

*   **Resposta de Sucesso (201 Created):** Retorna os dados do usuário criados (sem a senha).
    ```json
    {
      "id": "60a7b5... (Object ID do Mongo)",
      "nome": "João da Silva",
      "cpf_mascarado": "***.456.789-**",
      "email": "joao@email.com",
      "telefone": "(11) 98765-4321",
      "cnpj_mei": "12345678000190",
      "razao_social": "João da Silva Soluções MEI",
      "cnae_principal": "6204-0/00",
      "uf": "SP",
      "municipio": "São Paulo",
      "ativo": true,
      "criado_em": "2026-05-04T17:50:00Z"
    }
    ```

### Login (`/auth/login`)

Endpoint utilizado para autenticar o usuário e gerar o token de acesso (JWT).

*   **Método:** `POST`
*   **Autenticação:** Não necessária.
*   **Content-Type:** `application/x-www-form-urlencoded` (Padrão OAuth2)
*   **Body (Form-Data):**
    *   `username`: O CNPJ do usuário (ex: `12345678000190`)
    *   `password`: A senha cadastrada.

*   **Resposta de Sucesso (200 OK):**
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer"
    }
    ```

### Informações do Usuário Logado (`/auth/me`)

Endpoint utilizado para buscar os dados completos do usuário que está atualmente logado.

*   **Método:** `GET`
*   **Autenticação:** **Necessária** (`Authorization: Bearer <token>`).
*   **Funcionamento:** 
    1. O sistema lê o token do cabeçalho.
    2. Valida a assinatura e a expiração do JWT.
    3. Extrai o CNPJ do campo `sub` (subject) do payload do token.
    4. Consulta o banco de dados pelo CNPJ para garantir que o usuário ainda existe e está `ativo`.
*   **Resposta de Sucesso (200 OK):**
    ```json
    {
      "id": "60a7b5...",
      "nome": "João da Silva",
      "cpf_mascarado": "***.456.789-**",
      "email": "joao@email.com",
      "telefone": "(11) 98765-4321",
      "cnpj_mei": "12345678000190",
      "razao_social": "João da Silva Soluções MEI",
      "cnae_principal": "6204-0/00",
      "uf": "SP",
      "municipio": "São Paulo",
      "ativo": true,
      "criado_em": "2026-05-04T17:50:00Z"
    }
    ```

---

## 2. APIs de Contratações

As APIs de Contratações disponibilizam os dados consumidos do PNCP e que estão armazenados no MongoDB.

### Listar Contratações (`/contratacoes/`)

Lista de forma paginada e com filtros as contratações presentes no banco.

*   **Método:** `GET`
*   **Autenticação:** **Necessária**.
*   **Query Params (Opcionais):**
    *   `pagina` (int): Página atual (padrão: 1)
    *   `tamanho_pagina` (int): Itens por página (padrão: 20, máx: 100)
    *   `uf` (string): Filtrar por UF (ex: `PE`)
    *   `municipio_ibge` (string): Filtrar pelo código IBGE do município.
    *   `situacao_compra_id` (int): ID da situação da compra.
    *   `ano_compra` (int): Ano da compra.
*   **Resposta de Sucesso (200 OK):**
    ```json
    {
      "total": 150,
      "pagina": 1,
      "tamanho_pagina": 20,
      "data": [
        {
           // Dados mapeados no schema ContratacaoOut
           "numero_controle_pncp": "12345/2026",
           "orgao_nome": "Prefeitura de Exemplo",
           "valor_total_estimado": 5000.00,
           // ...
        }
      ]
    }
    ```

### Buscar Contratação Específica (`/contratacoes/{numero_controle_pncp}`)

Retorna os detalhes de uma contratação pelo seu Número de Controle PNCP.

*   **Método:** `GET`
*   **Autenticação:** **Necessária**.
*   **Path Params:**
    *   `numero_controle_pncp` (string): Número de controle completo. Ex: `12345678000190-1-000001-2026`
*   **Resposta de Sucesso (200 OK):** Retorna o objeto `ContratacaoOut` correspondente. (Gera 404 caso não encontrado).

---

## 3. APIs de ETL

APIs utilizadas para extrair dados do PNCP (Portal Nacional de Contratações Públicas), transformar (limpar/adequar) e carregar (inserir) no MongoDB.

### Executar Pipeline ETL (`/etl/run`)

Dispara um novo processamento ETL com base nos parâmetros enviados.

*   **Método:** `POST`
*   **Autenticação:** **Necessária**.
*   **Body (JSON - baseado em ETLParams):**
    ```json
    {
      "uf": "PE",
      "codigo_municipio_ibge": "2611606",
      "codigo_modalidade": 1,
      "data_final": "2026-12-31" 
    }
    ```
*   **Comportamento:**
    1. Instancia o `PNCPService` com UF e/ou Código IBGE para extrair os dados.
    2. Utiliza o `TransformService` para padronizar as informações.
    3. Instancia o `MongoService` para inserir ou atualizar os dados no banco de dados.
*   **Resposta de Sucesso (200 OK):**
    ```json
    {
      "extraidos": 105,
      "transformados": 100,
      "inseridos": 100,
      "mensagem": "ETL executado com sucesso."
    }
    ```
