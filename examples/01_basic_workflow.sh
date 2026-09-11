#!/bin/bash
# 01_basic_workflow.sh
# ============================================================
# Pandaone AI Agent 基础工作流 demo
# ============================================================
# 演示：init → lock → write → log → status 完整流程
# 预期：每个步骤输出对应状态，所有 write 记录 APPROVED
# ============================================================
set -e

# 颜色
G="\033[92m"; Y="\033[93m"; B="\033[94m"; R="\033[91m"; W="\033[0m"

PROJECT="$(pwd)/demo_01_basic"
GIT_EXE="$(command -v git)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PY_EXE="$("$SCRIPT_DIR/_detect_python.sh")" || {
    echo "请先运行: pip install pandaone-guard"
    exit 1
}

if [ -z "$GIT_EXE" ]; then echo "找不到 git"; exit 1; fi

echo -e "${B}============================================================${W}"
echo -e "${B}  Pandaone 基础工作流 demo${W}"
echo -e "${B}  PROJECT = $PROJECT${W}"
echo -e "${B}============================================================${W}"

# 清理
rm -rf "$PROJECT"
mkdir -p "$PROJECT/src"
cd "$PROJECT"

# 准备初始文件
cat > src/hello.py << 'EOF'
def hello(name):
    return f"Hello, {name}!"
EOF

cat > README.md << 'EOF'
# Demo Project
Just a test.
EOF

# 1. git init
echo -e "\n${Y}[1/7] git init${W}"
"$GIT_EXE" init -q
"$GIT_EXE" config user.email "demo@example.com"
"$GIT_EXE" config user.name "Demo"
echo "  ✓ git initialized"

# 2. pandaone init
echo -e "\n${Y}[2/7] pandaone init${W}"
"$PY_EXE" -m pandaone init --root "$PROJECT" 2>&1 | tail -5
echo "  ✓ Pandaone initialized"

# 3. pandaone lock
echo -e "\n${Y}[3/7] pandaone lock${W}"
"$PY_EXE" -m pandaone lock --root "$PROJECT" 2>&1 | grep -E "\[OK\]|\[" | tail -5
echo "  ✓ Files locked"

# 4. 验证锁定（用 Python 尝试写）
echo -e "\n${Y}[4/7] 攻击测试：尝试直接写入锁定文件${W}"
if "$PY_EXE" -c "open('src/hello.py', 'w').write('X = 1')" 2>&1; then
  echo -e "  ${R}❌ BUG: 锁定文件居然可写！${W}"
  exit 1
else
  echo -e "  ${G}✓ PermissionError（文件被锁）${W}"
fi

# 5. 通过 write 修改
echo -e "\n${Y}[5/7] pandaone write 合规修改${W}"
"$PY_EXE" -m pandaone write \
  --root "$PROJECT" \
  --file src/hello.py \
  --reason "添加默认 name 参数" \
  --problem "调用者经常忘传 name" \
  --approach "默认值为 World" \
  --old 'def hello(name):' \
  --new 'def hello(name="World"):' 2>&1 | tail -2

# 6. 验证审计记录
echo -e "\n${Y}[6/7] 查看审计日志${W}"
"$PY_EXE" -m pandaone log --root "$PROJECT" --last 5 2>&1 | tail -10

# 7. status
echo -e "\n${Y}[7/7] status 仪表盘${W}"
"$PY_EXE" -m pandaone status --root "$PROJECT" 2>&1 | tail -20

echo -e "\n${G}============================================================${W}"
echo -e "${G}  ✓ Demo 1 完成 — 基础工作流演示${W}"
echo -e "${G}============================================================${W}"