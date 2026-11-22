"""RIP-3 — the recorded founder RUN authorisation, checked in one place (OD-S9-17; FL-044, FL-045). SYNTHETIC ONLY.

Used by the run driver (`scripts/rip3_run.py`) and by the library guard (`rip3._guard`), so that no public call path
scores a registered set (eval 6201 / confirm 6301) without a recorded authorisation. Only committed content is read
(`git show HEAD:…`); working-tree files are not.

The consistency rule is the one the founder approved for FL-035 (OD-S9-18) and the guard now applies it itself:
every 'RIP-3 RUN' Markdown heading (H1–H6) in docs/DECISIONS.md must be the H2 form
'## Founder authorisation <id> — …' with <id> equal, as a whole word, to a recorded identifier; each entry has exactly
one such heading, and its section holds exactly one line equal to 'scope sha256: <hash of the entry>'.
Limit: Python code running in the same process can still replace these functions; the guard closes the public call
paths, it is not a sandbox."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

REGISTRY = "docs/research/RIP3_RUN_AUTHORISATIONS.json"
DECISIONS = "docs/DECISIONS.md"
ALLOWED_AFTER_APPROVAL = {REGISTRY, DECISIONS}
SCOPE_KEYS = ("id", "sets", "approved_commit", "approved_tree")
RUN_SETS = ("eval", "confirm")
_H2_FORM = re.compile(r"## Founder authorisation (\S+) — ")


class AuthorisationError(SystemExit):
    pass


def _git(root, *args):
    p = subprocess.run(["git", *args], capture_output=True, text=True, cwd=root)
    return p.returncode, p.stdout.strip()


def scope_sha256(entry):
    """The hash of an authorisation's scope (id, sets, approved commit and tree), canonical JSON."""
    blob = json.dumps({k: entry.get(k) for k in SCOPE_KEYS}, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("ascii")).hexdigest()


def run_headings(lines):
    """(line number, identifier or None) for every Markdown heading H1–H6 that contains 'RIP-3 RUN'. The identifier is
    taken only from the accepted H2 form; any other form gives None."""
    heads = []
    for n, ln in enumerate(lines):
        if re.match(r"#{1,6}[ \t]", ln) and "RIP-3 RUN" in ln:
            m = _H2_FORM.match(ln)
            heads.append((n, m.group(1) if m else None))
    return heads


def decision_section(text, auth_id):
    """The section of a RUN authorisation: its H2 heading '## Founder authorisation <auth_id> — …' containing
    'RIP-3 RUN' (identifier compared whole), up to the next '## ' heading. None unless there is exactly one."""
    lines = text.splitlines()
    starts = [n for n, h in run_headings(lines) if h is not None and h == auth_id]
    if len(starts) != 1:
        return None
    end = next((i for i in range(starts[0] + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "\n".join(lines[starts[0]:end]).rstrip()


def registry_problems(registry_text, decisions_text):
    """Consistency of the registry with DECISIONS.md, from file contents only (the FL-035 rule). [] = consistent."""
    try:
        entries = json.loads(registry_text)["authorisations"]
    except (ValueError, KeyError, TypeError):
        return ["registry is not an object with an 'authorisations' list"]
    if not isinstance(entries, list):
        return ["registry is not an object with an 'authorisations' list"]
    problems, ids = [], [e.get("id") if isinstance(e, dict) else None for e in entries]
    lines = decisions_text.splitlines()
    heads = run_headings(lines)
    for e, i in zip(entries, ids):
        if not isinstance(i, str) or not i:
            problems.append(f"entry without an id: {e!r}")
            continue
        if ids.count(i) != 1:
            problems.append(f"{i}: recorded {ids.count(i)} times")
            continue
        if set(e) != set(SCOPE_KEYS):
            problems.append(f"{i}: keys {sorted(e)} are not exactly the scope keys")
        s = e.get("sets")
        if (not isinstance(s, list) or not s or not all(isinstance(x, str) for x in s) or len(set(s)) != len(s)
                or not set(s) <= set(RUN_SETS)):
            problems.append(f"{i}: invalid sets {s!r}")
        for k in ("approved_commit", "approved_tree"):
            if not isinstance(e.get(k), str) or not re.fullmatch(r"[0-9a-f]{40}", e[k]):
                problems.append(f"{i}: {k} is not a full 40-hex id")
        mine = [n for n, h in heads if h == i]
        if len(mine) != 1:
            problems.append(f"{i}: {len(mine)} 'RIP-3 RUN' headings with exactly this identifier (need 1)")
            continue
        end = next((k for k in range(mine[0] + 1, len(lines)) if lines[k].startswith("## ")), len(lines))
        scope_lines = [ln for ln in lines[mine[0]:end] if ln.startswith("scope sha256:")]
        if scope_lines != [f"scope sha256: {scope_sha256(e)}"]:
            problems.append(f"{i}: its section needs exactly one line 'scope sha256: <hash of the entry>', "
                            f"found {scope_lines!r}")
    for n, h in heads:
        if h is None:
            problems.append(f"'RIP-3 RUN' heading not of the form '## Founder authorisation <id> — …': {lines[n]}")
        elif h not in ids:
            problems.append(f"'RIP-3 RUN' heading without a registry entry: {lines[n]}")
    return problems


def _at(root, rev, path):
    rc, out = _git(root, "show", f"{rev}:{path}")
    return out if rc == 0 else None


def _entry(registry_text, auth_id):
    try:
        es = [e for e in json.loads(registry_text).get("authorisations", []) if e.get("id") == auth_id]
    except (ValueError, AttributeError):
        return None
    return es[0] if len(es) == 1 else None


def check_authorisation(root, auth_id, set_name):
    """OD-S9-17, hardened (FL-044): the identifier must be a founder RUN authorisation recorded, in the committed HEAD,
    both in the registry (exactly one entry: sets, approved commit and tree) and in DECISIONS.md (exactly one H2
    heading of the accepted form with exactly this identifier, whose section states the entry's scope hash). The entry
    and that section must be byte-for-byte what they were in the first commit that recorded the entry, added together
    in that commit. The code must be the approved commit, or a descendant that differs from it only in these two
    files. Finally the whole registry must be consistent with DECISIONS.md (registry_problems). Working-tree files are
    not read."""
    root = Path(root)
    if not isinstance(auth_id, str) or not auth_id:
        raise AuthorisationError("the registered sets need the founder's RUN authorisation identifier (--authorisation)")
    reg_head = _at(root, "HEAD", REGISTRY)
    if reg_head is None:
        raise AuthorisationError(f"authorisation registry missing in HEAD: {REGISTRY}")
    e = _entry(reg_head, auth_id)
    if e is None:
        raise AuthorisationError(f"authorisation {auth_id!r} is not recorded (exactly once) in {REGISTRY}")
    sets = e.get("sets")
    if not isinstance(sets, list) or not sets or len(set(sets)) != len(sets) or not set(sets) <= set(RUN_SETS):
        raise AuthorisationError(f"authorisation {auth_id}: invalid sets {sets!r}")
    if set_name not in sets:
        raise AuthorisationError(f"authorisation {auth_id} does not cover the set {set_name!r}")
    dec_head = _at(root, "HEAD", DECISIONS) or ""
    sec_head = decision_section(dec_head, auth_id)
    if sec_head is None:
        raise AuthorisationError(f"authorisation {auth_id} has no single 'RIP-3 RUN' heading in docs/DECISIONS.md")
    h = scope_sha256(e)
    if f"scope sha256: {h}" not in sec_head:
        raise AuthorisationError(f"the DECISIONS.md section of {auth_id} does not state the entry's scope sha256 {h}")
    commit, tree = e.get("approved_commit", ""), e.get("approved_tree", "")
    rc, t = _git(root, "rev-parse", f"{commit}^{{tree}}")
    if rc != 0 or t != tree:
        raise AuthorisationError(f"approved commit {commit} not found or its tree is not {tree}")
    rc, _ = _git(root, "merge-base", "--is-ancestor", commit, "HEAD")
    if rc != 0:
        raise AuthorisationError(f"HEAD does not descend from the approved commit {commit}")
    rc, changed = _git(root, "diff", "--name-only", commit, "HEAD")
    extra = sorted(set(filter(None, changed.splitlines())) - ALLOWED_AFTER_APPROVAL)
    if rc != 0 or extra:
        raise AuthorisationError(f"files changed since the approved commit outside the authorisation records: {extra}")
    rc, revs = _git(root, "rev-list", "--reverse", f"{commit}..HEAD", "--", REGISTRY)
    first = next((c for c in revs.split() if _entry(_at(root, c, REGISTRY) or "{}", auth_id) is not None), None)
    if rc != 0 or first is None:
        raise AuthorisationError(f"no commit after {commit} records {auth_id}")
    if _entry(_at(root, first, REGISTRY), auth_id) != e:
        raise AuthorisationError(f"the registry entry of {auth_id} changed since it was recorded in {first}")
    if decision_section(_at(root, first, DECISIONS) or "", auth_id) != sec_head:
        raise AuthorisationError(f"the DECISIONS.md section of {auth_id} changed since it was recorded in {first}")
    rc, parents = _git(root, "rev-list", "--parents", "-n", "1", first)
    parents = parents.split()[1:] if rc == 0 else []
    if len(parents) != 1:
        raise AuthorisationError(f"the commit {first} that recorded {auth_id} must have exactly one parent")
    if decision_section(_at(root, parents[0], DECISIONS) or "", auth_id) is not None:
        raise AuthorisationError(f"the decision section of {auth_id} existed before {first}: the entry and the section "
                                 "must be added together in one commit")
    problems = registry_problems(reg_head, dec_head)
    if problems:
        raise AuthorisationError(f"the registry is not consistent with docs/DECISIONS.md in HEAD (FL-044): {problems}")
    _, head = _git(root, "rev-parse", "HEAD")
    return {"id": auth_id, "set": set_name, "sets": sets, "approved_commit": commit, "approved_tree": tree,
            "scope_sha256": h, "recorded_in": first, "head": head}


def tree_clean(root):
    """True if `git status --porcelain` is empty (ignored files do not count)."""
    rc, out = _git(Path(root), "status", "--porcelain")
    return rc == 0 and not out


def verify_registered(root, auth_id, set_name):
    """FL-045: what any caller must pass before a registered set is scored: a recorded authorisation for this set
    (check_authorisation) and a clean working tree, so the code that runs is exactly the committed code."""
    auth = check_authorisation(root, auth_id, set_name)
    if not tree_clean(root):
        raise AuthorisationError("working tree not clean: a registered set runs only exactly the committed code")
    return auth
