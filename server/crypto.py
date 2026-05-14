from server.core.crypto import encrypt, decrypt

__all__ = ["encrypt", "decrypt"]
"""
crypto.py — AES-256-GCM encryption for messages stored in the database.
"""

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# 32 bytes = 256-bit key. os.urandom is cryptographically secure.
# In production: load this from an environment variable, never hardcode it.
_KEY: bytes = os.urandom(32)


def encrypt(plaintext: str) -> str:
    """
    Encrypt a string. Returns a base64 blob safe to store in the database.

    Blob layout (concatenated, then base64-encoded):
        [ nonce: 12 bytes ][ ciphertext + auth-tag: variable ]
    """
    aesgcm = AESGCM(_KEY)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ciphertext).decode()


def decrypt(blob: str) -> str:
    """
    Decrypt a blob produced by encrypt(). Raises an exception if tampered with.
    """
    raw = base64.b64decode(blob.encode())
    nonce, ciphertext = raw[:12], raw[12:]
    aesgcm = AESGCM(_KEY)
    return aesgcm.decrypt(nonce, ciphertext, None).decode()
