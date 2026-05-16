import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv

load_dotenv()

_KEY: bytes = bytes.fromhex(os.getenv("ENCRYPTION_KEY"))


def encrypt(plaintext: str) -> str:
    """Encrypt a plaintext string using AES-GCM and return a base64 blob.

    The returned blob contains nonce + ciphertext encoded in base64.
    """
    aesgcm = AESGCM(_KEY)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ciphertext).decode()


def decrypt(blob: str) -> str:
    """Decrypt a base64-encoded nonce+ciphertext blob produced by `encrypt`.

    Returns the original plaintext string.
    """
    raw: bytes = base64.b64decode(blob.encode())
    nonce, ciphertext = raw[:12], raw[12:]
    return AESGCM(_KEY).decrypt(nonce, ciphertext, None).decode()
