# Security Policy

PandaX 是**代码审计门禁工具**，安全是它的核心职责。本文档说明如何报告 PandaX 自身的安全漏洞，以及我们的安全更新策略。

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.7.x   | ✅ Active          |
| 0.6.x   | ⚠️ Critical fixes only |
| < 0.6.0 | ❌ End of life     |

## Reporting a Vulnerability

**请勿在 GitHub Issues 公开披露安全漏洞。** 公开报告会让攻击者在补丁发布前利用漏洞。

### 报告渠道（按优先级）

1. **GitHub Security Advisories（推荐）**
   https://github.com/hellob1889/PandaX/security/advisories/new
   - 私密沟通，可协调披露时间
   - 允许我们在补丁准备好前隐藏报告
   - 修复后会公开发布 advisory + CVE（如适用）

2. **Email**
   hellob1889@users.noreply.github.com
   - PGP key：[TODO: 添加 PGP 公钥]
   - 响应时间：48 小时内

### 报告应包含

- 漏洞描述 + 利用场景
- 复现步骤（PoC 代码 / 命令）
- 影响范围（哪些版本 / 哪些平台）
- 是否已知的缓解措施
- 你的姓名 / 联系方式（如希望致谢）

### 我们的承诺

- **48 小时内** 确认收到报告
- **7 天内** 评估严重性 + 决定处置方式
- **30 天内** 发布补丁（Critical/High 漏洞更快）
- **披露前** 与报告者协调 release window
- **致谢** 所有负责任披露者（在 advisory / release notes）

## Security Update Channels

- **GitHub Security Advisories**：https://github.com/hellob1889/PandaX/security/advisories
- **PyPI Release History**：https://pypi.org/project/pandax-guard/#history
- **GitHub Releases**：https://github.com/hellob1889/PandaX/releases

订阅 GitHub Releases 的 "Watch → Releases only" 即可收到所有版本通知（含安全补丁）。

## PandaX 自身的安全模型

PandaX 提供 **7 层防御体系**，自身安全等同于其要保护的项目：

| 层 | 安全相关组件 | 已知限制 |
|---|------|------|
| L1 | 文件 chmod 只读锁 | 仅限本地用户，root/管理员可绕过 |
| L2 | watchdog 实时监控 | 进程级，单实例；不支持网络文件系统 |
| L3 | pre-commit hook | 仅本地 hook，CI 端需要额外的 `pandax ci` 检查 |
| L5 | 自指纹 SHA256 | 文件级，wheel 构建时已强制 LF normalize（避免 CRLF 漂移） |
| L7 | GitHub Actions CI | PR 合入前审计；无法防止本地 bypass |

**重要**：PandaX 是**威慑 + 审计**工具，不是**不可绕过**的强制访问控制。恶意开发者可以通过修改 PandaX 自身代码绕过所有层。PandaX 的核心价值是**事后可追溯性**（审计日志），而非**事前强制阻止**。

## Out of Scope（不在漏洞披露奖励范围内）

- PandaX 本身的依赖（click / pyyaml / openpyxl 等）漏洞 —— 请报告给上游
- 在未启用 PandaX 的项目中的代码泄露
- 社会工程学 / 钓鱼攻击
- DoS / 暴力破解 PandaX CLI 本身

## Recognition

负责任披露者将在以下渠道致谢：
- GitHub Security Advisory 的 "Credits" 段
- CHANGELOG.md 的 Security 段（如适用）
- （未来）项目 README 的 Hall of Fame

---

**TL;DR**：发现漏洞 → GitHub Security Advisories 私密报告 → 48h 确认 → 7d 评估 → 30d 修复 → 协调披露。