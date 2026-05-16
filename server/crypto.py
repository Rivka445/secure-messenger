"""Compatibility shim: re-export crypto helpers from server.core.crypto.

This module intentionally re-exports the implementations from
`server.core.crypto` so there is a single module that owns the
encryption key. Previously this file duplicated the implementation and
generated a different key which caused decryption to fail (InvalidTag).
"""

from server.core.crypto import encrypt, decrypt

__all__ = ["encrypt", "decrypt"]
