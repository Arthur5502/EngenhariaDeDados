# ETL — Portal Nacional de Contratações Públicas (PNCP)

Pipeline de Engenharia de Dados para coleta, tratamento e persistência de dados de contratações públicas municipais disponibilizados pela API do PNCP.

---

## Proposta

O objetivo é construir um pipeline ETL (Extract, Transform, Load) que consuma a API pública do [PNCP](https://pncp.gov.br) para coletar dados de contratações por dispensa eletrônica no município de Recife/PE, normalizar as informações e armazená-las no MongoDB Atlas para análises futuras.

---

## Arquitetura da Solução

```
┌─────────────────────────────────────────────────────────────┐
│                        FONTE DE DADOS                       │
│              API PNCP (pncp.gov.br/api/consulta)            │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP GET (paginado)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    EXTRACT (src/extract.py)                  │
│  PNCPExtractor — itera páginas e coleta todos os registros  │
└────────────────────────┬────────────────────────────────────┘
                         │ list[dict] (dados brutos)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  TRANSFORM (src/transform.py)                │
│  PNCPTransformer — normaliza campos aninhados, seleciona    │
│  atributos relevantes e adiciona metadados de controle      │
└────────────────────────┬────────────────────────────────────┘
                         │ list[dict] (dados normalizados)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    LOAD (src/load.py)                        │
│  MongoDBLoader — insere documentos no MongoDB Atlas         │
└────────────────────────┬────────────────────────────────────┘
                         │ insert_many
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     MongoDB Atlas                           │
│          banco: pncp   |   coleção: contratacoes            │
└─────────────────────────────────────────────────────────────┘
```

---

## Estrutura do Projeto

```
.
├── main.py               # Ponto de entrada — orquestra o ETL
├── src/
│   ├── __init__.py
│   ├── extract.py        # Classe PNCPExtractor
│   ├── transform.py      # Classe PNCPTransformer
│   └── load.py           # Classe MongoDBLoader
├── .env                  # Credenciais do MongoDB (não versionado)
├── .gitignore
└── README.md
```

---

## Fluxo de Dados

### 1. Extract
- `PNCPExtractor` recebe como parâmetros: UF, código IBGE do município, código da modalidade e data final.
- O método `extract_all()` percorre automaticamente todas as páginas da API, acumulando os registros brutos em uma lista.

### 2. Transform
- `PNCPTransformer` recebe a lista bruta e aplica `_transform_item()` em cada registro.
- São extraídos campos de objetos aninhados (`orgaoEntidade`, `unidadeOrgao`, `amparoLegal`), e é adicionado o campo `data_extracao` com o timestamp UTC do momento da coleta.

### 3. Load
- `MongoDBLoader` conecta ao MongoDB Atlas usando as credenciais do `.env`.
- O método `load()` executa um `insert_many()` com todos os documentos transformados na coleção `pncp.contratacoes`.

---

## Como Executar

### Pré-requisitos

- Python 3.12+
- Conta no [MongoDB Atlas](https://www.mongodb.com/atlas) com um cluster configurado

### Instalação

```bash
# Crie e ative o ambiente virtual
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# Instale as dependências
pip install requests pymongo python-dotenv
```

### Configuração

Crie o arquivo `.env` na raiz do projeto com as suas credenciais do MongoDB Atlas:

```env
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
```

### Execução

```bash
python main.py
```

A saída esperada é:

```
==================================================
Iniciando ETL — PNCP
==================================================

[1/3] EXTRACT
  Página 1/1 — 45 registros coletados
Total extraído: 45 registros

[2/3] TRANSFORM
Total transformado: 45 registros

[3/3] LOAD
45 documento(s) inserido(s) em 'pncp.contratacoes'

==================================================
ETL concluído com sucesso!
==================================================
```

---

## Parâmetros Configuráveis

Os parâmetros de filtro estão centralizados no topo de `main.py`:

| Variável | Valor padrão | Descrição |
|---|---|---|
| `UF` | `"pe"` | Estado |
| `CODIGO_MUNICIPIO_IBGE` | `"2611606"` | Código IBGE do município (Recife) |
| `CODIGO_MODALIDADE` | `"8"` | Modalidade de contratação (Dispensa) |
| `DATA_FINAL` | `"20260331"` | Data final da busca (`YYYYMMDD`) |
| `DB_NAME` | `"pncp"` | Banco de dados no MongoDB |
| `COLLECTION_NAME` | `"contratacoes"` | Coleção no MongoDB |
