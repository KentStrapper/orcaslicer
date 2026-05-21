"""
Kentstrapper splash screen patch for OrcaSlicer GUI_App.cpp.
Patches MakeBitmap() to load custom PNG from resources/images/OrcaSlicer_154.png
and Decorate() to skip the SVG logo overlay.
"""
import sys, os

def patch_file(path):
    if not os.path.exists(path):
        print(f"[WARN] file not found: {path} — skipping splash patch")
        return

    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    original = content

    # ── PATCH 1: MakeBitmap() — load custom PNG instead of white background ──
    old_make = (
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
    new_make = (
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

    if old_make in content:
        content = content.replace(old_make, new_make)
        print("  Patched: MakeBitmap() — loads custom PNG splash")
    else:
        print("  WARNING: MakeBitmap() pattern not found — skipping")

    # ── PATCH 2: Decorate() — remove SVG logo overlay ─────────────────────
    old_logo = (
        '        BitmapCache bmp_cache;\n'
        '        wxBitmap logo_bmp = *bmp_cache.load_svg(is_dark ? "splash_logo_dark" : "splash_logo", width, height);'
        '  // use with full width & height\n'
        '        memDc.DrawBitmap(logo_bmp, 0, 0, true);'
    )
    new_logo = (
        '        // Kentstrapper: skip SVG logo — custom PNG background is loaded in MakeBitmap()'
    )
    if old_logo in content:
        content = content.replace(old_logo, new_logo)
        print("  Patched: Decorate() — SVG logo overlay removed")
    else:
        print("  WARNING: Decorate() SVG logo pattern not found — skipping")

    # ── PATCH 3: Decorate() — version text in Kentstrapper orange ─────────
    old_color = 'memDc.SetTextForeground(StateColor::darkModeColorFor(wxColor(134, 134, 134)));'
    new_color = 'memDc.SetTextForeground(wxColour(255, 136, 0)); // Kentstrapper orange'
    if old_color in content:
        content = content.replace(old_color, new_color)
        print("  Patched: version text color -> Kentstrapper orange")
    else:
        print("  WARNING: version text color pattern not found — skipping")

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
