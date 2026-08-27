#!/usr/bin/env python3
"""把文案时间轴变成竖屏短视频风格的 ASS 字幕（自动跟随剪辑后的时间轴）。

用法:
    python3 vp_ass.py plan.json --segments segments.json --out subs.ass

segments.json: [{"start": 11.25, "end": 13.5, "text": "可能会取代人的工作"}, ...]
              时间是【原片】时间轴，脚本会按 plan.json 里保留的片段自动重新对时。

文本里用【】包住的部分会高亮成主题色，例如 "这就是【生产力】的提升"。
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

from vp_common import esc_path, timeline

CJK_PUNCT = "，。？！；：、,.?!;:…—"
NO_BREAK_BEFORE = "，。？！；：、,.?!;:）】》」』…"
NO_BREAK_AFTER = "（【《「『("


PROBE_ASS = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: P,{font},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,{spacing},0,1,0,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:01.00,P,,0,0,0,,{text}
"""


def measure_width(font, size, sample, W, H, fonts_dir=None):
    """渲染一帧再逐行扫描像素，量出这行字的实际墨迹宽度。

    不同中文字体的 hhea 度量差别很大：同一个 Fontsize 在 PingFang、微软雅黑、
    Noto Sans SC 下的实际字面能差三成，所以字号必须实测反推，不能照搬数字。
    """
    d = tempfile.mkdtemp(prefix="vpfit-")
    ap = os.path.join(d, "p.ass")
    with open(ap, "w", encoding="utf-8") as f:
        f.write(PROBE_ASS.format(w=W, h=H, font=font, size=size,
                                 spacing=round(size * 0.02), text=sample))
    vf = f"subtitles='{esc_path(ap)}'" + (f":fontsdir='{esc_path(fonts_dir)}'" if fonts_dir else "")
    r = subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi",
                        "-i", f"color=c=black:s={W}x{H}:d=1:r=1",
                        "-vf", vf + ",format=gray", "-frames:v", "1",
                        "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
    try:
        os.remove(ap)
        os.rmdir(d)
    except OSError:
        pass
    buf = r.stdout
    if len(buf) < W * H:
        return None
    hot = buf[:W * H].translate(bytes(255 if i > 48 else 0 for i in range(256)))
    lo, hi = W, -1
    for y in range(H):
        row = hot[y * W:(y + 1) * W]
        i = row.find(b"\xff")
        if i >= 0:
            lo = min(lo, i)
            hi = max(hi, row.rfind(b"\xff"))
    return hi - lo + 1 if hi >= lo else None


def autofit(font, W, H, units, fill, fonts_dir=None, base=100):
    """按『units 个汉字要占画面宽度的 fill』反推字号。"""
    sample = "汉" * max(1, int(round(units)))
    w = measure_width(font, base, sample, W, H, fonts_dir)
    if not w:
        return None
    return int(round(base * (W * fill) / w))


def to_ass_color(hex_rgb, alpha="00"):
    h = hex_rgb.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H{alpha}{b}{g}{r}".upper()


def ts(t):
    t = max(0.0, t)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def visual_len(s):
    """中文按 1 格、西文按 0.55 格估算，用来控制每行长度。"""
    n = 0.0
    for ch in s:
        n += 1.0 if ord(ch) > 0x2E7F else 0.55
    return n


def _is_word_char(ch):
    return ch.isascii() and (ch.isalnum() or ch in "'-")


def can_break(text, i):
    """能否在 text[:i] / text[i:] 之间断行。"""
    if i <= 0 or i >= len(text):
        return False
    prev, nxt = text[i - 1], text[i]
    if nxt in NO_BREAK_BEFORE or prev in NO_BREAK_AFTER:
        return False
    if _is_word_char(prev) and _is_word_char(nxt):   # 不拆英文单词
        return False
    return True


def _split_two(text, max_units):
    """两行均分：找最接近中点、且优先落在标点后的断点。"""
    total = visual_len(text)
    target = total / 2
    best, best_cost = None, None
    acc = 0.0
    for i, ch in enumerate(text):
        acc += 1.0 if ord(ch) > 0x2E7F else 0.55
        pos = i + 1
        if not can_break(text, pos):
            continue
        if acc > max_units or total - acc > max_units:
            continue
        cost = abs(acc - target)
        if ch in CJK_PUNCT:
            cost -= max_units * 0.30                 # 标点处断行更自然
        if best_cost is None or cost < best_cost:
            best, best_cost = pos, cost
    if best is None:
        return None
    return [text[:best].strip(), text[best:].strip()]


def wrap(text, max_units, max_lines):
    """中文字幕断行：一行放得下就不断；放不下优先两行均分；再长才贪心。"""
    text = text.strip()
    if not text:
        return [""]
    total = visual_len(text)
    if total <= max_units * 1.06:                    # 略微超出不值得断行
        return [text]

    if max_lines >= 2 and total <= max_units * 2:
        two = _split_two(text, max_units)
        if two:
            return two

    lines, cur = [], ""
    for i, ch in enumerate(text):
        wide = 1.0 if ord(ch) > 0x2E7F else 0.55
        if cur and visual_len(cur) + wide > max_units and can_break(text, i):
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)

    # 宁可多一行，也不把两行硬拼成会超出画面的长行——超框会被裁掉，丢字。
    return lines


def markup(text, accent):
    """把【…】转成高亮色，其余回到样式默认色。"""
    parts = re.split(r"【(.+?)】", text)
    out = ""
    for i, p in enumerate(parts):
        out += f"{{\\c{accent}}}{p}{{\\c}}" if i % 2 else p
    return out


def strip_markup(text):
    return re.sub(r"【(.+?)】", r"\1", text)


def highlights(text):
    return re.findall(r"【(.+?)】", text)


def wrap_marked(text, max_units, max_lines, accent):
    """先按纯文本断行（【】不占宽度），再把高亮词套回各行。

    高亮词被断行拆开时，该词就放弃高亮，避免出现半截着色。
    """
    words = highlights(text)
    lines = wrap(strip_markup(text), max_units, max_lines)
    if not words:
        return lines
    out = []
    for ln in lines:
        for w in words:
            if w and w in ln:
                ln = ln.replace(w, f"{{\\c{accent}}}{w}{{\\c}}", 1)
        out.append(ln)
    return out


def remap(segments, keepmap, min_dur):
    cues = []
    for seg in segments:
        s, e = float(seg["start"]), float(seg["end"])
        txt = seg.get("text", "").strip()
        if not txt:
            continue
        for ks, ke, base in keepmap:
            a, b = max(s, ks), min(e, ke)
            if b - a < min_dur:
                continue
            cues.append({"start": base + (a - ks), "end": base + (b - ks), "text": txt})
    cues.sort(key=lambda c: c["start"])

    merged = []
    for c in cues:                                    # 同一句被切成两段时合并
        if merged and merged[-1]["text"] == c["text"] and c["start"] - merged[-1]["end"] < 0.30:
            merged[-1]["end"] = c["end"]
        else:
            merged.append(c)
    for i in range(len(merged) - 1):                  # 消除重叠
        if merged[i]["end"] > merged[i + 1]["start"]:
            merged[i]["end"] = merged[i + 1]["start"]
    return [c for c in merged if c["end"] - c["start"] >= min_dur]


HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{font},{size},&H00FFFFFF,&H00FFFFFF,{outline_c},&H80000000,{bold},0,0,0,100,100,{spacing},0,1,{outline},{shadow},2,{ml},{mr},{mv},1
Style: Title,{font},{tsize},&H00FFFFFF,&H00FFFFFF,{plate_c},&H00000000,{bold},0,0,0,100,100,2,0,3,{pad},0,8,60,60,{tmv},1
Style: CTA,{font},{csize},&H00FFFFFF,&H00FFFFFF,{plate_c},&H00000000,{bold},0,0,0,100,100,2,0,3,{pad},0,8,60,60,{tmv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--segments", required=True)
    ap.add_argument("--out", default="subs.ass")
    ap.add_argument("--font", default=None)
    ap.add_argument("--size", type=int, default=None)
    ap.add_argument("--marginv", type=int, default=None)
    ap.add_argument("--accent", default=None, help="高亮色，如 #FFD400")
    ap.add_argument("--max-chars", type=float, default=None)
    ap.add_argument("--no-pop", action="store_true", help="关掉字幕弹出动效")
    ap.add_argument("--fill", type=float, default=None,
                    help="满行字幕占画面宽度的比例，默认 0.78")
    ap.add_argument("--no-autofit", action="store_true",
                    help="不实测字体宽度，直接用 size 的名义值")
    args = ap.parse_args()

    plan = json.load(open(args.plan, encoding="utf-8"))
    segs = json.load(open(args.segments, encoding="utf-8"))
    st = plan.get("subtitle_style", {})

    W, H = plan.get("size", [1080, 1920])
    font = args.font or st.get("font", "VP Sans SC")
    size = args.size or st.get("size", int(H * 0.040))
    mv = args.marginv if args.marginv is not None else st.get("margin_v", int(H * 0.225))
    accent = to_ass_color(args.accent or st.get("accent", "#FFD400"))
    outline_c = to_ass_color(st.get("outline_color", "#000000"))
    plate = to_ass_color(st.get("plate_color", "#141414"), st.get("plate_alpha", "2B"))
    max_chars = args.max_chars or st.get("max_chars", 12)
    pop = st.get("pop", True) and not args.no_pop
    ml = mr = int(W * 0.065)

    fill = args.fill if args.fill is not None else st.get("fill", 0.78)
    fonts_dir = plan.get("fonts_dir")
    tsize = int(size * 1.26)
    if not args.no_autofit and not (args.size or st.get("size_locked")):
        fit = autofit(font, W, H, max_chars, fill, fonts_dir)
        if fit:
            lo, hi = int(H * 0.028), int(H * 0.075)
            size = max(lo, min(hi, fit))
            ml = mr = int(W * (1 - fill) / 2 * 0.85)
        else:
            print("提示：字体宽度实测失败，改用名义字号", file=sys.stderr)
        widest = 0.0
        for ov in plan.get("overlays", []):
            for ln in ov["text"].split("\n"):
                widest = max(widest, visual_len(strip_markup(ln)))
        if widest:
            tfit = autofit(font, W, H, widest, min(0.88, fill + 0.08), fonts_dir)
            tsize = min(int(size * 1.35), tfit) if tfit else int(size * 1.26)
            tsize = max(int(size * 0.85), tsize)
        else:
            tsize = int(size * 1.26)

    keepmap, total = timeline(plan["segments"], plan.get("fps", 30))
    cues = remap(segs, keepmap, plan.get("min_cue", 0.18))

    head = HEADER.format(
        w=W, h=H, font=font, size=size, bold=1,
        outline=max(3, round(size * 0.085)), shadow=round(size * 0.03),
        spacing=round(size * 0.02), ml=ml, mr=mr, mv=mv, outline_c=outline_c,
        tsize=tsize, plate_c=plate, pad=max(10, round(size * 0.16)),
        tmv=int(H * 0.105), csize=int(tsize * 0.86),
    )

    lines, overlong = [], 0
    for c in cues:
        parts = wrap_marked(c["text"], max_chars, 2, accent)
        if len(parts) > 2:
            overlong += 1
        text = "\\N".join(parts)
        eff = "{\\fad(70,60)}"
        if pop:
            eff += "{\\fscx88\\fscy88\\t(0,110,\\fscx100\\fscy100)}"
        lines.append(f"Dialogue: 0,{ts(c['start'])},{ts(c['end'])},Sub,,0,0,0,,{eff}{text}")

    for ov in plan.get("overlays", []):
        style = "Title" if ov.get("type", "title") == "title" else "CTA"
        txt = "\\N".join(markup(x, accent) for x in ov["text"].split("\n"))
        eff = "{\\fad(180,180)}"
        lines.append(f"Dialogue: 1,{ts(ov['start'])},{ts(ov['end'])},{style},,0,0,0,,{eff}{txt}")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(lines) + "\n")

    print(f"字幕 {len(cues)} 条 + 覆盖文字 {len(plan.get('overlays', []))} 条 -> {args.out}")
    if overlong:
        print(f"提示：{overlong} 条字幕超过两行，可能挡脸。"
              f"把这几句在 segments.json 里拆短，或调大 max_chars。", file=sys.stderr)
    print(f"字号 正文 {size} / 标题 {tsize}（按 {font} 实测宽度自适应，满行占画面 {fill:.0%}）")
    print(f"成片时长约 {total:.2f} 秒")


if __name__ == "__main__":
    main()
