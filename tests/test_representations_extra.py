"""Pre_validate hook is a no-op without custody (approved behaviour preserved)."""
import uuid
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from xauusd_swarm.charter import Governance
from xauusd_swarm.claims import ClaimsCharter
from xauusd_swarm.identity import sign
from xauusd_swarm.ledger import Ledger

FK = Ed25519PrivateKey.generate()

def F(a, **k):
    return sign("founder", FK, {"action": a, "nonce": uuid.uuid4().hex, **k})

def test_claims_without_custody_unchanged():
    cc = ClaimsCharter(); g = Governance(FK.public_key(), Ledger(), extensions=[cc])
    g.set_initial_charter(F("charter_initial", charter="project", text="P"))
    g.set_initial_charter(F("charter_initial", charter="claims", text="C"))
    g.consume_slice("S1")
    cc.register(F("register_claim", card={"claim_id": "K", "version": 1, "tags": ["الموقع"], "category": None, "path": "أ",
        "uses_events": False, "scope_type": "stable", "scope": "s", "rulings": {"existence": "e", "size_with_uncertainty": "s", "importance": "i"}}))
    cc.open_on_slice("K", "S1")
