#!/usr/bin/env python3
"""
patch_mixed_support.py  —  Kentstrapper OrcaSlicer
Patches the upstream v2.3.2 source to enable per-region mixed support types
(normal/grid in some painted areas, tree/organic in others on the same object).

Changes applied:
  1. TreeSupport.cpp  — detect_overhangs() also collects ORGANIC_ENFORCER regions
     so they grow tree-support columns instead of falling through to normal support.
  2. PrintObject.cpp  — _generate_support_material() gains mixed-mode logic:
     when an object has ORGANIC_ENFORCER painted regions, both the normal-support
     generator (for overhangs + GRID_ENFORCER areas) and the tree-support generator
     (for ORGANIC_ENFORCER areas only, non-auto mode) are run together.
"""

import sys
import os
import re


def patch_file_exact(path: str, search: str, replacement: str, description: str) -> bool:
    """Try exact string match."""
    if not os.path.exists(path):
        print(f"[SKIP] {description} — file not found: {path}")
        return False

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if replacement in content:
        print(f"[OK]   {description} — already patched")
        return True

    if search not in content:
        return False

    patched = content.replace(search, replacement, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(patched)
    print(f"[DONE] {description} (exact match)")
    return True


def patch_file_regex(path: str, pattern: str, replacement: str, description: str) -> bool:
    """Try regex match (handles minor whitespace/formatting differences)."""
    if not os.path.exists(path):
        return False

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Already patched?
    if "Kentstrapper" in content and re.search(re.escape(replacement[:80]), content):
        print(f"[OK]   {description} — already patched")
        return True

    m = re.search(pattern, content, re.DOTALL)
    if not m:
        return False

    patched = content[:m.start()] + replacement + content[m.end():]
    with open(path, "w", encoding="utf-8") as f:
        f.write(patched)
    print(f"[DONE] {description} (regex match)")
    return True


def patch_file(path, searches, replacement, description):
    """Try each search string in order; fall back to regex patterns."""
    for search in searches:
        if patch_file_exact(path, search, replacement, description):
            return True

    # Regex fallbacks follow each call site
    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: patch_mixed_support.py <orcaslicer-source-root>")
        sys.exit(1)

    root = sys.argv[1]
    errors = 0

    # ── Patch 1: TreeSupport.cpp ──────────────────────────────────────────────
    # In detect_overhangs(), after collecting ENFORCER triangles, also collect
    # ORGANIC_ENFORCER triangles so they produce tree-support branches.
    tree_support_cpp = os.path.join(root, "src", "libslic3r", "Support", "TreeSupport.cpp")

    # Exact candidates: v2.3.2 may have the ENFORCER call with or without the
    # m_vertical_enforcer_points argument (added in BBS patches).
    search_tree_variants = [
        # With vertical enforcer points (BBS variant)
        (
            "    m_object->project_and_append_custom_facets(false, EnforcerBlockerType::ENFORCER, enforcers, &m_vertical_enforcer_points);\n"
            "    m_object->project_and_append_custom_facets(false, EnforcerBlockerType::BLOCKER, blockers);"
        ),
        # Without vertical enforcer points (upstream variant)
        (
            "    m_object->project_and_append_custom_facets(false, EnforcerBlockerType::ENFORCER, enforcers);\n"
            "    m_object->project_and_append_custom_facets(false, EnforcerBlockerType::BLOCKER, blockers);"
        ),
    ]

    replace_tree_bbs = (
        "    m_object->project_and_append_custom_facets(false, EnforcerBlockerType::ENFORCER, enforcers, &m_vertical_enforcer_points);\n"
        "    // Kentstrapper: also collect ORGANIC_ENFORCER painted regions for per-region mixed support.\n"
        "    m_object->project_and_append_custom_facets(false, EnforcerBlockerType::ORGANIC_ENFORCER, enforcers);\n"
        "    m_object->project_and_append_custom_facets(false, EnforcerBlockerType::BLOCKER, blockers);"
    )
    replace_tree_upstream = (
        "    m_object->project_and_append_custom_facets(false, EnforcerBlockerType::ENFORCER, enforcers);\n"
        "    // Kentstrapper: also collect ORGANIC_ENFORCER painted regions for per-region mixed support.\n"
        "    m_object->project_and_append_custom_facets(false, EnforcerBlockerType::ORGANIC_ENFORCER, enforcers);\n"
        "    m_object->project_and_append_custom_facets(false, EnforcerBlockerType::BLOCKER, blockers);"
    )

    # Try exact matches first
    tree_ok = False
    for search, replacement in [
        (search_tree_variants[0], replace_tree_bbs),
        (search_tree_variants[1], replace_tree_upstream),
    ]:
        if patch_file_exact(tree_support_cpp, search, replacement,
                            "TreeSupport.cpp: collect ORGANIC_ENFORCER in detect_overhangs"):
            tree_ok = True
            break

    if not tree_ok:
        # Regex fallback: match any project_and_append_custom_facets(ENFORCER) followed by BLOCKER
        tree_regex = (
            r"([ \t]*m_object->project_and_append_custom_facets\("
            r"false,\s*EnforcerBlockerType::ENFORCER,[^;]+;\n)"
            r"([ \t]*m_object->project_and_append_custom_facets\("
            r"false,\s*EnforcerBlockerType::BLOCKER,[^;]+;)"
        )
        tree_regex_replace = (
            r"\1"
            "    // Kentstrapper: also collect ORGANIC_ENFORCER painted regions for per-region mixed support.\n"
            "    m_object->project_and_append_custom_facets(false, EnforcerBlockerType::ORGANIC_ENFORCER, enforcers);\n"
            r"\2"
        )
        if patch_file_regex(tree_support_cpp, tree_regex, tree_regex_replace,
                            "TreeSupport.cpp: collect ORGANIC_ENFORCER (regex)"):
            tree_ok = True

    if not tree_ok:
        print(f"[FAIL] TreeSupport.cpp: could not locate ENFORCER+BLOCKER call site")
        errors += 1

    # ── Patch 2: PrintObject.cpp ──────────────────────────────────────────────
    print_object_cpp = os.path.join(root, "src", "libslic3r", "PrintObject.cpp")

    # Exact candidates: function body may vary slightly in whitespace
    search_print_variants = [
        # Standard form
        (
            "void PrintObject::_generate_support_material()\n"
            "{\n"
            "    if (is_tree(m_config.support_type.value)) {\n"
            "        TreeSupport tree_support(*this, m_slicing_params);\n"
            "        tree_support.throw_on_cancel = [this]() { this->throw_if_canceled(); };\n"
            "        tree_support.generate();\n"
            "    }\n"
            "    else {\n"
            "        PrintObjectSupportMaterial support_material(this, m_slicing_params);\n"
            "        support_material.generate(*this);\n"
            "    }\n"
            "}"
        ),
        # Variant: } else { (no newline before else)
        (
            "void PrintObject::_generate_support_material()\n"
            "{\n"
            "    if (is_tree(m_config.support_type.value)) {\n"
            "        TreeSupport tree_support(*this, m_slicing_params);\n"
            "        tree_support.throw_on_cancel = [this]() { this->throw_if_canceled(); };\n"
            "        tree_support.generate();\n"
            "    } else {\n"
            "        PrintObjectSupportMaterial support_material(this, m_slicing_params);\n"
            "        support_material.generate(*this);\n"
            "    }\n"
            "}"
        ),
    ]

    replace_print = (
        "// Kentstrapper: helper — does the model have any facets painted with `type`?\n"
        "static bool has_painted_enforcer_type(const PrintObject &obj, EnforcerBlockerType type)\n"
        "{\n"
        "    for (const ModelVolume *mv : obj.model_object()->volumes)\n"
        "        if (mv->is_model_part() && mv->supported_facets.has_facets(*mv, type))\n"
        "            return true;\n"
        "    return false;\n"
        "}\n"
        "\n"
        "void PrintObject::_generate_support_material()\n"
        "{\n"
        "    const bool want_tree   = is_tree(m_config.support_type.value);\n"
        "    const bool has_organic = has_painted_enforcer_type(*this, EnforcerBlockerType::ORGANIC_ENFORCER);\n"
        "    const bool has_grid    = has_painted_enforcer_type(*this, EnforcerBlockerType::GRID_ENFORCER);\n"
        "\n"
        "    if (!want_tree && has_organic) {\n"
        "        // Mixed mode A: global type is normal but user painted ORGANIC_ENFORCER regions.\n"
        "        // Step 1 — normal support covers all overhangs + GRID_ENFORCER areas.\n"
        "        {\n"
        "            PrintObjectSupportMaterial support_material(this, m_slicing_params);\n"
        "            support_material.generate(*this);\n"
        "        }\n"
        "        // Step 2 — tree support in non-auto mode covers only ORGANIC_ENFORCER areas.\n"
        "        {\n"
        "            auto saved_type = m_config.support_type.value;\n"
        "            m_config.support_type.value = stTree;  // enforcer-only, no auto-detect\n"
        "            TreeSupport tree_support(*this, m_slicing_params);\n"
        "            tree_support.throw_on_cancel = [this]() { this->throw_if_canceled(); };\n"
        "            tree_support.generate();\n"
        "            m_config.support_type.value = saved_type;\n"
        "        }\n"
        "    } else if (want_tree && has_grid) {\n"
        "        // Mixed mode B: global type is tree but user painted GRID_ENFORCER regions.\n"
        "        // Step 1 — tree support covers all overhangs + ORGANIC_ENFORCER areas.\n"
        "        {\n"
        "            TreeSupport tree_support(*this, m_slicing_params);\n"
        "            tree_support.throw_on_cancel = [this]() { this->throw_if_canceled(); };\n"
        "            tree_support.generate();\n"
        "        }\n"
        "        // Step 2 — normal support in enforcer-only mode covers GRID_ENFORCER areas.\n"
        "        {\n"
        "            auto saved_type = m_config.support_type.value;\n"
        "            m_config.support_type.value = stNormal;  // enforcer-only, no auto-detect\n"
        "            PrintObjectSupportMaterial support_material(this, m_slicing_params);\n"
        "            support_material.generate(*this);\n"
        "            m_config.support_type.value = saved_type;\n"
        "        }\n"
        "    } else if (want_tree) {\n"
        "        TreeSupport tree_support(*this, m_slicing_params);\n"
        "        tree_support.throw_on_cancel = [this]() { this->throw_if_canceled(); };\n"
        "        tree_support.generate();\n"
        "    } else {\n"
        "        PrintObjectSupportMaterial support_material(this, m_slicing_params);\n"
        "        support_material.generate(*this);\n"
        "    }\n"
        "}"
    )

    print_ok = False
    for search in search_print_variants:
        if patch_file_exact(print_object_cpp, search, replace_print,
                            "PrintObject.cpp: mixed support in _generate_support_material"):
            print_ok = True
            break

    if not print_ok:
        # Regex fallback: match the entire _generate_support_material function body
        print_regex = (
            r"void\s+PrintObject::_generate_support_material\(\)\s*\{"
            r"\s*if\s*\(\s*is_tree\s*\(\s*m_config\.support_type\.value\s*\)\s*\)\s*\{"
            r"\s*TreeSupport\s+tree_support\s*\(\s*\*this\s*,\s*m_slicing_params\s*\)\s*;"
            r"\s*tree_support\.throw_on_cancel\s*=[^;]+;\s*"
            r"tree_support\.generate\(\)\s*;"
            r"\s*\}\s*(else\s*\{|else\s+\{)\s*"
            r"PrintObjectSupportMaterial\s+support_material\s*\(\s*this\s*,\s*m_slicing_params\s*\)\s*;"
            r"\s*support_material\.generate\s*\(\s*\*this\s*\)\s*;"
            r"\s*\}\s*\}"
        )
        if patch_file_regex(print_object_cpp, print_regex, replace_print,
                            "PrintObject.cpp: mixed support (regex)"):
            print_ok = True

    if not print_ok:
        print(f"[FAIL] PrintObject.cpp: could not locate _generate_support_material() function body")
        errors += 1

    if errors:
        print(f"\n[ERROR] {errors} mixed-support patch(es) failed — BUILD WILL FAIL.")
        sys.exit(1)
    else:
        print("\nAll mixed-support patches applied successfully.")


if __name__ == "__main__":
    main()
