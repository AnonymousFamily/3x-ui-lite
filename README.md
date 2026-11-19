# 3X-UI Lite — sponsor-free build

Unofficial build of the [3X-UI](https://github.com/MHSanaei/3x-ui) panel: same features, with the
paid sponsor placements removed. Every upstream release is rebuilt here automatically.

> Not affiliated with the upstream author. Please do not report issues with this build upstream.

|  |  |
| --- | --- |
| Releases | [github.com/AnonymousFamily/3x-ui-lite/releases](https://github.com/AnonymousFamily/3x-ui-lite/releases) |
| Full guide | [GUIDE.md](GUIDE.md) (Chinese) |
| Changelog | [CHANGELOG.md](CHANGELOG.md) |
| License | GPL-3.0, see [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md) |
| Platform | Linux x86_64 + systemd |

## Install

```bash
curl -fsSL https://cdn.jsdelivr.net/gh/AnonymousFamily/3x-ui-lite@main/install-lite.sh | sudo bash
```

> This is **this repo's** installer. Do **not** use the upstream
> `bash <(curl -Ls .../mhsanaei/3x-ui/master/install.sh)` command — that installs the official
> build and brings the sponsor placements back.

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
| Backend service | `internal/web/service/panel/sponsor.go` (remote `sponsors.json` fetch, 1h cache, logo proxy) and its tests |
| Backend routes | `GET /sponsors`, `GET /sponsors/logo/:name` and handlers — no sponsor-related outbound requests remain |
| Frontend pages | `frontend/src/pages/sponsors/` |
| Frontend components | `frontend/src/components/sponsor/` (`SponsorCard`, `SponsorSlot`, stories) |
| Frontend logic | `frontend/src/lib/sponsors.ts`, `api/queries/useSponsorsQuery.ts` |
| Ad slots | `<SponsorSlot>` on the login page and dashboard |
| Navigation | Sponsors entry in sidebar, command palette, page titles and routes |
| Strings | `menu.sponsors`, `pages.sponsors.*` in all 14 locale files |
| Generated | Regenerated TS types and OpenAPI (no `Sponsor` schema, no `/sponsors` path) |

**Deliberately kept:** the sidebar `Donate` button (a donation link, not a sponsor slot), the
MTProto `ad-tag` (Telegram sponsored-channel tag, a client feature), the read-only update check,
and every other panel feature.

Each release also ships `nosponsor-v<version>.patch` with the exact source diff.

## Upgrade

Re-run the installer (keeps `/etc/x-ui`, backs up the old binary):

```bash
curl -fsSL https://cdn.jsdelivr.net/gh/AnonymousFamily/3x-ui-lite@main/install-lite.sh | sudo bash
```

> Never use "Update panel" inside the UI or `x-ui update` — that replaces this build with the
> upstream one.

## Automation

Daily at 02:17 UTC (and on demand) the workflow resolves the latest upstream release, strips the
sponsor feature, builds the frontend and a static CGO binary, asserts `GET /` = 200 and
`GET /sponsors` = 404, then publishes a release. See [GUIDE.md](GUIDE.md) for details.

## License

Based on [MHSanaei/3x-ui](https://github.com/MHSanaei/3x-ui) (GPL-3.0), redistributed under
GPL-3.0; all upstream copyrights remain with their authors. Change notice: [NOTICE.md](NOTICE.md).
Upstream READMEs are archived as `README.upstream*.md`.
