# 自动跟进上游版本

每天自动检查上游 `MHSanaei/3x-ui` 的最新 release，有新版就自动构建「去赞助商」版本并发 release。
不需要手工打补丁，也不用本地编译。

## 它做了什么

`.github/workflows/build-nosponsor.yml`，触发后按顺序：

1. 查上游最新 tag（或手动指定），若本仓库已有 `v<ver>-nosponsor` 的 release 则直接跳过
2. checkout 上游该 tag 的源码
3. 跑 `scripts/strip-sponsors.py`：删赞助商模块、路由、JSX 广告位、导航项、i18n 键、CSS 规则，
   并**自检**没有任何 `SponsorSlot/SponsorCard/SponsorsPage/SponsorList` 或 `/sponsors` 残留
4. `npm ci` → `npm run gen:zod` → `npm run build`（前端）
5. `CGO_ENABLED=1 go build` 静态编译面板
6. **运行期冒烟**：起面板，`/` 必须 200、`/sponsors` 必须 404，否则构建失败
7. 下载 Xray 内核、mtg-multi、geoip/geosite，打 tar.gz
8. 创建 release（附 tarball、源码 patch、SHA256SUMS）

## 手动触发

仓库 → `Actions` → `Build sponsor-free release` → `Run workflow`：

- 留空：构建上游最新 release
- 填 tag（例如 `v3.10.2`）：构建指定版本

首次想验证流水线，可以用一个本仓库还没有的旧 tag（如 `v3.10.2`），不会动到现有的 v3.11.0 release。

## 为什么不用 patch 文件

补丁是「按行上下文」的，上游一改赞助商相关代码就冲突。这里改成**语义化删除 + 自检**：

| 上游变化 | 结果 |
| --- | --- |
| 赞助商代码没变 | 正常删掉，出包 |
| 赞助商功能被上游自己删了 | 脚本变成空操作，自检通过，照常出包 |
| 赞助商被改名/重构（比如 `SponsorX`） | 自检失败并列出残留文件，job 红叉，改脚本匹配规则即可 |

## 需要维护的两处

1. **Xray 版本**：workflow 里 pin 了 `v26.10.21`。上游换内核版本时，改 `Fetch Xray...` 步骤里的一行
   （或改成从上游 `release.yml` 里解析）。
2. **系统依赖**：如果上游新增了语言级依赖（新 Go 版本、新 Node 版本），workflow 用
   `go-version-file: src/go.mod` 和 `node-version-file: src/.nvmrc` 自动跟随，一般不用动。

## 本地复现同一条流水线

```bash
git clone --depth 1 --branch v3.11.0 https://github.com/MHSanaei/3x-ui.git /tmp/src
python3 scripts/strip-sponsors.py /tmp/src
cd /tmp/src/frontend && npm ci && npm run gen:zod && npm run build
cd /tmp/src
CGO_ENABLED=1 go build -trimpath -buildvcs=false \
  -tags "netgo osusergo sqlite_omit_load_extension" \
  -ldflags="-w -s -linkmode external -extldflags '-static'" -o x-ui .
```

## 已验证

- 上游 `v3.11.0`：转换 → 前端构建 → 静态编译 → 冒烟 `/`=200、`/sponsors`=404，
  产物 BuildID 与手工发布的 `x-ui` **完全一致**（`0c3bb171…`）
- 上游 `v3.10.2`（旧版前端结构：`routes.tsx` + 侧边栏图标表 + `usePageTitle` 映射）：
  转换 36 项 → 构建 → 冒烟通过
- 上游最新 `main`（`5297fd3`）：转换 33 项、Go 编译通过
- 自检：无残留标识

## 已知限制

- 只构建 **amd64**；需要 arm64 就在 workflow 里加矩阵（`-tags` 相同，交叉编译需 aarch64 gcc）。
- release 标签是 `v<上游版本>-nosponsor`，与上游 tag 区分，不会覆盖官方发布。
