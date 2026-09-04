#!/usr/bin/env bash
# ============================================================
# PandaX Linux 右键菜单安装脚本
# ============================================================
#
# 用法：
#   bash installer/linux/install_context_menu.sh
#
# 自动检测：
#   - Nautilus  (GNOME / Files)
#   - Dolphin   (KDE)
#   - 其他      (Thunar / Caja / PCManFM)
#
# 第一性原理：
#   - Linux 没有跨桌面通用的右键菜单标准
#   - 主流是 Nautilus 脚本（GNOME）和 .desktop 服务菜单（KDE）
#   - 用户级安装到 ~/.local/share/...，无需 sudo
#   - 幂等：重复运行安全
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAUTILUS_SRC="$SCRIPT_DIR/nautilus/PandaX"
DOLPHIN_SRC="$SCRIPT_DIR/dolphin/pandax-lock.desktop"

# 目标路径
NAUTILUS_DST_DIR="$HOME/.local/share/nautilus/scripts"
DOLPHIN_DST_DIR="$HOME/.local/share/kservices5/ServiceMenus"

echo "==============================================="
echo "PandaX Linux 右键菜单安装程序"
echo "==============================================="
echo ""

# 1. 检查 pandax
if ! command -v pandax >/dev/null 2>&1; then
    echo "[WARN] 未找到 pandax！请先 pip install pandax"
    read -p "是否仍要继续？[y/N] " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "[OK] 找到 pandax: $(command -v pandax)"
fi

# 2. 检测桌面环境
detect_desktop() {
    local de="${XDG_CURRENT_DESKTOP:-${DESKTOP_SESSION:-unknown}}"
    echo "$de" | tr '[:upper:]' '[:lower:]'
}

DE="$(detect_desktop)"
echo "[INFO] 检测到桌面环境: $DE"

installed=0

# ============================================================
# 3. Nautilus（GNOME / Cinnamon / MATE）
# ============================================================
case "$DE" in
    *gnome*|*cinnamon*|*mate*|*unity*|*pop*)
        echo ""
        echo "[1/2] 安装 Nautilus 脚本..."
        mkdir -p "$NAUTILUS_DST_DIR"

        # 拷贝 + 赋权
        cp "$NAUTILUS_SRC" "$NAUTILUS_DST_DIR/PandaX"
        chmod +x "$NAUTILUS_DST_DIR/PandaX"
        echo "[OK] 已安装: $NAUTILUS_DST_DIR/PandaX"
        installed=$((installed + 1))
        ;;
esac

# ============================================================
# 4. Dolphin（KDE / Plasma）
# ============================================================
case "$DE" in
    *kde*|*plasma*)
        echo ""
        echo "[2/2] 安装 Dolphin 服务菜单..."
        mkdir -p "$DOLPHIN_DST_DIR"

        cp "$DOLPHIN_SRC" "$DOLPHIN_DST_DIR/pandax-lock.desktop"
        chmod +x "$DOLPHIN_DST_DIR/pandax-lock.desktop"

        # 刷新 KDE 服务缓存
        if command -v kbuildsycoca5 >/dev/null 2>&1; then
            kbuildsycoca5 --noincremental 2>/dev/null || true
        elif command -v kbuildsycoca6 >/dev/null 2>&1; then
            kbuildsycoca6 --noincremental 2>/dev/null || true
        fi
        echo "[OK] 已安装: $DOLPHIN_DST_DIR/pandax-lock.desktop"
        installed=$((installed + 1))
        ;;
esac

# ============================================================
# 5. 兜底：未检测到时主动询问
# ============================================================
if [ "$installed" -eq 0 ]; then
    echo ""
    echo "[WARN] 未检测到支持的桌面环境（$DE）"
    echo "支持：GNOME / KDE / Cinnamon / MATE / Unity / Pop"
    echo ""
    read -p "是否强行安装 Nautilus 脚本？[y/N] " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        mkdir -p "$NAUTILUS_DST_DIR"
        cp "$NAUTILUS_SRC" "$NAUTILUS_DST_DIR/PandaX"
        chmod +x "$NAUTILUS_DST_DIR/PandaX"
        echo "[OK] 已强制安装 Nautilus 脚本"
        installed=$((installed + 1))
    fi

    read -p "是否强行安装 KDE 服务菜单？[y/N] " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        mkdir -p "$DOLPHIN_DST_DIR"
        cp "$DOLPHIN_SRC" "$DOLPHIN_DST_DIR/pandax-lock.desktop"
        chmod +x "$DOLPHIN_DST_DIR/pandax-lock.desktop"
        echo "[OK] 已强制安装 KDE 服务菜单"
        installed=$((installed + 1))
    fi
fi

# ============================================================
# 6. 总结
# ============================================================
echo ""
if [ "$installed" -gt 0 ]; then
    echo "[OK] 安装完成 ($installed 项)！"
    echo ""
    echo "使用方式："
    echo "  Nautilus（Files）:"
    echo "    右键 → 脚本 → PandaX → 选择操作"
    echo ""
    echo "  Dolphin（KDE）:"
    echo "    右键 → Actions → PandaX → 选择子操作"
    echo ""
    echo "重启文件管理器（如果菜单没出现）:"
    case "$DE" in
        *gnome*)   echo "  nautilus --quit && nautilus &" ;;
        *kde*|*plasma*) echo "  dolphin --shutdown && dolphin &" ;;
        *cinnamon*) echo "  nautilus --quit && cinnamon --restart &" ;;
    esac
    echo ""
    echo "卸载："
    echo "  bash installer/linux/uninstall_context_menu.sh"
else
    echo "[INFO] 未安装任何右键菜单。"
fi
echo ""