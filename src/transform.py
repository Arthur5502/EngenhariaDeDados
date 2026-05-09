import logging
from datetime import datetime, timezone
from pydantic import ValidationError
from src.models import PNCPContractModel

logger = logging.getLogger(__name__)

class PNCPTransformer:

    def transform(self, raw_data: list[dict]) -> list[dict]:
        transformed = []
        for item in raw_data:
            validated_item = self._transform_item(item)
            if validated_item:
                transformed.append(validated_item)
        return transformed

    def _transform_item(self, item: dict) -> dict:
        try:
            model = PNCPContractModel.model_validate(item)
            
            bronze_data = model.model_dump()

            bronze_data["_id"] = bronze_data.pop("numeroControlePNCP")

            bronze_data["data_ingestao_sistema"] = datetime.now(timezone.utc).isoformat()

            return bronze_data

        except ValidationError as e:
            logger.error(f"Erro de validação no contrato {item.get('numeroControlePNCP', 'ID_DESCONHECIDO')}: {e.json()}")
            return None
