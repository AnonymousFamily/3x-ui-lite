# Changelog

## v3.11.0-nosponsor — 2026-11-19

基于上游 `v3.11.0`（commit `c621ba9`）的首个发布。

**删除（仅赞助商广告链路）**

- 后端：`internal/web/service/panel/sponsor.go` 及测试 —— 远程 `sponsors.json` 拉取、
  1 小时缓存、logo 代理全部移除；面板不再向赞助商仓库发起任何请求
- 后端：路由 `GET /sponsors`、`GET /sponsors/logo/:name` 及对应 handler
- 前端：`pages/sponsors/`、`components/sponsor/`、`lib/sponsors.ts`、`useSponsorsQuery.ts`
- 前端：登录页与仪表盘的 `<SponsorSlot>` 广告位
- 导航：侧边栏、命令面板、页面标题、路由中的「赞助商」入口
- 文案：14 个语言包的 `menu.sponsors`、`pages.sponsors.*`
- 生成物：TS 类型与 OpenAPI 重新生成（无 `Sponsor` schema、无 `/sponsors` 路径）

**保留**

- 侧边栏 `Donate` 按钮、MTProto `ad-tag`、面板更新检查，以及全部其他功能

**构建**

- 前端：Vite 构建后内嵌进二进制
- 后端：`CGO_ENABLED=1` 静态链接（`netgo` / `osusergo` / `sqlite_omit_load_extension`），
  产物 BuildID `0c3bb171…`
- 包内附带 Xray 26.10.21、mtg-multi 1.16.1、geoip/geosite

**验证**

- 冒烟：`GET /` = 200、`GET /sponsors` = 404
- 覆盖升级：沿用原 `/etc/x-ui/x-ui.db`，账号与节点不变
- 实机：Oracle Linux（SELinux Enforcing + 旧 drop-in）修复后正常运行

---

> 之后的版本由 `.github/workflows/build-nosponsor.yml` 自动生成；
> 上游每次发版都会得到对应条目（格式：`v<上游版本>-nosponsor`）。
