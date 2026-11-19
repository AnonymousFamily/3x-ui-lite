# NOTICE — modified build

This repository is an **unofficial modified build** of [3X-UI](https://github.com/MHSanaei/3x-ui).

- Upstream: https://github.com/MHSanaei/3x-ui
- Base version: tag `v3.11.0` (commit `c621ba9`, 2026-10-25)
- Modification date: 2026-11-19
- License: GNU GPL v3 — see [LICENSE](LICENSE). All upstream copyrights remain with
  their authors; this repository adds no new restrictions.

## What was changed

Only the paid **sponsor placement** feature was removed. Nothing else was altered.

- Removed `internal/web/service/panel/sponsor.go` (remote `sponsors.json` fetch with
  1-hour cache, logo proxy) and `sponsor_test.go`.
- Removed the public routes `GET /sponsors` and `GET /sponsors/logo/:name` and their
  handlers in `internal/web/controller/index.go`.
- Removed the frontend sponsor page, components, query, helpers and tests
  (`frontend/src/pages/sponsors/`, `frontend/src/components/sponsor/`,
  `frontend/src/lib/sponsors.ts`, `frontend/src/api/queries/useSponsorsQuery.ts`).
- Removed the sponsor slots from the login page and dashboard, the sidebar and command
  palette entries, and the `menu.sponsors` / `pages.sponsors.*` i18n keys in all 14 locales.
- Regenerated `frontend/src/generated/*` and `frontend/public/openapi.json`
  (187 paths, no `Sponsor` schema) and synced `docs/public/openapi.json`.

Kept on purpose: the sidebar **Donate** button (`donate.sanaei.dev`) and the MTProto
**ad-tag** (Telegram sponsored-channel tag) — neither is a sponsor placement.

## Changes / 修改说明（中文）

本仓库是 3X-UI `v3.11.0` 的非官方修改构建，**仅移除付费赞助位**（登录页/仪表盘广告卡、
侧边栏「赞助商」页、`/sponsors` 接口与远程 `sponsors.json` 拉取），其余功能未做任何改动。
侧边栏 Donate 捐赠按钮与 MTProto `ad-tag` 均予保留。许可证仍为 GPLv3。
