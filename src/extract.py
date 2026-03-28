import requests

class PNCPExtractor:
    """Responsável pela extração de dados de contratações públicas da API do PNCP.

    A API do Portal Nacional de Contratações Públicas (PNCP) disponibiliza dados
    sobre contratações por modalidade, estado e município. Esta classe encapsula
    a lógica de paginação e requisição HTTP para coletar todos os registros
    disponíveis dentro dos parâmetros fornecidos.

    Attributes:
        BASE_URL (str): Endpoint base da API de consulta de propostas.
        uf (str): Sigla do estado (ex: 'PE').
        codigo_municipio_ibge (str): Código IBGE do município.
        codigo_modalidade_contratacao (str): Código da modalidade (padrão '8' = Dispensa).
    """

    BASE_URL = "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta"

    def __init__(self, uf: str, codigo_municipio_ibge: str, codigo_modalidade_contratacao: str = "8"):
        """Inicializa o extrator com os filtros geográficos e de modalidade.

        Args:
            uf: Sigla do estado (ex: 'PE').
            codigo_municipio_ibge: Código IBGE do município (ex: '2611606' para Recife).
            codigo_modalidade_contratacao: Código da modalidade de contratação.
                Padrão '8' (Dispensa Eletrônica).
        """
        self.uf = uf
        self.codigo_municipio_ibge = codigo_municipio_ibge
        self.codigo_modalidade_contratacao = codigo_modalidade_contratacao

    def extract_page(self, data_final: str, pagina: int = 1, tamanho_pagina: int = 50) -> dict:
        """Realiza uma requisição à API para uma página específica de resultados.

        Args:
            data_final: Data limite para busca no formato 'YYYYMMDD' (ex: '20260331').
            pagina: Número da página a ser consultada. Padrão 1.
            tamanho_pagina: Quantidade de registros por página. Padrão 50.

        Returns:
            Dicionário com a resposta da API, incluindo os campos:
            'data', 'totalRegistros', 'totalPaginas', 'numeroPagina'.

        Raises:
            requests.HTTPError: Se a requisição retornar status de erro (4xx ou 5xx).
        """
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
        return response.json()

    def extract_all(self, data_final: str, tamanho_pagina: int = 50) -> list[dict]:
        """Extrai todos os registros disponíveis percorrendo todas as páginas da API.

        Itera automaticamente pelas páginas até que não haja mais resultados,
        consolidando tudo em uma única lista.

        Args:
            data_final: Data limite para busca no formato 'YYYYMMDD' (ex: '20260331').
            tamanho_pagina: Quantidade de registros por página. Padrão 50.

        Returns:
            Lista com todos os dicionários de contratações encontrados.
        """
        all_data = []
        pagina = 1

        while True:
            response = self.extract_page(data_final, pagina, tamanho_pagina)
            items = response.get("data", [])
            all_data.extend(items)

            total_paginas = response.get("totalPaginas", 1)
            print(f"  Página {pagina}/{total_paginas} — {len(items)} registros coletados")

            if pagina >= total_paginas:
                break
            pagina += 1

        return all_data
