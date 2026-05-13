import hashlib
from cryptography.fernet import Fernet
from app.config import settings

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(settings.DATA_ENCRYPTION_KEY.encode())
    return _fernet


def encrypt_field(value: str) -> str:
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt_field(value: str) -> str:
    return _get_fernet().decrypt(value.encode()).decode()


def hash_field(value: str) -> str:
    """SHA-256 determinístico — usado para unicidade sem expor o dado em claro."""
    return hashlib.sha256(value.encode()).hexdigest()
