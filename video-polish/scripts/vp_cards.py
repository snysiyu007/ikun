#!/usr/bin/env python3
"""把配图卡描述渲染成 PNG，用无头 Chrome 排版，只靠原片以外的零素材。

用法:
    python3 vp_cards.py cards.json --out cards/ [--browser /path/to/chrome]

cards.json:
{
 "size": [1080, 1920],
 "font": "PingFang SC",
 "accent": "#FFD400",
 "cards": [
   {"id":"steam", "type":"statement", "icon":"steam",
    "title":"蒸汽机<em>本身</em><br>不提升生产力", "sub":"把它装进汽车的人才提升了"},
   {"id":"vs", "type":"versus", "title":"岗位没消失，只是换了工具",
    "left":{"icon":"carriage","label":"马夫","note":"3 小时"},
    "right":{"icon":"car","label":"司机","note":"半小时"}},
   {"id":"flow", "type":"flow", "title":"生产力是怎么跃迁的",
    "steps":[{"icon":"steam","label":"蒸汽机被发明"},
             {"icon":"car","label":"有人把它装进汽车"},
             {"icon":"bolt","label":"生产力才真正提升"}]},
   {"id":"num", "type":"stat", "value":"1/6", "unit":"", "title":"同样的路程",
    "sub":"马车 3 小时 → 汽车 半小时"},
   {"id":"tools", "type":"chips", "title":"都是在做同一件事",
    "sub":"把蒸汽机放进新的载体", "chips":["通义千问","CodeBuddy","Claude Code","Codex"]}
 ]
}

type 可选 statement / versus / flow / stat / chips。
mode 设成 "banner" 时输出带透明背景的窄条，压在人物上方的空白区域。
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

from vp_icons import svg

BROWSERS = [
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def find_browser(explicit=None):
    if explicit:
        return explicit
    for name in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge", "brave-browser"):
        p = shutil.which(name)
        if p:
            return p
    for p in BROWSERS:
        if os.path.exists(p):
            return p
    return None


CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:{W}px;height:{H}px;background:{bg};overflow:hidden;
 font-family:"{font}","PingFang SC","Microsoft YaHei","Noto Sans SC",sans-serif;
 color:#fff;-webkit-font-smoothing:antialiased}
.glow{position:absolute;left:50%;top:{glow}px;transform:translate(-50%,-50%);
 width:1200px;height:1200px;border-radius:50%;
 background:radial-gradient({accent}22,transparent 62%)}
.box{position:absolute;left:0;right:0;top:{top}px;height:{boxh}px;
 display:flex;flex-direction:column;align-items:center;justify-content:center;
 padding:0 {pad}px;text-align:center}
.icon{display:block}
em{color:{accent};font-style:normal}
.title{font-weight:800;line-height:1.24;letter-spacing:1px}
.sub{margin-top:{gap}px;color:#8E99A8;font-weight:600;line-height:1.4}
.kicker{color:{accent};font-weight:800;letter-spacing:6px;margin-bottom:{gap}px}
.row{display:flex;align-items:stretch;justify-content:center;gap:{pad}px;width:100%}
.col{flex:1;display:flex;flex-direction:column;align-items:center;gap:{gap}px}
.col .lab{font-weight:800}
.col .note{color:{accent};font-weight:800}
.vs{align-self:center;color:#55637A;font-weight:800}
.steps{display:flex;flex-direction:column;gap:{gap}px;width:100%}
.step{display:flex;align-items:center;gap:{pad}px;background:#141922;
 border-radius:28px;padding:{gap}px {pad}px;text-align:left}
.step .lab{font-weight:700;line-height:1.3}
.step .n{color:{accent};font-weight:800;opacity:.5}
.arrow{color:{accent};text-align:center;font-weight:800;opacity:.7;line-height:.6}
.big{font-weight:800;color:{accent};line-height:1;letter-spacing:-2px}
.chips{display:flex;flex-wrap:wrap;justify-content:center;gap:{gap}px;width:100%}
.chip{background:#141922;border:3px solid #232B37;border-radius:999px;
 padding:{cy}px {pad}px;font-weight:700;white-space:nowrap}
"""


def build_html(card, cfg):
    W, H = cfg["size"]
    banner = card.get("mode") == "banner"
    s = W / 1080.0                       # 所有字号按画布宽度等比缩放
    accent = cfg.get("accent", "#FFD400")
    bg = "transparent" if banner else cfg.get("bg", "#0B0E13")

    if banner:
        top, boxh = int(30 * s), int(H - 60 * s)
    else:
        # 留出底部字幕带，内容整体往上放
        top, boxh = int(190 * s), int(1130 * s)

    css = (CSS.replace("{W}", str(W)).replace("{H}", str(H))
              .replace("{bg}", bg).replace("{font}", cfg.get("font", "PingFang SC"))
              .replace("{accent}", accent).replace("{top}", str(top))
              .replace("{boxh}", str(boxh)).replace("{pad}", str(int(64 * s)))
              .replace("{gap}", str(int(30 * s))).replace("{cy}", str(int(20 * s)))
              .replace("{glow}", str(top + boxh // 2)))

    t = card.get("type", "statement")
    ic = lambda n, px: svg(n, accent, int(px * s)) if n else ""
    fs = lambda px: f"font-size:{int(px * s)}px"
    parts = []
    if not banner:
        parts.append('<div class=glow></div>')
    parts.append('<div class=box>')

    if card.get("kicker"):
        parts.append(f'<div class=kicker style="{fs(38)}">{card["kicker"]}</div>')

    if t == "statement":
        if card.get("icon"):
            parts.append(f'<div style="margin-bottom:{int(46*s)}px">{ic(card["icon"], 210)}</div>')
        parts.append(f'<div class=title style="{fs(card.get("size", 112))}">{card["title"]}</div>')
        if card.get("sub"):
            parts.append(f'<div class=sub style="{fs(48)}">{card["sub"]}</div>')

    elif t == "versus":
        if card.get("title"):
            parts.append(f'<div class=title style="{fs(64)};margin-bottom:{int(56*s)}px">'
                         f'{card["title"]}</div>')
        cols = []
        for side in ("left", "right"):
            c = card[side]
            cols.append(f'<div class=col>{ic(c.get("icon"), 190)}'
                        f'<div class=lab style="{fs(66)}">{c["label"]}</div>'
                        f'<div class=note style="{fs(80)}">{c.get("note","")}</div></div>')
        div = card.get("divider", "→")
        parts.append(f'<div class=row>{cols[0]}<div class=vs style="{fs(56)}">{div}</div>{cols[1]}</div>')
        if card.get("sub"):
            parts.append(f'<div class=sub style="{fs(46)}">{card["sub"]}</div>')

    elif t == "flow":
        if card.get("title"):
            parts.append(f'<div class=title style="{fs(62)};margin-bottom:{int(46*s)}px">'
                         f'{card["title"]}</div>')
        rows = []
        for i, st in enumerate(card["steps"]):
            if i:
                rows.append(f'<div class=arrow style="{fs(58)}">↓</div>')
            rows.append(f'<div class=step>{ic(st.get("icon"), 108)}'
                        f'<div class=lab style="{fs(54)}">{st["label"]}</div></div>')
        parts.append(f'<div class=steps>{"".join(rows)}</div>')

    elif t == "stat":
        parts.append(f'<div class=big style="{fs(card.get("size", 300))}">'
                     f'{card["value"]}<span style="{fs(110)}">{card.get("unit","")}</span></div>')
        if card.get("title"):
            parts.append(f'<div class=title style="{fs(76)};margin-top:{int(36*s)}px">'
                         f'{card["title"]}</div>')
        if card.get("sub"):
            parts.append(f'<div class=sub style="{fs(50)}">{card["sub"]}</div>')

    elif t == "chips":
        if card.get("icon"):
            parts.append(f'<div style="margin-bottom:{int(40*s)}px">{ic(card["icon"], 170)}</div>')
        if card.get("title"):
            parts.append(f'<div class=title style="{fs(74)};margin-bottom:{int(48*s)}px">'
                         f'{card["title"]}</div>')
        chips = "".join(f'<div class=chip style="{fs(50)}">{c}</div>' for c in card["chips"])
        parts.append(f'<div class=chips>{chips}</div>')
        if card.get("sub"):
            parts.append(f'<div class=sub style="{fs(46)}">{card["sub"]}</div>')

    else:
        sys.exit(f"未知卡片类型：{t}")

    parts.append('</div>')
    return f'<!doctype html><meta charset="utf-8"><style>{css}</style>{"".join(parts)}'


def render(card, cfg, outdir, browser):
    W, H = cfg["size"]
    if card.get("mode") == "banner":
        H = card.get("height", int(H * 0.30))
    html = build_html(card, {**cfg, "size": [W, H]})
    hp = os.path.join(outdir, f"{card['id']}.html")
    pp = os.path.join(outdir, f"{card['id']}.png")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(html)
    cmd = [browser, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
           "--force-device-scale-factor=1", f"--window-size={W},{H}",
           f"--screenshot={pp}", f"file://{os.path.abspath(hp)}"]
    if card.get("mode") == "banner":
        cmd.insert(2, "--default-background-color=00000000")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.exists(pp):
        sys.exit(f"渲染 {card['id']} 失败：\n{r.stderr[-600:]}")
    return pp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out", default="cards")
    ap.add_argument("--browser", default=None)
    ap.add_argument("--keep-html", action="store_true")
    args = ap.parse_args()

    browser = find_browser(args.browser)
    if not browser:
        sys.exit("找不到 Chrome / Chromium / Edge。装一个，或用 --browser 指定可执行文件路径。")

    cfg = json.load(open(args.spec, encoding="utf-8"))
    cfg.setdefault("size", [1080, 1920])
    os.makedirs(args.out, exist_ok=True)

    made = []
    for card in cfg["cards"]:
        p = render(card, cfg, args.out, browser)
        made.append(p)
        print(f"  {card['id']:<14} {card.get('type','statement'):<10} -> {os.path.basename(p)}")
        if not args.keep_html:
            os.remove(os.path.join(args.out, f"{card['id']}.html"))

    print(f"\n配图卡 {len(made)} 张 -> {os.path.abspath(args.out)}")
    print(f"用的浏览器：{browser}")


if __name__ == "__main__":
    main()
