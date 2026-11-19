# 3X-UI Lite — sponsor-free build

**Independently maintained** build of the 3X-UI panel: same features, paid sponsor placements removed.
Every upstream release is rebuilt here automatically.

> This project is independent: **no affiliation, endorsement or cooperation** with the upstream author.
> Please do not report issues with this build upstream. Upstream 3X-UI is GPL-3.0, so this derivative
> distribution keeps its copyright notice and license (`LICENSE`, `NOTICE.md`); nothing else links the two.

|  |  |
| --- | --- |
| Releases | [github.com/AnonymousFamily/3x-ui-lite/releases](https://github.com/AnonymousFamily/3x-ui-lite/releases) |
| Features | [FEATURES.md](FEATURES.md) (Chinese) |
| Full guide | [GUIDE.md](GUIDE.md) (Chinese) |
| Changelog | [CHANGELOG.md](CHANGELOG.md) |
| 中文 | [README.md](README.md) |
| Platform | Linux x86_64 + systemd |

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/AnonymousFamily/3x-ui-lite/main/install-lite.sh | sudo bash
```

> This is the **only** install entry point for this project. Do **not** use the upstream
> `bash <(curl -Ls .../mhsanaei/3x-ui/master/install.sh)` command — it installs the official build
> and brings the sponsor placements back.

> If `raw.githubusercontent.com` is unreachable, prefix the URL with gh-proxy:
> `curl -fsSL https://gh-proxy.com/https://raw.githubusercontent.com/AnonymousFamily/3x-ui-lite/main/install-lite.sh | sudo bash`

| Option | Command |
| --- | --- |
| Custom panel port | `... | sudo bash -s -- --port 8443` |
| Pin a version | `... | sudo XUI_RELEASE_TAG=v3.11.0-nosponsor bash` |
| Uninstall (keep data) | `... | sudo bash -s -- --uninstall` |
| Uninstall and purge | `... | sudo bash -s -- --uninstall --purge` |

The installer verifies SHA256, backs up the previous binary, handles SELinux labels and legacy
systemd drop-ins, then reads the real port from the startup log.

## What changed

Compared to the matching upstream tag (currently `v3.11.0`), only the sponsor chain is removed:

| Layer | Removed |
| --- | --- |
| Backend service | `internal/web/service/panel/sponsor.go` (remote `sponsors.json` fetch, 1h cache, logo proxy) and tests |
| Backend routes | `GET /sponsors`, `GET /sponsors/logo/:name` and handlers |
| Frontend pages | `frontend/src/pages/sponsors/` |
| Frontend components | `frontend/src/components/sponsor/` |
| Frontend logic | `frontend/src/lib/sponsors.ts`, `api/queries/useSponsorsQuery.ts` |
| Ad slots | `<SponsorSlot>` on login page and dashboard |
| Navigation | Sponsors entry in sidebar, command palette, page titles, routes |
| Strings | `menu.sponsors`, `pages.sponsors.*` in all 14 locales |
| Generated | Regenerated TS types and OpenAPI (no `Sponsor` schema, no `/sponsors` path) |

**Deliberately kept:** the `Donate` button (a donation link, not a sponsor slot), the MTProto
`ad-tag`, the read-only update check, and every other panel feature.

Each release ships `nosponsor-v<version>.patch` with the exact source diff.

## Upgrade

**Panel updates and Xray core updates are independent**:

- **Panel**: the in-panel "Update panel" button (or re-running the installer) replaces panel files only —
  it never touches the Xray core in `bin/`
- **Core**: switch it whenever you like under "Xray version"; your choice survives panel upgrades
- Restore the packaged core with `--reset-xray`

```bash
# panel only (keeps the Xray version you selected)
curl -fsSL https://raw.githubusercontent.com/AnonymousFamily/3x-ui-lite/main/install-lite.sh | sudo bash

# panel + packaged core
curl -fsSL https://raw.githubusercontent.com/AnonymousFamily/3x-ui-lite/main/install-lite.sh | sudo bash -s -- --reset-xray
```

> The menu's `Install` / `Update` / `Update Menu` / `Legacy` entries are disabled because
> they fetch upstream scripts. The in-panel update button is safe: it only talks to this repo.

## Automation

The workflow checks upstream every **6 hours** (or on demand), strips the sponsor feature, builds the
frontend and a static CGO binary, asserts `GET /` = 200 and `GET /sponsors` = 404, then publishes a
release. See [GUIDE.md](GUIDE.md).

## License

Derivative distribution of 3X-UI under **GPL-3.0** (`LICENSE`); upstream copyrights are retained.
Change notice: `NOTICE.md`. Apart from the license, there is no relationship with the upstream author.
