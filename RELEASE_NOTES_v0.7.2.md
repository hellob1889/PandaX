# PandaX v0.7.2 — Release Notes

**Release date**: 2026-09-10
**Status**: Stable
**Python**: 3.8+
**Platforms**: Windows / macOS / Linux

---

## 🎯 What's New

PandaX v0.7.2 是 v0.7.1 之后的 **CI 发布工程化补丁版本**。重点是修复 `publish.yml` workflow 中 Tests job 在干净 ubuntu-latest 容器里 25 秒内 exit 1 的问题，并加入 pytest log 上传以便未来失败可诊断。

## 🐛 Bug 修复

### CI 工程化

- **CI Tests job 25 秒 exit 1**
  → 根因：test job 没 pin setuptools 版本，build-isolation 拉到的 setuptools 与 build job 不一致，`pip install -e .[dev]` 阶段 metadata 解析失败
  → 修复：pin `setuptools==80.10.2` + `pip install -e .[dev] --no-build-isolation`，与 build 步骤对齐

### 验证

- **v0.7.1 publish run** (34429112009): Build ✅ / Tests ❌ / Publish ✅
- **v0.7.2 publish run** (34430629959): Build ✅ / Tests ✅ / Publish ✅ (TestPyPI publish 失败是因为 TestPyPI 上没注册 Trusted Publisher，与本版本无关)

## 🆕 新增

- **pytest log artifact 上传**：CI 测试失败时 `tee /tmp/pytest.log` + `actions/upload-artifact@v4`，artifact 名 `pytest-log-{run_id}`
- **continue-on-error + 显式 fail step**：解耦"上传日志"与"标红"，下次 CI 失败可以直接从 artifact 下载完整 pytest 输出
- **本地版本号一致性保障**：清掉 `src/pandax.egg-info` 和 `src/pandax_guard.egg-info` 残留（之前会污染 `importlib.metadata.version()`）

## 📦 安装

### pip（推荐）

```bash
pip install pandax-guard==0.7.2
```

### 升级

```bash
pip install --upgrade pandax-guard
```

### 源码开发模式

```bash
git clone https://github.com/hellob1889/PandaX.git
cd PandaX
pip install -e .[dev]
```

## 🛡️ 安全声明

v0.7.2 与 v0.7.1 行为完全一致（仅修复 CI）。所有 v0.7.1 的对抗式审查结论保持：
- 所有用户输入路径都通过 AST 复查确认 try/except 正确
- 所有 subprocess.run 都加 TimeoutExpired
- 所有 JSON 序列化都使用 json.dumps 而非 f-string
- 所有国际化字符串都通过 t() 而非硬编码

## 🐞 已知问题

- **P3**: `_DEFAULT_FP_PASSWORD = "0000"` 是演示默认值，**生产环境必须用环境变量覆盖**（已有测试守门）
- **TestPyPI Trusted Publisher 未配置**：如果未来要发 `-test` tag，需要先在 test.pypi.org 注册 pending publisher（当前未注册）

## 🤝 贡献

欢迎提交 Issue 和 PR：
- 仓库: https://github.com/hellob1889/PandaX
- 文档: [README.md](README.md)
- 审计防御层: 7 层（L1 file chmod → L7 CI）

## 📝 License

MIT
