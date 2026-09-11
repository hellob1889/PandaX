"""Render social-preview.svg into a PNG (1280x640) using headless Playwright."""
import asyncio
import base64
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SVG_PATH = ROOT / "social-preview.svg"
PNG_OUT = ROOT / "social-preview.png"

# Try Playwright first (most reliable)
async def with_playwright():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return None
    svg = SVG_PATH.read_text(encoding="utf-8")
    html = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<style>html,body{margin:0;padding:0;background:#000;width:1280px;height:640px;overflow:hidden}"
        "svg{display:block;width:1280px;height:640px}</style>"
        "</head><body>" + svg + "</body></html>"
    )
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(viewport={"width": 1280, "height": 640}, device_scale_factor=1)
        page = await ctx.new_page()
        await page.set_content(html, wait_until="networkidle")
        await page.wait_for_timeout(300)
        elt = await page.query_selector("svg")
        if not elt:
            await browser.close()
            return None
        await elt.screenshot(path=str(PNG_OUT), omit_background=False)
        await browser.close()
        return str(PNG_OUT)

# Fallback: cairosvg
def with_cairosvg():
    try:
        import cairosvg  # type: ignore
    except ImportError:
        return None
    cairosvg.svg2png(url=str(SVG_PATH), write_to=str(PNG_OUT), output_width=1280, output_height=640)
    return str(PNG_OUT)

# Fallback: inkscape CLI
def with_inkscape():
    import subprocess
    if not any(pathlib.Path(p).exists() for p in [r"C:\Program Files\Inkscape\bin\inkscape.exe"]):
        return None
    subprocess.run([
        r"C:\Program Files\Inkscape\bin\inkscape.exe",
        str(SVG_PATH),
        "--export-type=png",
        "--export-width=1280",
        "--export-height=640",
        f"--export-filename={PNG_OUT}",
    ], check=True)
    return str(PNG_OUT)

async def main():
    out = await with_playwright()
    if not out:
        out = with_cairosvg()
    if not out:
        out = with_inkscape()
    if not out:
        print("ERROR: no SVG-to-PNG backend available", file=sys.stderr)
        sys.exit(2)
    print(out)

if __name__ == "__main__":
    asyncio.run(main())
