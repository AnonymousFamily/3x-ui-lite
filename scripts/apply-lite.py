#!/usr/bin/env python3
"""Point a 3X-UI checkout's panel updater at this fork's releases.

Usage: apply-lite.py <src-root>

The release workflow builds from an upstream checkout, so the fork's Go changes
must be re-applied there. Idempotent; if an anchor is missing the workflow's
verification step fails rather than silently shipping the upstream updater.
"""

import re
import sys
from pathlib import Path

PANEL = "internal/web/service/panel/panel.go"
UPDATER = "https://cdn.jsdelivr.net/gh/AnonymousFamily/3x-ui-lite@main/update-lite.sh"
REPO = "AnonymousFamily/3x-ui-lite"
UPSTREAM = "MHSanaei/3x-ui"


def main() -> int:
    root = Path(sys.argv[1])
    path = root / PANEL
    text = path.read_text(encoding="utf-8")
    before = text

    text = re.sub(
        r'panelUpdaterURL(\s*)= "[^"]*"',
        'panelUpdaterURL\\1= "' + UPDATER + '"',
        text,
    )
    text = text.replace(
        f"api.github.com/repos/{UPSTREAM}/releases",
        f"api.github.com/repos/{REPO}/releases",
    )
    text = text.replace(
        "return release.TagName, nil",
        "return panelVersionFromTag(release.TagName), nil",
    )
    text = re.sub(
        r"\tif devChannelActive\(\) \{\n\t\treturn getDevUpdateInfo\(\)\n\t\}\n",
        "",
        text,
    )
    text = text.replace("return s.startUpdate(devChannelActive())", "return s.startUpdate(false)")
    text = text.replace("return s.startUpdate(dev)\n", "return s.startUpdate(false)\n")

    if "func panelVersionFromTag" not in text:
        text += (
            "\n// panelVersionFromTag maps a release tag to its upstream version:\n"
            '// "v3.12.0-nosponsor" -> "3.12.0".\n'
            "func panelVersionFromTag(tag string) string {\n"
            '\treturn strings.TrimSuffix(strings.TrimPrefix(tag, "v"), "-nosponsor")\n'
            "}\n"
        )

    if text == before:
        print("already applied")
    else:
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"patched {PANEL}")

    for needle in (REPO, "update-lite.sh", "panelVersionFromTag"):
        if needle not in text:
            print(f"error: {needle!r} missing after patch", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
