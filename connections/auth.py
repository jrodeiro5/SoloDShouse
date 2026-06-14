"""JWT authentication and role-based access control (SDS-044).

Issues and validates JWTs with scoped roles for the connection manager API.

    auth = JWTAuth()
    token = auth.create_token(subject="dagster", roles=["reader", "admin"])
    claims = auth.verify_token(token)
    claims.roles  # -> ["reader", "admin"]
    auth.has_role(claims, "admin")  # -> True
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

import jwt

DEFAULT_ISSUER = "solodshouse"
DEFAULT_TTL = 3600 * 8  # 8 hours
DEFAULT_ALGORITHM = "HS256"


@dataclass(frozen=True)
class TokenClaims:
    """Deserialized JWT claims for authorization decisions."""

    subject: str
    roles: list[str] = field(default_factory=lambda: ["reader"])
    issuer: str = DEFAULT_ISSUER
    issued_at: int = 0
    expires_at: int = 0

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "TokenClaims":
        return cls(
            subject=payload.get("sub", ""),
            roles=list(payload.get("roles", ["reader"])),
            issuer=payload.get("iss", DEFAULT_ISSUER),
            issued_at=int(payload.get("iat", 0)),
            expires_at=int(payload.get("exp", 0)),
        )

    @property
    def expired(self) -> bool:
        return self.expires_at > 0 and time.time() > self.expires_at


class JWTAuth:
    """Issue and verify JWTs for API access control.

    Signing secret from ``SOLODSHOUSE_JWT_SECRET`` env var.
    Raises ``OSError`` if not set.

    Args:
        secret: Override secret. Defaults to env var.
        default_ttl: Token lifetime in seconds. Default 8 hours.
    """

    def __init__(
        self,
        secret: str | None = None,
        default_ttl: int = DEFAULT_TTL,
    ) -> None:
        self._secret = secret or os.environ.get("SOLODSHOUSE_JWT_SECRET")
        if not self._secret:
            raise OSError(
                "SOLODSHOUSE_JWT_SECRET is not set. "
                "Generate one and export it."
            )
        self._default_ttl = default_ttl

    def create_token(
        self,
        subject: str,
        roles: list[str] | None = None,
        ttl: int | None = None,
    ) -> str:
        """Issue a signed JWT for *subject* with *roles*.

        Args:
            subject: Token subject (e.g. "dagster", "api-client").
            roles: Roles to grant. Defaults to ``["reader"]``.
            ttl: Token lifetime in seconds. Defaults to ``self._default_ttl``.

        Returns:
            Encoded JWT string.
        """
        now = int(time.time())
        payload: dict[str, Any] = {
            "sub": subject,
            "roles": roles or ["reader"],
            "iss": DEFAULT_ISSUER,
            "iat": now,
            "exp": now + (ttl or self._default_ttl),
        }
        return jwt.encode(payload, self._secret, algorithm=DEFAULT_ALGORITHM)

    def verify_token(self, token: str) -> TokenClaims:
        """Verify and decode a JWT.

        Returns ``TokenClaims`` (with ``expired=True`` for expired tokens).

        Raises:
            jwt.InvalidTokenError: Token is invalid (wrong secret, tampered, etc.).
        """
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[DEFAULT_ALGORITHM],
                options={"require": ["sub", "roles", "exp", "iat"]},
            )
        except jwt.ExpiredSignatureError:
            # Decode without expiry check to get claims for expired tokens
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[DEFAULT_ALGORITHM],
                options={
                    "require": ["sub", "roles", "exp", "iat"],
                    "verify_exp": False,
                },
            )
        return TokenClaims.from_payload(payload)

    def has_role(self, claims: TokenClaims, role: str) -> bool:
        """Return True if *claims* includes *role*."""
        return role in claims.roles

    def require_role(self, claims: TokenClaims, role: str) -> None:
        """Raise ``PermissionError`` if *claims* lacks *role*."""
        if not self.has_role(claims, role):
            raise PermissionError(
                f"Subject '{claims.subject}' lacks required role '{role}'. "
                f"Granted: {claims.roles}."
            )


def generate_jwt_secret() -> str:
    """Return a new random secret suitable for ``SOLODSHOUSE_JWT_SECRET``."""
    import secrets
    return secrets.token_hex(32)
