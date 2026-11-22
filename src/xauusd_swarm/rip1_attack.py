"""RIP-1 attacker side (role reid_checker). SYNTHETIC ONLY. Design: docs/research/REID_PROGRAMME.md §3.

Public knowledge only (Kerckhoffs): the world description (reid.ASSETS, reid.PERIODS, reid.simulate), the
parameter-draw table `draw`, the representation definitions and the custody code. The attacker never
receives parameters, key, seeds, prices or labels of test families. It receives: blinded series grouped by
random family ID; in V1 a read-only ledger snapshot; for A5, labels of separate DEV families that custody
produced through the same pipeline (public training families; their parameters stay secret).

Attackers: A1–A3 (reid.attack, unchanged; S-ind), A4a/A4b (pooled; S-pool), A5-* (ledger channels; V1),
A6 (marginal likelihood over the published priors; reviewer-specified, derived from the actual transforms
in representations.py — derivation in the A6 section below).
"""
from __future__ import annotations

import math
import random

import numpy as np

from . import reid
from .representations import affine_level, level_residual, log_returns, tick_grid, volatility_time

REPS = ["log_returns", "tick_grid", "level_residual", "affine_level", "volatility_time"]
ALIASES = {"activity_time": "log_returns"}      # one update per step in this world: identical data (declared)
SCEN = {"ind": 1, "g4": 4, "g16": 16}
SPEC = {"n": 512, "families_per_class": {"ind": 25, "g4": 10, "g16": 5}, "grid": 257,
        "attacker_dev_seed": 4101, "m_set": [0.5, 1.0, 5.0, 10.0]}
CLASSES = [(a, p) for a in range(reid.K) for p in range(reid.P)]

# Frozen ledger field list (review R5): what a params_fixed entry exposes, fixed by the custody code — entry
# (seq, prev, digest, plus the derived rank of seq), signature envelope (signer, signature) and the statement
# written by rip1.run (action, nonce, family, params_commitment, delta). The orchestrator checks that the real
# snapshot yields exactly these before any V1 run.
LEDGER_FIELDS = ("entry.digest", "entry.prev", "entry.seq", "entry.seq_rank", "env.signature_hex", "env.signer",
                 "st.action", "st.delta", "st.family", "st.nonce", "st.params_commitment")


def expected_attackers(view: str, scenario: str, rep: str) -> frozenset:
    """Frozen attacker set per view × scenario × representation (review R5); the same for every representation."""
    if rep not in REPS or scenario not in SCEN or view not in ("V0", "V1"):
        raise ValueError((view, scenario, rep))
    if view == "V0":
        base = {"A1_knn_features", "A2_centroid_features", "A3_series_match"} if scenario == "ind" else {"A4a", "A4b"}
        return frozenset(base | {"A6"})
    return frozenset({"A5-delta", "A5-all", "A5-comb", "A6-V1"} |
                     {f"A5-f:{f}" for f in LEDGER_FIELDS if f != "st.delta"})


# ---------------- public draw table (§3.3) and transforms ----------------
def draw(asset: int, rnd) -> dict:
    """One family's secret values; rnd is secrets.SystemRandom() on the custody side. Order fixed: c, a, b, m."""
    L, tick = reid.ASSETS[asset]["level"], reid.ASSETS[asset]["tick"]
    return {"c": rnd.uniform(-1.0, 1.0) * L, "a": math.exp(rnd.uniform(-3.0, 3.0)),
            "b": rnd.uniform(-1000.0, 1000.0), "m": rnd.choice(SPEC["m_set"]) * 100 * tick}


def blind(rep: str, prices, asset: int, prm: dict):
    rep = ALIASES.get(rep, rep)
    if rep == "log_returns":
        return log_returns(prices)                      # scale not secret (س 205); unscaled here
    if rep == "volatility_time":
        return volatility_time(prices)
    if rep == "tick_grid":
        return tick_grid(prices, prm["c"], reid.ASSETS[asset]["tick"])
    if rep == "level_residual":
        return level_residual(prices, prm["m"])
    if rep == "affine_level":
        return affine_level(prices, prm["a"], prm["b"])
    raise ValueError(rep)


def simulate_families(rep, per_class, g, rnd):
    """Attacker's own dev families from the public description (own draws). Returns [(series_list, label)]."""
    out = []
    for (a, p) in CLASSES:
        for _ in range(per_class):
            prm = draw(a, rnd)
            out.append(([blind(rep, reid.simulate(a, p, SPEC["n"], rnd), a, prm) for _ in range(g)], (a, p)))
    rnd.shuffle(out)
    return out


# ---------------- A4 (pooled) ----------------
def _dist2(u, v):
    return sum((x - y) ** 2 for x, y in zip(u, v))


def a4(dev, test_groups):
    """dev: [(series_list, label)] with the scenario's g; test_groups: [series_list]. Returns {'A4a': [...], 'A4b': [...]}."""
    dev_feats = [[reid.features(x) for x in xs] for xs, _ in dev]
    z = reid._standardiser([f for fs in dev_feats for f in fs])
    dz = [[z(f) for f in fs] for fs in dev_feats]
    labels = [y for _, y in dev]
    k = len(dz[0][0])
    gm = [[sum(f[j] for f in fs) / len(fs) for j in range(k)] for fs in dz]
    cent_g = {c: [sum(m[j] for m, y in zip(gm, labels) if y == c) / labels.count(c) for j in range(k)] for c in CLASSES}
    flat = [(f, y) for fs, y in zip(dz, labels) for f in fs]
    cent_s = {c: [sum(f[j] for f, y in flat if y == c) / sum(1 for _, y in flat if y == c) for j in range(k)]
              for c in CLASSES}
    out_a, out_b = [], []
    for xs in test_groups:
        tz = [z(reid.features(x)) for x in xs]
        m = [sum(f[j] for f in tz) / len(tz) for j in range(k)]
        out_a.append(min(CLASSES, key=lambda c: (_dist2(cent_g[c], m), CLASSES.index(c))))
        votes = [min(CLASSES, key=lambda c: (_dist2(cent_s[c], f), CLASSES.index(c))) for f in tz]
        top = max(votes.count(c) for c in set(votes))
        tied = [c for c in CLASSES if votes.count(c) == top]
        out_b.append(min(tied, key=lambda c: (sum(_dist2(cent_s[c], f) for f in tz), CLASSES.index(c))))
    return {"A4a": out_a, "A4b": out_b}


# ---------------- A5 (ledger channels, V1) ----------------
def ledger_fields(records) -> dict:
    """family -> flat field dict, from params_fixed records of a ledger snapshot (entry and decoded statement)."""
    import json
    rows, order = {}, []
    for r in records:
        if r.get("kind") != "params_fixed":
            continue
        st = json.loads(bytes.fromhex(r["payload"]["statement_hex"]))
        f = {"entry.seq": r["seq"], "entry.prev": r["prev"], "entry.digest": r["digest"],
             "env.signer": r["payload"]["signer"], "env.signature_hex": r["payload"]["signature_hex"]}
        f.update({"st." + k: v for k, v in st.items()})
        rows[st["family"]] = f
        order.append(st["family"])
    for i, fam in enumerate(order):                 # rank fraction for numeric fields with many values
        rows[fam]["entry.seq_rank"] = i / max(1, len(order) - 1)
    return rows


def _encoder(dev_vals):
    nums = [v for v in dev_vals if isinstance(v, (int, float)) and not isinstance(v, bool)]
    if len(nums) == len(dev_vals) and len(set(nums)) > 16:
        qs = sorted(nums)
        cuts = [qs[int(len(qs) * i / 8)] for i in range(1, 8)]
        return lambda v: ("bin", sum(v >= c for c in cuts)) if isinstance(v, (int, float)) else ("str", str(v))
    return lambda v: ("v", repr(v))


def nb_model(dev_rows, dev_labels, fields, alpha=1.0):
    enc = {f: _encoder([r.get(f) for r in dev_rows]) for f in fields}
    tab = {f: {} for f in fields}
    for r, y in zip(dev_rows, dev_labels):
        for f in fields:
            tab[f].setdefault(enc[f](r.get(f)), {}).setdefault(y, 0)
            tab[f][enc[f](r.get(f))][y] += 1

    def score(row):
        s = {c: 0.0 for c in CLASSES}
        for f in fields:
            cnt = tab[f].get(enc[f](row.get(f)))
            if cnt is None:
                continue                                    # unseen value: uniform, no information
            tot = sum(cnt.values())
            for c in CLASSES:
                s[c] += math.log((cnt.get(c, 0) + alpha) / (tot + alpha * len(CLASSES)))
        return s
    return score


def argmax(scores: dict):
    return max(CLASSES, key=lambda c: (scores[c], -CLASSES.index(c)))


# ---------------- A6: marginal likelihood over the published priors ----------------
# World (reid.simulate): price_t = price_{t-1}·exp(r_t), r_t ~ N(μ_a, s_t²), s_t = vol_a·volx_p·(1 + act_a·sin(2πt/64)),
# price_{-1} = L_a·growth_p =: Lg, then rounding to the tick (ignored by the model: declared approximation).
# P_0 = Lg·exp(r_0) (lognormal), P_i (i ≥ 1) as above. log_returns(P) gives r_1 … r_{n-1}.
# Actual transforms (representations.py): affine x = a·P + b; tick_grid x = (P − c)/Δ; level_residual x = fmod(P, m);
# volatility_time x = [0, cumsum(r²)].
#  affine: P = (x − b)/a, so r_i = ln((x_i − b)/(x_{i−1} − b)) (a cancels). Density of x_0 given b:
#    ln(x_0 − b) = ln a + ln Lg + r_0, ln a ~ U(−3, 3) ⇒ p(x_0|b) = p_v(ln(x_0−b) − ln Lg)/(x_0 − b), p_v = U(−3,3) ⊛ N(μ, s_0²).
#    Jacobian of x_i → r_i given x_{i−1}: 1/(x_i − b). b integrated over U(−1000, 1000) by midpoint quadrature.
#    Group (shared a, b): ∫ (1/6) Π_k N(w_k − u; 0, s_0²) du with w_k = ln(x_0^k − b) − ln Lg − μ (closed form).
#  tick_grid: P = c + Δ·x; given c: p(x_0|c) = LN(P_0)·Δ, increments r_i = ln(P_i/P_{i−1}) with Jacobian Δ/P_i.
#    c ~ U(−L_a, L_a); quadrature over the window where P_0 is within exp(μ ± 8 s_0)·Lg (∩ prior; ∩ over group members).
#    Δ is the class's tick (custody rule, public); in V1 the ledger Δ must match the class tick, else probability 0.
#  level_residual: x = P mod m; d_i = x_i − x_{i−1} ≡ ΔP_i (mod m); ΔP_i ≈ Lg·r_i (approximation: level held at Lg,
#    declared); p(x_i|x_{i−1}) = Σ_j N(d_i + j·m; Lg·μ, (Lg·s_i)²) (wrapped normal); p(x_0) = Σ_j LN(x_0 + j·m).
#    m ∈ the class's 4-value set, exact sum with weight 1/4; group members share m.
#  volatility_time: u_i = x_i − x_{i−1} = r_i²; p(u) = [φ((√u−μ)/s) + φ((−√u−μ)/s)] / (2 s √u).
#  log_returns: r directly.
_SQ2 = math.sqrt(2.0)
_erfc = np.frompyfunc(math.erfc, 1, 1)


def _cls(c):
    a, p = c
    A, Pp = reid.ASSETS[a], reid.PERIODS[p]
    n = SPEC["n"]
    t = np.arange(n)
    s = A["vol"] * Pp["volx"] * (1 + A["act"] * np.sin(2 * np.pi * t / 64))
    return {"mu": A["drift"], "s": s, "Lg": A["level"] * Pp["growth"], "L": A["level"], "tick": A["tick"]}


def _logN(x, mu, s):
    return -0.5 * ((x - mu) / s) ** 2 - np.log(s) - 0.5 * math.log(2 * math.pi)


def _lse(v):
    v = np.asarray(v, dtype=float)
    m = np.max(v)
    return m + math.log(np.sum(np.exp(v - m))) if np.isfinite(m) else -math.inf


def _log_phi_diff(lo, hi):
    """log(Φ(hi) − Φ(lo)), stable in the tails."""
    if hi <= lo:
        return -math.inf
    if lo > 0:
        v = 0.5 * (math.erfc(lo / _SQ2) - math.erfc(hi / _SQ2))
    elif hi < 0:
        v = 0.5 * (math.erfc(-hi / _SQ2) - math.erfc(-lo / _SQ2))
    else:
        v = 1.0 - 0.5 * math.erfc(-lo / _SQ2) - 0.5 * math.erfc(hi / _SQ2)
    return math.log(v) if v > 0 else -math.inf


def ll_returns(xs, k):
    return sum(float(np.sum(_logN(np.asarray(x), k["mu"], k["s"][1:len(x) + 1]))) for x in xs)


def ll_voltime(xs, k):
    tot = 0.0
    for x in xs:
        u = np.maximum(np.diff(np.asarray(x)), 1e-300)
        s = k["s"][1:len(u) + 1]
        r = np.sqrt(u)
        a = np.exp(_logN(r, k["mu"], s)) + np.exp(_logN(-r, k["mu"], s))
        with np.errstate(divide="ignore"):
            tot += float(np.sum(np.log(a) - np.log(2 * r)))
    return tot


def _affine_grid(xs, k, bs):
    """log p(xs | class k, b) for every b in the grid bs (vectorised over b); shared a, b across members."""
    s0, mu = k["s"][0], k["mu"]
    G = len(bs)
    tot = np.zeros(G)
    valid = np.ones(G, dtype=bool)
    ws = []
    for x in xs:
        z = np.asarray(x)[None, :] - bs[:, None]
        ok = np.all(z > 0, axis=1)
        valid &= ok
        lz = np.log(np.where(z > 0, z, 1.0))
        ws.append(lz[:, 0] - math.log(k["Lg"]) - mu)
        tot -= lz[:, 0]                                           # Jacobian x_0 → ln(x_0 − b)
        r = np.diff(lz, axis=1)
        tot += np.sum(_logN(r, mu, k["s"][1:r.shape[1] + 1][None, :]) - lz[:, 1:], axis=1)
    g = len(ws)
    w = np.vstack(ws)                                             # g × G
    wb = np.mean(w, axis=0)
    tot += (-math.log(6.0) - 0.5 * g * math.log(2 * math.pi * s0 ** 2) - np.sum((w - wb) ** 2, axis=0) / (2 * s0 ** 2)
            + 0.5 * math.log(2 * math.pi * s0 ** 2 / g)
            + np.array([_log_phi_diff((-3.0 - v) * math.sqrt(g) / s0, (3.0 - v) * math.sqrt(g) / s0) for v in wb]))
    return np.where(valid, tot, -np.inf)


def ll_affine(xs, k, G):
    bs = -1000.0 + 2000.0 * (np.arange(G) + 0.5) / G
    return _lse(_affine_grid(xs, k, bs)) - math.log(G)


def _tick_grid_ll(xs, k, cs, delta):
    s0, mu, Lg = k["s"][0], k["mu"], k["Lg"]
    tot = np.zeros(len(cs))
    valid = np.ones(len(cs), dtype=bool)
    for x in xs:
        P = cs[:, None] + delta * np.asarray(x)[None, :]
        valid &= np.all(P > 0, axis=1)
        lP = np.log(np.where(P > 0, P, 1.0))
        tot += _logN(lP[:, 0], math.log(Lg) + mu, s0) - lP[:, 0] + math.log(delta)
        r = np.diff(lP, axis=1)
        tot += np.sum(_logN(r, mu, k["s"][1:r.shape[1] + 1][None, :]) - lP[:, 1:] + math.log(delta), axis=1)
    return np.where(valid, tot, -np.inf)


def ll_tick(xs, k, G, delta):
    s0, mu, Lg, L = k["s"][0], k["mu"], k["Lg"], k["L"]
    lo_p, hi_p = Lg * math.exp(mu - 8 * s0), Lg * math.exp(mu + 8 * s0)
    lo, hi = -L, L
    for x in xs:
        lo, hi = max(lo, lo_p - delta * x[0]), min(hi, hi_p - delta * x[0])
    if hi <= lo:
        return -math.inf
    cs = lo + (hi - lo) * (np.arange(G) + 0.5) / G
    return _lse(_tick_grid_ll(xs, k, cs, delta)) + math.log((hi - lo) / G) - math.log(2 * L)


def _ll_resid_given_m(xs, k, m):
    mu, s0, Lg = k["mu"], k["s"][0], k["Lg"]
    tot = 0.0
    for x in xs:
        x = np.asarray(x)
        lo, hi = Lg * math.exp(mu - 8 * s0), Lg * math.exp(mu + 8 * s0)
        js = np.arange(math.floor((lo - x[0]) / m), math.ceil((hi - x[0]) / m) + 1)
        P0 = x[0] + js * m
        P0 = P0[P0 > 0]
        if P0.size == 0:
            return -math.inf
        tot += _lse(_logN(np.log(P0), math.log(Lg) + mu, s0) - np.log(P0))
        d = np.diff(x)
        S = Lg * k["s"][1:len(d) + 1]
        J = int(math.ceil(8 * float(np.max(S)) / m)) + 2
        jj = np.arange(-J, J + 1)[None, :]
        v = _logN(d[:, None] + jj * m, Lg * mu, S[:, None])
        mx = np.max(v, axis=1)
        tot += float(np.sum(mx + np.log(np.sum(np.exp(v - mx[:, None]), axis=1))))
    return tot


def ll_resid(xs, k):
    tick = k["tick"]
    return _lse([_ll_resid_given_m(xs, k, f * 100 * tick) for f in SPEC["m_set"]]) - math.log(len(SPEC["m_set"]))


def a6_scores(rep, xs, delta_seen=None):
    """Log marginal likelihood per class for one unit (xs = the family's series). delta_seen: V1 ledger Δ."""
    rep = ALIASES.get(rep, rep)
    G = SPEC["grid"]
    out = {}
    for c in CLASSES:
        k = _cls(c)
        if delta_seen is not None and not math.isclose(delta_seen, k["tick"], rel_tol=1e-12):
            out[c] = -math.inf
            continue
        if rep == "log_returns":
            out[c] = ll_returns(xs, k)
        elif rep == "volatility_time":
            out[c] = ll_voltime(xs, k)
        elif rep == "affine_level":
            out[c] = ll_affine(xs, k, G)
        elif rep == "tick_grid":
            out[c] = ll_tick(xs, k, G, k["tick"])
        elif rep == "level_residual":
            out[c] = ll_resid(xs, k)
        else:
            raise ValueError(rep)
    return out


# ---------------- isolation probes (run inside the attacker process before any attack) ----------------
def probes(secret_paths: list[str], in_dir: str | None = None, out_dir: str | None = None) -> dict:
    import os
    import socket
    import subprocess
    res = {}

    def denied(fn):
        try:
            fn()
            return False
        except (PermissionError, FileNotFoundError, OSError):
            return True
    st = open("/proc/self/status").read()
    caps = {l.split(":")[0]: l.split(":")[1].strip() for l in st.splitlines() if l.startswith(("Cap", "NoNewPrivs"))}
    res["uid_nonzero"] = os.getuid() != 0 and os.geteuid() != 0 and os.getgid() != 0
    res["no_groups"] = os.getgroups() in ([], [os.getgid()])
    res["caps_all_zero"] = all(int(caps.get(c, "1"), 16) == 0 for c in ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb"))
    res["no_new_privs"] = caps.get("NoNewPrivs") == "1"
    fds = sorted(int(f) for f in os.listdir("/proc/self/fd"))
    res["fds"] = fds
    res["only_std_fds"] = set(fds) <= {0, 1, 2, max(fds)}         # max = the listdir handle itself
    res["env_keys"] = sorted(os.environ)
    res["env_only_path"] = set(os.environ) <= {"PATH", "LC_CTYPE"}
    for p in secret_paths:
        res[f"denied_read:{p}"] = denied(lambda: open(p, "rb").read(1)) and denied(lambda: os.listdir(p))
    pids = [d for d in os.listdir("/proc") if d.isdigit()]
    res["visible_pids"] = sorted(int(x) for x in pids)
    res["no_other_process_visible"] = len(pids) <= 2
    res["net_ifaces"] = [l.split(":")[0].strip() for l in open("/proc/net/dev").read().splitlines()[2:]]

    def tcp():
        s = socket.create_connection(("1.1.1.1", 443), timeout=2)
        s.close()

    def udp():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(b"x", ("1.1.1.1", 53))
        s.close()
    res["tcp_denied"], res["udp_denied"] = denied(tcp), denied(udp)
    try:
        r = subprocess.run(["sudo", "-n", "true"], capture_output=True, timeout=10)
        res["sudo_denied"] = r.returncode != 0
    except (OSError, subprocess.SubprocessError):
        res["sudo_denied"] = True
    skip = ("/proc", "/sys", "/dev", "/usr", "/lib", "/lib64", "/lib32", "/bin", "/sbin", "/etc", "/var/lib",
            "/var/cache", "/snap", "/boot")
    readable = []
    for root, dirs, files in os.walk("/", onerror=lambda e: None):
        if root.startswith(skip) and root != "/":
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if not os.path.join(root, d).startswith(skip)]
        for f in files:
            p = os.path.join(root, f)
            if os.access(p, os.R_OK):
                readable.append(p)
    # writable paths: only the run's own output directory may be writable (no channel between runs, R3-01)
    writable = []
    wskip = ("/proc", "/sys", "/dev/pts")
    for root, dirs, files in os.walk("/", onerror=lambda e: None):
        if root.startswith(wskip) and root != "/":
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if not os.path.join(root, d).startswith(wskip)]
        if os.access(root, os.W_OK) and not (out_dir and (root == out_dir or root.startswith(out_dir + "/"))):
            writable.append(root)
    res["writable_dirs_outside_out"] = sorted(writable)[:200]
    res["no_writable_dir_outside_out"] = not writable
    if in_dir:
        ins = [os.path.join(in_dir, f) for f in os.listdir(in_dir)]
        res["inputs_read_only"] = all(denied(lambda p=p: open(p, "ab").close()) for p in ins) and \
            denied(lambda: open(os.path.join(in_dir, "new_file"), "w").close())
    res["readable_nonsystem_count"] = len(readable)
    res["readable_nonsystem"] = sorted(readable)[:2000]
    res["no_secret_path_readable"] = not any(p.startswith(tuple(secret_paths)) for p in readable)
    checks = ["uid_nonzero", "no_groups", "caps_all_zero", "no_new_privs", "only_std_fds", "env_only_path",
              "no_other_process_visible", "tcp_denied", "udp_denied", "sudo_denied", "no_secret_path_readable",
              "no_writable_dir_outside_out"] + (["inputs_read_only"] if in_dir else []) + \
             [k for k in res if k.startswith("denied_read:")]
    res["all_pass"] = all(res[c] is True for c in checks)
    res["checks"] = checks
    return res


# ---------------- all predictions for one view (called by scripts/rip1_attacker.py after the probes,
# and by the reproduction test on the committed data) ----------------
def predict(IN, VIEW, inp):
    """One sandbox run = one representation × one view (review R3-02). IN holds only that representation's
    data (and the ledger snapshot in V1). Returns ({scenario: {attacker: {family: [asset, period]}}}, input hashes)."""
    import hashlib
    import json
    import os
    sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()     # noqa: E731
    import gzip
    import sys
    A = sys.modules[__name__]
    spec = inp["spec"]
    A.SPEC.update(spec)
    rep = inp["rep"]
    data_sha = {f"data_{rep}.npz": sha(os.path.join(IN, f"data_{rep}.npz"))}
    ledger = None
    if VIEW == "V1":
        lp = os.path.join(IN, "ledger.jsonl")
        if os.path.exists(lp):
            data_sha["ledger.jsonl"] = sha(lp)
            lines = open(lp, encoding="utf-8").read().splitlines()
        else:                                          # reproduction on the committed gzip copy
            raw = gzip.open(lp + ".gz").read()
            data_sha["ledger.jsonl"] = hashlib.sha256(raw).hexdigest()
            lines = raw.decode("utf-8").splitlines()
        ledger = A.ledger_fields([json.loads(l) for l in lines])
    preds = {}
    z = np.load(os.path.join(IN, f"data_{rep}.npz"))
    for sc, g in A.SCEN.items():
        fams = [str(f) for f in z[f"F_{sc}"]]
        X = z[f"X_{sc}"]                                   # units × g × length
        groups = [[list(map(float, X[u, i])) for i in range(g)] for u in range(len(fams))]
        rnd = random.Random(spec["attacker_dev_seed"] + 1000 * A.REPS.index(rep) + g)
        dev = A.simulate_families(rep, spec["families_per_class"][sc], g, rnd)
        P = {}
        if VIEW == "V0":
            if g == 1:
                dx, dy = [xs[0] for xs, _ in dev], [y for _, y in dev]
                for att in ("A1_knn_features", "A2_centroid_features", "A3_series_match"):
                    P[att] = reid.attack(att, dx, dy, [xs[0] for xs in groups])
            else:
                P.update(A.a4(dev, groups))
            P["A6"] = [A.argmax(A.a6_scores(rep, xs)) for xs in groups]
        else:
            dl = inp["dev_labels"][sc]                # custody pipeline dev families (labels public)
            drows = [ledger[f] for f in dl]
            dlab = [tuple(dl[f]) for f in dl]
            trows = [ledger[f] for f in fams]
            fields = list(LEDGER_FIELDS)                     # frozen list, not taken from the data (R5)
            if any(set(r) != set(LEDGER_FIELDS) for r in drows + trows):
                raise ValueError("ledger rows do not expose exactly the frozen field list")
            P["A5-delta"] = [A.argmax(A.nb_model(drows, dlab, ["st.delta"])(r)) for r in trows]
            for f in fields:
                if f != "st.delta":
                    P[f"A5-f:{f}"] = [A.argmax(A.nb_model(drows, dlab, [f])(r)) for r in trows]
            nb_all = A.nb_model(drows, dlab, fields)
            P["A5-all"] = [A.argmax(nb_all(r)) for r in trows]
            # A5-comb: ledger NB + series distance (A2 centroid for S-ind, A4a group mean for S-pool)
            fd = [[reid.features(x) for x in xs] for xs, _ in dev]
            zf = reid._standardiser([f for fs in fd for f in fs])
            gm = lambda fs: [sum(c) / len(fs) for c in zip(*fs)]          # noqa: E731
            dm = [gm([zf(f) for f in fs]) for fs in fd]
            lab = [y for _, y in dev]
            cent = {c: gm([m for m, y in zip(dm, lab) if y == c]) for c in A.CLASSES}
            comb = []
            for xs, r in zip(groups, trows):
                m = gm([zf(reid.features(x)) for x in xs])
                s = nb_all(r)
                comb.append(A.argmax({c: s[c] - 0.5 * A._dist2(cent[c], m) for c in A.CLASSES}))
            P["A5-comb"] = comb
            P["A6-V1"] = [A.argmax(A.a6_scores(rep, xs, delta_seen=ledger[f]["st.delta"]))
                          for xs, f in zip(groups, fams)]
        preds[sc] = {att: {f: list(p) for f, p in zip(fams, v)} for att, v in P.items()}
    return preds, data_sha
