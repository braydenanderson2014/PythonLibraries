"""
Local password hashing utilities for Financial Manager.

Avoids conflicts with any third-party packages named 'hasher'.
"""

from __future__ import annotations

import hashlib

# Import env_loader to load environment variables from env.env
from .env_loader import _loaded_vars as _env_vars  # type: ignore

from assets.Logger import Logger

logger = Logger()


def _get_salt() -> str:
    """Get the appropriate salt based on USE_TESTING_SALT flag.
    
    Reads from environment:
    - USE_TESTING_SALT: If "True", use TESTING_SALT, else use _SALT
    - TESTING_SALT: Salt for testing (default: RentTracker2025)
    - _SALT: Production salt
    
    Returns
    -------
    str
        The appropriate salt string
    """
    use_testing = _env_vars.get('USE_TESTING_SALT', 'False').lower() == 'true'
    
    if use_testing:
        salt = _env_vars.get('TESTING_SALT', 'RentTracker2025')
        logger.debug("hasher", f"Using TESTING_SALT for hashing (USE_TESTING_SALT=True)")
    else:
        salt = _env_vars.get('_SALT', 'RentTracker2025')
        logger.debug("hasher", f"Using production _SALT for hashing (USE_TESTING_SALT=False)")
    
    return salt


def hash_password(password: str) -> str:
    """Return a stable SHA-256 hash for the given password.

    Uses a static salt for compatibility with existing data. For a production
    system, prefer a per-user random salt and a slow KDF (e.g., PBKDF2, bcrypt,
    scrypt, or Argon2). This function exists to maintain backward compatibility
    with the existing dataset and tests.
    
    The salt is loaded from environment variables:
    - Uses TESTING_SALT if USE_TESTING_SALT=True
    - Uses _SALT otherwise
    """
    try:
        salt = _get_salt()
        hash_result = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()
        logger.debug("hasher", f"Successfully hashed password with salt length={len(salt)}")
        return hash_result
    except Exception as e:
        logger.error("hasher", f"Error hashing password: {str(e)}")
        raise


def legacy_hash(password: str) -> str:
    """Legacy hashing used by older stored accounts: SHA-256(password).

    We keep this for backward compatibility: many existing accounts were
    created with the unsalted hash. New accounts should use hash_password
    (salted). The verify_password helper below checks both forms.
    """
    try:
        hash_result = hashlib.sha256(password.encode("utf-8")).hexdigest()
        logger.debug("hasher", "Generated legacy unsalted hash for backward compatibility")
        return hash_result
    except Exception as e:
        logger.error("hasher", f"Error generating legacy hash: {str(e)}")
        raise


def verify_hash(stored_hash: str, password: str) -> bool:
    """Return True if stored_hash matches either the salted or legacy hash.
    
    Attempts verification in order:
    1. Current salted hash (preferred for new accounts)
    2. Legacy unsalted hash (for backward compatibility)
    """
    try:
        if not stored_hash:
            logger.debug("hasher", "verify_hash called with empty stored_hash, returning False")
            return False
        
        # Check current salted hash first (preferred for new accounts)
        if stored_hash == hash_password(password):
            logger.debug("hasher", "Password verified against current salted hash")
            return True
        
        # Fall back to legacy (unsalted) hash to maintain compatibility
        if stored_hash == legacy_hash(password):
            logger.debug("hasher", "Password verified against legacy unsalted hash (backward compatibility)")
            return True
        
        logger.warning("hasher", "Password hash verification failed - no matching hash found")
        return False
    except Exception as e:
        logger.error("hasher", f"Error verifying hash: {str(e)}")
        return False


__all__ = ["hash_password", "legacy_hash", "verify_hash"]
