#!/usr/bin/env bash
# ============================================================
# Pandaone AI Agent macOS 右键服务卸载脚本
# ============================================================
set -e

SERVICES_DIR="$HOME/Library/Services"
WORKFLOW_DST="$SERVICES_DIR/Pandaone Lock.workflow"

echo "==============================================="
echo "Pandaone macOS 右键服务卸载程序"
echo "==============================================="
echo ""

if [ ! -e "$WORKFLOW_DST" ]; then
    echo "[INFO] Pandaone 服务未安装。"
    exit 0
fi

rm -rf "$WORKFLOW_DST"
echo "[REMOVE] $WORKFLOW_DST"

# 刷新 Launch Services
LSREGISTER=/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister
if [ -x "$LSREGISTER" ]; then
    "$LSREGISTER" -kill -r -domain user 2>/dev/null || true
    echo "[OK] Launch Services 已刷新"
fi

echo ""
echo "[OK] Pandaone 服务已卸载。"
echo ""