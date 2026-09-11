# 发布清单（Release Checklist）

## 第一次发布到 PyPI 完整流程 / First-Time Publish to PyPI Complete Flow

### Step 1：注册账号（一次性）/ Step 1: Register Accounts (One-Time)

1. 注册 [PyPI](https://pypi.org/account/register/)（生产环境）
   Register [PyPI](https://pypi.org/account/register/) (production)
2. 注册 [TestPyPI](https://test.pypi.org/account/register/)（预发环境）
   Register [TestPyPI](https://test.pypi.org/account/register/) (staging)
3. 在两个账号都启用 **2FA**
   Enable **2FA** on both accounts
4. **不需要** 传统 API token —— 2026 年用 **Trusted Publishing**（OIDC），更安全
   **No** traditional API token needed — use **Trusted Publishing** (OIDC) in 2026, more secure

### Step 2：配置 Trusted Publishing（GitHub Actions）/ Step 2: Configure Trusted Publishing (GitHub Actions)

在 PyPI 项目页面配置（项目创建后）：
Configure on PyPI project page (after project is created):

1. 创建项目：[https://pypi.org/manage/project/pandaone-guard/](https://pypi.org/manage/project/pandaone-guard/)
   Create project: [https://pypi.org/manage/project/pandaone-guard/](https://pypi.org/manage/project/pandaone-guard/)
   - 第一次发布需要先手动上传一次（见 Step 3）来创建项目
     First publish requires manual upload (see Step 3) to create project
   - 或者用 PyPI 的 **PEP 691 / API** 创建
     Or use PyPI's **PEP 691 / API** to create
2. 进入项目 → **Publishing** → **Add a new pending publisher**
   Go to project → **Publishing** → **Add a new pending publisher**
3. 选择 **GitHub Actions**
   Select **GitHub Actions**
4. 填写 / Fill in：
   Fill in:
   - Owner: `你的 GitHub 用户名` / `Your GitHub username`
   - Repository: `Pandaone AI Agent`
   - Workflow filename: `publish.yml`
   - Environment name: `Any`（如果页面没有 Environment 字段，保持留空）
     `Any` (if no Environment field on page, leave blank)

### Step 3：第一次手动上传（创建项目）/ Step 3: First Manual Upload (Create Project)

```bash
# 仅第一次需要——创建 PyPI 项目记录
# Only needed once — to create the PyPI project record
pip install --upgrade twine build
python -m build --no-isolation
twine upload dist/pandaone_guard-0.7.2-py3-none-any.whl dist/pandaone_guard-0.7.2.tar.gz
# 输入 username + password（启用 2FA 后用 token）
# Enter username + password (after enabling 2FA, use token)
```

之后所有发布都用 Trusted Publishing，**不需要手动输入凭证**。
All subsequent publishes use Trusted Publishing, **no manual credentials needed**.

### Step 4：后续发布（自动化）/ Step 4: Subsequent Publishes (Automated)

```bash
git tag v0.7.2
git push origin v0.7.2
# GitHub Actions 自动：
# GitHub Actions auto:
#   1. 跑测试（确保 340 个全过）
#      Run tests (ensure all 340 pass)
#   2. build wheel + sdist
#   3. twine upload（OIDC 无 token）
#      twine upload (OIDC, no token)
#   4. 创建 GitHub Release
#      Create GitHub Release
```

### Step 5：TestPyPI 干跑（可选，推荐）/ Step 5: TestPyPI Dry Run (Optional, Recommended)

发布前先验证 PyPI 页面渲染正常：
Verify PyPI page renders correctly before publishing:

```bash
twine upload --repository testpypi dist/*
# 在 https://test.pypi.org/project/pandaone-guard/ 预览页面
# Preview page at https://test.pypi.org/project/pandaone-guard/
```

---

## 发布前的本地检查清单 / Pre-Publish Local Checklist

### ✅ 代码质量 / Code Quality

```bash
# 1. 跑全部测试
# Run all tests
pytest tests/ -v
# 期望：340 passed
# Expected: 340 passed

# 2. 验证 CLI 命令完整
# Verify CLI commands are complete
pandaone --version
pandaone --help
pandaone init --help
pandaone write --help
pandaone log --help
pandaone status --help
pandaone install-hook --help
pandaone watch --help
pandaone install-git --help
pandaone ci --help
pandaone-mcp  # MCP server stdio JSON-RPC

# 3. 验证 wheel + sdist 能正常构建
# Verify wheel + sdist build correctly
python -m build --no-isolation
ls dist/  # 应看到 .whl + .tar.gz
              # Should see .whl + .tar.gz
```

### ✅ 跨平台兼容性 / Cross-Platform Compatibility

- ✅ `Operating System :: OS Independent` 已在 classifiers
  `Operating System :: OS Independent` is in classifiers
- ✅ 所有依赖是纯 Python（watchdog / openpyxl / python-docx / reportlab / pyyaml）
  All dependencies are pure Python (watchdog / openpyxl / python-docx / reportlab / pyyaml)
- ✅ `py3-none-any.whl` 是跨平台 wheel 格式
  `py3-none-any.whl` is cross-platform wheel format
- ✅ `os.chmod` 跨平台 POSIX（Linux/macOS 支持，Windows 通过 chmod 等价）
  `os.chmod` cross-platform POSIX (Linux/macOS supported, Windows via chmod equivalent)

### ✅ README.md PyPI 渲染 / README.md PyPI Rendering

PyPI 的项目页面显示的是 README.md 内容（需 `long_description_content_type = "text/markdown"`）：
PyPI project page shows README.md content (requires `long_description_content_type = "text/markdown"`):

- ✅ 有项目标题 + 一句话描述 / Project title + one-line description
  Has project title + one-line description
- ✅ 有 shields.io 徽章（版本/license/Python/测试状态）
  Has shields.io badges (version/license/Python/test status)
- ✅ 有安装命令 / Install command
  Has install command
- ✅ 有快速开始示例 / Quick start example
  Has quick start example
- ✅ 有功能列表 / Feature list
  Has feature list
- ✅ 有 license（MIT）
  Has license (MIT)

### ✅ 元数据完整 / Metadata Complete

pyproject.toml 已包含：
pyproject.toml already includes:

- ✅ name / version / description
- ✅ readme = "README.md"
- ✅ license = "MIT"
- ✅ authors + email
- ✅ requires-python = ">=3.8"
- ✅ keywords
- ✅ 14 classifiers
- ✅ 5 dependencies（核心）/ 5 dependencies (core)
- ✅ 3 console_scripts（pandaone / pandaone-watchdog / pandaone-mcp）
  3 console_scripts (pandaone / pandaone-watchdog / pandaone-mcp)
- ✅ optional-dependencies: dev / download
- ✅ 4 project urls (Homepage/Documentation/Repository/Issues)

### ✅ GitHub Actions workflow

- ✅ `.github/workflows/audit.yml`（已有）— PR 时自动跑审计
  `.github/workflows/audit.yml` (existing) — auto-runs audit on PR
- ✅ `.github/workflows/publish.yml`（待建）— tag 触发自动发布
  `.github/workflows/publish.yml` (to be created) — tag triggers auto-publish

---

## 安装验证（每个新版本都要做的）/ Install Verification (Required for Each New Version)

发布后**立刻**测试安装 / **Immediately** test installation after publishing：
Test installation **immediately** after publishing:

```bash
# 新建临时环境
# Create temporary environment
python -m venv /tmp/pandaone-verify
source /tmp/pandaone-verify/bin/activate  # Windows: Scripts\activate

# 安装（生产）
# Install (production)
pip install pandaone-guard
# 或指定版本
# Or pin version
pip install pandaone-guard==0.7.2

# 验证
# Verify
pandaone --version  # pandaone-guard v0.7.2
pandaone init --help
pandaone init /tmp/test-project
pandaone write --root /tmp/test-project --file test.py \
    --reason "verify install" --problem "test" --approach "test" \
    --content "x = 1\n"

# 测试 MCP server
# Test MCP server
echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}' | pandaone-mcp
```

---

## 发布后 / After Publishing

1. **更新 CHANGELOG.md** 添加新版本
   **Update CHANGELOG.md** to add new version
2. **创建 GitHub Release**（带 changelog 摘要）
   **Create GitHub Release** (with changelog summary)
3. **更新 README.md 中的徽章链接**（shields.io 自动）
   **Update badge links in README.md** (shields.io auto-updates)
4. **如果 breaking change**，更新 README 中的兼容性说明
   **If breaking change**, update compatibility notes in README

---

## 第一性原理 / First Principles

> **发布 = 让任何人都能 1 行命令安装并使用**。
> **Publishing = letting anyone install and use it with 1 command**.
> **Publishing = letting anyone install and use it with 1 command**.
> 一切准备工作（wheel / 签名 / 验证）都为此服务。
> All preparation work (wheel / signing / validation) serves this.

> **信任从文档来**——README 是 PyPI 项目的"门面"，必须让陌生用户 30 秒内理解"这是什么 / 我为什么要用 / 怎么安装"。
> **Trust comes from documentation** — README is the "front door" of a PyPI project; it must let a stranger understand "what is this / why would I use it / how to install" in 30 seconds.

> **自动化从流程来**——Trusted Publishing 消除了"分发凭证给 CI"的信任问题。
> **Automation comes from process** — Trusted Publishing eliminates the trust issue of "distributing credentials to CI".
