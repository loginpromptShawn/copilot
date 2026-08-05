import hashlib
import logging
import secrets
import time

logger = logging.getLogger(__name__)
HASH_ALGORITHM = "sha256"
DEFAULT_SALT_BYTES = 16


def generate_token() -> str:
    token = secrets.token_urlsafe(32)
    logger.debug("Generated auth token")
    return token


def hash_password(password: str, algorithm: str = HASH_ALGORITHM) -> str:
    salt = secrets.token_hex(DEFAULT_SALT_BYTES)
    digest = hashlib.new(algorithm, f"{salt}{password}".encode("utf-8")).hexdigest()
    logger.debug("Generated password hash with algorithm %s", algorithm)
    return f"{salt}${digest}"


def verify_password(password: str, password_hash: str, algorithm: str = HASH_ALGORITHM) -> bool:
    try:
        salt, stored_hash = password_hash.split("$", 1)
    except ValueError:
        logger.warning("Invalid password hash format")
        return False
    computed_hash = hashlib.new(algorithm, f"{salt}{password}".encode("utf-8")).hexdigest()
    valid = secrets.compare_digest(stored_hash, computed_hash)
    if not valid:
        logger.debug("Password verification failed")
    return valid


def token_expiry(hours: int = 8) -> float:
    expiry = time.time() + float(hours * 3600)
    logger.debug("Computed token expiry timestamp: %s", expiry)
    return expiry
