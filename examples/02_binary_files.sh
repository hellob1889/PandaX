#!/bin/bash
# 02_binary_files.sh
# ============================================================
# Pandaone AI Agent 二进制文件保护 demo
# ============================================================
# 演示：init 时建立 SHA256 snapshot → write 替换 → 检测篡改
# 预期：直接覆盖 .png 后 status 显示 SHA256 mismatch
# ============================================================
set -e

G="\033[92m"; Y="\033[93m"; B="\033[94m"; R="\033[91m"; W="\033[0m"

PROJECT="$(pwd)/demo_02_binary"
GIT_EXE="$(command -v git)"

echo -e "${B}============================================================${W}"
echo -e "${B}  Pandaone 二进制文件保护 demo${W}"
echo -e "${B}============================================================${W}"

rm -rf "$PROJECT"
mkdir -p "$PROJECT/assets"
cd "$PROJECT"

# 准备初始二进制文件
echo -e "\n${Y}[1/5] 准备初始二进制文件${W}"
printf '\x89PNG\r\n\x1a\nOLD_LOGO_CONTENT' > assets/logo.png
printf '\xff\xd8\xff\xe0OLD_PHOTO' > assets/photo.jpg
printf 'PK\x03\x04OLD_ZIP' > assets/data.zip
ls -la assets/

# 1. init
echo -e "\n${Y}[2/5] pandaone init（建立 snapshot）${W}"
python -m pandaone init --root "$PROJECT" 2>&1 | grep -E "snapshot|init" | tail -3

# 查看 snapshot
echo "  当前 snapshot:"
cat .pandaone/binary_snapshots.json | python -m json.tool | head -10

# 2. 合规 write 替换 logo
echo -e "\n${Y}[3/5] 合规 write 替换 logo.png${W}"
printf '\x89PNG\r\n\x1a\nNEW_LOGO_V2' > /tmp/new_logo.png
python -m pandaone write \
  --root "$PROJECT" \
  --file assets/logo.png \
  --reason "升级 logo" \
  --problem "品牌色变更" \
  --approach "用新 PNG 替换" \
  --from-file /tmp/new_logo.png 2>&1 | tail -2

echo "  ✓ snapshot 已更新:"
cat .pandaone/binary_snapshots.json | python -m json.tool | head -10

# 3. 攻击：直接覆盖 photo.jpg
echo -e "\n${Y}[4/5] 攻击：直接覆盖 photo.jpg（绕过 write）${W}"
chmod +w assets/photo.jpg
printf '\xff\xd8\xff\xe0HIJACKED_PHOTO' > assets/photo.jpg
echo "  ⚠️  photo.jpg 已被覆盖（绕过 write）"

# 4. status 显示 mismatch
echo -e "\n${Y}[5/5] status 检测到篡改${W}"
python -m pandaone status --root "$PROJECT" 2>&1 | tail -15

echo -e "\n${B}============================================================${W}"
echo -e "${B}  预期：status 显示 photo.jpg SHA256 mismatch${W}"
echo -e "${B}============================================================${W}"