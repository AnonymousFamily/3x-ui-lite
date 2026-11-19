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
def strip_tsx(text):
    out = []
    for line in text.split("\n"):
        if "<SponsorSlot" in line:
            continue
        if re.search(r"from ['\"][^'\"]*(components/sponsor/|lib/sponsors|useSponsorsQuery)", line):
            continue
        out.append(line)
    return "\n".join(out)


def strip_routes_tsx(text):
    lines = [l for l in text.split("\n") if "path: '/sponsors'" not in l and "SponsorsPage" not in l]
    new = "\n".join(lines)
    body = "\n".join(l for l in new.split("\n") if not l.startswith("import "))
    if len(re.findall(r"<CrownOutlined", body)) == 0 and "CrownOutlined," in new:
        new = new.replace("  CrownOutlined,\n", "")
    return new


def strip_endpoints(text):
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if "path: '/sponsors'" in line:
            start = i
            while start > 0 and lines[start].strip() != "{":
                start -= 1
            end = i
            while end < len(lines) - 1 and lines[end].strip() not in ("},", "},"):
                end += 1
                if lines[end].strip() == "},":
                    break
            del lines[start : end + 1]
            break
    return "\n".join(lines)


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
                    # sibling of a selector list: move the brace up, keep the body
                    out[k] = out[k].rstrip().rstrip(",") + " {"
                else:
                    skipping = True
            continue
        out.append(line)
    return "\n".join(out)


edit("frontend/src/pages/login/LoginPage.tsx", strip_tsx)
edit("frontend/src/pages/index/IndexPage.tsx", strip_tsx)
edit("frontend/src/routes/panelRoutes.tsx", strip_routes_tsx)
edit("frontend/src/components/command-palette/CommandPalette.tsx", lambda t: re.sub(r"\n\s*'/sponsors': \[[^\]]*\],", "", t))
edit("frontend/src/api/queryKeys.ts", lambda t: re.sub(r"\n\s*sponsors: \(\) => \['sponsors'\] as const,", "", t))
edit("frontend/src/pages/api-docs/endpoints.ts", strip_endpoints)
edit("frontend/vite.config.js", lambda t: t.replace("sponsors|", ""))
edit("frontend/src/pages/login/LoginPage.css", strip_css)
edit("frontend/src/styles/page-shell.css", strip_css)


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
