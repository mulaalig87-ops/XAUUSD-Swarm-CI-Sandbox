"""Build the RIP-3 review bundle from ONE commit, with the complete import closure of the tests and scripts it ships.
Usage: python scripts/rip3_bundle.py COMMIT OUT_ZIP [EXTRA_PATH ...]

The closure is computed from the files AT THAT COMMIT (git show), by parsing every shipped Python file with ast and
following each import that resolves to a file of the repository (package xauusd_swarm under src/, sibling scripts
under scripts/, test helpers under tests/), until no new file appears. Third-party imports (numpy, pytest, ...) are
listed in the manifest with the pinned lock file env/test.lock.txt, which is shipped. Data files read by the tests
are added explicitly (ROOTS_DATA). MANIFEST.json carries the commit, the clean-tree flag and SHA-256 per file."""
import ast
import hashlib
import json
import subprocess
import sys
import zipfile

ROOTS_PY = ["tests/test_rip3.py", "tests/conftest.py", "scripts/rip3_run.py", "scripts/rip3_rescore.py",
            "scripts/rip3_partial_repro.py", "scripts/rip3_w2_truth_verify.py", "scripts/rip3_w2_truth_verify_v3.py",
            "scripts/rip3_a6_verify.py", "scripts/rip3_a6_verify_hp.py", "scripts/rip3_build_validate.py",
            "scripts/rip3_dcr01_study.py", "scripts/rip3_dcr01_study_v2.py", "scripts/rip3_b1_case10_hp.py",
            "scripts/rip3_bundle.py", "src/xauusd_swarm/__init__.py"]
ROOTS_DATA = ["pyproject.toml", "env/test.lock.txt", "docs/research/RIP3_DESIGN.md",
              "docs/research/RIP3_DESIGN_v0.5_DCR01_DRAFT.md", "docs/research/RIP3_DESIGN_v0.5r2_DCR01_DRAFT.md", "docs/research/RIP3_BUILD_NOTES.md",
              "docs/research/RIP3_IC_REPORT.md", "docs/research/RIP2_UVOL_DERIVATION.md", "docs/FL.md",
              "docs/DECISIONS.md", "docs/audit/RIP_register.md", "docs/RELEASES.md", "docs/HANDOFF.md",
              "docs/results/rip2/results.json"]


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, check=True).stdout


def resolve(mod, level, frm_file, files):
    """Repository files that an import refers to (empty for third-party modules)."""
    out = []
    cands = []
    if level:                                                       # relative import inside src/xauusd_swarm
        base = frm_file.rsplit("/", 1)[0]
        cands.append(f"{base}/{mod.replace('.', '/')}.py" if mod else None)
    else:
        top = mod.split(".")[0]
        if top == "xauusd_swarm":
            rest = mod.split(".")[1:]
            cands.append("src/xauusd_swarm/" + ("/".join(rest) + ".py" if rest else "__init__.py"))
        cands += [f"scripts/{mod}.py", f"tests/{mod.replace('.', '/')}.py"]
    for c in cands:
        if c and c in files:
            out.append(c)
    return out


def closure(commit):
    files = set(git("ls-tree", "-r", "--name-only", commit).decode().split())
    todo, seen, third = [f for f in ROOTS_PY if f in files], set(), set()
    while todo:
        f = todo.pop()
        if f in seen:
            continue
        seen.add(f)
        tree = ast.parse(git("show", f"{commit}:{f}").decode("utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    r = resolve(n.name, 0, f, files)
                    todo += r
                    if not r:
                        third.add(n.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                r = resolve(mod, node.level, f, files)
                for n in node.names:                                # from . import x / from xauusd_swarm import x
                    sub = f"{mod}.{n.name}" if mod else n.name
                    r += resolve(sub, node.level, f, files)
                todo += r
                if not r and not node.level:
                    third.add(mod.split(".")[0])
    return sorted(seen), sorted(third - {"xauusd_swarm"}), files


def main(commit, out, extra):
    commit = git("rev-parse", commit).decode().strip()
    py, third, files = closure(commit)
    data = [f for f in ROOTS_DATA if f in files] + sorted(f for f in files if f.startswith("docs/results/rip3_build/"))
    data += [e for e in extra if e in files]
    allf = sorted(set(py) | set(data))
    clean = git("status", "--porcelain").decode().strip() == ""
    man = {"commit": commit, "git_status_clean_at_extraction": clean, "extracted_with": "git show <commit>:<path>",
           "python_import_closure": py, "third_party_imports": third,
           "third_party_pins": "env/test.lock.txt (shipped); scipy/sklearn are optional (tests skip without them)",
           "files": {}}
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in allf:
            b = git("show", f"{commit}:{f}")
            man["files"][f] = hashlib.sha256(b).hexdigest()
            z.writestr(f, b)
        z.writestr("MANIFEST.json", json.dumps(man, indent=1))
    print(out, len(allf), "files;", len(py), "python files in the closure; third-party:", third, "; clean:", clean)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
