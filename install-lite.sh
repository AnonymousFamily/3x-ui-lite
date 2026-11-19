#!/usr/bin/env bash
# 3X-UI Lite installer — installs the sponsor-free build from GitHub releases.
# Usage: bash install-lite.sh [--port N] [--dir PATH] [--no-start] [--uninstall] [--purge]
set -euo pipefail

REPO="AnonymousFamily/3x-ui-lite"
# Pick the highest v*-nosponsor tag, not /releases/latest: "latest" follows the
# publish time, so back-filling an older version would win there.
# Pin with XUI_RELEASE_TAG=v3.11.0-nosponsor when a specific build is needed.
TAG="${XUI_RELEASE_TAG:-}"
if [ -z "$TAG" ]; then
  TAG=$(curl -fsSL --max-time 20 "https://api.github.com/repos/$REPO/releases?per_page=100" 2>/dev/null \
    | sed -n 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' \
    | grep -- '-nosponsor$' | sort -V | tail -1)
fi
[ -n "$TAG" ] || TAG="v3.11.0-nosponsor"
VER="${TAG#v}"
VER="${VER%-nosponsor}"
PKG="3x-ui-${VER}-nosponsor"
TARBALL="${PKG}-linux-amd64.tar.gz"
BASE="https://github.com/${REPO}/releases/download/${TAG}"
DIR="${XUI_INSTALL_DIR:-/usr/local/x-ui}"
SERVICE=/etc/systemd/system/x-ui.service
PORT=""
NO_START=0
PREFIX=""
UNINSTALL=0
PURGE=0
RESET_XRAY=0

say()  { printf '%s\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
die()  { printf '\033[31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

usage() {
  cat <<'EOF'
3X-UI Lite installer (sponsor-free build of 3X-UI)

  bash install-lite.sh                 install or upgrade, keep existing data
  bash install-lite.sh --port 8443     also change the panel port
  bash install-lite.sh --uninstall     remove the panel (keeps /etc/x-ui data)
  bash install-lite.sh --uninstall --purge   also delete the database

Options:
  --port N      panel port after install
  --dir PATH    install directory (default /usr/local/x-ui)
  --no-start    install files only, do not enable/start the service
  --reset-xray  also replace bin/ with the packaged Xray core (default: keep
                the core already installed, so a panel upgrade never changes it)
  --prefix PATH test mode: install under PATH without root/systemd
  -h, --help    this help
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --port) PORT="${2:-}"; shift 2 ;;
    --dir) DIR="${2:-}"; shift 2 ;;
    --no-start) NO_START=1; shift ;;
    --prefix) PREFIX="${2:-}"; DIR="${2:-}"; NO_START=1; shift 2 ;;
    --reset-xray) RESET_XRAY=1; shift ;;
    --uninstall) UNINSTALL=1; shift ;;
    --purge) PURGE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown option: $1 (try --help)" ;;
  esac
done

[ "$(id -u)" = "0" ] || [ -n "$PREFIX" ] || die "please run as root: sudo bash install-lite.sh"

has_systemd() { command -v systemctl >/dev/null 2>&1 && [ -d /run/systemd/system ]; }

stop_panel() {
  if has_systemd; then systemctl stop x-ui >/dev/null 2>&1 || true; fi
  pkill -f "$DIR/x-ui" >/dev/null 2>&1 || true
  sleep 1
}

do_uninstall() {
  say "== Uninstalling 3X-UI Lite =="
  stop_panel
  if has_systemd; then systemctl disable x-ui >/dev/null 2>&1 || true; fi
  rm -f "$SERVICE" /usr/bin/x-ui
  if has_systemd; then systemctl daemon-reload >/dev/null 2>&1 || true; fi
  rm -rf "$DIR"
  ok "removed $DIR, /usr/bin/x-ui and the systemd unit"
  if [ "$PURGE" = 1 ]; then
    rm -rf /etc/x-ui /var/log/x-ui
    ok "purged /etc/x-ui and /var/log/x-ui"
  else
    warn "data kept in /etc/x-ui (use --purge to delete)"
  fi
  exit 0
}
[ "$UNINSTALL" = 1 ] && do_uninstall

# --- platform checks -------------------------------------------------------
ARCH="$(uname -m)"
case "$ARCH" in
  x86_64|amd64) ok "arch $ARCH" ;;
  aarch64|arm64) die "this release is amd64-only; an arm64 build is not published yet" ;;
  *) die "unsupported arch: $ARCH" ;;
esac

[ -n "$PREFIX" ] || [ "$(uname -s)" = "Linux" ] || die "Linux only"
command -v curl >/dev/null 2>&1 || die "curl is required"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fetch() { # fetch <url> <out>
  local url="$1" out="$2" p
  for p in "" "https://gh-proxy.com/" "https://ghproxy.net/"; do
    if curl -fL --retry 2 --connect-timeout 15 --max-time 900 -o "$out" "${p}${url}" 2>/dev/null; then
      return 0
    fi
  done
  return 1
}

# --- download + verify -----------------------------------------------------
say "== Downloading $TARBALL (${TAG}) =="
fetch "$BASE/$TARBALL" "$TMP/$TARBALL" || die "download failed (check network, or set https_proxy)"
ok "$(du -h "$TMP/$TARBALL" | cut -f1)"

say "== Verifying checksum =="
if fetch "$BASE/SHA256SUMS.txt" "$TMP/SHA256SUMS.txt"; then
  ( cd "$TMP" && sha256sum -c SHA256SUMS.txt --ignore-missing ) || die "checksum mismatch"
  ok "sha256 ok"
else
  warn "SHA256SUMS.txt unavailable, skipping verification"
fi

say "== Unpacking =="
tar -xzf "$TMP/$TARBALL" -C "$TMP"
[ -x "$TMP/$PKG/x-ui" ] || die "archive layout unexpected"
ok "unpacked"

# --- install ---------------------------------------------------------------
DB_EXISTED=0
[ -f /etc/x-ui/x-ui.db ] && DB_EXISTED=1

say "== Installing to $DIR =="
stop_panel
install -d "$DIR"
if [ -f "$DIR/x-ui" ]; then
  cp -p "$DIR/x-ui" "$DIR/x-ui.bak.$(date +%Y%m%d-%H%M%S)"
  ok "previous binary backed up"
fi

# Panel files are installed one by one so bin/ can stay untouched: the Xray
# core belongs to the panel's own version switcher, not to a panel upgrade.
install -m 755 "$TMP/$PKG/x-ui" "$DIR/x-ui"
install -m 755 "$TMP/$PKG/x-ui.sh" "$DIR/x-ui.sh"
chmod +x "$DIR/x-ui" "$DIR/x-ui.sh"

KEEP_CORE=0
if [ "$RESET_XRAY" = 0 ] && [ -d "$DIR/bin" ] && [ -n "$(ls -A "$DIR/bin" 2>/dev/null)" ]; then
  KEEP_CORE=1
fi
if [ "$KEEP_CORE" = 1 ]; then
  ok "existing Xray core kept (use --reset-xray to replace it)"
else
  rm -rf "$DIR/bin"
  cp -a "$TMP/$PKG/bin" "$DIR/bin"
  find "$DIR/bin" -maxdepth 1 -type f -exec chmod +x {} \; 2>/dev/null || true
  ok "Xray core installed from the package"
fi

if command -v restorecon >/dev/null 2>&1; then
  restorecon -R "$DIR" >/dev/null 2>&1 || true
fi
ok "files installed"

if [ -n "$PREFIX" ]; then
  say ""
  ok "test install done: $DIR"
  say "run it with:"
  say "  XUI_DB_FOLDER=$TMP/db XUI_PORT=2099 $DIR/x-ui"
  exit 0
fi

[ -f "$DIR/x-ui.sh" ] && install -m 755 "$DIR/x-ui.sh" /usr/bin/x-ui

# --- service ---------------------------------------------------------------
. /etc/os-release 2>/dev/null || true
case "${ID:-}${ID_LIKE:-}" in
  *debian*|*ubuntu*|*linuxmint*) SVC=debian ;;
  *rhel*|*centos*|*fedora*|*rocky*|*almalinux*|*ol*) SVC=rhel ;;
  *arch*) SVC=arch ;;
  *) SVC=debian ;;
esac
if [ -f "$DIR/x-ui.service.$SVC" ]; then
  install -m 644 "$DIR/x-ui.service.$SVC" "$SERVICE"
  ok "systemd unit installed ($SVC)"
fi
# A drop-in left by an older official install can abort startup (status=2).
DROPIN=/etc/systemd/system/x-ui.service.d
if [ -d "$DROPIN" ] && compgen -G "$DROPIN/*.conf" >/dev/null 2>&1; then
  mv "$DROPIN" "$DROPIN.bak.$(date +%Y%m%d-%H%M%S)"
  warn "moved legacy systemd drop-in aside"
fi

# --- port ------------------------------------------------------------------
if [ -n "$PORT" ]; then
  "$DIR/x-ui" setting -port "$PORT" >/dev/null 2>&1 && ok "panel port set to $PORT"
fi

# --- start -----------------------------------------------------------------
if [ "$NO_START" = 1 ]; then
  warn "service not started (--no-start); start it with: systemctl start x-ui"
  exit 0
fi
if ! has_systemd; then
  warn "systemd not found; start manually: $DIR/x-ui"
  exit 0
fi

systemctl daemon-reload
systemctl enable x-ui >/dev/null 2>&1
systemctl reset-failed x-ui >/dev/null 2>&1 || true
systemctl restart x-ui
sleep 2
if systemctl is-active --quiet x-ui; then
  ok "service running"
else
  warn "service failed to start; last log lines:"
  journalctl -u x-ui -n 30 --no-pager 2>/dev/null || true
  if journalctl -u x-ui -n 10 --no-pager 2>/dev/null | grep -q '203/EXEC'; then
    warn "203/EXEC = exec denied; fix the file label and retry:"
    warn "  sudo restorecon -Rv $DIR && sudo systemctl reset-failed x-ui"
  fi
  die "fix the error above, then: systemctl restart x-ui"
fi

# --- summary ---------------------------------------------------------------
# The panel may keep a port from the previous install (often a random one),
# so read the real listener from the log instead of assuming 2053.
SCHEME=http
LINE=$(journalctl -u x-ui -n 200 --no-pager -o cat 2>/dev/null | grep -E 'Web server running (HTTP|HTTPS) on' | tail -1 || true)
case "$LINE" in *"HTTPS on"*) SCHEME=https ;; esac
LISTEN_PORT=$(printf '%s' "$LINE" | grep -oE '[0-9]+$' || true)
LISTEN_PORT="${LISTEN_PORT:-${PORT:-2053}}"

# The panel may also sit behind a custom webBasePath; read it so the printed
# URL is the one that actually answers (a bare "/" would 404).
BASE_PATH=$("$DIR/x-ui" setting -show 2>/dev/null | sed -n 's/^webBasePath:[[:space:]]*//p' | head -1 || true)
BASE_PATH="${BASE_PATH:-/}"
case "$BASE_PATH" in
  */) ;;
  *) BASE_PATH="$BASE_PATH/" ;;
esac

say ""
say "================================================================"
say " 3X-UI Lite installed (sponsor-free build)"
say " Panel : ${SCHEME}://<server-ip>:${LISTEN_PORT}${BASE_PATH}"
if [ "$DB_EXISTED" = 1 ]; then
  say " Login : existing database kept, use your previous credentials"
else
  say " Login : generated on first start — see below"
fi
say "================================================================"
if [ "$DB_EXISTED" = 0 ]; then
  say ""
  journalctl -u x-ui -n 120 --no-pager 2>/dev/null | grep -i "Username:" | tail -1 || \
    say " (open: journalctl -u x-ui -n 50 --no-pager | grep Username)"
fi
say ""
say "Next: allow the port in your firewall / cloud security group,"
say "then add inbounds in the panel."
say ""
say "Upgrades: the panel's 'Update panel' button installs this repo's newest"
say "sponsor-free release. The menu's Install/Update entries are disabled on"
say "purpose (they would fetch the upstream build)."
