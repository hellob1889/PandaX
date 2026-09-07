#!/usr/bin/env bash
# ============================================================
# PandaX Linux right-click menu installer
# ============================================================
#
# Usage:
#   bash installer/linux/install_context_menu.sh
#
# Or via pandax (preferred, sets --lang):
#   pandax install-context              # uses ~/.pandax/config.json
#   pandax install-context --lang=en    # overrides saved preference
#
# Auto-detects:
#   - Nautilus (GNOME / Files)
#   - Dolphin  (KDE)
#   - Others   (Thunar / Caja / PCManFM)
#
# First principles:
#   - No cross-desktop standard for right-click menus on Linux
#   - Mainstream: Nautilus scripts (GNOME) and .desktop service menus (KDE)
#   - User-level install to ~/.local/share/..., no sudo
#   - Idempotent: safe to re-run
#
# i18n: language comes from ~/.pandax/config.json (written by `pandax --lang`),
#       env PANDAX_LANG, or default zh-CN.
# ============================================================

set -e

# ---- Resolve language ----
USER_LANG="${PANDAX_LANG:-}"
if [ -z "$USER_LANG" ] && [ -f "$HOME/.pandax/config.json" ]; then
    USER_LANG=$(grep -o '"lang":[[:space:]]*"[^"]*"' "$HOME/.pandax/config.json" 2>/dev/null \
                | head -1 | sed 's/.*"\([^"]*\)"$/\1/' || echo "")
fi
USER_LANG="${USER_LANG:-zh-CN}"

# ---- Load text strings ----
if [ "$USER_LANG" = "en" ]; then
    TXT_TITLE="PandaX Linux Context Menu Installer"
    TXT_NOT_FOUND="[WARN] pandax not found! Please run 'pip install pandax' first"
    TXT_CONFIRM="Continue anyway? [y/N]"
    TXT_FOUND="[OK] Found pandax:"
    TXT_DETECT_DE="[INFO] Detected desktop environment:"
    TXT_STEP_NAUTILUS="[1/2] Installing Nautilus script..."
    TXT_INSTALLED="[OK] Installed:"
    TXT_STEP_DOLPHIN="[2/2] Installing Dolphin service menu..."
    TXT_NO_DE="[WARN] No supported desktop environment detected"
    TXT_DE_SUPPORTED="Supports: GNOME / KDE / Cinnamon / MATE / Unity / Pop"
    TXT_FORCE_NAUTILUS="Force-install Nautilus script? [y/N]"
    TXT_FORCED_NAUTILUS="[OK] Force-installed Nautilus script"
    TXT_FORCE_KDE="Force-install KDE service menu? [y/N]"
    TXT_FORCED_KDE="[OK] Force-installed KDE service menu"
    TXT_DONE="[OK] Installation complete (${installed} items)!"
    TXT_USAGE_HEADER="How to use:"
    TXT_USAGE_NAUTILUS="  Nautilus (Files):"
    TXT_USAGE_NAUTILUS_1="    right-click -> Scripts -> PandaX -> choose action"
    TXT_USAGE_DOLPHIN="  Dolphin (KDE):"
    TXT_USAGE_DOLPHIN_1="    right-click -> Actions -> PandaX -> choose sub-action"
    TXT_RESTART_HEADER="Restart file manager (if menu doesn't appear):"
    TXT_RESTART_GNOME="  nautilus --quit && nautilus &"
    TXT_RESTART_KDE="  dolphin --shutdown && dolphin &"
    TXT_RESTART_CINNAMON="  nautilus --quit && cinnamon --restart &"
    TXT_UNINST_HEADER="To uninstall:"
    TXT_UNINST_CMD="  bash installer/linux/uninstall_context_menu.sh"
    TXT_NOTHING="[INFO] No right-click menu installed."
else
    TXT_TITLE="PandaX Linux 右键菜单安装程序"
    TXT_NOT_FOUND="[WARN] 未找到 pandax！请先 pip install pandax"
    TXT_CONFIRM="是否仍要继续？[y/N]"
    TXT_FOUND="[OK] 找到 pandax:"
    TXT_DETECT_DE="[INFO] 检测到桌面环境:"
    TXT_STEP_NAUTILUS="[1/2] 安装 Nautilus 脚本..."
    TXT_INSTALLED="[OK] 已安装:"
    TXT_STEP_DOLPHIN="[2/2] 安装 Dolphin 服务菜单..."
    TXT_NO_DE="[WARN] 未检测到支持的桌面环境"
    TXT_DE_SUPPORTED="支持：GNOME / KDE / Cinnamon / MATE / Unity / Pop"
    TXT_FORCE_NAUTILUS="是否强行安装 Nautilus 脚本？[y/N]"
    TXT_FORCED_NAUTILUS="[OK] 已强制安装 Nautilus 脚本"
    TXT_FORCE_KDE="是否强行安装 KDE 服务菜单？[y/N]"
    TXT_FORCED_KDE="[OK] 已强制安装 KDE 服务菜单"
    TXT_DONE="[OK] 安装完成（${installed} 项）！"
    TXT_USAGE_HEADER="使用方式："
    TXT_USAGE_NAUTILUS="  Nautilus（Files）:"
    TXT_USAGE_NAUTILUS_1="    右键 → 脚本 → PandaX → 选择操作"
    TXT_USAGE_DOLPHIN="  Dolphin（KDE）:"
    TXT_USAGE_DOLPHIN_1="    右键 → Actions → PandaX → 选择子操作"
    TXT_RESTART_HEADER="重启文件管理器（如果菜单没出现）:"
    TXT_RESTART_GNOME="  nautilus --quit && nautilus &"
    TXT_RESTART_KDE="  dolphin --shutdown && dolphin &"
    TXT_RESTART_CINNAMON="  nautilus --quit && cinnamon --restart &"
    TXT_UNINST_HEADER="卸载："
    TXT_UNINST_CMD="  bash installer/linux/uninstall_context_menu.sh"
    TXT_NOTHING="[INFO] 未安装任何右键菜单。"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAUTILUS_SRC="$SCRIPT_DIR/nautilus/PandaX"
DOLPHIN_SRC="$SCRIPT_DIR/dolphin/pandax-lock.desktop"

# 目标路径
NAUTILUS_DST_DIR="$HOME/.local/share/nautilus/scripts"
DOLPHIN_DST_DIR="$HOME/.local/share/kservices5/ServiceMenus"

echo "==============================================="
echo "$TXT_TITLE"
echo "==============================================="
echo ""

# 1. 检查 pandax
if ! command -v pandax >/dev/null 2>&1; then
    echo "$TXT_NOT_FOUND"
    read -p "$TXT_CONFIRM " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "$TXT_FOUND $(command -v pandax)"
fi

# 2. 检测桌面环境
detect_desktop() {
    local de="${XDG_CURRENT_DESKTOP:-${DESKTOP_SESSION:-unknown}}"
    echo "$de" | tr '[:upper:]' '[:lower:]'
}

DE="$(detect_desktop)"
echo "$TXT_DETECT_DE $DE"

installed=0

# ============================================================
# 3. Nautilus（GNOME / Cinnamon / MATE）
# ============================================================
case "$DE" in
    *gnome*|*cinnamon*|*mate*|*unity*|*pop*)
        echo ""
        echo "$TXT_STEP_NAUTILUS"
        mkdir -p "$NAUTILUS_DST_DIR"

        # 拷贝 + 赋权
        cp "$NAUTILUS_SRC" "$NAUTILUS_DST_DIR/PandaX"
        chmod +x "$NAUTILUS_DST_DIR/PandaX"
        echo "$TXT_INSTALLED $NAUTILUS_DST_DIR/PandaX"
        installed=$((installed + 1))
        ;;
esac

# ============================================================
# 4. Dolphin（KDE / Plasma）
# ============================================================
case "$DE" in
    *kde*|*plasma*)
        echo ""
        echo "$TXT_STEP_DOLPHIN"
        mkdir -p "$DOLPHIN_DST_DIR"

        cp "$DOLPHIN_SRC" "$DOLPHIN_DST_DIR/pandax-lock.desktop"
        chmod +x "$DOLPHIN_DST_DIR/pandax-lock.desktop"

        # 刷新 KDE 服务缓存
        if command -v kbuildsycoca5 >/dev/null 2>&1; then
            kbuildsycoca5 --noincremental 2>/dev/null || true
        elif command -v kbuildsycoca6 >/dev/null 2>&1; then
            kbuildsycoca6 --noincremental 2>/dev/null || true
        fi
        echo "$TXT_INSTALLED $DOLPHIN_DST_DIR/pandax-lock.desktop"
        installed=$((installed + 1))
        ;;
esac

# ============================================================
# 5. 兜底：未检测到时主动询问
# ============================================================
if [ "$installed" -eq 0 ]; then
    echo ""
    echo "$TXT_NO_DE ($DE)"
    echo "$TXT_DE_SUPPORTED"
    echo ""
    read -p "$TXT_FORCE_NAUTILUS " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        mkdir -p "$NAUTILUS_DST_DIR"
        cp "$NAUTILUS_SRC" "$NAUTILUS_DST_DIR/PandaX"
        chmod +x "$NAUTILUS_DST_DIR/PandaX"
        echo "$TXT_FORCED_NAUTILUS"
        installed=$((installed + 1))
    fi

    read -p "$TXT_FORCE_KDE " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        mkdir -p "$DOLPHIN_DST_DIR"
        cp "$DOLPHIN_SRC" "$DOLPHIN_DST_DIR/pandax-lock.desktop"
        chmod +x "$DOLPHIN_DST_DIR/pandax-lock.desktop"
        echo "$TXT_FORCED_KDE"
        installed=$((installed + 1))
    fi
fi

# ============================================================
# 6. 总结
# ============================================================
echo ""
if [ "$installed" -gt 0 ]; then
    # 使用变量扩展后的字符串（必须在 installed 设置后）
    if [ "$USER_LANG" = "en" ]; then
        TXT_DONE="[OK] Installation complete (${installed} items)!"
    else
        TXT_DONE="[OK] 安装完成（${installed} 项）！"
    fi
    echo "$TXT_DONE"
    echo ""
    echo "$TXT_USAGE_HEADER"
    echo "$TXT_USAGE_NAUTILUS"
    echo "    $TXT_USAGE_NAUTILUS_1"
    echo ""
    echo "$TXT_USAGE_DOLPHIN"
    echo "    $TXT_USAGE_DOLPHIN_1"
    echo ""
    echo "$TXT_RESTART_HEADER"
    case "$DE" in
        *gnome*)   echo "$TXT_RESTART_GNOME" ;;
        *kde*|*plasma*) echo "$TXT_RESTART_KDE" ;;
        *cinnamon*) echo "$TXT_RESTART_CINNAMON" ;;
    esac
    echo ""
    echo "$TXT_UNINST_HEADER"
    echo "$TXT_UNINST_CMD"
else
    echo "$TXT_NOTHING"
fi
echo ""
