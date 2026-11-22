"""Signed statements (WP8-02, governance core).

Authority is never a string the caller passes: every privileged act is an Ed25519 signature over
a canonical statement, verified against a registered PUBLIC key. Registration of keys, nonces and
all other governance state live in the ledger (see charter.Governance, which rebuilds everything
from it). Stated limit: a signature proves key possession, not the person; key custody is
operational.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from .ledger import canonical


class AuthError(Exception):
    pass


def public_hex(pk: Ed25519PublicKey) -> str:
    return pk.public_bytes(Encoding.Raw, PublicFormat.Raw).hex()


@dataclass(frozen=True)
class Signed:
    identity: str
    statement: bytes
    signature: bytes

    def to_payload(self) -> dict:
        return {"signer": self.identity, "statement_hex": self.statement.hex(), "signature_hex": self.signature.hex()}

    @staticmethod
    def from_payload(p: dict) -> "Signed":
        """A malformed signed payload is an authentication refusal, never a crash (WP9-05b sweep)."""
        try:
            if not isinstance(p, dict) or not isinstance(p.get("signer"), str):
                raise TypeError("payload")
            return Signed(p["signer"], bytes.fromhex(p["statement_hex"]), bytes.fromhex(p["signature_hex"]))
        except (KeyError, TypeError, ValueError, AttributeError) as x:
            raise AuthError(f"malformed signed payload ({type(x).__name__})") from x


def sign(identity: str, key: Ed25519PrivateKey, statement: dict) -> Signed:
    b = canonical(statement)
    return Signed(identity, b, key.sign(b))


def check_signature(pub_hex: str, s: Signed) -> dict:
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub_hex)).verify(s.signature, s.statement)
    except (InvalidSignature, ValueError):
        raise AuthError("invalid signature")
    return json.loads(s.statement)
