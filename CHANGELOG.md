# Changelog

All notable changes to Pandaone AI Agent will be documented in this file.

## [0.7.7] - 2026-09-13

### Fixed (验证报告驱动的批量 bugfix)

本 release 修复了 pandaone-运行可行性验证报告.html 中识别的 6 个问题，让 L7 防线 (GitHub Actions CI 审计) 真正生效。

- BUG-04a (P0 / 阻断): .github/workflows/audit.yml 切到 pip install -e . + pandaone ci
  - 之前 audit.yml 装的是 PyPI 上的 pandax-guard 固定版本 + 调用旧 CLI pandax ci。
  - 后果：CI 一直跑"绿色假阳性"，验证的是被废弃的旧实现。
  - 修复：装当前分支 (pip install -e .)，调用命令切到 pandaone ci。
- BUG-01 (P1): src/pandaone_mcp/__init__.py 补 from .__main__ import main re-export
  - console_scripts 入口 pandaone_mcp:main 要求 main 从 package 顶层可导入。
  - 修复：参考 pandaone_guard/__init__.py 的同模式，显式 re-export。
- BUG-04b (P2): README 解析器兼容中英对照标题 ## 当前阶段 / Current Phase
  - 旧解析器严格相等匹配，双语标题会让 phase_lines 永远为空。
  - 修复：增加 OR 分支接受双语标题。
- BUG-05 (P3): pandaone write 用 git add -f 强制暂存审计日志
  - .pandaone/pandaone.jsonl 被 .gitignore 排除，普通 git add 会被 git 拒绝。
  - 修复：加 -f 强制暂存，让审计 jsonl 跟 commit 原子绑定。
- BUG-02 + BUG-06 (P4): 仓库卫生清理
  - 清理磁盘残留：src/pandax_guard.egg-info/ / test_project/ / __pycache__/ x 6 / .pytest_cache/
  - 验证 .gitignore 已覆盖所有模式。

### Notes
- 本 release 是纯 bugfix，不引入新功能、不破坏 API
- 升级方式：pip install --upgrade pandaone-guard
- 用户面行为变化：MCP server 现在能正常启动（之前是 import 报错）

## [0.7.6] - 2026-09-13

### Changed (品牌切回 / Rebrand Cutover)

- PyPI 分发名从 pandax-guard 切回 pandaone-guard (PR #23)
- pyproject.toml name = "pandaone-guard", version = "0.7.6"
- 13 个用户面文件:pandax-guard → pandaone-guard (还原 PR #12 临时回退)
- 发布到 PyPI 后用户可执行 pip install pandaone-guard