# 功能与特点

3X-UI Lite 是 **3X-UI 的去赞助商独立发行版**：面板功能与上游 v3.11.0 一致，
只移除付费赞助位；上游每次发版，本仓库自动构建并发布新版本。

> 独立维护，与上游作者无隶属关系。许可证 GPL-3.0（见 [LICENSE](LICENSE) 与 [NOTICE.md](NOTICE.md)）。

---

## 一、面板功能（与上游一致，全量保留）

| 类别 | 能力 |
| --- | --- |
| **协议** | VLESS、VMess、Trojan、Shadowsocks、WireGuard、AmneziaWG、TUIC v5、Hysteria2、MTProto、HTTP、SOCKS(Mixed)、Dokodemo-door / Tunnel、TUN |
| **传输与安全** | TCP(Raw)、mKCP、WebSocket、gRPC、HTTPUpgrade、XHTTP；TLS、XTLS、REALITY |
| **客户端管理** | 流量配额、到期时间、IP 限制（支持信任地址豁免）、HWID 设备数限制、定时自动续期、实时在线状态、一键分享链接 / 二维码 / 订阅 |
| **流量统计** | 按入站、按客户端、按出站统计，支持单独重置 |
| **多节点** | 一个面板管理多台服务器，入站克隆、节点心跳与配置同步 |
| **出站与路由** | WARP、NordVPN、PIA、自定义路由规则、负载均衡（含 balancer 互备）、出站链式代理、geo 分类浏览器 |
| **订阅服务** | 内置 raw / JSON / Clash 输出，按客户端 UA 自动选择，支持自定义订阅页面模板 |
| **通知** | Telegram 机器人、Discord 机器人、邮件通知 |
| **其他** | REST API + OpenAPI 文档、API Token、PostgreSQL 可选、Fail2ban IP 限制、面板 SSL 证书管理、14 种语言界面 |

**相对上游删除的内容（仅赞助商）**：登录页与仪表盘的广告卡、侧边栏「赞助商」页、
`GET /sponsors` 与 logo 代理接口、远程 `sponsors.json` 拉取与缓存。

**明确保留**：侧边栏 `Donate` 捐赠按钮、MTProto `ad-tag`（Telegram 赞助频道标签，客户端功能）、
只读的版本检查。

---

## 二、项目自身的工程特点

| 特点 | 说明 |
| --- | --- |
| **自动跟随上游** | 每 6 小时检查上游 Release；有新版本自动：去赞助商 → 前端构建 → 静态编译 → 冒烟 → 发布 `v<版本>-nosponsor` |
| **语义化去广告** | 用 `scripts/strip-sponsors.py` 按语义删除并自检，而不是打行级补丁 —— 上游重构不会因补丁冲突卡死 |
| **三重门禁** | ① 无赞助商标识残留 ② 完整编译 ③ 启动后断言 `GET /`=200、`GET /sponsors`=404；任一失败不出包 |
| **构建时打补丁** | `harden-menu.py` 给 `x-ui.sh` 加拦截、`apply-lite.py` 把更新逻辑指向本仓库；补丁未生效则构建失败 |
| **一键安装** | SHA256 校验、下载镜像回退、SELinux 标签修复、旧 systemd drop-in 处理、打印含 `webBasePath` 的完整访问地址 |
| **面板内更新** | 版本检查查本仓库 Release；点更新运行 `update-lite.sh`，安装本仓库的去赞助商包 |
| **面板与内核分离** | 面板更新只换面板文件，不动 `bin/`；Xray 版本可随时切换且被保留；`--reset-xray` 恢复随包内核 |
| **防误装官方版** | 上游 `install.sh` / `update.sh` / `deploy` 已移除；菜单 `Install` / `Update` / `Update Menu` / `Legacy` 全部拦截 |
| **独立仓库** | 只保留本项目文档与源码；上游工程文档、文档站、CI 模板、品牌素材均已清理 |

---

## 三、稳定性与可恢复性

- 安装/更新前自动备份旧二进制（`x-ui.bak.<时间戳>`）
- 更新先校验 SHA256 再替换，并把结果写入 `update-status.json` 供面板轮询
- **内核坏了**：面板里切回可用版本，或 `install-lite.sh --reset-xray` 恢复随包内核
- **面板坏了**：重跑安装器即可，数据库 `/etc/x-ui/x-ui.db` 不受影响
- 构建侧有测试兜底：路由契约测试、版本解析单测、启动冒烟断言

---

## 四、边界与限制

1. 只构建 **amd64**；ARM 服务器需要额外交叉编译。
2. 随包内核固定为 **26.10.21**（与面板编译时的 `xray-core` 模块配套）；可自由切换其他版本，但不保证兼容。
3. 面板内更新需要服务器能访问 `api.github.com` 与 `raw.githubusercontent.com`；不通时改用命令行重装。
4. dev 频道已禁用，只跟随本仓库的稳定版。
5. 许可证为 **GPL-3.0**，`NOTICE.md` 保留上游版权声明 —— 这是分发衍生作品的法律前提，与「独立维护」不冲突。

---

## 五、仓库结构

```
README.md / README.en.md   项目说明（安装入口 + 变更清单）
GUIDE.md                   完整使用文档（安装 / 升级 / 机制 / 排错）
FEATURES.md                本文档（功能与特点）
CHANGELOG.md               变更记录
NOTICE.md                  改动声明 + 独立声明
LICENSE                    GPL-3.0
install-lite.sh            一键安装 / 卸载（默认保留内核，--reset-xray 重置）
update-lite.sh             面板内更新（只换面板）
scripts/strip-sponsors.py  去赞助商 + 自检
scripts/harden-menu.py     构建时加固 x-ui.sh
scripts/apply-lite.py      构建时把更新逻辑指向本仓库
.github/workflows/build-nosponsor.yml   自动构建流水线
frontend/ internal/ tools/ 源码
Dockerfile / Makefile      自行构建
```
