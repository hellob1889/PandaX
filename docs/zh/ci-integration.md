# CI/CD 集成

> **每次 PR 提交都自动审计验证** — L7 防御。

## GitHub Actions（推荐）

`.github/workflows/audit.yml`：

```yaml
name: Pandaone AI Agent CI
on:
  pull_request:
    branches: [main, master, develop]
  push:
    branches: [main, master]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # 需要完整 git 历史
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - run: pip install pandax-guard
      - run: pandaone ci --root . --base origin/main
      - if: failure() && github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const { data: pr } = await github.rest.pulls.get({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: context.issue.number,
            });
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: '## Pandaone CI Failed\n\n所有变更必须通过 `pandaone write` 审计。\n\n修复步骤：\n```bash\npandaone write --file <FILE> --reason "..." --problem "..." --approach "..."\n```',
            });
```

完整文件：[`.github/workflows/audit.yml`](https://github.com/hellob1889/Pandaone-AI-Agent/blob/main/.github/workflows/audit.yml)

## GitLab CI

`.gitlab-ci.yml`：

```yaml
audit:
  stage: test
  image: python:3.10
  before_script:
    - pip install pandax-guard
  script:
    - pandaone ci --root . --base origin/main
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
```

## CircleCI

`.circleci/config.yml`：

```yaml
version: 2.1
jobs:
  audit:
    docker:
      - image: python:3.10
    steps:
      - checkout
      - run: pip install pandax-guard
      - run: pandaone ci --root . --base origin/main
workflows:
  version: 2
  audit:
    jobs:
      - audit:
          filters:
            branches:
              only: [main, develop]
```

## CI 输出示例

```
================================================================
[FAIL] 检测到 2 个未审计的变更：

  [文本  ] src/auth.py      原因: 未找到 APPROVED 审计记录
  [二进制] assets/icon.ico  原因: SHA256 不一致 (snapshot=abc, actual=def)

{"status":"FAIL","violations":2,"changed":5}
```

## 修复流程

CI 失败时：

```bash
# 1. 重新审计修改
pandaone write --file src/auth.py \
    --reason "..." --problem "..." --approach "..." \
    --old "..." --new "..."

# 2. 替换二进制
pandaone write --file assets/icon.ico \
    --reason "..." --problem "..." --approach "..." \
    --from-file /tmp/new_icon.ico

# 3. 提交
git add -A
git commit -m "fix: address CI audit feedback"
git push
```

## 自动发布到 PyPI

详见 [RELEASE.md](../../RELEASE.md)。首次需要手动 `twine upload` 创建项目，之后 `git tag v*.*.* && git push --tags` 自动触发 Trusted Publishing。

---

[← 返回首页](index.md) | [查看命令参考](commands.md)