"""Tests for connections.vault — Fernet credential encryption."""

from __future__ import annotations

import pytest
from cryptography.fernet import InvalidToken

from connections.vault import FernetVault, generate_key


class TestFernetVault:
    def test_encrypt_decrypt_roundtrip(self, monkeypatch) -> None:
        key = generate_key()
        monkeypatch.setenv("SOLODSHOUSE_VAULT_KEY", key)
        vault = FernetVault()

        plain = "my-secret-api-key-12345"
        token = vault.encrypt(plain)
        assert token != plain
        assert vault.decrypt(token) == plain

    def test_different_values_produce_different_tokens(self, monkeypatch) -> None:
        key = generate_key()
        monkeypatch.setenv("SOLODSHOUSE_VAULT_KEY", key)
        vault = FernetVault()

        t1 = vault.encrypt("foo")
        t2 = vault.encrypt("bar")
        assert t1 != t2

    def test_tampered_token_raises_invalid_token(self, monkeypatch) -> None:
        key = generate_key()
        monkeypatch.setenv("SOLODSHOUSE_VAULT_KEY", key)
        vault = FernetVault()

        token = vault.encrypt("secret")
        tampered = token[:-4] + "AAAA"
        with pytest.raises(InvalidToken):
            vault.decrypt(tampered)

    def test_wrong_key_raises_invalid_token(self, monkeypatch) -> None:
        key1 = generate_key()
        monkeypatch.setenv("SOLODSHOUSE_VAULT_KEY", key1)
        vault1 = FernetVault()

        token = vault1.encrypt("secret")

        key2 = generate_key()
        vault2 = FernetVault(key=key2)
        with pytest.raises(InvalidToken):
            vault2.decrypt(token)

    def test_missing_env_var_raises_os_error(self, monkeypatch) -> None:
        monkeypatch.delenv("SOLODSHOUSE_VAULT_KEY", raising=False)
        with pytest.raises(OSError, match="SOLODSHOUSE_VAULT_KEY"):
            FernetVault()

    def test_invalid_key_raises_value_error(self, monkeypatch) -> None:
        monkeypatch.setenv("SOLODSHOUSE_VAULT_KEY", "not-a-valid-fernet-key")
        with pytest.raises(ValueError, match="valid Fernet key"):
            FernetVault()

    def test_key_override_constructor(self) -> None:
        key = generate_key()
        vault = FernetVault(key=key)
        plain = "overridden-key-test"
        assert vault.decrypt(vault.encrypt(plain)) == plain

    def test_encrypt_if_needed_plaintext_passthrough(self, monkeypatch) -> None:
        monkeypatch.setenv("SOLODSHOUSE_VAULT_KEY", generate_key())
        vault = FernetVault()
        assert vault.encrypt_if_needed("unencrypted-value") == "unencrypted-value"

    def test_encrypt_if_needed_vault_prefix_encrypts(self, monkeypatch) -> None:
        monkeypatch.setenv("SOLODSHOUSE_VAULT_KEY", generate_key())
        vault = FernetVault()
        token = vault.encrypt_if_needed("vault://my-secret")
        assert token != "my-secret"
        assert vault.decrypt(token) == "my-secret"

    def test_generate_key_returns_urlsafe_base64(self) -> None:
        key = generate_key()
        assert isinstance(key, str)
        assert len(key) > 32

    def test_same_plaintext_same_key_different_tokens(self, monkeypatch) -> None:
        key = generate_key()
        monkeypatch.setenv("SOLODSHOUSE_VAULT_KEY", key)
        vault = FernetVault()
        t1 = vault.encrypt("secret")
        t2 = vault.encrypt("secret")
        assert t1 != t2
        assert vault.decrypt(t1) == "secret"
        assert vault.decrypt(t2) == "secret"
