#!/usr/bin/env python3
"""Remove the paid sponsor-placement feature from a 3X-UI checkout.

Usage: strip-sponsors.py <repo-root>

Best-effort and idempotent: it deletes the sponsor modules, drops the routes,
JSX slots, nav entries, i18n keys and CSS rules, then fails loudly if any
sponsor identifier survived. Upstream refactors that rename the feature make
this a no-op; the verification step is what actually gates the build.
"""

import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
changed = []


def rel(p):
    return str(p.relative_to(ROOT))


def drop(path):
    p = ROOT / path
    if p.is_dir():
        shutil.rmtree(p)
        changed.append(f"rm -r {path}")
    elif p.exists():
        p.unlink()
        changed.append(f"rm {path}")


def edit(path, fn):
    p = ROOT / path
    if not p.exists():
        return
    old = p.read_text(encoding="utf-8")
    new = fn(old)
    if new != old:
        p.write_text(new, encoding="utf-8", newline="\n")
        changed.append(f"edit {path}")


# ---------------------------------------------------------------- files
for pattern in (
    "internal/web/service/panel/sponsor*.go",
    "frontend/src/components/sponsor",
    "frontend/src/pages/sponsors",
    "frontend/src/lib/sponsors.ts",
    "frontend/src/api/queries/useSponsorsQuery.ts",
    "frontend/src/test/sponsors.test.tsx",
):
    base = ROOT / pattern
    for p in sorted(base.parent.glob(base.name)) if "*" in pattern else [base]:
        drop(str(p.relative_to(ROOT)) if p.exists() else pattern)


# ---------------------------------------------------------------- backend
def strip_go_handlers(text):
    # Drop `func (a *IndexController) sponsors(...) {...}` blocks and their comment.
    text = re.sub(
        r"\n//[^\n]*sponsor[^\n]*\n(?=func )",
        "\n",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"\nfunc \(a \*IndexController\) sponsor\w*\(c \*gin\.Context\) \{.*?\n\}\n",
        "\n",
        text,
        flags=re.S,
    )
    return re.sub(
        r"\nfunc \(a \*IndexController\) sponsors\(c \*gin\.Context\) \{.*?\n\}\n",
        "\n",
        text,
        flags=re.S,
    )


def strip_go_routes(text):
    lines = [l for l in text.split("\n") if '"/sponsors' not in l]
    return "\n".join(lines)


def strip_go_fields(text):
    # panelService existed only for the sponsor handlers.
    if len(re.findall(r"\bpanelService\b", text)) == 1:
        text = re.sub(r"\n\tpanelService\s+panel\.PanelService", "", text)
    return text


def strip_unused_go_imports(text):
    m = re.search(r"^import \(\n(.*?)^\)\n", text, flags=re.S | re.M)
    if not m:
        return text
    block = m.group(1)
    body = text[m.end():]
    kept, dropped = [], []
    for line in block.split("\n"):
        s = line.strip()
        mm = re.match(r'^(?:(\w+|\.|_)\s+)?"([^"]+)"$', s)
        if not mm:
            kept.append(line)
            continue
        alias, path = mm.group(1), mm.group(2)
        if alias == "_":
            kept.append(line)
            continue
        name = alias or path.rsplit("/", 1)[-1]
        if re.search(rf"\b{re.escape(name)}\.", body) or re.search(rf"\b{re.escape(name)}\b", body):
            kept.append(line)
        else:
            dropped.append(name)
    if not dropped:
        return text
    imp = re.sub(r"\n{2,}$", "\n", "\n".join(kept))
    return text[: m.start()] + "import (\n" + imp + "\n)\n" + body


edit(
    "internal/web/controller/index.go",
    lambda t: strip_unused_go_imports(strip_go_fields(strip_go_routes(strip_go_handlers(t)))),
)
edit(
    "internal/web/routes_contract_test.go",
    lambda t: re.sub(r'\n\t"GET /sponsors":\s*true,', "", t).replace(", /sponsors,", ","),
)


def strip_openapigen(text):
    lines = []
    for line in text.split("\n"):
        if "StructAllow" in line:
            line = re.sub(r'"Sponsor(List)?"\s*,?\s*', "", line)
            line = re.sub(r"\(\s*,", "(", line)
            line = re.sub(r",\s*\)", ")", line)
            line = re.sub(r",\s*,", ",", line)
        lines.append(line)
    return "\n".join(lines)


edit("tools/openapigen/main.go", strip_openapigen)


# ---------------------------------------------------------------- frontend
SPONSOR_MARK = re.compile(
    r"SponsorSlot|SponsorsPage|SponsorCard|sponsorsForSlot|useSponsorsQuery"
    r"|menu\.sponsors|pages\.sponsors"
)
ROUTE_MARK = re.compile(r"""["']/?sponsors["']""")
UNION_MARK = re.compile(r"""^\s*\|\s*["']sponsors["']\s*$""")
ICON_MARK = re.compile(r"""^\s*sponsors:\s*\w+,\s*$""")


def object_block(lines, i):
    """Return the (start, end) lines of the `{ ... },` literal around line i.

    Config objects in this repo are one key per line with no nested literals,
    so matching the nearest bracket lines beats counting braces (strings such
    as '/sponsors/logo/{name}' would skew a counter).
    """
    if lines[i].strip().startswith("{"):
        return i, i
    s = i
    while s >= 0 and lines[s].strip() != "{":
        s -= 1
    if s < 0:
        return i, i
    e = i
    while e < len(lines) and lines[e].strip() not in ("},", "};", "}"):
        e += 1
    if e >= len(lines):
        return i, i
    return s, e


def sweep_tsx(text):
    lines = text.split("\n")
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        route = ROUTE_MARK.search(line)
        hit = SPONSOR_MARK.search(line) or route or UNION_MARK.match(line) or ICON_MARK.match(line)
        if not hit:
            out.append(line)
            i += 1
            continue
        if route and re.search(r"(path|key|to)\s*:\s*[\"']/?sponsors[\"']", line):
            s, e = object_block(lines, i)
            if s < i:
                del out[len(out) - (i - s):]  # drop the opener lines already kept
            i = e + 1
            continue
        i += 1
    return "\n".join(out)


for p in sorted((ROOT / "frontend/src").rglob("*")):
    if not p.is_file() or p.suffix not in (".ts", ".tsx"):
        continue
    if "generated" in p.parts or "node_modules" in p.parts:
        continue
    before = p.read_text(encoding="utf-8")
    after = sweep_tsx(before)
    if after != before:
        p.write_text(after, encoding="utf-8", newline="\n")
        changed.append(f"edit {rel(p)}")

# CrownOutlined was only used by the sponsor entry.
for p in sorted((ROOT / "frontend/src").rglob("*.tsx")):
    if "generated" in p.parts or "node_modules" in p.parts:
        continue
    text = p.read_text(encoding="utf-8")
    if len(re.findall(r"\bCrownOutlined\b", text)) != 1:
        continue
    lines = text.split("\n")
    kept = []
    for line in lines:
        if re.match(r"^\s*CrownOutlined,\s*$", line):
            kept.append(None)  # drop
            continue
        if "CrownOutlined" in line and "import" in line:
            cleaned = re.sub(r"CrownOutlined,\s*", "", line)
            kept.append(cleaned)
            continue
        kept.append(line)
    new = "\n".join(l for l in kept if l is not None)
    if new != text:
        p.write_text(new, encoding="utf-8", newline="\n")
        changed.append(f"edit {rel(p)}")

def strip_css(text):
    """Drop rules whose selector mentions sponsor; keep sibling selectors."""
    lines = text.split("\n")
    out, skipping = [], False
    for line in lines:
        if skipping:
            if line.strip() == "}":
                skipping = False
            continue
        low = line.lower()
        if "sponsor" in low and line.rstrip().endswith(("{", ",")):
            if line.rstrip().endswith("{"):
                k = len(out) - 1
                while k >= 0 and not out[k].strip():
                    k -= 1
                if k >= 0 and out[k].rstrip().endswith(","):
                    out[k] = out[k].rstrip().rstrip(",") + " {"
                else:
                    skipping = True
            continue
        out.append(line)
    return "\n".join(out)


edit("frontend/src/pages/login/LoginPage.css", strip_css)
edit("frontend/src/styles/page-shell.css", strip_css)
edit("frontend/vite.config.js", lambda t: t.replace("sponsors|", ""))


# ---------------------------------------------------------------- i18n
for p in sorted((ROOT / "internal/web/translation").glob("*.json")):
    data = json.loads(p.read_text(encoding="utf-8"))
    hit = False
    for section, key in (("menu", "sponsors"), ("pages", "sponsors")):
        if isinstance(data.get(section), dict) and key in data[section]:
            del data[section][key]
            hit = True
    if hit:
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        changed.append(f"edit {rel(p)}")


# ---------------------------------------------------------------- verify
BAD_IDENT = re.compile(r"SponsorSlot|SponsorCard|SponsorsPage|sponsorsForSlot|useSponsorsQuery|SponsorList")
BAD_ROUTE = re.compile(r"""["']/sponsors["']""")
problems, skipped = [], 0
for p in ROOT.rglob("*"):
    if not p.is_file():
        continue
    parts = set(p.parts)
    if parts & {".git", "node_modules", "dist", "generated", "docs"}:
        continue
    if "internal" in parts and "web" in parts and "dist" in p.parts:
        continue
    if p.suffix not in (".go", ".ts", ".tsx", ".js", ".css"):
        continue
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        continue
    if BAD_IDENT.search(text) or BAD_ROUTE.search(text):
        problems.append(rel(p))

if problems:
    print("sponsor references survived in:", file=sys.stderr)
    for x in problems[:20]:
        print("  " + x, file=sys.stderr)
    sys.exit(1)

print(f"stripped {len(changed)} items; sponsor identifiers gone ({skipped} stale openapi copies will be regenerated)")
