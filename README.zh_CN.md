# 3X-UI Lite — 去赞助商版

3X-UI 面板的**非官方**构建：功能与上游一致，只删掉付费赞助商广告位。
上游每次发布新版本，本仓库会自动跟随构建并发 Release。

> 与上游作者无关，请勿把本构建的问题报到上游。上游项目：[MHSanaei/3x-ui](https://github.com/MHSanaei/3x-ui)。

|  |  |
| --- | --- |
| 最新版本 | [Releases](https://github.com/AnonymousFamily/3x-ui-lite/releases) |
| 完整说明 | [GUIDE.md](GUIDE.md) |
| 变更记录 | [CHANGELOG.md](CHANGELOG.md) |
| 许可证 | GPL-3.0，见 [LICENSE](LICENSE) 与 [NOTICE.md](NOTICE.md) |
| 支持平台 | Linux x86_64 + systemd |

## 一键安装

```bash
curl -fsSL https://cdn.jsdelivr.net/gh/AnonymousFamily/3x-ui-lite@main/install-lite.sh | sudo bash
```

> 这是**本仓库**的安装脚本。**不要**使用上游 README 里的
> `bash <(curl -Ls .../mhsanaei/3x-ui/master/install.sh)` —— 那会装成官方版本，赞助商广告会回来。

常用参数：

| 用法 | 命令 |
| --- | --- |
| 指定面板端口 | `... | sudo bash -s -- --port 8443` |
| 固定版本 | `... | sudo XUI_RELEASE_TAG=v3.11.0-nosponsor bash` |
| 卸载（保留数据） | `... | sudo bash -s -- --uninstall` |
| 卸载并删数据 | `... | sudo bash -s -- --uninstall --purge` |

脚本会校验 SHA256、备份旧二进制、自动处理 SELinux 标签与旧 systemd drop-in，
并从日志里读出真实端口打印访问地址。

## 变更内容

相对上游对应版本（当前 `v3.11.0`），**只删除赞助商广告链路**：

| 层 | 删除内容 |
| --- | --- |
| 后端服务 | `internal/web/service/panel/sponsor.go`（远程 `sponsors.json` 拉取、1 小时缓存、logo 代理）及测试 |
| 后端路由 | `GET /sponsors`、`GET /sponsors/logo/:name` 及 handler；不再有任何赞助商相关的出站请求 |
| 前端页面 | `frontend/src/pages/sponsors/`（赞助商页 + 样式） |
| 前端组件 | `frontend/src/components/sponsor/`（`SponsorCard`、`SponsorSlot`、故事文件） |
| 前端逻辑 | `frontend/src/lib/sponsors.ts`（slot 过滤、dismiss 存储）、`api/queries/useSponsorsQuery.ts` |
| 广告位 | 登录页、仪表盘的 `<SponsorSlot>` |
| 导航 | 侧边栏/命令面板/页面标题中的「赞助商」入口、`routes` 里的 `/sponsors` |
| 文案 | 14 个语言包的 `menu.sponsors`、`pages.sponsors.*` |
| 生成物 | 重新生成 TS 类型与 OpenAPI（无 `Sponsor` schema、无 `/sponsors` 路径） |

**保留未动**（逐处核对过）：

- 侧边栏 `Donate` 按钮（`donate.sanaei.dev`，捐赠入口，不是赞助位）
- MTProto 的 `ad-tag`（Telegram 赞助频道标签，客户端功能）
- 面板更新检查（只读查版本，不覆盖文件）
- 入站 / 客户端 / 订阅 / 节点 / 主机 / 路由 / 出站 / 通知 / 多节点等全部功能

完整的逐文件补丁：每个 Release 都附带 `nosponsor-v<版本>.patch`。

## 升级

重跑安装命令即可（保留 `/etc/x-ui` 数据，自动备份旧二进制）：

```bash
curl -fsSL https://cdn.jsdelivr.net/gh/AnonymousFamily/3x-ui-lite@main/install-lite.sh | sudo bash
```

> **不要**在面板里点「更新面板」，也不要执行 `x-ui update` —— 那会覆盖成上游官方版本，广告回来。

## 自动构建

- 每天 02:17 UTC 检查上游 Release；有新版本就自动构建
- 也可在 Actions 页手动触发，并指定上游 tag
- 门禁：自检无赞助商标识 → 编译 → 启动后断言 `GET /`=200、`GET /sponsors`=404，任一失败不出包
- 产物：`3x-ui-<版本>-nosponsor-linux-amd64.tar.gz`、`nosponsor-v<版本>.patch`、`SHA256SUMS.txt`

机制与排错细节见 [GUIDE.md](GUIDE.md)，脚本见 `scripts/strip-sponsors.py` 与
`.github/workflows/build-nosponsor.yml`。

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

基于 [MHSanaei/3x-ui](https://github.com/MHSanaei/3x-ui)（GPL-3.0）修改，遵循 GPL-3.0 发布，
版权归上游作者所有；改动范围见 [NOTICE.md](NOTICE.md)。
上游原始说明（含全部功能文档）存档于 [README.upstream.md](README.upstream.md) 与
[README.upstream.zh_CN.md](README.upstream.zh_CN.md)。
