#!/usr/bin/env bash
# Updates the panel only. The Xray core in bin/ is owned by the panel's own
# "Xray version" switcher and is deliberately left untouched here, so users can
# run whatever core version they chose.
#
# Invoked by the panel's in-app updater; honours XUI_MAIN_FOLDER,
# XUI_UPDATE_STATUS_FILE, XUI_UPDATE_RUN_ID and XUI_UPDATE_TAG.
set -euo pipefail

REPO="AnonymousFamily/3x-ui-lite"
MAIN="${XUI_MAIN_FOLDER:-/usr/local/x-ui}"
STATUS="${XUI_UPDATE_STATUS_FILE:-/etc/x-ui/update-status.json}"
RUN_ID="${XUI_UPDATE_RUN_ID:-0}"
TAG="${XUI_UPDATE_TAG:-}"
TMP="$(mktemp -d)"

log() { printf '%s\n' "$*"; }

write_status() { # <state> <exit code>
  mkdir -p "$(dirname "$STATUS")" 2>/dev/null || true
  printf '{"runId":"%s","state":"%s","exitCode":%s,"finishedAt":%s}\n' \
    "$RUN_ID" "$1" "$2" "$(date +%s)" >"$STATUS.tmp" 2>/dev/null || return 0
  mv "$STATUS.tmp" "$STATUS" 2>/dev/null || true
}

cleanup() {
  local code=$?
  rm -rf "$TMP"
  if [ "$code" -ne 0 ]; then
    log "update failed with exit code $code"
    write_status failed "$code"
  fi
}
trap cleanup EXIT

fetch() { # <url> <out>
  local url="$1" out="$2" p
  for p in "" "https://gh-proxy.com/" "https://ghproxy.net/"; do
    if curl -fL --retry 2 --connect-timeout 15 --max-time 600 -o "$out" "${p}${url}"; then
      return 0
    fi
  done
  return 1
}

[ "$(id -u)" = "0" ] || { log "root is required to update the panel"; exit 1; }

write_status pending 0

if [ -z "$TAG" ]; then
  TAG=$(curl -fsSL -o /dev/null -w '%{url_effective}' --max-time 30 \
    "https://github.com/$REPO/releases/latest" | sed -n 's#.*/tag/##p')
fi

case "$TAG" in
  v*-nosponsor) ;;
  *) log "latest release is not a sponsor-free build ($TAG)"; exit 1 ;;
esac

VER="${TAG#v}"
VER="${VER%-nosponsor}"
PKG="3x-ui-${VER}-nosponsor"
ASSET="$PKG-linux-amd64.tar.gz"
BASE="https://github.com/$REPO/releases/download/$TAG"

log "installing panel $TAG (xray core is left as-is)"
fetch "$BASE/$ASSET" "$TMP/$ASSET"
fetch "$BASE/SHA256SUMS.txt" "$TMP/SHA256SUMS.txt"
( cd "$TMP" && sha256sum -c SHA256SUMS.txt --ignore-missing )

mkdir -p "$TMP/extract"
tar -xzf "$TMP/$ASSET" -C "$TMP/extract"
SRC="$TMP/extract/$PKG"
[ -x "$SRC/x-ui" ] || { log "unexpected archive layout"; exit 1; }

mkdir -p "$MAIN"
if [ -f "$MAIN/x-ui" ]; then
  cp -p "$MAIN/x-ui" "$MAIN/x-ui.bak.$(date +%Y%m%d-%H%M%S)"
fi

systemctl stop x-ui 2>/dev/null || rc-service x-ui stop 2>/dev/null || true

# Panel files only: bin/ (xray, mtg, geo data) stays exactly as the user left it.
install -m 755 "$SRC/x-ui" "$MAIN/x-ui"
if [ -f "$SRC/x-ui.sh" ]; then
  install -m 755 "$SRC/x-ui.sh" "$MAIN/x-ui.sh"
  install -m 755 "$SRC/x-ui.sh" /usr/bin/x-ui 2>/dev/null || true
fi
for unit in x-ui.service.debian x-ui.service.arch x-ui.service.rhel; do
  [ -f "$SRC/$unit" ] && cp -f "$SRC/$unit" "$MAIN/$unit"
done

# A host without a core yet (unusual) still needs one to run.
if [ ! -d "$MAIN/bin" ] || [ -z "$(ls -A "$MAIN/bin" 2>/dev/null)" ]; then
  log "no xray core present, installing the packaged one"
  cp -a "$SRC/bin" "$MAIN/bin"
  chmod +x "$MAIN/bin/"* 2>/dev/null || true
fi

if command -v restorecon >/dev/null 2>&1; then
  restorecon -R "$MAIN" >/dev/null 2>&1 || true
fi

systemctl daemon-reload 2>/dev/null || true
systemctl start x-ui 2>/dev/null || rc-service x-ui start 2>/dev/null || true

CORE=$("$MAIN/bin/xray-linux-amd64" -version 2>/dev/null | head -1 || true)
write_status success 0
log "panel updated to $TAG; xray core unchanged${CORE:+ ($CORE)}"
trap - EXIT
rm -rf "$TMP"
