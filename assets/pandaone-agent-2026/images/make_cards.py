"""Generate supporting text-card images for Xiaohongshu post via Playwright."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

OUT = Path(r"d:\绿联云办公\项目 水龙头项目 CodeAudit_项目文档\assets\pandaone-agent-2026\images")
OUT.mkdir(exist_ok=True, parents=True)

# Card content
CARDS = [
    {
        "filename": "card1_what.png",
        "bg": "#fff8f0",
        "title": "一句话讲清楚 Pandaone",
        "lines": [
            ("AI Agent 改代码前的", "#1c1917"),
            ("最后一道", "#1c1917"),
            ("人工闸门", "#dc2626", "bold-underline"),
        ],
        "footer": "Lock · Audit · Approve",
    },
    {
        "filename": "card2_layers.png",
        "bg": "#f0f9ff",
        "title": "5 层防御 · 第一性原理",
        "lines": [
            ("L1 文件锁 · L2 watchdog", "#1c1917"),
            ("L3 pre-commit hook", "#1c1917"),
            ("L4 README startup", "#1c1917"),
            ("L5 自指纹", "#1c1917"),
        ],
        "footer": "挡住 AI 改代码的所有路径",
    },
    {
        "filename": "card3_install.png",
        "bg": "#f0fdf4",
        "title": "4 行命令 · 装完",
        "code": "pip install pandaone-guard\npandaone init --root .\npandaone lock\npandaone install-hook",
        "footer": "已发版 · PyPI: pandaone-guard",
    },
    {
        "filename": "card4_suits.png",
        "bg": "#fef3c7",
        "title": "适合谁",
        "lines": [
            ("• 团队刚把 agent 接进 CI/CD", "#1c1917"),
            ("• 一个人写项目,想不依赖人脑 review", "#1c1917"),
            ("• 老被问 'agent 改坏了怎么发现'", "#1c1917"),
        ],
        "footer": "开源免费 · GitHub hellob1889/Pandaone-AI-Agent",
    },
]


async def render_card(page, card):
    html = f"""<!doctype html><html><head><meta charset='utf-8'><style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ width: 1080px; height: 1440px; background: {card['bg']}; padding: 100px 80px; font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; }}
    .title {{ font-size: 64px; font-weight: 700; color: #4f46e5; margin-bottom: 80px; letter-spacing: -0.02em; }}
    .line {{ font-size: 72px; line-height: 1.4; font-weight: 500; }}
    .line span.highlight {{ color: #dc2626; font-weight: 800; text-decoration: underline; text-decoration-thickness: 6px; text-underline-offset: 12px; }}
    pre {{ font-size: 56px; line-height: 1.6; color: #16a34a; background: #1c1917; padding: 60px; border-radius: 30px; font-family: 'JetBrains Mono', Consolas, monospace; white-space: pre-wrap; word-break: break-all; }}
    .footer {{ position: absolute; bottom: 100px; left: 80px; right: 80px; font-size: 36px; color: #78716c; border-top: 4px solid #e7e5e4; padding-top: 30px; }}
    </style></head><body>
    <div class='title'>{card['title']}</div>
    """
    if 'code' in card:
        html += f"<pre>{card['code']}</pre>"
    else:
        for line in card['lines']:
            text, color, *style = line if isinstance(line, tuple) else (line, "#1c1917")
            cls = "highlight" if style and "bold-underline" in style else ""
            html += f"<div class='line'>{text.replace('XHIGHLIGHTX', f'<span class={chr(34)}{cls}{chr(34)}>').replace('XENDX', '</span>')}</div>"
    html += f"<div class='footer'>{card['footer']}</div></body></html>"
    await page.set_content(html, wait_until="networkidle")
    await page.wait_for_timeout(300)
    elt = await page.query_selector("body")
    out_path = OUT / card["filename"]
    await elt.screenshot(path=str(out_path))
    print(f"  {out_path}")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(viewport={"width": 1080, "height": 1440}, device_scale_factor=1)
        page = await ctx.new_page()
        for card in CARDS:
            await render_card(page, card)
        await browser.close()


asyncio.run(main())