"""
Fix: crash ("Unhandled unknown exception") when saving a printer preset
after changing extruder count from 1 to 2+.

Root cause: ConfigOptionVector::set_with_nil() in src/libslic3r/Config.hpp
throws ConfigurationError when inherits->size() != rhs->size().
This always happens when switching extruder count because the inherited
preset has a different-sized array than the edited one.

Fix: backport of OrcaSlicer PR #13035 — tolerate size mismatches by using
rhs as source of truth and nil-marking only the overlapping range.
"""
import sys
import os


THROW_MARKER  = 'rhs size different with inherits size'
RESIZE_MARKER = 'this->values.resize(inherits->size(), this->values.front());'
FOR_MARKER    = 'for (size_t i = 0; i < inherits_opt->size()'


def find_indent(text, pos):
    """Return the leading whitespace of the line that contains pos."""
    line_start = text.rfind('\n', 0, pos) + 1
    indent = ''
    for ch in text[line_start:]:
        if ch in (' ', '\t'):
            indent += ch
        else:
            break
    return indent


def make_replacement(indent):
    """Build the fixed loop with the correct indentation level."""
    i0 = indent
    i1 = indent + '    '
    i2 = indent + '        '
    i3 = indent + '            '
    return (
        f'{i0}// Tolerate presets where vector sizes may diverge\n'
        f'{i0}// (e.g. after changing extruder count). Keep rhs as source\n'
        f'{i0}// of truth and nil-mark only the overlapping range.\n'
        f'{i0}// Fix: OrcaSlicer PR #13035\n'
        f'{i0}this->values = rhs_opt->values;\n'
        f'\n'
        f'{i0}const size_t overlap_size = std::min(rhs_opt->size(), inherits_opt->size());\n'
        f'{i0}for (size_t i = 0; i < overlap_size; i += size_t(stride)) {{\n'
        f'{i1}const size_t group_size = std::min(size_t(stride), overlap_size - i);\n'
        f'{i1}bool set_nil = true;\n'
        f'{i1}for (size_t j = 0; j < group_size; ++j) {{\n'
        f'{i2}if (inherits_opt->values[i + j] != rhs_opt->values[i + j]) {{\n'
        f'{i3}set_nil = false;\n'
        f'{i3}break;\n'
        f'{i2}}}\n'
        f'{i1}}}\n'
        f'\n'
        f'{i1}for (size_t j = 0; j < group_size; ++j) {{\n'
        f'{i2}if (set_nil)\n'
        f'{i3}this->set_at_to_nil(i + j);\n'
        f'{i2}else\n'
        f'{i3}this->values[i + j] = rhs_opt->values[i + j];\n'
        f'{i1}}}\n'
        f'{i0}}}'
    )


def patch(base_dir):
    path = os.path.join(base_dir, 'src', 'libslic3r', 'Config.hpp')

    if not os.path.exists(path):
        print(f'SKIP (not found): {path}')
        return

    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()

    if THROW_MARKER not in text:
        print('Config.hpp: size-mismatch throw not present — already patched or different version.')
        return

    if RESIZE_MARKER not in text:
        print('WARNING: Config.hpp: resize marker not found — cannot apply patch.')
        sys.exit(1)

    resize_pos = text.index(RESIZE_MARKER)

    # Locate the 'if (inherits->size() != rhs->size())' line before the resize
    if_marker = 'if (inherits->size() != rhs->size())'
    if_pos = text.rfind(if_marker, 0, resize_pos)
    if if_pos < 0:
        print('WARNING: Config.hpp: if-check not found before resize — cannot apply patch.')
        sys.exit(1)

    # Start of replacement = start of the line containing the if
    block_start = text.rfind('\n', 0, if_pos) + 1

    # Determine indentation from that line
    indent = find_indent(text, if_pos)

    # Locate the for loop after the resize
    for_pos = text.find(FOR_MARKER, resize_pos)
    if for_pos < 0:
        print('WARNING: Config.hpp: for-loop marker not found after resize — cannot apply patch.')
        sys.exit(1)

    # Find the opening brace of the for loop
    open_brace = text.index('{', for_pos)

    # Walk forward counting braces to find the matching closing '}'
    depth = 0
    loop_end = -1
    for i in range(open_brace, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                loop_end = i
                break

    if loop_end < 0:
        print('WARNING: Config.hpp: could not find closing brace of for-loop — cannot apply patch.')
        sys.exit(1)

    # Replace from block_start to loop_end (inclusive)
    new_block = make_replacement(indent)
    new_text = text[:block_start] + new_block + text[loop_end + 1:]

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_text)

    print(f'SUCCESS: Config.hpp patched — extruder count save crash fixed.')


if __name__ == '__main__':
    base = sys.argv[1] if len(sys.argv) > 1 else 'orcaslicer-source'
    patch(base)
