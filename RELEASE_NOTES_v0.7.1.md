# PandaX v0.7.1 — Release Notes

**Release date / 发布日期**: 2026-09-10
**Status / 状态**: Stable
**Python / Python 版本**: 3.8+
**Platforms / 支持平台**: Windows / macOS / Linux

---

## 🎯 What's New / 新版本亮点

PandaX v0.7.1 是 v0.7.0 之后的**安全与稳定性加固版本**。重点是消除 v0.7.0 引入的几处安全漏洞、改进错误处理鲁棒性、并完成剩余模块的国际化（i18n）覆盖。
PandaX v0.7.1 is a **security and stability hardening release** following v0.7.0. Focus is on eliminating several security vulnerabilities introduced in v0.7.0, improving error handling robustness, and completing i18n coverage for remaining modules.

## 🐛 Bug 修复（11 个）/ Bug Fixes (11 Bugs)

### P0 安全类 / P0 Security

- **Bug #1**: `desktop_icon.py` 5 处 `os.system` 命令注入 / 5 instances of `os.system` command injection
  → 用 `ctypes.windll.kernel32.SetFileAttributesW` 直接调 Windows API / Replaced with direct Windows API call

- **Bug #17**: `cli.py` 5 处 f-string JSON 注入（用户输入含反斜杠/双引号时破坏 JSON）/ 5 instances of f-string JSON injection (breaks JSON when user input contains backslash/double-quote)
  → 全部改用 `json.dumps(..., ensure_ascii=False)` / All migrated to `json.dumps(..., ensure_ascii=False)`

### P1 鲁棒性 / P1 Robustness

- **Bug #16**: `cli.py` 6 处 `json.loads` 无 try/except / 6 `json.loads` without try/except
  → 加 `(JSONDecodeError, OSError)` 捕获，友好错误 + 正确 return code / Added catch with friendly error and proper return code

- **Bug #18**: `cli.py` 3 处 `subprocess.run` 无 `TimeoutExpired` 捕获 / 3 `subprocess.run` without `TimeoutExpired` catch
  → 加 try/except，超时返回 None 或 124（标准 timeout exit code）/ Added try/except, returns None or 124 (standard timeout exit code)

### P1 i18n
- **Bug #11/12/10/13**: `cli.py` 4 处硬编码中文/英文 + 死代码 / 4 hardcoded Chinese/English + dead code
  → 全用 `t()` 替换，移除 `in dir(__builtins__)` 永远为 False 的 dead branch / All replaced with `t()`, removed dead branch

### P2 i18n 化 / P2 i18n Migration

- `desktop_icon.py` + `gitignore_helper.py` 加 i18n 集成（之前 2 个模块完全无 i18n）/ Added i18n integration (previously 2 modules had no i18n)

### P3 测试 / P3 Tests

- `test_i18n.py` 加 **8 个回归测试** / **8 regression tests**:
  - t() with backslash / double quote / CJK / None / extra kwargs
  - zh-CN ↔ en keys parity 严格相等 / strict parity
  - 扫描 src/pandax 全部 t() 调用，断言 0 个 undefined key / scan all t() calls, assert 0 undefined keys

## 🌍 i18n 同步 / i18n Sync

- zh-CN **248** keys ↔ en **246** keys（修复前 zh-CN 缺 11 个 key + 几个 key 不一致）/ zh-CN **248** keys ↔ en **246** keys (before fix: zh-CN missing 11 keys + several inconsistencies)
- 新增 16 个 key（zh-CN + en 各 8 份）/ Added 16 keys (8 in zh-CN + 8 in en)

## 📊 测试结果 / Test Results

```
全部 340 个测试通过 / All 340 tests pass
  - baseline 332 + 新增 8 个 t() 鲁棒性测试 / + 8 new t() robustness tests
0 个 missing keys (修复前 11 个) / 0 missing keys (before fix: 11)
66 个 dead keys (已记录，不影响功能) / 66 dead keys (documented, doesn't affect functionality)
```

## 📦 安装 / Installation

### pip（推荐）/ pip (Recommended)

```bash
pip install pandax-guard==0.7.1
```

### 下载安装包 / Download Installer

下载附件 `PandaX-0.7.1-install.zip`，解压后运行 / Download `PandaX-0.7.1-install.zip`, extract and run:
**Windows**:
```powershell
.\install.bat
```
**macOS / Linux**:
```bash
bash install.sh
```

### 源码开发模式 / Source Dev Mode

```bash
git clone https://github.com/hellob1889/PandaX.git
cd PandaX
pip install -e .
```

## 🛡️ 安全声明 / Security Statement

v0.7.1 是第一个**经过对抗式复查**的版本 / v0.7.1 is the first version to pass adversarial review:
- 所有用户输入路径都通过 AST 复查确认 try/except 正确 / All user input paths verified by AST review
- 所有 subprocess.run 都加 TimeoutExpired / All subprocess.run with TimeoutExpired
- 所有 JSON 序列化都使用 json.dumps 而非 f-string / All JSON serialization via json.dumps not f-string
- 所有国际化字符串都通过 t() 而非硬编码 / All i18n strings via t() not hardcoded

## 🐞 已知问题 / Known Issues

- **P3**: `_DEFAULT_FP_PASSWORD = "0000"` 是演示默认值，**生产环境必须用环境变量覆盖**（已有测试守门）/ is demo default; **production must override via env var** (test gatekeeper in place)
- **P3**: `D:\软件\Git\cmd\git.exe` 仍是 Windows 上 Git 路径的候选 fallback（已在 `examples/` 中改为 `shutil.which("git")`，但 `src/pandax/` 中保留作为 fallback）/ remains candidate fallback on Windows; `examples/` uses `shutil.which("git")`, `src/pandax/` keeps as fallback

## 🤝 贡献 / Contributing

欢迎提交 Issue 和 PR / Issues and PRs welcome:
- 仓库 / Repo: https://github.com/hellob1889/PandaX
- 文档 / Docs: [README.md](README.md)
- 审计防御层 / Audit defense layers: 7 层（L1 file chmod → L7 CI） / 7 layers (L1 file chmod → L7 CI)

## 📝 License

MIT
