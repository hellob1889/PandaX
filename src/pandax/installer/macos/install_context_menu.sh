#!/usr/bin/env bash
# ============================================================
# PandaX macOS context menu installer
# ============================================================
#
# Usage:
#   bash installer/macos/install_context_menu.sh
#
# Or via pandax (preferred, sets --lang):
#   pandax install-context              # uses ~/.pandax/config.json (set by pandax)
#   pandax install-context --lang=en    # overrides saved preference
#
# First principles:
#   - macOS "Services" (Quick Actions) live in ~/Library/Services/ as .workflow dirs
#   - Finder right-click -> Services -> PandaX -> choose action -> Terminal runs pandax
#   - User-level install, no sudo
#   - Idempotent: safe to re-run
#
# Adversarial review:
#   - Threat: malicious .workflow replacement
#     Mitigation: verify CFBundleIdentifier matches
#   - Threat: services execute arbitrary commands
#     Mitigation: osascript menu limits to 4 actions; Terminal shows output
#
# i18n: language comes from ~/.pandax/config.json (written by `pandax --lang`),
#       env PANDAX_LANG, or default zh-CN. Override via env or --lang= CLI flag.
# ============================================================

set -e

# ---- Resolve language ----
# Priority: env PANDAX_LANG > config.json > default zh-CN
USER_LANG="${PANDAX_LANG:-}"
if [ -z "$USER_LANG" ] && [ -f "$HOME/.pandax/config.json" ]; then
    USER_LANG=$(grep -o '"lang":[[:space:]]*"[^"]*"' "$HOME/.pandax/config.json" 2>/dev/null \
                | head -1 | sed 's/.*"\([^"]*\)"$/\1/' || echo "")
fi
USER_LANG="${USER_LANG:-zh-CN}"

# ---- Load text strings ----
if [ "$USER_LANG" = "en" ]; then
    TXT_TITLE="PandaX macOS Context Menu Installer"
    TXT_NOT_FOUND="[WARN] pandax command not found!"
    TXT_INSTALL_HINT_1="Please install first:"
    TXT_INSTALL_HINT_2="  pip3 install pandax"
    TXT_INSTALL_HINT_3="Or:"
    TXT_INSTALL_HINT_4="  pip3 install --user git+https://github.com/pandax/pandax.git"
    TXT_CONFIRM="Continue anyway? [y/N]"
    TXT_CANCELLED="Cancelled."
    TXT_FOUND="[OK] Found pandax:"
    TXT_NO_WORKFLOW="[ERROR] Workflow source not found:"
    TXT_BAD_ID="[ERROR] Workflow identifier mismatch (expected com.pandax.workflow.lock, got"
    TXT_STEP_1="[1/3] Installing Quick Action to ~/Library/Services/ ..."
    TXT_EXISTS="[INFO] Existing service found, cleaning old version..."
    TXT_INSTALLED="[OK] Installed:"
    TXT_STEP_2="[2/3] Refreshing Launch Services database..."
    TXT_LS_OK="[OK] Launch Services refreshed"
    TXT_LS_MISSING="[WARN] lsregister not available, manually restart Finder"
    TXT_STEP_3="[3/3] Setup complete!"
    TXT_NEXT="Next: enable this service in System Settings"
    TXT_NEXT_1="  System Settings -> Keyboard -> Shortcuts -> Services"
    TXT_NEXT_2="  Check 'Files and Folders' -> 'PandaX'"
    TXT_USAGE="After enabling:"
    TXT_USAGE_1="  Finder -> right-click file/folder -> Services -> PandaX"
    TXT_USAGE_2="  -> choose init / lock / unlock / status"
    TXT_USAGE_3="  -> Terminal opens automatically and runs pandax"
    TXT_UNINST="To uninstall:"
    TXT_UNINST_CMD="  bash installer/macos/uninstall_context_menu.sh"
else
    TXT_TITLE="PandaX macOS 右键服务安装程序"
    TXT_NOT_FOUND="[WARN] 未找到 pandax 命令！"
    TXT_INSTALL_HINT_1="请先安装："
    TXT_INSTALL_HINT_2="  pip3 install pandax"
    TXT_INSTALL_HINT_3="或者："
    TXT_INSTALL_HINT_4="  pip3 install --user git+https://github.com/pandax/pandax.git"
    TXT_CONFIRM="是否仍要继续？[y/N]"
    TXT_CANCELLED="已取消。"
    TXT_FOUND="[OK] 找到 pandax:"
    TXT_NO_WORKFLOW="[ERROR] 未找到 workflow 源:"
    TXT_BAD_ID="[ERROR] workflow 标识不符（期望 com.pandax.workflow.lock，实际"
    TXT_STEP_1="[1/3] 安装 Quick Action 到 ~/Library/Services/ ..."
    TXT_EXISTS="[INFO] 已存在同名服务，先清理旧版本..."
    TXT_INSTALLED="[OK] 已安装:"
    TXT_STEP_2="[2/3] 刷新 Launch Services 数据库..."
    TXT_LS_OK="[OK] Launch Services 已刷新"
    TXT_LS_MISSING="[WARN] lsregister 不可用，请手动重启 Finder"
    TXT_STEP_3="[3/3] 配置完成！"
    TXT_NEXT="下一步：在系统设置中启用此服务"
    TXT_NEXT_1="  系统设置 → 键盘 → 快捷键 → 服务"
    TXT_NEXT_2="  勾选「文件和文件夹」→「PandaX」"
    TXT_USAGE="启用后使用方式："
    TXT_USAGE_1="  Finder → 右键点击文件/文件夹 → 服务 → PandaX"
    TXT_USAGE_2="  → 选择 init / lock / unlock / status"
    TXT_USAGE_3="  → Terminal 自动打开并执行 pandax 命令"
    TXT_UNINST="卸载："
    TXT_UNINST_CMD="  bash installer/macos/uninstall_context_menu.sh"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_SRC="$SCRIPT_DIR/PandaX Lock.workflow"
SERVICES_DIR="$HOME/Library/Services"
WORKFLOW_DST="$SERVICES_DIR/PandaX Lock.workflow"

echo "==============================================="
echo "$TXT_TITLE"
echo "==============================================="
echo ""

# 1. 检查 pandax 是否可用
if ! command -v pandax >/dev/null 2>&1; then
    echo "$TXT_NOT_FOUND"
    echo "$TXT_INSTALL_HINT_1"
    echo "$TXT_INSTALL_HINT_2"
    echo "$TXT_INSTALL_HINT_3"
    echo "$TXT_INSTALL_HINT_4"
    echo ""
    read -p "$TXT_CONFIRM " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "$TXT_CANCELLED"
        exit 1
    fi
else
    PANDAX_PATH="$(command -v pandax)"
    echo "$TXT_FOUND $PANDAX_PATH"
fi

# 2. 检查 workflow 源
if [ ! -d "$WORKFLOW_SRC" ]; then
    echo "$TXT_NO_WORKFLOW $WORKFLOW_SRC"
    exit 1
fi

# 3. 检查 Info.plist 的标识
PLIST_ID=$(/usr/libexec/PlistBuddy -c "Print :CFBundleIdentifier" "$WORKFLOW_SRC/Contents/Info.plist" 2>/dev/null || echo "")
if [ "$PLIST_ID" != "com.pandax.workflow.lock" ]; then
    echo "$TXT_BAD_ID $PLIST_ID)"
    exit 1
fi

# 4. 创建 Services 目录
mkdir -p "$SERVICES_DIR"

# 5. 拷贝 workflow + 渲染 {TXT_XXX} 占位符
echo ""
echo "$TXT_STEP_1"
if [ -e "$WORKFLOW_DST" ]; then
    echo "$TXT_EXISTS"
    rm -rf "$WORKFLOW_DST"
fi
cp -R "$WORKFLOW_SRC" "$WORKFLOW_DST"

# i18n 渲染：用 sed 把 .wflow 内的占位符替换为当前语言文案
WFLOW_DOC="$WORKFLOW_DST/Contents/document.wflow"
case "$USER_LANG" in
    en)
        WF_COMMENT_INPUT="Receive file/folder paths from Finder selection"
        WF_COMMENT_STDIN="Standard Automator input: one path per line (stdin)"
        WF_NO_SELECTION="No file or folder selected"
        WF_COMMENT_PICK_FIRST="Pick the first selection (Finder multi-select)"
        WF_COMMENT_PARENT_DIR="If file, use parent directory"
        WF_COMMENT_MENU_HEADER="Show action menu (init / lock / unlock / status)"
        WF_MENU_PROMPT="Choose action (target:"
        WF_COMMENT_CANCELLED="user cancelled"
        WF_COMMENT_TERMINAL="Execute pandax in Terminal.app"
        WF_PRESS_ANY_KEY="Press any key to close"
        ;;
    *)
        WF_COMMENT_INPUT="接收 Finder 选中的文件/文件夹路径作为输入"
        WF_COMMENT_STDIN="标准 Automator 输入：每个路径占一行（stdin）"
        WF_NO_SELECTION="没有选中任何文件或文件夹"
        WF_COMMENT_PICK_FIRST="选择第一个作为目标（Finder 多选时取第一个）"
        WF_COMMENT_PARENT_DIR="如果是文件，取所在目录"
        WF_COMMENT_MENU_HEADER="显示选择菜单（init / lock / unlock / status）"
        WF_MENU_PROMPT="选择要执行的操作（目标："
        WF_COMMENT_CANCELLED="用户取消"
        WF_COMMENT_TERMINAL="在 Terminal.app 中执行 pandax"
        WF_PRESS_ANY_KEY="按任意键关闭"
        ;;
esac

# 用 python 做安全替换（XML 内容，sed 转义复杂）
WFLOW_DOC="$WORKFLOW_DST/Contents/document.wflow" python - <<'PYEOF'
import os, sys, pathlib
p = pathlib.Path(os.environ["WFLOW_DOC"])
text = p.read_text(encoding="utf-8")
replacements = {
    "{TXT_COMMENT_INPUT}":     os.environ.get("WF_COMMENT_INPUT", ""),
    "{TXT_COMMENT_STDIN}":     os.environ.get("WF_COMMENT_STDIN", ""),
    "{TXT_NO_SELECTION}":      os.environ.get("WF_NO_SELECTION", ""),
    "{TXT_COMMENT_PICK_FIRST}":os.environ.get("WF_COMMENT_PICK_FIRST", ""),
    "{TXT_COMMENT_PARENT_DIR}":os.environ.get("WF_COMMENT_PARENT_DIR", ""),
    "{TXT_COMMENT_MENU_HEADER}":os.environ.get("WF_COMMENT_MENU_HEADER", ""),
    "{TXT_MENU_PROMPT}":       os.environ.get("WF_MENU_PROMPT", ""),
    "{TXT_COMMENT_CANCELLED}": os.environ.get("WF_COMMENT_CANCELLED", ""),
    "{TXT_COMMENT_TERMINAL}":  os.environ.get("WF_COMMENT_TERMINAL", ""),
    "{TXT_PRESS_ANY_KEY}":     os.environ.get("WF_PRESS_ANY_KEY", ""),
}
for k, v in replacements.items():
    text = text.replace(k, v)
p.write_text(text, encoding="utf-8")
PYEOF

echo "$TXT_INSTALLED $WORKFLOW_DST"

# 6. 刷新 Launch Services 数据库
echo ""
echo "$TXT_STEP_2"
LSREGISTER=/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister
if [ -x "$LSREGISTER" ]; then
    "$LSREGISTER" -f "$WORKFLOW_DST" 2>/dev/null || true
    echo "$TXT_LS_OK"
else
    echo "$TXT_LS_MISSING"
fi

# 7. 提示用户在系统设置中启用
echo ""
echo "$TXT_STEP_3"
echo ""
echo "$TXT_NEXT"
echo "$TXT_NEXT_1"
echo "$TXT_NEXT_2"
echo ""
echo "$TXT_USAGE"
echo "$TXT_USAGE_1"
echo "$TXT_USAGE_2"
echo "$TXT_USAGE_3"
echo ""
echo "$TXT_UNINST"
echo "$TXT_UNINST_CMD"
echo ""
