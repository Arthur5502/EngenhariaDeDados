# Requisito 1: Segurança da Informação - Autenticação e Proteção de Dados

Este documento detalha a implementação do primeiro requisito de Segurança da Informação no projeto integrador, focado no controle de acesso, integridade de senhas e proteção das APIs.

## 1. Visão Geral da Arquitetura de Segurança

A segurança do backend foi desenhada seguindo o padrão **OAuth2 com Tokens Bearer (JWT - JSON Web Tokens)**. O objetivo principal é garantir que as rotas da API só possam ser acessadas por usuários autenticados e autorizados, protegendo assim o acesso ao banco de dados e à execução de pipelines de dados (ETL).

## 2. Proteção de Credenciais e Criptografia

O armazenamento seguro de senhas é uma premissa básica da aplicação. Senhas em texto plano nunca são registradas ou transitadas no banco de dados.

### 2.1 Algoritmo de Hashing (Bcrypt)
As senhas dos usuários são protegidas usando o algoritmo de derivação de chave **Bcrypt**. 
* O Bcrypt é resistente a ataques de força bruta devido ao seu custo computacional ajustável (work factor).
* Cada senha recebe um *salt* único gerado aleatoriamente (`bcrypt.gensalt()`), impossibilitando ataques baseados em tabelas precomputadas (*rainbow tables*).

### 2.2 Mitigação do Limite de 72 Bytes
O Bcrypt possui uma limitação técnica onde apenas os primeiros 72 bytes da senha são considerados no cálculo do hash. Para evitar truncamento silencioso (que comprometeria a segurança de senhas longas) ou erros na aplicação, foi adotada a técnica de **Pré-hashing**:
1. A senha fornecida pelo usuário passa primeiro por um hash rápido usando **SHA-256**.
2. O resultado é uma string hexadecimal de tamanho fixo (64 caracteres).
3. Esse valor fixo de 64 caracteres é então passado para a função Bcrypt.

*Trecho de implementação (`app/services/auth.py`):*
```python
def _prehash(password: str) -> str:
    """Pré-hash SHA-256 para contornar o limite de 72 bytes do bcrypt."""
    return hashlib.sha256(password.encode()).hexdigest()

def hash_password(password: str) -> str:
    return _pwd_context.hash(_prehash(password))
```

## 3. Autenticação Baseada em Token (JWT)

A manutenção de sessões é feita sem estado (*stateless*), utilizando JSON Web Tokens.

* **Geração (`/auth/login`):** Após validação bem-sucedida de CNPJ e senha, a API emite um JWT assinado usando o algoritmo `HS256` e uma chave secreta (`SECRET_KEY`) configurada no ambiente.
* **Payload:** O token contém a identificação do usuário (`sub`: CNPJ) e uma data de expiração curta (`exp`), reduzindo a janela de oportunidade em caso de vazamento do token.
* **Validação (`app/dependencies.py`):** Toda requisição a rotas protegidas passa pelo `HTTPBearer`. O sistema decodifica o token, valida a assinatura e verifica se o token não expirou. Caso seja inválido, a conexão é rejeitada imediatamente com HTTP `401 Unauthorized`.

## 4. Segurança de Rotas (Endpoints)

As rotas da API são divididas em públicas e privadas:

* **Públicas:** Rotas que não exigem autenticação.
  * `/auth/register`: Apenas para criação de novos acessos.
  * `/auth/login`: Para troca de credenciais por um Token de Acesso.

* **Privadas (Protegidas):** Requerem o envio de um header HTTP `Authorization: Bearer <token>`.
  * `/auth/me`: Retorna os dados do usuário autenticado. Garante que um usuário não acesse os dados de outro.
  * `/contratacoes/*`: O acesso aos dados do PNCP exige que a empresa (CNPJ) esteja devidamente logada no sistema.
  * `/etl/run`: A execução de processamento em lote é restrita para evitar abusos de uso de recursos computacionais e sobrecarga do banco de dados (ataques de negação de serviço - DoS).

## 5. Validação e Sanitização de Entrada

Para mitigar injeções e dados malformados, o Pydantic (`app/schemas/user.py`) atua como camada de segurança na entrada de dados:
* **Validação de Documentos:** CPF e CNPJ passam por funções lógicas que calculam e validam os dígitos verificadores (além de bloquear sequências repetidas como `111.111.111-11`).
* **Regex e Limpeza:** Somente números são extraídos dos documentos (`re.sub(r"\D", "", v)`), evitando a entrada de scripts maliciosos (XSS) ou comandos em SQL/NoSQL no momento do login ou cadastro.
* **Email:** Validação rigorosa do formato de e-mail (RFC 5322) via `EmailStr`.

## 6. Mascaramento de Dados Sensíveis

Princípio de *Privacy by Design*. Ao retornar informações através da API (`UserOut`), o sistema não devolve dados inteiramente expostos que podem ser considerados sensíveis:
* A senha (mesmo em hash) é **removida** de qualquer payload de resposta.
* O CPF do usuário é retornado mascarado (`cpf_mascarado`: `***.456.789-**`) para estar em conformidade com as boas práticas de proteção de dados (como a LGPD), visando que front-ends ou integrações não recebam o dado bruto a não ser que estritamente necessário.
