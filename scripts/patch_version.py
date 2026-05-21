#!/usr/bin/env python3
"""
patch_version.py — Kentstrapper OrcaSlicer
Injects the Kentstrapper build version string into CMakeLists.txt so that
the About dialog shows our version (e.g. "V2.3.2-Kentstrapper-abc1234")
instead of the upstream git SHA.
"""
import sys, os, re


def patch_cmake(path: str, version: str) -> bool:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # Pattern 1 — existing set(SLIC3R_BUILD_ID ...)
    patched, n = re.subn(
        r'set\s*\(\s*SLIC3R_BUILD_ID\s+[^\)]+\)',
        f'set(SLIC3R_BUILD_ID "{version}")',
        content,
    )
    if n:
        content = patched
        print(f"[DONE] Replaced set(SLIC3R_BUILD_ID ...) → {version}")

    # Pattern 2 — string(CONCAT SLIC3R_BUILD_ID ...)
    if not n:
        patched, n = re.subn(
            r'string\s*\(\s*CONCAT\s+SLIC3R_BUILD_ID[^\)]+\)',
            f'set(SLIC3R_BUILD_ID "{version}")',
            content,
        )
        if n:
            content = patched
            print(f"[DONE] Replaced string(CONCAT SLIC3R_BUILD_ID ...) → {version}")

    # Pattern 3 — execute_process that fetches a git hash into SLIC3R_BUILD_HASH
    #   Replace the whole block and just set the variable directly.
    if not n:
        patched, n = re.subn(
            r'execute_process\s*\([^)]*SLIC3R_BUILD_HASH[^)]*\)',
            f'set(SLIC3R_BUILD_HASH "{version}")',
            content,
            flags=re.DOTALL,
        )
        if n:
            content = patched
            print(f"[DONE] Replaced execute_process(SLIC3R_BUILD_HASH) → {version}")

    # Pattern 4 — any execute_process that fetches git log/rev-parse into a var
    #   used later for a build-id.  We broaden the search a bit.
    if not n:
        patched, n = re.subn(
            r'execute_process\s*\([^)]*git\s+log[^)]*OUTPUT_VARIABLE\s+(\w+)[^)]*\)',
            lambda m: f'set({m.group(1)} "{version}")',
            content,
            flags=re.DOTALL,
        )
        if n:
            content = patched
            print(f"[DONE] Replaced execute_process(git log ...) → {version}")

    if not n:
        patched, n = re.subn(
            r'execute_process\s*\([^)]*git\s+rev-parse[^)]*OUTPUT_VARIABLE\s+(\w+)[^)]*\)',
            lambda m: f'set({m.group(1)} "{version}")',
            content,
            flags=re.DOTALL,
        )
        if n:
            content = patched
            print(f"[DONE] Replaced execute_process(git rev-parse ...) → {version}")

    # Last resort — inject after the first project() declaration
    if not n:
        patched, n = re.subn(
            r'(project\s*\([Oo]rca[Ss]licer[^\)]*\))',
            rf'\1\nset(SLIC3R_BUILD_ID "{version}")',
            content,
        )
        if n:
            content = patched
            print(f"[DONE] Injected set(SLIC3R_BUILD_ID ...) after project() → {version}")
        else:
            print("[WARN] patch_version.py: could not find any injection point in CMakeLists.txt")
            return False

    if content != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    return True


def main():
    if len(sys.argv) < 3:
        print("Usage: patch_version.py <orcaslicer-source-root> <version-string>")
        sys.exit(1)

    root = sys.argv[1]
    version = sys.argv[2]

    if not version:
        print("[WARN] Empty version string — skipping version injection")
        return

    cmake_path = os.path.join(root, "CMakeLists.txt")
    if not os.path.exists(cmake_path):
        print(f"[WARN] CMakeLists.txt not found at: {cmake_path} — skipping")
        return

    ok = patch_cmake(cmake_path, version)
    if not ok:
        print("[WARN] Version injection had no effect — About dialog will show upstream build ID")
        # Non-fatal: don't break the build over a cosmetic change
    else:
        print(f"\nVersion injection complete: {version}")


if __name__ == "__main__":
    main()
