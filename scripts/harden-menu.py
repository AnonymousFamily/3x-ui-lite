#!/usr/bin/env python3
"""Insert guards into x-ui.sh so its install/update paths cannot replace this build.

Usage: harden-menu.py <path/to/x-ui.sh>

Idempotent: a function that already mentions 3X-UI Lite in its first lines is
left alone. Works on future upstream versions as long as the function names
stay the same; a missing function is reported but not fatal.
"""

import re
import sys
from pathlib import Path

FUNCS = ("install", "update", "update_dev", "update_menu", "legacy_version")
MARK = "3X-UI Lite blocks"
GUARD = """    LOGE "3X-UI Lite blocks the built-in '{fn}' path: it would install the upstream build with sponsors."
    LOGI "Upgrade with:"
    LOGI "  curl -fsSL https://cdn.jsdelivr.net/gh/AnonymousFamily/3x-ui-lite@main/install-lite.sh | sudo bash"
    return 1
"""


def main() -> int:
    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")
    missing = []
    for fn in FUNCS:
        header = f"\n{fn}() {{\n"
        idx = text.find(header)
        if idx < 0:
            missing.append(fn)
            continue
        start = idx + len(header)
        window = text[start : start + 400]
        if MARK in window:
            continue
        text = text[:start] + GUARD.format(fn=fn) + text[start:]
    path.write_text(text, encoding="utf-8", newline="\n")
    if missing:
        print(f"warning: functions not found: {', '.join(missing)}", file=sys.stderr)
    print(f"hardened {path} (guards: {', '.join(f for f in FUNCS if f not in missing)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
