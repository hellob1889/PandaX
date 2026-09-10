# 发布清单（Release Checklist）

## 第一次发布到 PyPI 完整流程

### Step 1：注册账号（一次性）

1. 注册 [PyPI](https://pypi.org/account/register/)（生产环境）
2. 注册 [TestPyPI](https://test.pypi.org/account/register/)（预发环境）
3. 在两个账号都启用 **2FA**
4. **不需要** 传统 API token —— 2026 年用 **Trusted Publishing**（OIDC），更安全

### Step 2：配置 Trusted Publishing（GitHub Actions）

在 PyPI 项目页面配置（项目创建后）：

1. 创建项目：[https://pypi.org/manage/project/pandax-guard/](https://pypi.org/manage/project/pandax-guard/)
   - 第一次发布需要先手动上传一次（见 Step 3）来创建项目
   - 或者用 PyPI 的 **PEP 691 / API** 创建
2. 进入项目 → **Publishing** → **Add a new pending publisher**
3. 选择 **GitHub Actions**
4. 填写：
   - Owner: `你的 GitHub 用户名`
   - Repository: `PandaX`
   - Workflow filename: `publish.yml`
   - Environment name: `Any`（如果页面没有 Environment 字段，保持留空）

### Step 3：第一次手动上传（创建项目）

```bash
# 仅第一次需要——创建 PyPI 项目记录
pip install --upgrade twine build
python -m build --no-isolation
twine upload dist/pandax_guard-0.7.1-py3-none-any.whl dist/pandax_guard-0.7.1.tar.gz
# 输入 username + password（启用 2FA 后用 token）
```

之后所有发布都用 Trusted Publishing，**不需要手动输入凭证**。

### Step 4：后续发布（自动化）

```bash
git tag v0.7.1
git push origin v0.7.1
# GitHub Actions 自动：
#   1. 跑测试（确保 340 个全过）
#   2. build wheel + sdist
#   3. twine upload（OIDC 无 token）
#   4. 创建 GitHub Release
```

### Step 5：TestPyPI 干跑（可选，推荐）

发布前先验证 PyPI 页面渲染正常：

```bash
twine upload --repository testpypi dist/*
# 在 https://test.pypi.org/project/pandax-guard/ 预览页面
```

---

## 发布前的本地检查清单

### ✅ 代码质量

```bash
# 1. 跑全部测试
pytest tests/ -v
# 期望：340 passed

# 2. 验证 CLI 命令完整
pandax --version
pandax --help
pandax init --help
pandax write --help
pandax log --help
pandax status --help
pandax install-hook --help
pandax watch --help
pandax install-git --help
pandax ci --help
pandax-mcp  # MCP server stdio JSON-RPC

# 3. 验证 wheel + sdist 能正常构建
python -m build --no-isolation
ls dist/  # 应看到 .whl + .tar.gz
```

### ✅ 跨平台兼容性

- ✅ `Operating System :: OS Independent` 已在 classifiers
- ✅ 所有依赖是纯 Python（watchdog / openpyxl / python-docx / reportlab / pyyaml）
- ✅ `py3-none-any.whl` 是跨平台 wheel 格式
- ✅ `os.chmod` 跨平台 POSIX（Linux/macOS 支持，Windows 通过 chmod 等价）

### ✅ README.md PyPI 渲染

PyPI 的项目页面显示的是 README.md 内容（需 `long_description_content_type = "text/markdown"`）：

- ✅ 有项目标题 + 一句话描述
- ✅ 有 shields.io 徽章（版本/license/Python/测试状态）
- ✅ 有安装命令
- ✅ 有快速开始示例
- ✅ 有功能列表
- ✅ 有 license（MIT）

### ✅ 元数据完整

pyproject.toml 已包含：

- ✅ name / version / description
- ✅ readme = "README.md"
- ✅ license = "MIT"
- ✅ authors + email
- ✅ requires-python = ">=3.8"
- ✅ keywords
- ✅ 14 classifiers
- ✅ 5 dependencies（核心）
- ✅ 3 console_scripts（pandax / pandax-watchdog / pandax-mcp）
- ✅ optional-dependencies: dev / download
- ✅ 4 project urls (Homepage/Documentation/Repository/Issues)

### ✅ GitHub Actions workflow

- ✅ `.github/workflows/audit.yml`（已有）— PR 时自动跑审计
- ✅ `.github/workflows/publish.yml`（待建）— tag 触发自动发布

---

## 安装验证（每个新版本都要做的）

发布后**立刻**测试安装：

```bash
# 新建临时环境
python -m venv /tmp/pandax-verify
source /tmp/pandax-verify/bin/activate  # Windows: Scripts\activate

# 安装（生产）
pip install pandax-guard
# 或指定版本
pip install pandax-guard==0.7.1

# 验证
pandax --version  # pandax-guard v0.7.1
pandax init --help
pandax init /tmp/test-project
pandax write --root /tmp/test-project --file test.py \
    --reason "verify install" --problem "test" --approach "test" \
    --content "x = 1\n"

# 测试 MCP server
echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}' | pandax-mcp
```

---

## 发布后

1. **更新 CHANGELOG.md** 添加新版本
2. **创建 GitHub Release**（带 changelog 摘要）
3. **更新 README.md 中的徽章链接**（shields.io 自动）
4. **如果 breaking change**，更新 README 中的兼容性说明

---

## 第一性原理

> **发布 = 让任何人都能 1 行命令安装并使用**。
> 一切准备工作（wheel / 签名 / 验证）都为此服务。

> **信任从文档来**——README 是 PyPI 项目的"门面"，必须让陌生用户 30 秒内理解"这是什么 / 我为什么要用 / 怎么安装"。

> **自动化从流程来**——Trusted Publishing 消除了"分发凭证给 CI"的信任问题。
