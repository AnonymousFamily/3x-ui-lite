# 3X-UI Lite — 去赞助商版本

**独立维护**的 3X-UI 面板构建：功能与上游一致，只移除付费赞助商广告位。
上游每次发布新版本，本仓库会自动构建去赞助商版本并发布 Release。

> 本项目与上游作者无隶属、无背书关系。上游采用 GPL-3.0，本项目依法保留其版权声明与许可证
> （见 `LICENSE`、`NOTICE.md`），除此之外无其他关联。

|  |  |
| --- | --- |
| 上游项目 | [MHSanaei/3x-ui](https://github.com/MHSanaei/3x-ui)（GPL-3.0） |
| 当前版本 | [v3.11.0-nosponsor](https://github.com/AnonymousFamily/3x-ui-lite/releases/tag/v3.11.0-nosponsor) |
| 许可证 | GPL-3.0，见 [LICENSE](LICENSE) 与 [NOTICE.md](NOTICE.md) |
| 支持平台 | Linux x86_64（amd64）+ systemd |

---

## 1. 这是什么

上游 3X-UI 从 v3.10 起加入付费赞助位：登录页与仪表盘各有一张广告卡，侧边栏多一个「赞助商」页面，
内容由 `raw.githubusercontent.com/MHSanaei/sponsors` 远程拉取，并带 1 小时缓存和 logo 代理。

本版本把这条链路整体删除：

- **后端**：删除 `internal/web/service/panel/sponsor.go`（远程拉取、缓存、logo 代理），
  移除 `GET /sponsors` 与 `GET /sponsors/logo/:name` 两条公开路由及处理函数。
  → 面板不再向赞助商仓库发起任何请求。
- **前端**：删除赞助商页面、卡片组件、查询与工具函数；摘掉登录页、仪表盘的广告位；
  删除侧边栏、命令面板、页面标题里的「赞助商」入口。
- **文案**：14 个语言包中删除 `menu.sponsors` 与 `pages.sponsors.*`。
- **生成物**：重新生成 TypeScript 类型与 OpenAPI（无 `Sponsor` schema、无 `/sponsors` 路径）。

**没有删任何其他功能。** 以下内容原样保留，且经逐处核对：

| 保留项 | 说明 |
| --- | --- |
| 侧边栏 `Donate` 按钮 | 指向 `donate.sanaei.dev`，是捐赠入口，不属于赞助位 |
| MTProto `ad-tag` | Telegram 赞助频道标签，属于客户端功能 |
| 面板更新检查 | 只读查询版本，不会覆盖文件 |
| 全部协议 / 订阅 / 多节点 / 通知 / 路由 / 出站 | 与上游 v3.11.0 完全一致 |

数据完全兼容：直接沿用原 `/etc/x-ui/x-ui.db`，账号、节点、客户端、设置无需迁移。

---

## 2. 一键安装

```bash
curl -fsSL https://cdn.jsdelivr.net/gh/AnonymousFamily/3x-ui-lite@main/install-lite.sh | sudo bash
```

脚本会依次：检查架构 → 下载 Release（直连失败自动切 gh-proxy / ghproxy 镜像）→ 校验 SHA256 →
停旧服务 → 备份旧二进制 → 解压到 `/usr/local/x-ui` → `restorecon` 修正 SELinux 标签 →
移走旧版 systemd drop-in → 安装 unit 并启动 → 从日志读出真实端口与协议，打印访问地址。

> 安装到哪个版本：脚本列出所有 `v*-nosponsor` Release，**按版本号取最高**（不是「最近发布」），
> 避免补发旧版本时误装。

### 可选参数

| 参数 | 作用 |
| --- | --- |
| `--port N` | 安装后把面板端口改为 N |
| `--dir PATH` | 安装目录（默认 `/usr/local/x-ui`） |
| `--no-start` | 只铺文件，不 enable/start |
| `--uninstall` | 卸载（保留 `/etc/x-ui` 数据） |
| `--uninstall --purge` | 卸载并删除数据库与日志 |
| `--prefix PATH` | 测试用：装到指定目录，不需要 root/systemd |

固定版本（不跟随最高版）：

```bash
curl -fsSL https://cdn.jsdelivr.net/gh/AnonymousFamily/3x-ui-lite@main/install-lite.sh \
  | sudo XUI_RELEASE_TAG=v3.11.0-nosponsor bash
```

> `raw.githubusercontent.com` 在部分网络下会超时，所以上面的链接用 jsDelivr CDN；
> 两者内容一致（同一 commit）。

### 手动安装（离线环境）

从 [Releases](https://github.com/AnonymousFamily/3x-ui-lite/releases) 下载
`3x-ui-<版本>-nosponsor-linux-amd64.tar.gz` 传到服务器，然后：

```bash
tar -xzf 3x-ui-*-nosponsor-linux-amd64.tar.gz
sudo install -d /usr/local/x-ui
sudo cp -a 3x-ui-*-nosponsor/. /usr/local/x-ui/
sudo chmod +x /usr/local/x-ui/x-ui /usr/local/x-ui/bin/* /usr/local/x-ui/x-ui.sh
sudo install -m 755 /usr/local/x-ui/x-ui.sh /usr/bin/x-ui
sudo install -m 644 /usr/local/x-ui/x-ui.service.debian /etc/systemd/system/x-ui.service
sudo systemctl daemon-reload
sudo systemctl enable --now x-ui
```

CentOS / RHEL / Rocky / Alma 用 `x-ui.service.rhel`，Arch 用 `x-ui.service.arch`，其余相同。

### 覆盖已有的官方安装

不用重装，只换二进制，数据保留：

```bash
sudo systemctl stop x-ui
sudo cp -a /usr/local/x-ui /root/x-ui-backup-$(date +%F)
sudo cp x-ui /usr/local/x-ui/x-ui && sudo chmod +x /usr/local/x-ui/x-ui
sudo systemctl start x-ui
```

---

## 3. 装好之后

### 3.1 拿登录账号

全新安装会随机生成管理员，只打印一次：

```bash
sudo journalctl -u x-ui -n 50 --no-pager | grep -i "Username:"
```

覆盖安装则沿用原数据库里的账号。忘记密码：`sudo x-ui` → 菜单 `7` 重置。

### 3.2 打开面板

```bash
sudo x-ui settings
# port: 2053
# webBasePath: /kor/
# Access URL: https://域名:2053/kor/
```

默认端口 2053、默认路径 `/`；装了证书就是 `https://`。
如果根路径返回 404，说明设置了 `webBasePath`，要访问 `https://IP:端口/<basePath>/`。

### 3.3 放行端口

```bash
sudo ufw allow 2053/tcp                      # Debian/Ubuntu
sudo firewall-cmd --permanent --add-port=2053/tcp && sudo firewall-cmd --reload   # RHEL 系
```

云服务器还要在控制台安全组放行面板端口与后续入站端口。

### 3.4 添加节点

面板 → `入站列表` → `添加入站`（协议、端口、传输、TLS）→ 保存 →
`客户端` 添加用户 → 复制链接 / 二维码 / 订阅。

### 3.5 面板 HTTPS（可选）

`sudo x-ui` → 菜单 `20` 申请证书并写入面板设置；或在面板 `Settings` 直接填已有证书路径。

---

## 4. 升级

**面板内更新**：版本检查已改为查询**本仓库**的 Release。上游发新版 → 本仓库自动产出
`v<版本>-nosponsor` → 面板提示有更新 → 点「更新面板」即下载并安装本仓库的包
（`update-lite.sh`：校验 SHA256、备份旧二进制、重启服务）。不会安装上游版本。

**命令行升级**：

```bash
curl -fsSL https://cdn.jsdelivr.net/gh/AnonymousFamily/3x-ui-lite@main/install-lite.sh | sudo bash
```

> 命令行菜单里的 `Install` / `Update` / `Update Menu` / `Legacy` 已禁用（只打印提示并退出），
> 因为它们会去拉上游官方包；面板里的更新按钮走本仓库，不受影响。

---

## 5. 自动构建机制

`.github/workflows/build-nosponsor.yml` 每天 **02:17 UTC（北京 10:17）** 检查上游 Release；
也可在 Actions 页面手动触发并指定上游 tag。

一次构建的步骤：

1. 解析上游最新 tag；若本仓库已有 `v<版本>-nosponsor`，直接跳过（幂等）
2. checkout 上游该 tag 源码
3. 运行 `scripts/strip-sponsors.py` 去赞助商，并**自检**不存在
   `SponsorSlot` / `SponsorCard` / `SponsorsPage` / `SponsorList` / `/sponsors` 残留
4. 运行 `scripts/harden-menu.py` 加固 `x-ui.sh`：禁用 `install` / `update` / `update_dev` /
   `update_menu` / `legacy_version` 五个入口，发布包里不会再一键装回官方版
5. `npm ci` → `npm run gen:zod` → `npm run build`（前端）
5. `CGO_ENABLED=1 go build` 静态编译（`netgo` / `osusergo` / `sqlite_omit_load_extension`）
6. **运行期冒烟**：启动面板，断言 `GET /` = 200 且 `GET /sponsors` = 404，否则构建失败
7. 下载 Xray 内核、mtg-multi、geoip/geosite，打包
8. 创建 Release，附 tarball、源码 patch、SHA256SUMS

### 为什么用脚本而不是 patch

补丁按行匹配，上游一动赞助商代码就冲突；脚本做的是语义删除：

| 上游变化 | 结果 |
| --- | --- |
| 赞助商代码没变 | 正常删除、出包 |
| 上游自己删了赞助商 | 脚本空操作，自检通过，照常出包 |
| 赞助商被改名/重构 | 自检失败，job 红叉并列出残留文件，更新脚本匹配规则即可 |

---

## 6. 自己构建

```bash
git clone --depth 1 --branch v3.11.0 https://github.com/MHSanaei/3x-ui.git /tmp/src
python3 scripts/strip-sponsors.py /tmp/src
cd /tmp/src/frontend && npm ci && npm run gen:zod && npm run build
cd /tmp/src
CGO_ENABLED=1 go build -trimpath -buildvcs=false \
  -tags "netgo osusergo sqlite_omit_load_extension" \
  -ldflags="-w -s -linkmode external -extldflags '-static'" -o x-ui .
```

要求：Go（版本见上游 `go.mod`）、Node（见 `.nvmrc`）、gcc（SQLite 驱动需要 CGO，
`CGO_ENABLED=0` 无法构建）。改动 14 个翻译 JSON 后必须重建前端，因为它会被 Vite 直接打进 JS。

---

## 7. 验证记录

| 项目 | 结果 |
| --- | --- |
| 上游 v3.11.0 全流程 | 转换 34 项 → 构建 → 冒烟 200/404 |
| 产物一致性 | BuildID `0c3bb171…`，与手工发布的二进制完全相同 |
| 上游 v3.10.2（旧前端结构） | 转换 36 项 → 构建 → 冒烟 200/404 |
| 上游 main（`5297fd3`） | 转换 33 项、Go 编译通过 |
| GitHub Actions 实跑 | run #4 全绿（14 步），产出 `v3.10.2-nosponsor` 后已删除 |
| 静态链接 | `statically linked`，无 glibc / NSS 依赖 |

---

## 8. 常见问题

**服务反复重启，日志 `status=203/EXEC`**
systemd 无法执行文件，常见于 SELinux（RHEL / Oracle Linux）：

```bash
ls -Z /usr/local/x-ui/x-ui        # 若显示 user_tmp_t 就是它
sudo restorecon -Rv /usr/local/x-ui
sudo systemctl reset-failed x-ui && sudo systemctl restart x-ui
```

**服务反复重启，`status=2/INVALIDARGUMENT`**
旧版官方安装留下的 drop-in 与新二进制冲突：

```bash
sudo mv /etc/systemd/system/x-ui.service.d ~/x-ui-dropin.bak
sudo systemctl daemon-reload && sudo systemctl reset-failed x-ui && sudo systemctl restart x-ui
```

**面板 404**
设置了 `webBasePath`，访问 `https://IP:端口/<basePath>/`；`x-ui settings` 可查。

**端口不是 2053**
旧安装可能用了随机端口，升级会沿用。`journalctl -u x-ui | grep "Web server running"` 看真实端口。

**忘记密码**：`sudo x-ui` → `7`。
**Xray 未运行**：`systemctl status x-ui`、`journalctl -u x-ui -n 100`、`ls -l /usr/local/x-ui/bin/`、`sudo x-ui restart-xray`。

---

## 9. 文件说明

发布包内容：

| 文件 | 说明 |
| --- | --- |
| `x-ui` | 面板主程序（静态链接，前端已内嵌） |
| `bin/xray-linux-amd64` | Xray 内核，面板按此文件名查找 |
| `bin/mtg-linux-amd64` | MTProto sidecar（mtg-multi） |
| `bin/geoip.dat`、`bin/geosite.dat` | geo 规则数据 |
| `x-ui.sh` | 管理脚本（安装到 `/usr/bin/x-ui`） |
| `x-ui.service.debian` / `.arch` / `.rhel` | systemd unit |

仓库结构：

```
.github/workflows/build-nosponsor.yml   自动构建流水线
scripts/strip-sponsors.py               去赞助商转换脚本（含自检）
install-lite.sh                         一键安装/卸载脚本
GUIDE.md                                本文档
NOTICE.md                               改动声明（GPL 要求）
```

---

## 10. 许可证与声明

本项目基于 [MHSanaei/3x-ui](https://github.com/MHSanaei/3x-ui)（GPL-3.0）修改，
遵循 GPL-3.0 发布，版权归上游作者所有；改动范围见 [NOTICE.md](NOTICE.md)。

**非官方构建**，与上游作者无关，请勿据此向上游报告问题。
上游的功能文档与安装命令见[上游仓库](https://github.com/MHSanaei/3x-ui)，其安装命令不要照用。
