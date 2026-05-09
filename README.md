# ETL — Portal Nacional de Contratações Públicas (PNCP)

Pipeline de Engenharia de Dados para coleta, tratamento e persistência de dados de contratações públicas municipais disponibilizados pela API do PNCP.

---

## Integrantes

- Arthur Felipe Campos Pina
- Jácio Alves Neto Filho
- Vinicius Silva Queiroz
- Guilherme Wolf Nogueira
- Mateus Felipe Cavalcanti e Silva
- Gabriel Victor de Melo Reis
- Lucas Carvalho

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
│  PNCPTransformer — valida via Pydantic, normaliza campos    │
│  aninhados e adiciona metadados de controle                 │
└────────────────────────┬────────────────────────────────────┘
                         │ list[dict] (dados normalizados)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    LOAD (src/load.py)                        │
│  MongoDBLoader — upsert de documentos no MongoDB Atlas      │
└────────────────────────┬────────────────────────────────────┘
                         │ upsert por numeroControlePNCP
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     MongoDB Atlas                           │
│          banco: pncp   |   coleção: bronze_pncp             │
└─────────────────────────────────────────────────────────────┘
```

---

## Estrutura do Projeto

```
.
├── main.py                    # Execução direta do pipeline ETL
├── orchestrate_prefect.py     # Execução orquestrada com Prefect
├── src/
│   ├── __init__.py
│   ├── extract.py             # Classe PNCPExtractor
│   ├── transform.py           # Classe PNCPTransformer
│   ├── load.py                # Classe MongoDBLoader
│   └── models.py              # Modelos Pydantic dos contratos
├── config/
│   └── settings.py            # Configurações centralizadas via .env
├── .env                       # Credenciais (não versionado)
├── requirements.txt
└── README.md
```

---

## Fluxo de Dados

### 1. Extract
- `PNCPExtractor` recebe UF, código IBGE do município, código da modalidade e intervalo de datas (`dataInicial` e `dataFinal`).
- O método `extract_all()` percorre automaticamente todas as páginas da API, acumulando os registros brutos em uma lista.

### 2. Transform
- `PNCPTransformer` valida cada registro contra o modelo `PNCPContractModel` (Pydantic).
- Registros inválidos são descartados com log de erro.
- É adicionado o campo `data_ingestao_sistema` com o timestamp UTC da coleta.

### 3. Load
- `MongoDBLoader` conecta ao MongoDB Atlas usando as credenciais do `.env`.
- O método `load()` executa **upsert** por `numeroControlePNCP`, evitando duplicatas a cada nova execução.

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
pip install -r requirements.txt
```

### Configuração

Crie o arquivo `.env` na raiz do projeto:

```env
MONGO_URI=mongodb+srv://<usuario>:<senha>@<cluster>.mongodb.net/

# Opcional — sobrescreve os valores padrão
PNCP_UF=pe
PNCP_CODIGO_MUNICIPIO_IBGE=2611606
PNCP_CODIGO_MODALIDADE=8
PNCP_DATA_INICIAL=20260101
PNCP_DATA_FINAL=20260630
MONGO_DB_NAME=pncp
MONGO_COLLECTION_NAME=bronze_pncp
```

---

## Execução

### Modo direto

Executa o pipeline uma vez imediatamente:

```bash
python main.py
```

### Modo orquestrado com Prefect

Executa o pipeline com monitoramento de tasks, logs estruturados e retry automático na extração:

```bash
python orchestrate_prefect.py
```

Cada etapa aparece como uma task separada no terminal:

```
INFO | Task run 'Extração PNCP'    - Iniciando extração — UF: pe | Período: 20260209 → 20260708
INFO | Task run 'Extração PNCP'    - 50 registros brutos extraídos da API PNCP
INFO | Task run 'Transformação PNCP' - 50 registros válidos prontos para carga
INFO | Task run 'Carga MongoDB'    - 12 novo(s) documento(s) inserido(s) no MongoDB Atlas
INFO | Flow run                    - Pipeline concluído — 12 contratos carregados no MongoDB Atlas
```

### Modo agendado com Prefect (painel em http://127.0.0.1:4200)

Para agendar execuções automáticas (ex: todo dia às 8h), ative o `.serve()` em `orchestrate_prefect.py`:

```python
if __name__ == "__main__":
    etl_pncp_flow.serve(
        name="etl-pncp-schedule",
        cron="0 8 * * *",
        tags=["etl", "pncp", "mongodb"],
    )
```

**Terminal 1** — inicia o servidor Prefect:
```bash
prefect server start
```

**Terminal 2** — registra e mantém o agendamento ativo:
```bash
python orchestrate_prefect.py
```

Acesse `http://127.0.0.1:4200` para acompanhar execuções, histórico e disparar o pipeline manualmente.

---

## Parâmetros Configuráveis

Todos os parâmetros são controlados via `config/settings.py` e podem ser sobrescritos pelo `.env`:

| Variável `.env`              | Padrão                  | Descrição                              |
|------------------------------|-------------------------|----------------------------------------|
| `PNCP_UF`                    | `pe`                    | Estado                                 |
| `PNCP_CODIGO_MUNICIPIO_IBGE` | `2611606`               | Código IBGE do município (Recife)      |
| `PNCP_CODIGO_MODALIDADE`     | `8`                     | Modalidade de contratação (Dispensa)   |
| `PNCP_DATA_INICIAL`          | hoje − 90 dias          | Início do intervalo de busca           |
| `PNCP_DATA_FINAL`            | hoje + 60 dias          | Fim do intervalo de busca              |
| `PNCP_TAMANHO_PAGINA`        | `50`                    | Registros por página na API            |
| `MONGO_URI`                  | —                       | URI de conexão do MongoDB Atlas        |
| `MONGO_DB_NAME`              | `pncp`                  | Banco de dados no MongoDB              |
| `MONGO_COLLECTION_NAME`      | `bronze_pncp`           | Coleção no MongoDB                     |
