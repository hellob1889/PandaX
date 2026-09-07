#!/usr/bin/env bash
# ============================================================
# PandaX Linux 右键菜单卸载脚本
# ============================================================
set -e

NAUTILUS_DST="$HOME/.local/share/nautilus/scripts/PandaX"
DOLPHIN_DST="$HOME/.local/share/kservices5/ServiceMenus/pandax-lock.desktop"

echo "==============================================="
echo "PandaX Linux 右键菜单卸载程序"
echo "==============================================="
echo ""

removed=0
if [ -e "$NAUTILUS_DST" ]; then
    rm -f "$NAUTILUS_DST"
    echo "[REMOVE] $NAUTILUS_DST"
    removed=$((removed + 1))
fi

if [ -e "$DOLPHIN_DST" ]; then
    rm -f "$DOLPHIN_DST"
    echo "[REMOVE] $DOLPHIN_DST"
    removed=$((removed + 1))

    # 刷新 KDE
    if command -v kbuildsycoca5 >/dev/null 2>&1; then
        kbuildsycoca5 --noincremental 2>/dev/null || true
    elif command -v kbuildsycoca6 >/dev/null 2>&1; then
        kbuildsycoca6 --noincremental 2>/dev/null || true
    fi
fi

if [ "$removed" -eq 0 ]; then
    echo "[INFO] PandaX 右键菜单未安装。"
else
    echo ""
    echo "[OK] 已移除 $removed 项。"
fi
echo ""