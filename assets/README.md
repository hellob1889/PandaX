# 项目素材 (Marketing & Documentation Assets)

本目录存放项目对外展示用的视觉素材、营销内容、文档配图与辅助脚本。**不是运行时依赖**，可以被独立删除而不影响项目功能。

---

## 目录结构

```
assets/
├── README.md                          ← 本文件
│
├── ── 预存项目素材(已纳入版本控制) ──
├── banner-readme.svg                  ← README 顶部 banner
├── favicon.svg                        ← 网站 favicon
├── icon-github.svg / icon-pypi.svg    ← 平台徽章
├── pandax_locked.ico / pandax_unlocked.ico   ← Windows 右键菜单图标
│   └── *.preview.png                  ← 图标预览图
├── quick-demo.svg                     ← Quick Demo 流程图
├── social-preview.png / social-preview.svg  ← 社交媒体分享预览
├── preview.html                       ← 通用预览页骨架
├── preview-server.py                  ← 预览启动脚本
├── render_social.py                   ← 社交预览渲染脚本
│
├── ── 营销活动素材(2026-01 本次新增) ──
├── dashboard.png                      ← Quick Demo 实拍截图(1440×900, 15 条审计记录)
├── pandaone-agent-2026/               ← 小红书推广图文(HTML 预览 + 4 张图卡 + 生成脚本)
└── wechat-pandaone-2026/              ← 公众号介绍帖(HTML 预览 + 正文 + 配图)
│
└── ── 历史预览归档(只读快照) ──
    └── preview/
        ├── folder_states_simulation.png
        ├── icons_locked_sizes.png
        ├── icons_unlocked_sizes.png
        └── ui_dashboard_preview.png
```

---

## 各文件用途详解

### 预存项目素材

| 文件 | 用途 | 备注 |
|------|------|------|
| `banner-readme.svg` | 项目主页顶部视觉 banner | 跟随 README.md 同步更新 |
| `favicon.svg` | 浏览器标签图标 | 16×16 / 32×32 |
| `icon-github.svg` / `icon-pypi.svg` | 平台徽章 | 用于 README 链接装饰 |
| `pandax_locked.ico` / `pandax_unlocked.ico` | Windows 右键菜单图标 | **文件名保留 PandaX 命名**（详见下方"命名约定说明"） |
| `quick-demo.svg` | Quick Demo 流程图 | 用于 README 快速演示区 |
| `social-preview.png` / `.svg` | 社交分享卡片预览 | OG image 标准 1200×630 |
| `preview.html` | 通用 HTML 预览页骨架 | 可复用于新素材预览 |
| `preview-server.py` | 启动本地预览 HTTP 服务器 | `python preview-server.py` |
| `render_social.py` | 社交预览图渲染工具 | 调用 Playwright |

### 营销活动素材

#### `dashboard.png`
Pandaone dashboard 的 Quick Demo 实拍截图，1440×900 PNG。展示：
- **15 条审计记录**（11 APPROVED + 4 REJECTED）
- **3 个不同 agent** 的协作活动（claude-code / cursor / trae）
- L1 锁定状态可视化
- 五层防御模型的实际工作流

**使用场景**：项目 README、官网首页、社交媒体封面图。

**复现方式**：
```bash
# 1. 在任意项目根目录运行
pandaone init --trust-default --silent
pandaone lock --trust-default --silent

# 2. 触发若干 pandaone write 操作产生审计记录
pandaone write --file demo.py --content "..." --force-write --silent

# 3. 启动 dashboard
pandaone serve --port 8765 &

# 4. 用 Playwright 打开 http://127.0.0.1:8765 并截图
```

#### `pandaone-agent-2026/` — 小红书图文

小红书爆款图文的 HTML 预览稿与素材，包含：

| 文件 | 用途 |
|------|------|
| `index.html` | iPhone 真机预览页（信息流 + 详情页） |
| `post/rednote-post.html` | 可发布到小红书的最终图文内容 |
| `images/cover_dashboard.png` | 封面图 |
| `images/card1_what.png` ~ `card4_suits.png` | 正文 4 张图卡（1080×1440） |
| `images/make_cards.py` | 图卡生成脚本（Playwright） |
| `images/preview.py` | 预览截图脚本 |
| `images/inject_args.py` | 内容注入辅助脚本 |
| `preview.png` | 预览截图，用于验证布局 |

**标题**：agent 改代码我装了一道闸（15/20 字）

**话题标签**：
`#AI编程助手 #代码审计 #开源工具 #Cursor规则 #AIAgent #效率工具 #程序员的日常 #干货分享 #Cursor #开发者工具`

**预览方式**：用浏览器打开 `index.html`，切换手机竖屏模式（480px 宽）即可看到完整效果。

#### `wechat-pandaone-2026/` — 公众号介绍帖

微信公众号图文的 HTML 预览稿与素材，包含：

| 文件 | 用途 |
|------|------|
| `index.html` | 预览页（可直接打开看效果） |
| `body.html` | 文章正文（内联样式，可粘贴到公众号后台） |
| `assets/dashboard.png` | 文中嵌入的 dashboard 截图 |
| `assets/social-preview.png` | 封面图 |
| `inject_args.py` | 内容注入辅助脚本 |
| `preview.py` | 预览截图脚本 |
| `preview.png` | 预览截图（480×800） |

**标题**：我让 AI 改代码,装了一道闸

**结构**（9 节）：
1. 痛点引子
2. 一个被忽视的事实
3. 把 audit 当成 git commit 一样严肃
4. 5 层防御 · 第一性原理
5. 实测：装一遍，改一次
6. 不吹不黑
7. 适合谁
8. 怎么装
9. 写在最后

**公众号适配要点**：
- 所有样式内联（`<h1>`-`<h6>`/`<style>` 块会被微信后台过滤）
- 关键句用 `<strong>` + 颜色高亮
- 代码块用 `<pre>` 内联样式
- 图片用绝对 URL 或 base64（部署到 CDN 后替换）

### 历史预览归档 (`preview/`)

只读的早期预览快照，保留作为视觉迭代对比基准。如需替换为新版预览图，直接覆盖即可。

---

## 命名约定说明

### 为什么图标文件名是 `pandax_*.ico` 而不是 `pandaone_*.ico`？

**这是有意的向后兼容决策，不是漏修。**

`src/pandaone/desktop_icon.py:5` 明确注释：

> `IconFile=pandax_locked.ico` 引用 ICO 文件(相对或绝对路径,**文件名保留 PandaX 兼容命名**)

Windows 右键菜单安装器会在注册表写入：
```
HKCR\*\shell\pandaone_lock\Icon=pandax_locked.ico
```

如果重命名 ICO 文件，**已安装用户的右键菜单会显示缺失图标**，必须重装或手动清理注册表才能恢复。在产品改名阶段（PandaX → Pandaone），保留二进制资产文件名是比用户感知一致更重要的工程取舍。

**同样的命名约定也适用于**：
- `PANDAX_LANG` 环境变量（`src/pandaone/i18n.py:805+`）—— 用户/CI 可能已在 shell profile 中设置
- `PANDAX_FP_PASSWORD` 环境变量（`src/pandaone/cli.py:326+`）—— 用于生产部署密码覆盖

这两个环境变量也保持 PANDAX 前缀以避免破坏现有用户配置。

---

## 更新策略

每次发布新版 Pandaone 时（如 0.8.0、0.9.0），建议同步更新：

1. `dashboard.png` — 反映新功能
2. `pandaone-agent-2026/` — 替换封面与图卡
3. `wechat-pandaone-2026/` — 同步文章正文

素材迭代与代码 release 节奏对齐，但**不需要每个 PR 都更新**。

---

## 不应提交到 git 的内容

如果你扩展本目录，请确保以下内容**不**被 git 追踪：
- 截图时的本地临时文件（如 `*.tmp.png`）
- 编辑中的草稿（如 `draft-*.html`）
- 大体积未压缩原图（如直接来自录屏的视频帧，建议压缩到 < 500KB）
- 任何包含真实个人信息的截图（审核记录、用户名等敏感数据）

当前 `.gitignore` 已通过 `assets/` 子目录的精确 `git add` 模式避免误提交，但若新增子目录请保持 `git status` 检查习惯。

---

## 体积检查

```bash
# 查看 assets/ 总大小
du -sh assets/

# 查看各子目录大小
du -sh assets/*/  assets/*.*
```

如果某个素材超过 1 MB（如未经压缩的截图），建议先优化再提交：
```bash
# PNG 压缩（需 ImageMagick）
mogrify -strip -define png:compression-level=9 assets/dashboard.png
```
