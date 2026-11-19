# 3X-UI Lite — 去赞助商版

**独立维护**的 3X-UI 面板构建：功能与上游一致，只删掉付费赞助商广告位。
上游每次发布新版本，本仓库会自动构建去赞助商版本并发布 Release。

> 本项目独立维护，与上游作者**无隶属、无背书、无任何合作关系**，请勿把本构建的问题报到上游。
> 上游 3X-UI 采用 GPL-3.0，本项目作为衍生分发**依法保留其版权声明与许可证**（见 `LICENSE`、`NOTICE.md`），
> 除此之外与上游无其他关联。

|  |  |
| --- | --- |
| 最新版本 | [Releases](https://github.com/AnonymousFamily/3x-ui-lite/releases) |
| 完整说明 | [GUIDE.md](GUIDE.md) |
| 变更记录 | [CHANGELOG.md](CHANGELOG.md) |
| English | [README.en.md](README.en.md) |
| 支持平台 | Linux x86_64 + systemd |

## 一键安装

```bash
curl -fsSL https://raw.githubusercontent.com/AnonymousFamily/3x-ui-lite/main/install-lite.sh | sudo bash
```

> 这是本项目**唯一**的安装入口。不要使用上游 README 或旧安装脚本里的
> `bash <(curl -Ls .../mhsanaei/3x-ui/master/install.sh)` —— 那会装成官方版本，赞助商广告会回来。

> 国内网络访问不了 `raw.githubusercontent.com` 时，在 URL 前加 gh-proxy 前缀：
> `curl -fsSL https://gh-proxy.com/https://raw.githubusercontent.com/AnonymousFamily/3x-ui-lite/main/install-lite.sh | sudo bash`

常用参数：

| 用法 | 命令 |
| --- | --- |
| 指定面板端口 | `... | sudo bash -s -- --port 8443` |
| 固定版本 | `... | sudo XUI_RELEASE_TAG=v3.11.0-nosponsor bash` |
| 卸载（保留数据） | `... | sudo bash -s -- --uninstall` |
| 卸载并删数据 | `... | sudo bash -s -- --uninstall --purge` |

脚本会校验 SHA256、备份旧二进制、处理 SELinux 标签与旧 systemd drop-in，
并从启动日志读出真实端口打印访问地址。

## 变更内容

相对上游对应版本（当前 `v3.11.0`），**只删除赞助商广告链路**：

| 层 | 删除内容 |
| --- | --- |
| 后端服务 | `internal/web/service/panel/sponsor.go`（远程 `sponsors.json` 拉取、1 小时缓存、logo 代理）及测试 |
| 后端路由 | `GET /sponsors`、`GET /sponsors/logo/:name` 及 handler；不再有任何赞助商相关的出站请求 |
| 前端页面 | `frontend/src/pages/sponsors/`（赞助商页 + 样式） |
| 前端组件 | `frontend/src/components/sponsor/`（`SponsorCard`、`SponsorSlot`、故事文件） |
| 前端逻辑 | `frontend/src/lib/sponsors.ts`、`api/queries/useSponsorsQuery.ts` |
| 广告位 | 登录页、仪表盘的 `<SponsorSlot>` |
| 导航 | 侧边栏/命令面板/页面标题/路由中的「赞助商」入口 |
| 文案 | 14 个语言包的 `menu.sponsors`、`pages.sponsors.*` |
| 生成物 | 重新生成 TS 类型与 OpenAPI（无 `Sponsor` schema、无 `/sponsors` 路径） |

**保留未动**：侧边栏 `Donate` 按钮（捐赠入口，不是赞助位）、MTProto `ad-tag`（Telegram 赞助频道标签，
客户端功能）、面板更新检查（只读），以及入站 / 客户端 / 订阅 / 节点 / 主机 / 路由 / 出站 / 通知 / 多节点等全部功能。

每个 Release 附带 `nosponsor-v<版本>.patch`，可逐行核对改动。

## 自动部署

- 每 **6 小时**检查一次上游 Release（也可在 Actions 页手动触发并指定上游 tag）
- 有新版本则自动：去赞助商 → 前端构建 → 静态编译 → 冒烟断言 → 发布 `v<版本>-nosponsor`
- 门禁：自检无赞助商标识、编译通过、运行后 `GET /` = 200 且 `GET /sponsors` = 404，任一失败不出包
- 产物：`3x-ui-<版本>-nosponsor-linux-amd64.tar.gz`、`nosponsor-v<版本>.patch`、`SHA256SUMS.txt`

机制细节见 [GUIDE.md](GUIDE.md)，实现见 `scripts/strip-sponsors.py` 与
`.github/workflows/build-nosponsor.yml`。

## 升级

**面板更新与 Xray 内核更新是分开的两件事**：

- **面板**：面板里的「更新面板」（或重跑下面的命令）只替换面板文件，**不会动 `bin/` 里的 Xray 内核**
- **内核**：在面板的「Xray 版本」里随时切换，所选版本会一直保留，面板升级不会覆盖它
- 想把内核恢复成随包版本：加 `--reset-xray`

```bash
# 只更新面板（保留你选的 Xray 版本）
curl -fsSL https://raw.githubusercontent.com/AnonymousFamily/3x-ui-lite/main/install-lite.sh | sudo bash

# 面板 + 内核一起换回随包版本
curl -fsSL https://raw.githubusercontent.com/AnonymousFamily/3x-ui-lite/main/install-lite.sh | sudo bash -s -- --reset-xray
```

> 命令行菜单里的 `Install` / `Update` / `Update Menu` / `Legacy` 已禁用（它们会拉上游官方包）。
> 面板里的更新按钮走的是本仓库的 Release，可以放心使用。

## 常用命令

| 命令 | 作用 |
| --- | --- |
| `x-ui` | 交互菜单（端口、账号、证书、防火墙…） |
| `x-ui status` / `start` / `stop` / `restart` | 服务状态与启停 |
| `x-ui settings` | 查看端口、webBasePath、访问地址 |
| `x-ui log` | 查看日志 |
| `x-ui restart-xray` | 只重启 Xray |

首次登录账号在启动日志里：

```bash
sudo journalctl -u x-ui -n 50 --no-pager | grep -i Username
```

## 许可证

本项目作为 3X-UI 的衍生分发，遵循 **GPL-3.0**（见 `LICENSE`），保留上游版权声明；
改动范围见 `NOTICE.md`。除许可证要求外，与上游作者无任何关联。
