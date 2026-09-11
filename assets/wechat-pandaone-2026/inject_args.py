"""Inject wechat article content via bash script."""
import subprocess

POST_DIR = "/mnt/d/绿联云办公/项目 水龙头项目 CodeAudit_项目文档/assets/wechat-pandaone-2026"
SCRIPT = "/mnt/c/Users/Administrator/.trae-cn/plugins/trae-remote-official/wechat-mp-article/0.1.1/skills/wechat-mp-article/scripts/inject-content.sh"
TITLE = "我让 AI 改代码,装了一道闸"

cmd = [
    "bash", SCRIPT, POST_DIR,
    "--title", TITLE,
    "--body-file", f"{POST_DIR}/body.html",
]
res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
print("RC:", res.returncode)