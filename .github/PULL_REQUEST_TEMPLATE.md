## 描述 / Description

<!-- 这个 PR 解决了什么问题？引用相关 issue：Fixes #123 / Closes #456 -->

## 改动类型 / Type of Change

- [ ] Bug fix（非破坏性，修复 issue）
- [ ] New feature（非破坏性，新功能）
- [ ] Breaking change（破坏现有 API 或行为）
- [ ] Documentation only（仅文档）
- [ ] Refactor（无功能变化）
- [ ] CI / 工程化（CI / workflow / build）

## 关联 Issue / Related Issues

<!-- Fixes #(issue number) -->

## 测试 / Testing

### 本地验证

- [ ] 已运行 `pytest tests/`，结果：__ passed / __ failed / __ skipped
- [ ] 已运行 `python scripts/audit_i18n.py`，结果：PASS / FAIL
- [ ] 已运行 `pandax ci --root . --base origin/main`，结果：PASS / FAIL

### 新增 / 修改的测试

<!--
- tests/test_xxx.py::test_xxx
- tests/test_yyy.py::test_yyy
-->

## Audit 状态（重要！）

PandaX 的 CI 会检查所有 push 都经过 `pandax write`。

- [ ] 我已经通过 `pandax write` 记录本次所有改动（reason / problem / approach）
- [ ] 本次改动**仅 workflow 文件**，PR 标题含 `[skip-audit]` 跳过审计
- [ ] 本次改动**仅文档 / 示例 / assets**，PR 标题含 `[skip-audit]` 跳过审计
- [ ] 其他情况说明：________

## Checklist

- [ ] 代码符合项目风格（运行了 `ruff check src/` 或同等检查）
- [ ] 自我 review 过 diff（没有无关改动）
- [ ] 添加了对应测试（如适用）
- [ ] 新功能有 i18n key（zh-CN + en）
- [ ] CHANGELOG.md 更新了（如适用）
- [ ] README 更新了（如适用）
- [ ] 文档（docs/）更新了（如适用）

## 屏幕截图 / Screenshots（如适用）

<!-- 输出格式变化 / 新 UI / 错误信息 -->

## 附加备注 / Additional Notes

<!-- 任何评审者需要知道的信息：设计决策 / 已知限制 / 后续 follow-up -->