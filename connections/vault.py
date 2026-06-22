"""Credential vault — Fernet-based symmetric encryption for connection secrets (SDS-044).

Encryption key injected via ``SOLODSHOUSE_VAULT_KEY`` environment variable.
Generate one with ``generate_key()`` and store it securely.

    vault = FernetVault()
    token = vault.encrypt("my-api-key")
    plain = vault.decrypt(token)  # -> "my-api-key"
"""

from __future__ import annotations

import os

from cryptography.fernet import Fernet


class FernetVault:
    """Encrypt / decrypt connection secrets with Fernet symmetric encryption.

    Reads the key from ``SOLODSHOUSE_VAULT_KEY`` at init time.
    Raises ``OSError`` if the variable is not set.
    """

    def __init__(self, key: str | None = None) -> None:
        env_key = key or os.environ.get("SOLODSHOUSE_VAULT_KEY")
        if not env_key:
            raise OSError(
                "SOLODSHOUSE_VAULT_KEY is not set. "
                "Generate a key with `python -c 'from connections.vault "
                "import generate_key; print(generate_key())'` and export it."
            )
        try:
            self._fernet = Fernet(env_key.encode("utf-8"))
        except Exception as exc:
            raise ValueError(
                "SOLODSHOUSE_VAULT_KEY is not a valid Fernet key. "
                "Generate one with generate_key()."
            ) from exc

    def encrypt(self, value: str) -> str:
        """Encrypt *value* and return a base64-encoded token."""
        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, token: str) -> str:
        """Decrypt *token* and return the original plaintext.

        Raises ``cryptography.fernet.InvalidToken`` on tampered / wrong-key data.
        """
        return self._fernet.decrypt(token.encode("utf-8")).decode("utf-8")

    def encrypt_if_needed(self, value: str) -> str:
        """Return the value as-is unless it starts with ``vault://``,
        in which case the prefix is stripped and the rest is encrypted."""
        if value.startswith("vault://"):
            return self.encrypt(value.removeprefix("vault://"))
        return value


def generate_key() -> str:
    """Return a new random Fernet key suitable for ``SOLODSHOUSE_VAULT_KEY``."""
    return Fernet.generate_key().decode("utf-8")
