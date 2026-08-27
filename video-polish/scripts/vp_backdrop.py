#!/usr/bin/env python3
"""生成用来替换背景的背景图，配合 vp_bg.py 使用。

用法:
    python3 vp_backdrop.py --style bookshelf --size 720x1280 --out backdrop.png

风格:
    bookshelf  塞满书的书架（做成浅景深，避免抢主体）
    studio     深色渐变棚拍背景，最百搭
    grid       深色 + 细网格，偏科技感

想要照片级真实的背景，就自己用即梦 / Midjourney 生成一张，
直接喂给 vp_bg.py --bg，不必用这里的。
"""

import argparse
import os
import subprocess
import sys

from vp_cards import find_browser

# 定死随机序列，保证同一参数每次生成的图一样
def rng(seed):
    x = seed
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x / 0x7FFFFFFF


# 偏亮的自然书脊色。背景要跟被摄者的光比接近，太暗一眼就看出是合成的
SPINES = ["#7E8C99", "#9A7B5F", "#5F7C8C", "#A85D5D", "#7C9060", "#C0A067",
          "#6C7A88", "#9B7EA0", "#4F6473", "#C8BBA0", "#7692A0", "#8D6B5A",
          "#B4A88C", "#5D7F72"]


def bookshelf(W, H, seed=7):
    r = rng(seed)
    cols, rows = 3, 5
    cw, ch = W / cols, H / rows
    cells = []
    for i in range(rows):
        for j in range(cols):
            books, x = [], 0.0
            lean_at = int(next(r) * 14) if next(r) > 0.55 else -1
            while x < 88:
                w = 2.2 + next(r) * 3.4
                if x + w > 92:
                    break
                h = 62 + next(r) * 30
                c = SPINES[int(next(r) * len(SPINES)) % len(SPINES)]
                tilt = f"transform:rotate({4 + next(r) * 5:.1f}deg);" if len(books) == lean_at else ""
                cap = ("<i></i>" if next(r) > 0.6 else "")
                books.append(f'<b style="width:{w:.1f}%;height:{h:.0f}%;'
                             f'background:{c};{tilt}">{cap}</b>')
                x += w + 0.35
            stack = ""
            if next(r) > 0.62:                       # 偶尔来一摞平放的书
                sh = ""
                for _ in range(2 + int(next(r) * 2)):
                    sh += (f'<u style="width:{16 + next(r) * 10:.0f}%;'
                           f'background:{SPINES[int(next(r) * len(SPINES)) % len(SPINES)]}"></u>')
                stack = f'<div class="stack">{sh}</div>'
            cells.append(f'<div class="cell"><div class="books">{"".join(books)}</div>{stack}</div>')

    return f"""<!doctype html><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:#cfc4b4}}
.shelf{{position:absolute;inset:0;display:grid;
  grid-template-columns:repeat({cols},1fr);grid-template-rows:repeat({rows},1fr);
  background:linear-gradient(#d9c39c,#c3a97f);
  gap:{max(7, int(W * 0.020))}px;padding:{max(7, int(W * 0.020))}px}}
.cell{{background:linear-gradient(#efe9df,#ddd4c6);position:relative;
  display:flex;align-items:flex-end;padding:{int(cw * 0.045)}px;
  box-shadow:inset 0 {int(ch * 0.05)}px {int(ch * 0.08)}px rgba(90,70,45,.30),
             inset 0 -2px 0 rgba(120,95,60,.30)}}
.books{{display:flex;align-items:flex-end;gap:{max(1, int(cw * 0.006))}px;
  width:100%;height:100%}}
.books b{{display:block;border-radius:2px 2px 0 0;transform-origin:bottom left;
  box-shadow:inset -2px 0 0 rgba(0,0,0,.20), inset 2px 0 0 rgba(255,255,255,.16);
  position:relative}}
.books b i{{position:absolute;left:14%;right:14%;top:15%;height:4.5%;
  background:rgba(255,255,255,.45);border-radius:1px}}
.stack{{position:absolute;right:{int(cw * 0.06)}px;bottom:{int(ch * 0.05)}px;
  display:flex;flex-direction:column-reverse;gap:1px}}
.stack u{{display:block;height:{max(4, int(ch * 0.035))}px;border-radius:2px;
  box-shadow:0 1px 0 rgba(80,60,40,.35)}}
.lamp{{position:absolute;inset:0;background:
  radial-gradient(75% 50% at 50% 10%, rgba(255,236,205,.34), transparent 66%)}}
.vig{{position:absolute;inset:0;background:
  radial-gradient(95% 78% at 50% 42%, transparent 52%, rgba(60,45,30,.30) 100%)}}
.soft{{position:absolute;inset:-24px;backdrop-filter:blur(2.6px)}}
</style>
<div class="shelf">{"".join(cells)}</div>
<div class="lamp"></div><div class="soft"></div><div class="vig"></div>
"""


def studio(W, H):
    return f"""<!doctype html><meta charset="utf-8"><style>
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;background:#0d1117}}
.a{{position:absolute;inset:0;background:
 radial-gradient(78% 55% at 50% 24%, #3b4a5c 0%, #1a222c 68%)}}
.b{{position:absolute;inset:0;background:
 radial-gradient(46% 30% at 50% 16%, rgba(255,212,0,.20), transparent 72%)}}
.c{{position:absolute;inset:0;background:
 radial-gradient(96% 78% at 50% 46%, transparent 46%, rgba(0,0,0,.48) 100%)}}
</style><div class="a"></div><div class="b"></div><div class="c"></div>"""


def grid(W, H):
    g = max(28, int(W / 18))
    return f"""<!doctype html><meta charset="utf-8"><style>
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;background:#18202b}}
.g{{position:absolute;inset:0;background-image:
 linear-gradient(rgba(255,255,255,.075) 1px, transparent 1px),
 linear-gradient(90deg, rgba(255,255,255,.075) 1px, transparent 1px);
 background-size:{g}px {g}px}}
.b{{position:absolute;inset:0;background:
 radial-gradient(62% 38% at 50% 18%, rgba(255,212,0,.22), transparent 72%)}}
.c{{position:absolute;inset:0;background:
 radial-gradient(94% 76% at 50% 46%, transparent 42%, rgba(0,0,0,.58) 100%)}}
</style><div class="g"></div><div class="b"></div><div class="c"></div>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", default="bookshelf", choices=["bookshelf", "studio", "grid"])
    ap.add_argument("--size", default="1080x1920")
    ap.add_argument("--out", default="backdrop.png")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--browser", default=None)
    args = ap.parse_args()

    W, H = (int(v) for v in args.size.lower().split("x"))
    html = {"bookshelf": lambda: bookshelf(W, H, args.seed),
            "studio": lambda: studio(W, H),
            "grid": lambda: grid(W, H)}[args.style]()

    browser = find_browser(args.browser)
    if not browser:
        sys.exit("找不到 Chrome / Chromium / Edge，用 --browser 指定路径。")

    hp = os.path.splitext(args.out)[0] + ".html"
    with open(hp, "w", encoding="utf-8") as f:
        f.write(html)
    subprocess.run([browser, "--headless", "--disable-gpu", "--no-sandbox",
                    "--hide-scrollbars", "--force-device-scale-factor=1",
                    f"--window-size={W},{H}", f"--screenshot={args.out}",
                    f"file://{os.path.abspath(hp)}"], capture_output=True)
    os.remove(hp)
    if not os.path.exists(args.out):
        sys.exit("背景图渲染失败")
    print(f"{args.style} 背景 {W}x{H} -> {os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()
