import httpx
from app.config import settings

class PNCPService:
    def __init__(
        self,
        uf: str = settings.PNCP_UF,
        codigo_municipio_ibge: str = settings.PNCP_MUNICIPIO_IBGE,
        codigo_modalidade: str = settings.PNCP_MODALIDADE,
    ):
        self.uf = uf
        self.codigo_municipio_ibge = codigo_municipio_ibge
        self.codigo_modalidade = codigo_modalidade

    async def extract_page(self, data_final: str, pagina: int = 1, tamanho_pagina: int = 50) -> dict:
        params = {
            "dataFinal": data_final,
            "codigoModalidadeContratacao": self.codigo_modalidade,
            "uf": self.uf,
            "codigoMunicipioIbge": self.codigo_municipio_ibge,
            "pagina": pagina,
            "tamanhoPagina": tamanho_pagina,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(settings.PNCP_BASE_URL, params=params)
            response.raise_for_status()
            return response.json()

    async def extract_all(self, data_final: str, tamanho_pagina: int = 50) -> list[dict]:
        all_data: list[dict] = []
        pagina = 1

        while True:
            response = await self.extract_page(data_final, pagina, tamanho_pagina)
            items = response.get("data", [])
            all_data.extend(items)

            total_paginas = response.get("totalPaginas", 1)
            if pagina >= total_paginas:
                break
            pagina += 1

        return all_data