from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db
from app.services.pncp import PNCPService
from app.services.transform import TransformService
from app.services.mongo import MongoService
from app.schemas.contratacao import ETLParams, ETLResult
from app.dependencies import get_current_user

router = APIRouter(
    prefix="/etl",
    tags=["ETL"],
    dependencies=[Depends(get_current_user)],
)


def get_mongo_service():
    return MongoService(get_db())


@router.post("/run", response_model=ETLResult)
async def executar_etl(
    params: ETLParams,
    service: MongoService = Depends(get_mongo_service),
):
    try:
        extractor = PNCPService(
            uf=params.uf,
            codigo_municipio_ibge=params.codigo_municipio_ibge,
            codigo_modalidade=params.codigo_modalidade,
        )
        raw_data = await extractor.extract_all(params.data_final)

        transformer = TransformService()
        transformed_data = transformer.transform(raw_data)

        inseridos = await service.insert_many(transformed_data)

        return ETLResult(
            extraidos=len(raw_data),
            transformados=len(transformed_data),
            inseridos=inseridos,
            mensagem="ETL executado com sucesso.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
