"""
Kentstrapper color replacement script for OrcaSlicer.
Replaces all teal/green accent colors (#009688 family) with Kentstrapper orange (#FF8800).
Run from the repo root: python scripts/patch_colors.py
"""
import os
import sys

# All known variants of the OrcaSlicer teal/green accent color
REPLACEMENTS = [
    # Primary teal hex variants
    ("#009688", "#FF8800"),
    ("#009688".upper(), "#FF8800"),
    ("009688",  "FF8800"),
    ("0x009688", "0xFF8800"),
    ("0X009688", "0XFF8800"),

    # Hover teal variants
    ("#26A69A", "#CC6E00"),
    ("#26a69a", "#cc6e00"),
    ("26A69A",  "CC6E00"),
    ("26a69a",  "cc6e00"),
    ("0x26A69A", "0xCC6E00"),
    ("0x26a69a", "0xcc6e00"),

    # Light teal variants
    ("#00675b", "#CC6E00"),
    ("#00675B", "#CC6E00"),
    ("00675b",  "CC6E00"),
    ("00675B",  "CC6E00"),

    # Other teal shades
    ("0x52c7b8", "0xFFAA33"),
    ("0x52C7B8", "0xFFAA33"),
    ("52c7b8",   "FFAA33"),
    ("52C7B8",   "FFAA33"),
    ("#52c7b8",  "#FFAA33"),
    ("#52C7B8",  "#FFAA33"),

    ("22bfb0", "FF9933"),
    ("22BFB0", "FF9933"),
    ("00FFD4", "FFAA44"),

    # Light teal tints (used in backgrounds/highlights)
    ("#BFE1DE", "#FFE0B2"),
    ("#bfe1de", "#ffe0b2"),
    ("BFE1DE",  "FFE0B2"),
    ("bfe1de",  "ffe0b2"),

    ("#E5F0EE", "#FFF3E0"),
    ("#e5f0ee", "#fff3e0"),
    ("E5F0EE",  "FFF3E0"),
    ("e5f0ee",  "fff3e0"),

    ("#EDFAF2", "#FFF8EE"),
    ("#edfaf2", "#fff8ee"),
    ("EDFAF2",  "FFF8EE"),
    ("edfaf2",  "fff8ee"),

    ("#EBF9F0", "#FFF8EE"),
    ("#ebf9f0", "#fff8ee"),
    ("EBF9F0",  "FFF8EE"),
    ("ebf9f0",  "fff8ee"),

    ("#D7E8DE", "#FFE8CC"),
    ("#d7e8de", "#ffe8cc"),
    ("D7E8DE",  "FFE8CC"),
    ("d7e8de",  "ffe8cc"),

    ("#DBFDD5", "#FFE8CC"),
    ("DBFDD5",  "FFE8CC"),

    # RGB decimal format: wxColour(0, 150, 136)
    ("0, 150, 136",  "255, 136, 0"),
    ("0,150,136",    "255,136,0"),
    ("0,150, 136",   "255,136, 0"),     # mixed spacing variant found in Notebook.cpp
    ("0, 150, 136,", "255, 136, 0,"),   # with trailing comma

    # Additional teal/green shades found in MainFrame.cpp, AmsWidgets, etc.
    ("0, 137, 123",  "200, 110, 0"),
    ("0,137,123",    "200,110,0"),
    ("48, 221, 112", "255, 170, 0"),
    ("48,221,112",   "255,170,0"),
    ("#00897B", "#CC6E00"),
    ("#00897b", "#cc6e00"),
    ("00897B",  "CC6E00"),
    ("00897b",  "cc6e00"),
    ("0x00897B", "0xCC6E00"),
    ("0x00897b", "0xcc6e00"),
]

EXTENSIONS = {'.cpp', '.hpp', '.h', '.hxx', '.cxx', '.c',
              '.svg', '.xml', '.json', '.inc', '.txt', '.cmake'}


def patch_directory(root_dir):
    root_dir = os.path.abspath(root_dir)
    if not os.path.isdir(root_dir):
        print(f"  SKIP (not found): {root_dir}")
        return 0

    total = 0
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip .git and build directories
        dirnames[:] = [d for d in dirnames if d not in {'.git', 'build', '__pycache__'}]

        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in EXTENSIONS:
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    original = f.read()
                content = original
                for old, new in REPLACEMENTS:
                    content = content.replace(old, new)
                if content != original:
                    with open(fpath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    total += 1
                    rel = os.path.relpath(fpath, root_dir)
                    print(f"  Patched: {rel}")
            except Exception as exc:
                print(f"  SKIP {fpath}: {exc}", file=sys.stderr)
    return total


if __name__ == '__main__':
    base = sys.argv[1] if len(sys.argv) > 1 else 'orcaslicer-source'
    print(f"Patching colors in: {os.path.abspath(base)}")

    total = 0
    for sub in ('src', 'resources'):
        d = os.path.join(base, sub)
        print(f"\n--- {d} ---")
        n = patch_directory(d)
        total += n
        print(f"  ({n} files patched)")

    print(f"\nTotal files patched: {total}")
    if total == 0:
        print("WARNING: 0 files patched — check that orcaslicer-source/ exists")
        sys.exit(1)
