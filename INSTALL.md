# 安装（一键脚本）

## 支持环境

- Linux **x86_64 / amd64**、systemd
- Ubuntu / Debian / Linux Mint、CentOS / RHEL / Rocky / Alma、Arch
- 需要 root（脚本内部用 sudo 跑）

## 一键安装

```bash
curl -fsSL https://raw.githubusercontent.com/AnonymousFamily/3x-ui-lite/main/install-lite.sh | sudo bash
```

指定面板端口（默认沿用 2053 或原有设置）：

```bash
curl -fsSL https://raw.githubusercontent.com/AnonymousFamily/3x-ui-lite/main/install-lite.sh | sudo bash -s -- --port 8443
```

脚本按顺序做这些事：

1. 检查架构（非 x86_64 直接退出并提示）与 curl
2. 从本仓库 release 下载安装包，**校验 SHA256**（失败即中止）
3. 停掉正在运行的 `x-ui`
4. 把旧二进制备份成 `x-ui.bak.<时间戳>`
5. 铺文件到 `/usr/local/x-ui`（含 `bin/xray-linux-amd64`、`bin/mtg-linux-amd64`、geo 数据）
6. 装 `x-ui` 管理脚本到 `/usr/bin/x-ui`，按发行版选 systemd unit
7. `enable --now` 启动，等 2 秒确认 active
8. 打印面板地址；全新安装时从 journal 抓取随机生成的账号密码

数据始终在 `/etc/x-ui/x-ui.db`，升级不会动它。

## 常见问题

### 服务起不来，日志里是 `status=203/EXEC`

systemd 无法执行 `/usr/local/x-ui/x-ui`，RHEL/Oracle Linux 上几乎都是 SELinux 标签问题：

```bash
ls -Z /usr/local/x-ui/x-ui            # 若显示 user_tmp_t / tmp_t 就是它
sudo restorecon -Rv /usr/local/x-ui
sudo systemctl reset-failed x-ui
sudo systemctl restart x-ui
```

脚本 2026-11-20 之后的版本已改为直接解压到安装目录并执行 `restorecon`，不会再出现。

### 2053 打不开

```bash
sudo ss -lntp | grep 2053
sudo firewall-cmd --add-port=2053/tcp --permanent && sudo firewall-cmd --reload   # RHEL 系
sudo ufw allow 2053/tcp                                                            # Debian 系
```

云服务器还要在控制台安全组放行。

### 服务反复重启，`status=2/INVALIDARGUMENT`

旧版官方安装留下的 `/etc/systemd/system/x-ui.service.d/10-xui-sandbox.conf` 里的
sandbox 参数（`SystemCallFilter` 等）会和本二进制冲突，程序启动即退出：

```bash
sudo mv /etc/systemd/system/x-ui.service.d ~/x-ui-dropin.bak
sudo systemctl daemon-reload
sudo systemctl reset-failed x-ui
sudo systemctl restart x-ui
```

脚本 2026-11-20 之后的版本会自动把旧 drop-in 移到 `.bak`。

### 端口不是 2053

老安装可能用的是随机端口，升级后会沿用。看真实端口：

```bash
sudo journalctl -u x-ui -n 50 --no-pager | grep "Web server running"
sudo x-ui settings | head -20
```

新脚本安装完会直接从日志里读真实端口并打印访问地址。

### 忘记面板账号

`sudo x-ui` → 菜单 `7`（Reset Username & Password）。

### Xray 没运行

```bash
systemctl status x-ui --no-pager
sudo journalctl -u x-ui -n 100 --no-pager
ls -l /usr/local/x-ui/bin/
sudo x-ui restart-xray
```

## 升级

重跑同一条命令即可（会备份旧二进制、保留数据库与设置）。脚本会挑**版本号最高**的 release
（不是「最近发布」的，避免补发旧版本时装错），所以上游出新版后重跑就是升级：

```bash
curl -fsSL https://raw.githubusercontent.com/AnonymousFamily/3x-ui-lite/main/install-lite.sh | sudo bash
```

需要固定在某个版本时指定 tag：

```bash
curl -fsSL https://raw.githubusercontent.com/AnonymousFamily/3x-ui-lite/main/install-lite.sh | sudo XUI_RELEASE_TAG=v3.11.0-nosponsor bash
```

> 不要用面板里的「更新面板」或 `x-ui update`：那会拉上游官方包，赞助商广告会回来。

## 卸载

```bash
# 保留 /etc/x-ui 数据
curl -fsSL https://raw.githubusercontent.com/AnonymousFamily/3x-ui-lite/main/install-lite.sh | sudo bash -s -- --uninstall

# 连数据一起删
curl -fsSL https://raw.githubusercontent.com/AnonymousFamily/3x-ui-lite/main/install-lite.sh | sudo bash -s -- --uninstall --purge
```

## 参数

| 参数 | 作用 |
| --- | --- |
| `--port N` | 安装后把面板端口改为 N |
| `--dir PATH` | 安装目录（默认 `/usr/local/x-ui`） |
| `--no-start` | 只铺文件，不 enable/start 服务 |
| `--prefix PATH` | 测试用：装到指定目录，不写 systemd、不需要 root |
| `--uninstall` | 卸载（默认保留数据） |
| `--purge` | 配合 `--uninstall`，连 `/etc/x-ui`、`/var/log/x-ui` 一起删 |
| `-h, --help` | 帮助 |

## 装完之后

1. 放行面板端口（`ufw allow 8443/tcp` 或 firewalld、云安全组）
2. 打开 `http://服务器IP:端口/`，用打印出的账号登录
3. `入站列表` → 添加入站 → `客户端` 加用户 → 复制链接/订阅
4. 可选：`x-ui` 菜单 `20` 申请证书开 HTTPS

## 自动化

本仓库会每天自动检查上游 `MHSanaei/3x-ui` 的新版本，自动去赞助商、编译并发 release。
想手动跑一次或了解机制，见 [AUTOMATION.md](AUTOMATION.md)。

## 没有网络 / 想手动装

从 [Releases](https://github.com/AnonymousFamily/3x-ui-lite/releases/tag/v3.11.0-nosponsor) 下载
`3x-ui-3.11.0-nosponsor-linux-amd64.tar.gz` 上传到服务器，然后：

```bash
tar -xzf 3x-ui-3.11.0-nosponsor-linux-amd64.tar.gz
sudo install -d /usr/local/x-ui
sudo cp -a 3x-ui-3.11.0-nosponsor/. /usr/local/x-ui/
sudo chmod +x /usr/local/x-ui/x-ui /usr/local/x-ui/bin/* /usr/local/x-ui/x-ui.sh
sudo install -m 755 /usr/local/x-ui/x-ui.sh /usr/bin/x-ui
sudo install -m 644 /usr/local/x-ui/x-ui.service.debian /etc/systemd/system/x-ui.service
sudo systemctl daemon-reload && sudo systemctl enable --now x-ui
```
