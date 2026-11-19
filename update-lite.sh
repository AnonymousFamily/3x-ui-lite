#!/usr/bin/env bash
# Installs the newest sponsor-free release of this fork.
#
# Invoked by the panel's in-app updater, so it honours the same environment
# contract as the upstream update.sh: XUI_MAIN_FOLDER, XUI_UPDATE_STATUS_FILE,
# XUI_UPDATE_RUN_ID and XUI_UPDATE_TAG, and it records the result in the status
# file the panel polls.
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

log "installing $TAG"
fetch "$BASE/$ASSET" "$TMP/$ASSET"
fetch "$BASE/SHA256SUMS.txt" "$TMP/SHA256SUMS.txt"
( cd "$TMP" && sha256sum -c SHA256SUMS.txt --ignore-missing )

mkdir -p "$MAIN"
if [ -f "$MAIN/x-ui" ]; then
  cp -p "$MAIN/x-ui" "$MAIN/x-ui.bak.$(date +%Y%m%d-%H%M%S)"
fi

systemctl stop x-ui 2>/dev/null || rc-service x-ui stop 2>/dev/null || true

tar -xzf "$TMP/$ASSET" -C "$MAIN" --strip-components=1
chmod +x "$MAIN/x-ui" "$MAIN/x-ui.sh" 2>/dev/null || true
find "$MAIN/bin" -maxdepth 1 -type f -exec chmod +x {} \; 2>/dev/null || true
if command -v restorecon >/dev/null 2>&1; then
  restorecon -R "$MAIN" >/dev/null 2>&1 || true
fi
install -m 755 "$MAIN/x-ui.sh" /usr/bin/x-ui 2>/dev/null || true

systemctl daemon-reload 2>/dev/null || true
systemctl start x-ui 2>/dev/null || rc-service x-ui start 2>/dev/null || true

write_status success 0
log "installed $TAG"
trap - EXIT
rm -rf "$TMP"
