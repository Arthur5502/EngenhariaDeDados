from fastmcp import FastMCP
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from config import settings
from src.extract import PNCPExtractor
from src.transform import PNCPTransformer
from src.load import MongoDBLoader

mcp = FastMCP("pncp-contratos")


def _get_collection():
    client = MongoClient(settings.MONGO_URI, server_api=ServerApi("1"))
    return client, client[settings.DB_NAME][settings.COLLECTION_NAME]


def _serializar(doc: dict) -> dict:
    result = {}
    for k, v in doc.items():
        if k == "_id":
            result["numeroControlePNCP"] = str(v)
        elif isinstance(v, dict):
            result[k] = _serializar(v)
        elif isinstance(v, list):
            result[k] = [_serializar(i) if isinstance(i, dict) else i for i in v]
        else:
            result[k] = v
    return result


@mcp.tool()
def buscar_contratos(
    data_inicial: str | None = None,
    data_final: str | None = None,
    orgao: str | None = None,
    situacao: str | None = None,
    valor_min: float | None = None,
    valor_max: float | None = None,
    limite: int = 10,
) -> list[dict]:
    """
    Busca contratos públicos do PNCP armazenados no MongoDB.

    Args:
        data_inicial: Data de início no formato YYYY-MM-DD (filtra por dataPublicacaoPncp)
        data_final: Data de fim no formato YYYY-MM-DD
        orgao: Nome ou parte do nome do órgão contratante (busca parcial, sem acento)
        situacao: Situação da compra (ex: "Divulgada no PNCP", "Encerrada")
        valor_min: Valor mínimo estimado em R$
        valor_max: Valor máximo estimado em R$
        limite: Quantidade máxima de registros a retornar (padrão 10, máx 50)
    """
    query: dict = {}

    if data_inicial or data_final:
        filtro_data: dict = {}
        if data_inicial:
            filtro_data["$gte"] = data_inicial
        if data_final:
            filtro_data["$lte"] = data_final
        query["dataPublicacaoPncp"] = filtro_data

    if orgao:
        query["orgaoEntidade.razaoSocial"] = {"$regex": orgao, "$options": "i"}

    if situacao:
        query["situacaoCompraNome"] = {"$regex": situacao, "$options": "i"}

    if valor_min is not None or valor_max is not None:
        filtro_valor: dict = {}
        if valor_min is not None:
            filtro_valor["$gte"] = valor_min
        if valor_max is not None:
            filtro_valor["$lte"] = valor_max
        query["valorTotalEstimado"] = filtro_valor

    cliente, collection = _get_collection()
    try:
        docs = list(collection.find(query).limit(min(limite, 50)))
        return [_serializar(d) for d in docs]
    finally:
        cliente.close()


@mcp.tool()
def resumo_contratos(
    data_inicial: str | None = None,
    data_final: str | None = None,
) -> dict:
    """
    Retorna estatísticas agregadas dos contratos: totais, valor estimado, ranking por órgão e distribuição por situação.

    Args:
        data_inicial: Data de início no formato YYYY-MM-DD (opcional)
        data_final: Data de fim no formato YYYY-MM-DD (opcional)
    """
    match: dict = {}
    if data_inicial or data_final:
        filtro_data: dict = {}
        if data_inicial:
            filtro_data["$gte"] = data_inicial
        if data_final:
            filtro_data["$lte"] = data_final
        match["dataPublicacaoPncp"] = filtro_data

    cliente, collection = _get_collection()
    try:
        pipeline_geral = [
            {"$match": match},
            {
                "$group": {
                    "_id": None,
                    "total_contratos": {"$sum": 1},
                    "valor_total_estimado": {"$sum": "$valorTotalEstimado"},
                    "valor_total_homologado": {"$sum": "$valorTotalHomologado"},
                }
            },
        ]

        pipeline_orgao = [
            {"$match": match},
            {
                "$group": {
                    "_id": "$orgaoEntidade.razaoSocial",
                    "quantidade": {"$sum": 1},
                    "valor_total": {"$sum": "$valorTotalEstimado"},
                }
            },
            {"$sort": {"valor_total": -1}},
            {"$limit": 10},
        ]

        pipeline_situacao = [
            {"$match": match},
            {
                "$group": {
                    "_id": "$situacaoCompraNome",
                    "quantidade": {"$sum": 1},
                }
            },
            {"$sort": {"quantidade": -1}},
        ]

        geral_raw = list(collection.aggregate(pipeline_geral))
        geral = geral_raw[0] if geral_raw else {"total_contratos": 0, "valor_total_estimado": 0, "valor_total_homologado": 0}
        geral.pop("_id", None)

        por_orgao = [
            {"orgao": r["_id"], "quantidade": r["quantidade"], "valor_total": r["valor_total"]}
            for r in collection.aggregate(pipeline_orgao)
        ]

        por_situacao = [
            {"situacao": r["_id"], "quantidade": r["quantidade"]}
            for r in collection.aggregate(pipeline_situacao)
        ]

        return {"geral": geral, "por_orgao": por_orgao, "por_situacao": por_situacao}
    finally:
        cliente.close()


@mcp.tool()
def buscar_contrato_por_id(numero_controle: str) -> dict:
    """
    Retorna os dados completos de um contrato específico pelo número de controle PNCP.

    Args:
        numero_controle: Número de controle PNCP (ex: "00394502000175-1-000001/2026")
    """
    cliente, collection = _get_collection()
    try:
        doc = collection.find_one({"_id": numero_controle})
        if not doc:
            return {"erro": f"Contrato '{numero_controle}' não encontrado."}
        return _serializar(doc)
    finally:
        cliente.close()


@mcp.tool()
def executar_etl(
    data_inicial: str | None = None,
    data_final: str | None = None,
) -> dict:
    """
    Executa o pipeline ETL: extrai contratos da API PNCP e carrega no MongoDB.
    Pode levar alguns segundos dependendo do volume de dados.

    Args:
        data_inicial: Data de início no formato YYYYMMDD (padrão: configuração do settings)
        data_final: Data de fim no formato YYYYMMDD (padrão: configuração do settings)
    """
    di = data_inicial or settings.DATA_INICIAL
    df = data_final or settings.DATA_FINAL

    extractor = PNCPExtractor(settings.UF, settings.CODIGO_MUNICIPIO_IBGE, settings.CODIGO_MODALIDADE)
    raw = extractor.extract_all(di, df)

    transformer = PNCPTransformer()
    transformed = transformer.transform(raw)

    loader = MongoDBLoader()
    try:
        inseridos = loader.load(transformed, settings.DB_NAME, settings.COLLECTION_NAME)
    finally:
        loader.close()

    return {
        "extraidos": len(raw),
        "transformados": len(transformed),
        "inseridos": inseridos,
        "periodo": f"{di} → {df}",
    }


if __name__ == "__main__":
    mcp.run()
