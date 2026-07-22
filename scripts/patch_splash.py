"""
Kentstrapper splash screen patch for OrcaSlicer GUI_App.cpp.

Supports:
  v2.3.x  — patches MakeBitmap() and Decorate() (old-style)
  v2.4.2+ — patches SplashScreen constructor (new-style)

Loads resources/images/OrcaSlicer_154.png (copied from branding/background.png
in PATCH 5 of the CI workflow) instead of the upstream SVG logo, and sets the
version-text color to Kentstrapper orange.
"""
import sys, os, re


# ── v2.4.2+ ─────────────────────────────────────────────────────────────────
# Matches the full  m_logo_bmp = *bmp_cache.load_svg(...);  statement.
# [^;] matches any char including newlines so multi-line calls are handled.
LOGO_PATTERN_NEW = re.compile(
    r'^([ \t]*)m_logo_bmp\s*=\s*\*bmp_cache\.load_svg\([^;]+\);',
    re.MULTILINE,
)

OLD_FG_COLOR_NEW = 'm_fg_color = StateColor::darkModeColorFor(wxColour("#6B6A6A"));'
NEW_FG_COLOR_NEW = 'm_fg_color = wxColour(255, 136, 0); // Kentstrapper orange'

# ── v2.3.x ───────────────────────────────────────────────────────────────────
OLD_MAKE = (
    '    static wxBitmap MakeBitmap()\n'
    '    {\n'
    '        int width = FromDIP(480, nullptr);\n'
    '        int height = FromDIP(480, nullptr);\n'
    '\n'
    '        wxImage image(width, height);\n'
    '        wxBitmap new_bmp(image);\n'
    '\n'
    '        wxMemoryDC memDC;\n'
    '        memDC.SelectObject(new_bmp);\n'
    '        memDC.SetBrush(StateColor::darkModeColorFor(*wxWHITE));\n'
    '        memDC.DrawRectangle(-1, -1, width + 2, height + 2);\n'
    '        memDC.DrawBitmap(new_bmp, 0, 0, true);\n'
    '        return new_bmp;\n'
    '    }'
)
NEW_MAKE = (
    '    static wxBitmap MakeBitmap()\n'
    '    {\n'
    '        // Kentstrapper: load custom splash from resources/images/OrcaSlicer_154.png\n'
    '        wxString splash_path = from_u8(Slic3r::resources_dir() + "/images/OrcaSlicer_154.png");\n'
    '        if (wxFileExists(splash_path)) {\n'
    '            wxImage img;\n'
    '            if (img.LoadFile(splash_path, wxBITMAP_TYPE_ANY) && img.IsOk()) {\n'
    '                int target = FromDIP(480, nullptr);\n'
    '                img = img.Scale(target, target, wxIMAGE_QUALITY_BILINEAR);\n'
    '                return wxBitmap(img);\n'
    '            }\n'
    '        }\n'
    '        // Fallback: white background\n'
    '        int width = FromDIP(480, nullptr);\n'
    '        int height = FromDIP(480, nullptr);\n'
    '        wxImage image(width, height);\n'
    '        wxBitmap new_bmp(image);\n'
    '        wxMemoryDC memDC;\n'
    '        memDC.SelectObject(new_bmp);\n'
    '        memDC.SetBrush(StateColor::darkModeColorFor(*wxWHITE));\n'
    '        memDC.DrawRectangle(-1, -1, width + 2, height + 2);\n'
    '        memDC.DrawBitmap(new_bmp, 0, 0, true);\n'
    '        return new_bmp;\n'
    '    }'
)

OLD_LOGO_LEGACY = (
    '        BitmapCache bmp_cache;\n'
    '        wxBitmap logo_bmp = *bmp_cache.load_svg(is_dark ? "splash_logo_dark" : "splash_logo", width, height);'
    '  // use with full width & height\n'
    '        memDc.DrawBitmap(logo_bmp, 0, 0, true);'
)
NEW_LOGO_LEGACY = (
    '        // Kentstrapper: skip SVG logo — custom PNG background is loaded in MakeBitmap()'
)

OLD_COLOR_LEGACY = 'memDc.SetTextForeground(StateColor::darkModeColorFor(wxColor(134, 134, 134)));'
NEW_COLOR_LEGACY = 'memDc.SetTextForeground(wxColour(255, 136, 0)); // Kentstrapper orange'


def patch_file(path):
    if not os.path.exists(path):
        print(f"ERROR: file not found: {path}")
        sys.exit(1)

    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    original = content
    patched_logo = False
    patched_color = False

    # ── v2.4.2+ SplashScreen constructor patch ───────────────────────────────

    m = LOGO_PATTERN_NEW.search(content)
    if m:
        indent = m.group(1)
        i1 = indent + '    '
        i2 = indent + '        '
        replacement = (
            f'{indent}// Kentstrapper: load custom splash from resources/images/OrcaSlicer_154.png\n'
            f'{indent}wxString splash_path = from_u8(Slic3r::resources_dir() + "/images/OrcaSlicer_154.png");\n'
            f'{indent}if (wxFileExists(splash_path)) {{\n'
            f'{i1}wxImage img;\n'
            f'{i1}if (img.LoadFile(splash_path, wxBITMAP_TYPE_ANY) && img.IsOk()) {{\n'
            f'{i2}img = img.Scale(sz.GetWidth(), sz.GetHeight(), wxIMAGE_QUALITY_BILINEAR);\n'
            f'{i2}m_logo_bmp = wxBitmap(img);\n'
            f'{i1}}}\n'
            f'{indent}}}\n'
            f'{indent}if (!m_logo_bmp.IsOk())\n'
            f'{i1}m_logo_bmp = *bmp_cache.load_svg(dark_mode ? "splash_logo_dark" : "splash_logo", sz.GetWidth(), sz.GetHeight());'
        )
        content = content[:m.start()] + replacement + content[m.end():]
        print("  Patched: SplashScreen constructor — loads custom PNG (v2.4.2+ style)")
        patched_logo = True

    if OLD_FG_COLOR_NEW in content:
        content = content.replace(OLD_FG_COLOR_NEW, NEW_FG_COLOR_NEW)
        print("  Patched: m_fg_color -> Kentstrapper orange")
        patched_color = True

    # ── v2.3.x MakeBitmap / Decorate patches ────────────────────────────────

    if not patched_logo:
        if OLD_MAKE in content:
            content = content.replace(OLD_MAKE, NEW_MAKE)
            print("  Patched: MakeBitmap() — loads custom PNG (v2.3.x style)")
            patched_logo = True
        else:
            print("  WARNING: MakeBitmap() pattern not found (v2.3.x) — skipping")

    if OLD_LOGO_LEGACY in content:
        content = content.replace(OLD_LOGO_LEGACY, NEW_LOGO_LEGACY)
        print("  Patched: Decorate() — SVG logo overlay removed")

    if not patched_color:
        if OLD_COLOR_LEGACY in content:
            content = content.replace(OLD_COLOR_LEGACY, NEW_COLOR_LEGACY)
            print("  Patched: version text color -> Kentstrapper orange (v2.3.x style)")
            patched_color = True
        else:
            print("  WARNING: version text color pattern not found — skipping")

    # ── Fail hard if logo was never patched ─────────────────────────────────

    if not patched_logo:
        print("  ERROR: Could not patch splash logo — no matching pattern in GUI_App.cpp")
        sys.exit(1)

    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Saved: {path}")
    else:
        print("  No changes made.")


if __name__ == '__main__':
    base = sys.argv[1] if len(sys.argv) > 1 else 'orcaslicer-source'
    gui_app = os.path.join(base, 'src', 'slic3r', 'GUI', 'GUI_App.cpp')
    print(f"Patching splash screen in: {gui_app}")
    patch_file(gui_app)
