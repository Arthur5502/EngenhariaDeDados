from datetime import datetime, timezone

class PNCPTransformer:

    def transform(self, raw_data: list[dict]) -> list[dict]:
        return [self._transform_item(item) for item in raw_data]

    def _transform_item(self, item: dict) -> dict:
        orgao = item.get("orgaoEntidade") or {}
        unidade = item.get("unidadeOrgao") or {}
        amparo = item.get("amparoLegal") or {}

        return {
            "numero_controle_pncp": item.get("numeroControlePNCP"),
            "ano_compra": item.get("anoCompra"),
            "numero_compra": item.get("numeroCompra"),
            "processo": item.get("processo"),
            "objeto_compra": item.get("objetoCompra"),
            "modalidade_id": item.get("modalidadeId"),
            "modalidade_nome": item.get("modalidadeNome"),
            "modo_disputa_nome": item.get("modoDisputaNome"),
            "situacao_compra_id": item.get("situacaoCompraId"),
            "situacao_compra_nome": item.get("situacaoCompraNome"),
            "tipo_instrumento_convocatorio": item.get("tipoInstrumentoConvocatorioNome"),
            "valor_total_estimado": item.get("valorTotalEstimado"),
            "valor_total_homologado": item.get("valorTotalHomologado"),
            "srp": item.get("srp"),
            "orgao_cnpj": orgao.get("cnpj"),
            "orgao_razao_social": orgao.get("razaoSocial"),
            "orgao_poder_id": orgao.get("poderId"),
            "orgao_esfera_id": orgao.get("esferaId"),
            "unidade_codigo": unidade.get("codigoUnidade"),
            "unidade_nome": unidade.get("nomeUnidade"),
            "municipio_nome": unidade.get("municipioNome"),
            "municipio_ibge": unidade.get("codigoIbge"),
            "uf_sigla": unidade.get("ufSigla"),
            "uf_nome": unidade.get("ufNome"),
            "amparo_legal_codigo": amparo.get("codigo"),
            "amparo_legal_nome": amparo.get("nome"),
            "data_inclusao": item.get("dataInclusao"),
            "data_atualizacao": item.get("dataAtualizacao"),
            "data_publicacao_pncp": item.get("dataPublicacaoPncp"),
            "data_abertura_proposta": item.get("dataAberturaProposta"),
            "data_encerramento_proposta": item.get("dataEncerramentoProposta"),
            "link_sistema_origem": item.get("linkSistemaOrigem"),
            "data_extracao": datetime.now(timezone.utc).isoformat(),
        }
