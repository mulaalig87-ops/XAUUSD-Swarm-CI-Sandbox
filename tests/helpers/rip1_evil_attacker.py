"""Adversarial attacker for tests/test_rip1.py (review R4). Runs inside the RIP-1 sandbox exactly like the real
attacker and ACTUALLY tries to break isolation. Each attempt records "denied" or "ALLOWED: ...".
Usage (inside the sandbox): python -I rip1_evil_attacker.py CODE IN OUT VIEW"""
import json
import os
import sys
import time

CODE, IN, OUT, VIEW = sys.argv[1:5]
T = json.load(open(os.path.join(IN, "input.json")))["targets"]
R = {}


def attempt(name, fn):
    try:
        r = fn()
        R[name] = f"ALLOWED: {r!r}"[:300]
    except Exception as e:                                  # noqa: BLE001 — any refusal counts as denied
        R[name] = "denied" if isinstance(e, (OSError, ImportError, PermissionError)) else f"error {type(e).__name__}"


data = os.path.join(IN, T["data_name"])
orig = open(data, "rb").read()
# 1. modify inputs, then try to restore them
attempt("input_append", lambda: open(data, "ab").write(b"x"))
attempt("input_truncate", lambda: open(data, "wb").write(b""))
attempt("input_restore", lambda: open(data, "wb").write(orig))
attempt("input_chmod", lambda: os.chmod(data, 0o666))
attempt("input_unlink", lambda: os.unlink(data))
attempt("input_rename", lambda: os.rename(data, data + ".x"))
attempt("input_new_file", lambda: open(os.path.join(IN, "new"), "w").write("x"))
attempt("code_write", lambda: open(os.path.join(CODE, "xauusd_swarm", "reid.py"), "a").write("#"))
# 2. other runs
attempt("prior_run_read", lambda: os.listdir(T["prior_run"]) if T["prior_run"] else (_ for _ in ()).throw(OSError()))
attempt("prior_run_output_read", lambda: open(os.path.join(T["prior_run"], "out", "predictions.json")).read(10)
        if T["prior_run"] else (_ for _ in ()).throw(OSError()))
attempt("future_run_create", lambda: os.makedirs(T["future_run"]))
attempt("runs_dir_write", lambda: open(os.path.join(T["runs_dir"], "planted"), "w").write("x"))
# 3. secrets
attempt("vault_read", lambda: open(T["vault"], "rb").read(4))
attempt("custody_list", lambda: os.listdir(T["custody"]))
attempt("key_file_read", lambda: open(T["key_file"]).read(4))
attempt("root_home_list", lambda: os.listdir("/root"))
attempt("repo_list", lambda: os.listdir("/home"))
# 4. writes outside OUT
for p in ("/tmp", "/var/tmp", "/dev/shm", "/run/lock", "/", "/usr", "/etc", T["base"], CODE, IN):
    attempt(f"write:{p}", lambda p=p: open(os.path.join(p, "rip1_evil_marker"), "w").write("x"))
# 5. links and path escape out of OUT
attempt("symlink_to_vault", lambda: os.symlink(T["vault"], os.path.join(OUT, "l_vault")))
attempt("read_via_symlink", lambda: open(os.path.join(OUT, "l_vault"), "rb").read(4))
attempt("hardlink_input", lambda: os.link(data, os.path.join(OUT, "h_input")))
attempt("escape_dotdot_in", lambda: open(os.path.join(OUT, "..", "in", "x"), "w").write("x"))
attempt("escape_dotdot_base", lambda: open(os.path.join(OUT, "..", "..", "x"), "w").write("x"))
# 6. self-signing: the system's signing module is not in the code copy; a home-made key signs nothing valid
attempt("import_system_identity", lambda: __import__("xauusd_swarm.identity"))
sig = None
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    sig = Ed25519PrivateKey.generate().sign(b"predictions").hex()
except Exception:                                           # noqa: BLE001
    pass
# 7. a background process that tries to change the output after the run ended
pid = os.fork()
if pid == 0:
    os.setsid()
    time.sleep(3)
    try:
        open(os.path.join(OUT, "predictions.json"), "w").write("TAMPERED")
    finally:
        os._exit(0)
with open(os.path.join(OUT, "predictions.json"), "w") as fh:
    json.dump({"attempts": R, "signature_hex": sig, "uid": os.getuid()}, fh)
