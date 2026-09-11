---
name: Bug Report / 缺陷报告
about: Report something not working as expected
title: "[BUG] "
labels: ["bug"]
assignees: []
---

## 描述 / Description

<!-- 简要描述 bug 现象 -->

## 复现步骤 / Reproduction Steps

<!-- 最小复现命令，越具体越好 -->

1.
2.
3.

## 期望行为 / Expected Behavior

<!-- 你期望发生什么 -->

## 实际行为 / Actual Behavior

<!-- 实际发生了什么 -->

## 环境 / Environment

- **OS**：Windows / macOS / Linux + 版本（如 Win 11 23H2）
- **Python 版本**：`python --version` 输出
- **PandaX 版本**：`pip show pandax-guard | grep Version` 输出
- **安装方式**：PyPI (`pip install pandax-guard`) / Source (`pip install -e .`)
- **git 版本**（如相关）：`git --version`

## 审计日志 / Audit Log（若相关）

```bash
pandax log --last 20
```

输出请粘贴到下面：

```
[paste here]
```

## 屏幕截图 / Screenshots

<!-- 如适用 -->

## 附加上下文 / Additional Context

<!-- 任何其他相关信息：第一次发生 / 必现 / 偶现 / 影响范围 -->

## 可接受修复时间 / Acceptable Fix Timeline

- [ ] 紧急（影响数据完整性 / 安全）
- [ ] 重要（功能不可用）
- [ ] 普通（小问题 / 边缘 case）
- [ ] 不急（仅 cosmetic / docs）