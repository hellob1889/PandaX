#!/bin/bash
# 03_bypass_attempt.sh
# ============================================================
# Pandaone AI Agent 7 层防御实战 demo
# ============================================================
# 演示：尝试用各种方法绕过审计门禁，验证拦截
# 预期：所有攻击都被对应层拦截
# ============================================================
set -e

G="\033[92m"; Y="\033[93m"; B="\033[94m"; R="\033[91m"; W="\033[0m"

PROJECT="$(pwd)/demo_03_bypass"
GIT_EXE="$(command -v git)"

echo -e "${B}============================================================${W}"
echo -e "${B}  Pandaone 7 层防御实战 demo${W}"
echo -e "${B}  模拟攻击 → 验证拦截${W}"
echo -e "${B}============================================================${W}"

rm -rf "$PROJECT"
mkdir -p "$PROJECT/src"
cd "$PROJECT"

# 准备 + git + init + lock
"$GIT_EXE" init -q
"$GIT_EXE" config user.email "demo@example.com"
"$GIT_EXE" config user.name "Demo"
echo 'INITIAL = 1' > src/main.py
python -m pandaone init --root "$PROJECT" 2>&1 | tail -2
python -m pandaone lock --root "$PROJECT" 2>&1 | tail -2

# ================================================================
# 攻击 1: 直接 write 锁定文件（L1 拦截）
# ================================================================
echo -e "\n${Y}[攻击 1/5] 直接 write 锁定文件（攻击 L1）${W}"
if echo "HIJACK = True" > src/main.py 2>&1; then
  echo -e "  ${R}❌ BUG: L1 失效！${W}"
  exit 1
else
  echo -e "  ${G}✓ L1 拦截：PermissionError${W}"
fi

# ================================================================
# 攻击 2: chmod +w 后 write（L1 失守，依赖 L2 兜底）
# ================================================================
echo -e "\n${Y}[攻击 2/5] chmod +w + write（L1 失守）${W}"
chmod +w src/main.py
echo "HIJACK = True" > src/main.py
echo -e "  ${Y}⚠️  L1 被 chmod 解除，写入成功（攻击者拿到 root 权限的场景）${W}"
echo -e "  现实：依赖 L2 watchdog 兜底"

# ================================================================
# 攻击 3: install-hook + 直接 git commit（攻击 L3）
# ================================================================
echo -e "\n${Y}[攻击 3/5] 装 hook + 提交新文件（攻击 L3）${W}"
python -m pandaone install-hook --root "$PROJECT" 2>&1 | tail -2

# 创建新文件（不在 approved set） + 直接 commit
echo 'EVIL_NEW = True' > src/evil.py
"$GIT_EXE" add src/evil.py
if "$GIT_EXE" commit -m "bypass via direct commit" 2>&1; then
  echo -e "  ${R}❌ BUG: L3 hook 失效！${W}"
  exit 1
else
  echo -e "  ${G}✓ L3 拦截：hook 拒绝 commit${W}"
fi

# ================================================================
# 攻击 4: --no-verify 绕过 hook（依赖 L7 CI 兜底）
# ================================================================
echo -e "\n${Y}[攻击 4/5] git commit --no-verify（绕过 L3）${W}"
"$GIT_EXE" add src/evil.py
if "$GIT_EXE" commit --no-verify -m "force bypass hook" 2>&1; then
  echo -e "  ${Y}⚠️  L3 被 --no-verify 绕过（攻击者用逃生通道）${W}"
  echo -e "  现实：依赖 L7 CI 兜底"
fi

# ================================================================
# 攻击 5: CI 验证（最终兜底）
# ================================================================
echo -e "\n${Y}[攻击 5/5] pandaone ci（L7 最终验证）${W}"
if python -m pandaone ci --root "$PROJECT" --base HEAD~1 2>&1; then
  echo -e "  ${R}❌ BUG: L7 CI 失效！${W}"
  exit 1
else
  echo -e "  ${G}✓ L7 拦截：CI 检测到未审计的 src/evil.py${W}"
fi

echo -e "\n${G}============================================================${W}"
echo -e "${G}  ✓ Demo 3 完成 — 所有攻击都被对应层拦截${W}"
echo -e "${G}============================================================${W}"