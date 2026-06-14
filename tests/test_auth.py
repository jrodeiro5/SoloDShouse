"""Tests for connections.auth — JWT role-based access control."""

from __future__ import annotations

import jwt
import pytest

from connections.auth import JWTAuth, TokenClaims, generate_jwt_secret


@pytest.fixture
def auth() -> JWTAuth:
    return JWTAuth(secret=generate_jwt_secret())


class TestJWTAuth:
    def test_create_and_verify_token_roundtrip(self, auth: JWTAuth) -> None:
        token = auth.create_token(subject="dagster", roles=["reader", "admin"])
        assert isinstance(token, str)
        claims = auth.verify_token(token)
        assert claims.subject == "dagster"
        assert claims.roles == ["reader", "admin"]
        assert claims.issuer == "solodshouse"
        assert not claims.expired

    def test_default_roles_is_reader(self, auth: JWTAuth) -> None:
        token = auth.create_token(subject="api-client")
        claims = auth.verify_token(token)
        assert claims.roles == ["reader"]

    def test_expired_token_detected(self, auth: JWTAuth) -> None:
        token = auth.create_token(subject="expired", ttl=-1)
        claims = auth.verify_token(token)
        assert claims.expired

    def test_wrong_secret_raises_invalid_token(self, auth: JWTAuth) -> None:
        token = auth.create_token(subject="test")
        other = JWTAuth(secret=generate_jwt_secret())
        with pytest.raises(jwt.InvalidTokenError):
            other.verify_token(token)

    def test_tampered_token_raises_invalid_token(self, auth: JWTAuth) -> None:
        token = auth.create_token(subject="test")
        tampered = token[:-4] + "AAAA"
        with pytest.raises(jwt.InvalidTokenError):
            auth.verify_token(tampered)

    def test_missing_secret_raises_os_error(self, monkeypatch) -> None:
        monkeypatch.delenv("SOLODSHOUSE_JWT_SECRET", raising=False)
        with pytest.raises(OSError, match="SOLODSHOUSE_JWT_SECRET"):
            JWTAuth()

    def test_has_role_true(self, auth: JWTAuth) -> None:
        claims = auth.verify_token(auth.create_token(subject="admin", roles=["admin"]))
        assert auth.has_role(claims, "admin")

    def test_has_role_false(self, auth: JWTAuth) -> None:
        claims = auth.verify_token(auth.create_token(subject="reader", roles=["reader"]))
        assert not auth.has_role(claims, "admin")

    def test_require_role_raises_permission_error(self, auth: JWTAuth) -> None:
        claims = auth.verify_token(auth.create_token(subject="reader", roles=["reader"]))
        with pytest.raises(PermissionError, match="lacks required role"):
            auth.require_role(claims, "admin")

    def test_require_role_passes(self, auth: JWTAuth) -> None:
        claims = auth.verify_token(auth.create_token(subject="admin", roles=["admin"]))
        auth.require_role(claims, "admin")

    def test_custom_ttl(self, auth: JWTAuth) -> None:
        claims = auth.verify_token(auth.create_token(subject="short", ttl=60))
        assert claims.expires_at - claims.issued_at == 60

    def test_token_claims_from_payload_preserves_roles(self) -> None:
        payload = {"sub": "test", "roles": ["admin"], "iss": "s", "iat": 1000, "exp": 2000}
        claims = TokenClaims.from_payload(payload)
        assert claims.subject == "test"
        assert claims.roles == ["admin"]

    def test_generate_jwt_secret_is_hex(self) -> None:
        secret = generate_jwt_secret()
        assert len(secret) == 64
