"""Append-only, hash-chained ledger (WP8-02, governance core).

What it guarantees, stated precisely:
- Entries are immutable in memory: each payload is stored as canonical JSON bytes; reads return
  fresh copies, so no caller holds a reference into the ledger.
- verify() detects any edit, deletion or reordering of entries that does NOT rebuild a new
  consistent chain. A full rewrite with recomputed digests is NOT detectable from the file alone.
  That is why anchors exist: anchor() returns (length, head digest) to be stored OUTSIDE the
  ledger file (e.g. in the Stage register or an auditor's record), and verify(anchors=...) checks
  that every stored anchor still matches. A rewrite of anchored history is then detected.
- File-backed ledgers REQUIRE an AnchorStore outside the ledger's folder. Every append records
  (length, head) there, and every load verifies all stored anchors automatically. Not optional.
  Coverage rule (write-ahead intent protocol, see AnchorStore): a trailing unanchored entry is
  accepted ONLY if a matching INTENT was declared for it before it was written; a deleted, emptied
  or truncated anchor store is refused, including for a single-entry ledger.
- File writes AND loads: one at a time, under an exclusive lock file (<file>.lock, O_EXCL).
  Before appending, the writer re-reads the file, so entries appended by another writer are
  chained correctly. Each entry is one line written with a single write() and fsync().
- A partial trailing line (an unfinished last write: bytes after the last newline) makes loading
  FAIL by default; recover=True moves that tail to <file>.partial-<n> (kept) and truncates the
  ledger to its last complete entry. A malformed line INSIDE the file is corruption: loading
  fails and recover=True is refused, so no valid later entry can ever be cut away.
No market data of any kind.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

GENESIS = "0" * 64


class LedgerError(Exception):
    pass


class DuplicateError(LedgerError):
    pass


class AnchorStore:
    """Append-only, hash-chained anchor store kept OUTSIDE the ledger's folder.

    Write-ahead protocol for every ledger append (entry n with digest h):
      1. record INTENT(n, h) here (fsync);
      2. write entry n to the ledger (fsync);
      3. record COMMIT(n, h) here (fsync).
    On load, the ledger's length L and the last COMMIT n_c must satisfy:
      L == n_c                       -> consistent;
      L == n_c + 1 AND the LAST record here is INTENT(L, digest of entry L)
                                     -> a crash between steps 2 and 3; accepted, and the COMMIT is
                                        completed by the next writer (controlled recovery);
      anything else                  -> refused (anchors missing, emptied, truncated, or the entry
                                        does not match a declared intent).
    A crash between steps 1 and 2 leaves a dangling INTENT with L == n_c: consistent; the next
    INTENT for the same n supersedes it.
    So a deleted or emptied store is refused even when the ledger has a single entry: that entry
    would need a matching INTENT here.
    Trust boundary, stated: protection holds as far as this file is kept on storage the ledger's
    writer cannot rewrite (a separate drive or the auditor's copy)."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def _complete(self) -> tuple[bytes, bytes]:
        data = self.path.read_bytes() if self.path.exists() else b""
        cut = data.rfind(b"\n") + 1
        return data[:cut], data[cut:]             # (complete lines, unfinished write)

    @staticmethod
    def _h(t, n, head, prev):
        return hashlib.sha256(canonical({"type": t, "n": n, "head": head, "prev": prev})).hexdigest()

    def records(self) -> list[dict]:
        """Bytes after the last newline are an unfinished write of this store: ignored here
        (that record never existed), quarantined by the next append."""
        done, _ = self._complete()
        out, prev = [], GENESIS
        for line in done.splitlines():
            try:
                d = json.loads(line)
                ok = d["prev"] == prev and d["digest"] == self._h(d["type"], d["n"], d["head"], prev) \
                    and d["type"] in ("intent", "commit")
            except (ValueError, KeyError, TypeError):
                ok = False
            if not ok:
                raise LedgerError("anchor store integrity broken")
            out.append(d); prev = d["digest"]
        return out

    def read(self) -> list[tuple[int, str]]:
        return [(d["n"], d["head"]) for d in self.records() if d["type"] == "commit"]

    def last_record(self) -> dict | None:
        r = self.records()
        return r[-1] if r else None

    def _append(self, t: str, n: int, head: str) -> None:
        done, tail = self._complete()
        if tail:                                   # this store's own unfinished write: keep it, cut it
            k = 1
            while self.path.with_name(f"{self.path.name}.partial-{k}").exists():
                k += 1
            self.path.with_name(f"{self.path.name}.partial-{k}").write_bytes(tail)
            with open(self.path, "r+b") as fh:
                fh.truncate(len(done)); fh.flush(); os.fsync(fh.fileno())
        recs = self.records()
        prev = recs[-1]["digest"] if recs else GENESIS
        d = {"type": t, "n": n, "head": head, "prev": prev, "digest": self._h(t, n, head, prev)}
        fd = os.open(self.path, os.O_WRONLY | os.O_APPEND | os.O_CREAT)
        try:
            os.write(fd, canonical(d) + b"\n"); os.fsync(fd)
        finally:
            os.close(fd)

    def record_intent(self, n: int, head: str) -> None:
        self._append("intent", n, head)

    def record_commit(self, n: int, head: str) -> None:
        self._append("commit", n, head)


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True)
class Entry:
    seq: int
    kind: str
    _payload: bytes
    prev: str
    digest: str

    @property
    def payload(self) -> dict:
        return json.loads(self._payload)          # always a fresh copy

    def as_record(self) -> dict:
        return {"seq": self.seq, "kind": self.kind, "payload": self.payload, "prev": self.prev, "digest": self.digest}


def _digest(seq: int, kind: str, payload_bytes: bytes, prev: str) -> str:
    return hashlib.sha256(canonical({"seq": seq, "kind": kind, "payload": json.loads(payload_bytes), "prev": prev})).hexdigest()


class _FileLock:
    def __init__(self, path: Path, timeout: float = 10.0):
        self.path, self.timeout, self.fd = path, timeout, None

    def __enter__(self):
        t0 = time.monotonic()
        while True:
            try:
                self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                return self
            except (FileExistsError, PermissionError) as e:
                # Windows: a lock file in "delete pending" state (being removed by the previous
                # holder) makes O_CREAT|O_EXCL fail with access denied, not "exists". Treat it as
                # locked and retry within the same timeout. On POSIX a PermissionError is a real error.
                if isinstance(e, PermissionError) and os.name != "nt":
                    raise
                if time.monotonic() - t0 > self.timeout:
                    raise LedgerError(f"ledger is locked by another writer ({self.path}); not overriding the lock")
                time.sleep(0.01)

    def __exit__(self, *exc):
        os.close(self.fd)
        os.unlink(self.path)                        # only the lock file this writer created


class Ledger:
    def __init__(self, path: Path | None = None, *, anchors: "AnchorStore | None" = None, recover: bool = False):
        self._path = Path(path) if path else None
        self._anchors = anchors
        self._entries: list[Entry] = []
        self._pending = False
        if self._path is not None:
            if anchors is None:
                raise LedgerError("a file-backed ledger requires an AnchorStore (anchors are not optional)")
            if anchors.path.resolve().parent == self._path.resolve().parent:
                raise LedgerError("the anchor store must live outside the ledger's folder")
        if self._path is not None:
            # Load under the writer lock, so another process's append is never seen half-done
            # (an INTENT already recorded, its entry not yet written).
            with _FileLock(self._path.with_name(self._path.name + ".lock")):
                if self._path.exists():
                    self._load(recover=recover)
                else:
                    recs = self._anchors.records()
                    dangling_first = len(recs) >= 1 and all(r["type"] == "intent" and r["n"] == 1 for r in recs)
                    if recs and not dangling_first:
                        raise LedgerError("anchors exist but the ledger file is missing: history was removed")

    # ---- file handling ---------------------------------------------------------------------
    def _parse(self, data: bytes) -> tuple[list[Entry], int, bool]:
        """Returns (entries, end_of_last_complete_entry, corrupt).
        Every newline-terminated line must be a valid entry; a malformed one anywhere is
        CORRUPTION (corrupt=True). Only bytes after the last newline (a write that never finished
        its line) count as a partial tail."""
        entries, good, pos = [], 0, 0
        while True:
            nl = data.find(b"\n", pos)
            if nl == -1:
                break
            try:
                d = json.loads(data[pos:nl])
                entries.append(Entry(d["seq"], d["kind"], canonical(d["payload"]), d["prev"], d["digest"]))
            except (ValueError, KeyError, TypeError):
                return entries, good, True
            pos = good = nl + 1
        return entries, good, False

    def _load(self, recover: bool):
        data = self._path.read_bytes()
        entries, good, corrupt = self._parse(data)
        if corrupt:
            raise LedgerError("malformed entry INSIDE the ledger (not an unfinished last write); "
                              "automatic recovery is refused; every byte is kept for explicit handling")
        if good != len(data):
            if not recover:
                raise LedgerError("partial entry at the end of the ledger (unfinished write); load with recover=True to quarantine it")
            n = 1
            while self._path.with_name(f"{self._path.name}.partial-{n}").exists():
                n += 1
            self._path.with_name(f"{self._path.name}.partial-{n}").write_bytes(data[good:])
            with open(self._path, "r+b") as fh:
                fh.truncate(good)
                fh.flush(); os.fsync(fh.fileno())
        self._entries = entries
        self.verify()
        if self._anchors is not None:
            anchors = self._anchors.read()
            self.verify(anchors=anchors)
            last = anchors[-1][0] if anchors else 0
            gap = len(self._entries) - last
            self._pending = False
            if gap == 1:
                lr = self._anchors.last_record()
                if not (lr and lr["type"] == "intent" and lr["n"] == len(self._entries)
                        and lr["head"] == self._entries[-1].digest):
                    raise LedgerError("last entry is not anchored and has no matching declared intent: "
                                      "anchors missing, emptied or truncated")
                self._pending = True              # crash between entry and commit: completed on next write
            elif gap != 0:
                raise LedgerError(f"anchor store does not cover the ledger ({last} committed of "
                                  f"{len(self._entries)} entries): anchors missing, emptied or truncated")

    # ---- API -------------------------------------------------------------------------------
    def append_with(self, kind: str, build) -> Entry:
        """Transactional append: under the write lock, re-read the file, call build(entries) to
        validate and produce the payload from the FRESH history (it may raise to abort), then
        append. Nothing is written if build raises."""
        if self._path is None:
            return self._append_mem(kind, canonical(build(tuple(self._entries))))
        with _FileLock(self._path.with_name(self._path.name + ".lock")):
            if self._path.exists():
                self._load(recover=False)
            payload = build(tuple(self._entries))
            return self._write(kind, canonical(payload))

    def _write(self, kind: str, pb: bytes) -> Entry:
        if self._pending:                          # complete a crash-interrupted commit first
            self._anchors.record_commit(len(self._entries), self._entries[-1].digest)
            self._pending = False
        e = self._make(kind, pb)
        self._anchors.record_intent(e.seq + 1, e.digest)          # 1. intent
        line = canonical(e.as_record()) + b"\n"
        fd = os.open(self._path, os.O_WRONLY | os.O_APPEND | os.O_CREAT)
        try:
            if os.write(fd, line) != len(line):
                raise LedgerError("short write")
            os.fsync(fd)                                          # 2. entry
        finally:
            os.close(fd)
        self._entries.append(e)
        self._commit_anchor(e)                                    # 3. commit
        return e

    def _commit_anchor(self, e: Entry) -> None:
        self._anchors.record_commit(e.seq + 1, e.digest)

    def append(self, kind: str, payload: dict, *, unique_key: str | None = None) -> Entry:
        """Append an entry. If unique_key is given, refuse when an entry of the same kind already
        has the same value for that key. The check and the append happen under the same lock,
        after re-reading the file, so the check holds across processes and restarts."""
        if not kind or not isinstance(payload, dict):
            raise LedgerError("kind and dict payload are required")
        pb = canonical(payload)

        def dup():
            if unique_key is None:
                return False
            v = payload.get(unique_key)
            return any(e.kind == kind and e.payload.get(unique_key) == v for e in self._entries)

        if self._path is None:
            if dup():
                raise DuplicateError(f"{kind}.{unique_key} already recorded")
            return self._append_mem(kind, pb)
        with _FileLock(self._path.with_name(self._path.name + ".lock")):
            if self._path.exists():
                self._load(recover=False)            # pick up entries from other writers
            if dup():
                raise DuplicateError(f"{kind}.{unique_key} already recorded")
            return self._write(kind, pb)

    def _make(self, kind: str, pb: bytes) -> Entry:
        seq = len(self._entries)
        prev = self._entries[-1].digest if self._entries else GENESIS
        return Entry(seq, kind, pb, prev, _digest(seq, kind, pb, prev))

    def _append_mem(self, kind, pb):
        e = self._make(kind, pb)
        self._entries.append(e)
        return e

    def anchor(self) -> tuple[int, str]:
        """(length, head digest): store this OUTSIDE the ledger file."""
        return len(self._entries), self.head

    def verify(self, anchors: list[tuple[int, str]] | None = None) -> None:
        prev = GENESIS
        for i, e in enumerate(self._entries):
            if e.seq != i or e.prev != prev or e.digest != _digest(e.seq, e.kind, e._payload, e.prev):
                raise LedgerError(f"ledger integrity broken at entry {i}")
            prev = e.digest
        for n, h in anchors or []:
            if n > len(self._entries) or (n > 0 and self._entries[n - 1].digest != h) or (n == 0 and h != GENESIS):
                raise LedgerError(f"anchor ({n}, {h[:12]}) does not match: history was rewritten or truncated")

    def __iter__(self) -> Iterator[Entry]:
        return iter(tuple(self._entries))

    def __len__(self) -> int:
        return len(self._entries)

    def __bool__(self) -> bool:
        # An empty ledger is still a ledger: never let "ledger or Ledger()" silently swap a
        # file-backed ledger for an in-memory one (a trap found while testing WP8-02 #2).
        return True

    @property
    def head(self) -> str:
        return self._entries[-1].digest if self._entries else GENESIS
