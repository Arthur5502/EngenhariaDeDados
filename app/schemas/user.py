from pydantic import BaseModel, EmailStr, field_validator
import re

def _cpf_valido(cpf: str) -> bool:
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
    for i, peso_inicial in enumerate([10, 11]):
        soma = sum(int(cpf[j]) * (peso_inicial - j) for j in range(i + 9))
        digito = 0 if (soma * 10 % 11) >= 10 else (soma * 10 % 11)
        if digito != int(cpf[9 + i]):
            return False
    return True

def _cnpj_valido(cnpj: str) -> bool:
    if len(cnpj) != 14 or len(set(cnpj)) == 1:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for i, pesos in enumerate([pesos1, pesos2]):
        soma = sum(int(cnpj[j]) * pesos[j] for j in range(12 + i))
        digito = 0 if (soma % 11) < 2 else 11 - (soma % 11)
        if digito != int(cnpj[12 + i]):
            return False
    return True

def mascarar_cpf(cpf: str) -> str:
    return f"***.***.{cpf[6:9]}-**"

def mascarar_email(email: str) -> str:
    local, domain = email.split("@", 1)
    return f"{local[:2]}***@{domain}"

def mascarar_telefone(telefone: str) -> str:
    digits = re.sub(r"\D", "", telefone)
    return f"({'*' * (len(digits) - 4)}{digits[-4:]})"

class UserCreate(BaseModel):
    nome: str
    cpf: str
    email: EmailStr
    telefone: str
    password: str

    cnpj_mei: str
    razao_social: str
    cnae_principal: str
    uf: str
    municipio: str

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if not _cpf_valido(digits):
            raise ValueError("CPF inválido")
        return digits

    @field_validator("cnpj_mei")
    @classmethod
    def validar_cnpj(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if not _cnpj_valido(digits):
            raise ValueError("CNPJ inválido")
        return digits

    @field_validator("uf")
    @classmethod
    def validar_uf(cls, v: str) -> str:
        return v.upper()

class LoginBody(BaseModel):
    cnpj: str
    password: str

    @field_validator("cnpj")
    @classmethod
    def validar_cnpj(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if not _cnpj_valido(digits):
            raise ValueError("CNPJ inválido")
        return digits

class UserOut(BaseModel):
    id: str
    nome: str
    cpf_mascarado: str
    email_mascarado: str
    telefone_mascarado: str
    cnpj_mei: str
    razao_social: str
    cnae_principal: str
    uf: str
    municipio: str
    ativo: bool
    criado_em: str

class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"