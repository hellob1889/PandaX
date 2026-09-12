#!/bin/bash
# _detect_python.sh
# ============================================================
# 跨平台检测有 pandaone 的 Python 解释器
# ============================================================

# Windows 默认 Python 安装路径（按优先级排序）
WINDOWS_PYTHONS=(
    "/c/Python310/python.exe"
    "/c/Python311/python.exe"
    "/c/Python312/python.exe"
    "/c/Users/Administrator/AppData/Local/Programs/Python/Python310/python.exe"
    "/c/Users/Administrator/AppData/Local/Programs/Python/Python311/python.exe"
    "/c/Users/Administrator/AppData/Roaming/hermes/hermes-agent/venv/Scripts/python.exe"
    "/c/Users/Administrator/AppData/Roaming/TRAE SOLO CN/ModularData/ai-agent/vm/tools/python/python.exe"
    "/c/Users/Administrator/AppData/Roaming/TRAE SOLO CN/ModularData/ai-agent/vm/tools/bin/python.exe"
)

# 先尝试通用命令
COMMON_CMDS=("python" "python3" "py" "python3.10" "python3.11" "python3.12")

# 1. 先试通用命令
for cmd in "${COMMON_CMDS[@]}"; do
    if command -v "$cmd" >/dev/null 2>&1; then
        if "$cmd" -c "import pandaone" 2>/dev/null; then
            echo "$cmd"
            exit 0
        fi
    fi
done

# 2. 试常见 Windows Python 安装路径（Git Bash 专用）
for p in "${WINDOWS_PYTHONS[@]}"; do
    if [ -f "$p" ]; then
        if "$p" -c "import pandaone" 2>/dev/null; then
            echo "$p"
            exit 0
        fi
    fi
done

echo "[ERROR] 没找到有 pandaone 的 Python 解释器" >&2
echo "" >&2
echo "请运行以下命令之一：" >&2
echo "  pip install pandax-guard       # 系统默认 Python" >&2
echo "  python -m pip install pandax-guard  # 显式 Python" >&2
echo "" >&2
echo "如果已安装，可能是 PATH 问题。试试：" >&2
echo "  python -c 'import pandaone; print(pandaone.__file__)'" >&2
exit 1