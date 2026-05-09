import requests
import logging

logger = logging.getLogger(__name__)

class PNCPExtractor:
    BASE_URL = "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta"

    def __init__(self, uf: str, codigo_municipio_ibge: str, codigo_modalidade_contratacao: str = "8"):
        self.uf = uf
        self.codigo_municipio_ibge = codigo_municipio_ibge
        self.codigo_modalidade_contratacao = codigo_modalidade_contratacao

    def extract_page(self, data_final: str, pagina: int = 1, tamanho_pagina: int = 50) -> dict:
        params = {
            "dataFinal": data_final,
            "codigoModalidadeContratacao": self.codigo_modalidade_contratacao,
            "uf": self.uf,
            "codigoMunicipioIbge": self.codigo_municipio_ibge,
            "pagina": pagina,
            "tamanhoPagina": tamanho_pagina,
        }
        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()
        if response.status_code == 204 or not response.text:
            return {}
        return response.json()

    def extract_all(self, data_final: str, tamanho_pagina: int = 50) -> list[dict]:
        all_data = []
        pagina = 1

        while True:
            response = self.extract_page(data_final, pagina, tamanho_pagina)

            if not response:
                print("  Nenhum dado encontrado para o período consultado.")
                break

            items = response.get("data", [])
            all_data.extend(items)

            total_paginas = response.get("totalPaginas", 1)
            logger.info(f"Página {pagina}/{total_paginas} — {len(items)} registros coletados")

            if pagina >= total_paginas:
                break
            pagina += 1

        return all_data
