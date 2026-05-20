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


def patch_file(path: str, search: str, replacement: str, description: str) -> bool:
    if not os.path.exists(path):
        print(f"[SKIP] {description} — file not found: {path}")
        return False

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if search not in content:
        if replacement in content:
            print(f"[OK]   {description} — already patched")
            return True
        print(f"[FAIL] {description} — search string not found in {path}")
        return False

    patched = content.replace(search, replacement, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(patched)
    print(f"[DONE] {description}")
    return True


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
    search_tree = (
        "    m_object->project_and_append_custom_facets(false, EnforcerBlockerType::ENFORCER, enforcers, &m_vertical_enforcer_points);\n"
        "    m_object->project_and_append_custom_facets(false, EnforcerBlockerType::BLOCKER, blockers);"
    )
    replace_tree = (
        "    m_object->project_and_append_custom_facets(false, EnforcerBlockerType::ENFORCER, enforcers, &m_vertical_enforcer_points);\n"
        "    // Kentstrapper: also collect ORGANIC_ENFORCER painted regions for per-region mixed support.\n"
        "    m_object->project_and_append_custom_facets(false, EnforcerBlockerType::ORGANIC_ENFORCER, enforcers);\n"
        "    m_object->project_and_append_custom_facets(false, EnforcerBlockerType::BLOCKER, blockers);"
    )
    if not patch_file(tree_support_cpp, search_tree, replace_tree,
                      "TreeSupport.cpp: collect ORGANIC_ENFORCER in detect_overhangs"):
        errors += 1

    # ── Patch 2: PrintObject.cpp ──────────────────────────────────────────────
    # Replace _generate_support_material() with a mixed-mode version that:
    #   • Runs normal support for all overhangs + GRID_ENFORCER areas.
    #   • Additionally runs tree support in non-auto mode for ORGANIC_ENFORCER areas.
    print_object_cpp = os.path.join(root, "src", "libslic3r", "PrintObject.cpp")
    search_print = (
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
    )
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
    if not patch_file(print_object_cpp, search_print, replace_print,
                      "PrintObject.cpp: mixed support in _generate_support_material"):
        errors += 1

    if errors:
        print(f"\n{errors} patch(es) failed.")
        sys.exit(1)
    else:
        print("\nAll mixed-support patches applied successfully.")


if __name__ == "__main__":
    main()
