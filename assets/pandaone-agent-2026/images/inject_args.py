"""Inject Xiaohongshu post content via direct call to bash script."""
import subprocess
from pathlib import Path

POST_DIR = "/mnt/d/绿联云办公/项目 水龙头项目 CodeAudit_项目文档/assets/pandaone-agent-2026"
SCRIPT = "/mnt/c/Users/Administrator/.trae-cn/plugins/trae-remote-official/rednote-post/0.1.3/skills/rednote-post/scripts/inject-content.sh"

TITLE = "agent 改代码我装了一道闸"
BODY = """说真的,上次 cursor 把我 .py 文件改了,我事后 3 天才发现有个 bug,差点上线

后来朋友推荐了 Pandaone(原 PandaX),装了一下午,我现在每次让 AI 改代码都得走它

它的逻辑挺简单:
改之前必须告诉它为什么改、要解决什么问题、用什么方法,差一项都不让写
改完了会发到浏览器,我自己盯一眼再放行
还能追到是哪个 agent 改的,Cursor / Trae / Claude Code 都行

最戳我的是文件夹图标会变色,locked 是熊猫头 unlocked 是透明,扫一眼就知道现在什么状态

适合谁:
1. 团队刚把 agent 接进 CI/CD 的
2. 一个人写项目,想让代码 review 不依赖人脑
3. 老被人问 "你那个 agent 改坏了怎么发现" 的

怎么装:
pip install pandaone-guard
pandaone init --root .
pandaone lock
pandaone install-hook

这套下来体感是真不焦虑了,AI 改完了我自己把关,出错率肉眼可见往下掉

GitHub: github.com/hellob1889/Pandaone-AI-Agent
开源免费,欢迎吐槽"""
TAGS = "AI编程助手,代码审计,开源工具,Cursor规则,AIAgent,效率工具,程序员的日常,干货分享,Cursor,开发者工具"
IMAGES = "cover_dashboard.png,card1_what.png,card2_layers.png,card3_install.png,card4_suits.png"

cmd = [
    "bash", SCRIPT, str(POST_DIR),
    "--title", TITLE,
    "--body", BODY,
    "--tags", TAGS,
    "--images", IMAGES,
]
res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:", res.stdout)
print("STDERR:", res.stderr)
print("RC:", res.returncode)