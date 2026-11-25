"""
カードイラスト（illust/*.webp）と cards.json をゲーム本体の描画コードから書き出すスクリプト。

使い方（リポジトリのルートで実行）:
    pip install playwright pillow
    python -m playwright install chromium
    python tools/export_illust.py              # 全カードを書き出し
    python tools/export_illust.py N001 SW-UR005   # 指定したIDだけ書き出し

※ cards.json を作り直すのは全件書き出しのときだけです（手で編集したカード名は上書きされます）。
"""
import asyncio, io, json, sys
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
ONLY = set(sys.argv[1:])


async def main():
    (ROOT / "illust").mkdir(exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 840, "height": 1000})
        await page.goto((ROOT / "index.html").as_uri())
        await page.wait_for_timeout(500)
        cards = await page.evaluate("""() => { const P = window.__prisma;
          return P.CARDS.map(c => ({ id: c.code, no: c.id, pack: P.PACKS[c.pk].title, name: c.name, rarity: c.rarity,
            element: c.elName, motif: c.motif,
            theme: `${c.tag} × ${c.motif}`, file: c.file,
            svg: P.artTpl(c, false).replaceAll('§', 'a').replace('<svg ', '<svg width="840" height="1000" ') })) }""")
        for c in cards:
            svg = c.pop("svg")
            if ONLY and c["id"] not in ONLY:
                continue
            await page.set_content(f"<html><body style='margin:0'>{svg}</body></html>")
            png = await page.screenshot(clip={"x": 0, "y": 0, "width": 840, "height": 1000})
            Image.open(io.BytesIO(png)).convert("RGB").save(ROOT / c["file"], "WEBP", quality=86, method=6)
            print("wrote", c["file"])
        if not ONLY:
            (ROOT / "cards.json").write_text(json.dumps(cards, ensure_ascii=False, indent=1), encoding="utf-8")
            print("wrote cards.json", len(cards))
        await browser.close()

asyncio.run(main())
