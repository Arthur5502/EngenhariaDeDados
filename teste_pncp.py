import requests
import json

base_url = "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta"

#Parâmetros de Busca
dataFinal="20260331"
codigoModalidadeContratacao="8"
uf="pe"
codigoMunicipioIbge="2611606"
pagina="1"
tamanhoPagina="50"
parametros = {
    "dataFinal": dataFinal,
    "codigoModalidadeContratacao": codigoModalidadeContratacao,
    "uf": uf,
    "codigoMunicipioIbge": codigoMunicipioIbge,
    "pagina": pagina,
    "tamanhoPagina": tamanhoPagina
}

req = requests.get(base_url,params=parametros)

data = req.json()

print(data['data'])

with open('data.json', 'w') as f:
    json.dump(data, f)