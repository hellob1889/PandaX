# PandaX v0.7.2 — Release Notes

**Release date**: 2026-09-10
**Status**: Stable
**Python**: 3.8+
**Platforms**: Windows / macOS / Linux

---

## 🎯 What's New / 新版本亮点

PandaX v0.7.2 是 v0.7.1 之后的 **CI 发布工程化补丁版本**。重点是修复 `publish.yml` workflow 中 Tests job 在干净 ubuntu-latest 容器里 25 秒内 exit 1 的问题，并加入 pytest log 上传以便未来失败可诊断。
PandaX v0.7.2 is a **CI release engineering patch version** following v0.7.1. It focuses on fixing the issue where the Tests job in the `publish.yml` workflow exits with code 1 within 25 seconds on a clean ubuntu-latest container, and adds pytest log upload for future failure diagnostics.

## 🐛 Bug 修复 / Bug Fixes

### CI 工程化 / CI Engineering

- **CI Tests job 25 秒 exit 1**
  **CI Tests job exits 1 within 25 seconds**
  → 根因：test job 没 pin setuptools 版本，build-isolation 拉到的 setuptools 与 build job 不一致，`pip install -e .[dev]` 阶段 metadata 解析失败
  → Root cause: the test job didn't pin setuptools version; the setuptools pulled by build-isolation was inconsistent with the build job, causing metadata parsing failure during `pip install -e .[dev]`
  → 修复：pin `setuptools==80.10.2` + `pip install -e .[dev] --no-build-isolation`，与 build 步骤对齐
  → Fix: pin `setuptools==80.10.2` + `pip install -e .[dev] --no-build-isolation`, aligned with the build step

### 验证 / Verification

- **v0.7.1 publish run** (34429112009): Build ✅ / Tests ❌ / Publish ✅
- **v0.7.2 publish run** (34430629959): Build ✅ / Tests ✅ / Publish ✅ (TestPyPI publish 失败是因为 TestPyPI 上没注册 Trusted Publisher，与本版本无关)
  (TestPyPI publish failure is because the Trusted Publisher is not registered on TestPyPI, unrelated to this version)

## 🆕 新增 / New Features

- **pytest log artifact 上传 / pytest log artifact upload**：CI 测试失败时 `tee /tmp/pytest.log` + `actions/upload-artifact@v4`，artifact 名 `pytest-log-{run_id}`
  When CI tests fail: `tee /tmp/pytest.log` + `actions/upload-artifact@v4`, artifact name `pytest-log-{run_id}`
- **continue-on-error + 显式 fail step / explicit fail step**：解耦"上传日志"与"标红"，下次 CI 失败可以直接从 artifact 下载完整 pytest 输出
  Decouples "uploading logs" from "marking red"; next time CI fails, full pytest output can be downloaded directly from the artifact
- **本地版本号一致性保障 / local version consistency guarantee**：清掉 `src/pandax.egg-info` 和 `src/pandax_guard.egg-info` 残留（之前会污染 `importlib.metadata.version()`）
  Clear residual `src/pandax.egg-info` and `src/pandax_guard.egg-info` (previously polluted `importlib.metadata.version()`)

## 📦 安装 / Installation

### pip（推荐 / Recommended）

```bash
pip install pandax-guard==0.7.2
```

### 升级 / Upgrade

```bash
pip install --upgrade pandax-guard
```

### 源码开发模式 / Source Dev Mode

```bash
git clone https://github.com/hellob1889/PandaX.git
cd PandaX
pip install -e .[dev]
```

## 🛡️ 安全声明 / Security Statement

v0.7.2 与 v0.7.1 行为完全一致（仅修复 CI）。所有 v0.7.1 的对抗式审查结论保持：
v0.7.2 is fully consistent with v0.7.1 in behavior (only CI is fixed). All v0.7.1 adversarial review conclusions are preserved:
- 所有用户输入路径都通过 AST 复查确认 try/except 正确
  All user-input paths have AST-review-confirmed correct try/except
- 所有 subprocess.run 都加 TimeoutExpired
  All subprocess.run calls include TimeoutExpired
- 所有 JSON 序列化都使用 json.dumps 而非 f-string
  All JSON serialization uses json.dumps instead of f-string
- 所有国际化字符串都通过 t() 而非硬编码
  All internationalized strings go through t() instead of being hardcoded

## 🐞 已知问题 / Known Issues

- **P3**: `_DEFAULT_FP_PASSWORD = "0000"` 是演示默认值，**生产环境必须用环境变量覆盖**（已有测试守门）
  `_DEFAULT_FP_PASSWORD = "0000"` is a demo default value, **production environments MUST override via environment variable** (already guarded by tests)
- **TestPyPI Trusted Publisher 未配置 / TestPyPI Trusted Publisher not configured**：如果未来要发 `-test` tag，需要先在 test.pypi.org 注册 pending publisher（当前未注册）
  If `-test` tags need to be published in the future, register the pending publisher on test.pypi.org first (currently unregistered)

## 🤝 贡献 / Contributing

欢迎提交 Issue 和 PR：
Issues and PRs are welcome:
- 仓库 / Repository: https://github.com/hellob1889/PandaX
- 文档 / Documentation: [README.md](README.md)
- 审计防御层 / Audit Defense Layers: 7 层（L1 file chmod → L7 CI）
  7 layers (L1 file chmod → L7 CI)

## 📝 License

MIT
