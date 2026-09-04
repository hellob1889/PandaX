#!/usr/bin/env bash
# ============================================================
# PandaX macOS 右键服务安装脚本
# ============================================================
#
# 用法：
#   bash installer/macos/install_context_menu.sh
#
# 第一性原理：
#   - macOS 的「服务」(Quick Action) 是基于 ~/Library/Services/ 的 .workflow 目录
#   - Finder 右键 → "服务" → "PandaX" → 弹出操作选择 → Terminal 执行
#   - 用户级安装，无需 sudo
#   - 幂等：重复运行安全
#
# 对抗式审查：
#   - 攻击：恶意 .workflow 替换
#     缓解：检查 CFBundleIdentifier 一致
#   - 攻击：服务执行任意命令
#     缓解：osascript 菜单限定 4 个动作；Terminal 可视化运行
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_SRC="$SCRIPT_DIR/PandaX Lock.workflow"
SERVICES_DIR="$HOME/Library/Services"
WORKFLOW_DST="$SERVICES_DIR/PandaX Lock.workflow"

echo "==============================================="
echo "PandaX macOS 右键服务安装程序"
echo "==============================================="
echo ""

# 1. 检查 pandax 是否可用
if ! command -v pandax >/dev/null 2>&1; then
    echo "[WARN] 未找到 pandax 命令！"
    echo "请先安装："
    echo "  pip3 install pandax"
    echo "  # 或者"
    echo "  pip3 install --user git+https://github.com/pandax/pandax.git"
    echo ""
    read -p "是否仍要继续？[y/N] " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "已取消。"
        exit 1
    fi
else
    PANDAX_PATH="$(command -v pandax)"
    echo "[OK] 找到 pandax: $PANDAX_PATH"
fi

# 2. 检查 workflow 源
if [ ! -d "$WORKFLOW_SRC" ]; then
    echo "[ERROR] 未找到 workflow 源: $WORKFLOW_SRC"
    exit 1
fi

# 3. 检查 Info.plist 的标识
PLIST_ID=$(/usr/libexec/PlistBuddy -c "Print :CFBundleIdentifier" "$WORKFLOW_SRC/Contents/Info.plist" 2>/dev/null || echo "")
if [ "$PLIST_ID" != "com.pandax.workflow.lock" ]; then
    echo "[ERROR] workflow 标识不符（期望 com.pandax.workflow.lock，实际 $PLIST_ID）"
    exit 1
fi

# 4. 创建 Services 目录
mkdir -p "$SERVICES_DIR"

# 5. 拷贝 workflow
echo ""
echo "[1/3] 安装 Quick Action 到 ~/Library/Services/ ..."
if [ -e "$WORKFLOW_DST" ]; then
    echo "[INFO] 已存在同名服务，先清理旧版本..."
    rm -rf "$WORKFLOW_DST"
fi
cp -R "$WORKFLOW_SRC" "$WORKFLOW_DST"
echo "[OK] 已安装: $WORKFLOW_DST"

# 6. 刷新 Launch Services 数据库
echo ""
echo "[2/3] 刷新 Launch Services 数据库..."
LSREGISTER=/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister
if [ -x "$LSREGISTER" ]; then
    "$LSREGISTER" -f "$WORKFLOW_DST" 2>/dev/null || true
    echo "[OK] Launch Services 已刷新"
else
    echo "[WARN] lsregister 不可用，请手动重启 Finder"
fi

# 7. 提示用户在系统设置中启用
echo ""
echo "[3/3] 配置完成！"
echo ""
echo "下一步：在系统设置中启用此服务"
echo "  系统设置 → 键盘 → 快捷键 → 服务"
echo "  勾选「文件和文件夹」→「PandaX」"
echo ""
echo "启用后使用方式："
echo "  Finder → 右键点击文件/文件夹 → 服务 → PandaX"
echo "  → 选择 init / lock / unlock / status"
echo "  → Terminal 自动打开并执行 pandax 命令"
echo ""
echo "卸载："
echo "  bash installer/macos/uninstall_context_menu.sh"
echo ""