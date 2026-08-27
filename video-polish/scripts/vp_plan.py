#!/usr/bin/env python3
"""生成 plan.json：选段 → 自动剔除段内停顿 → 分配镜头变焦 → 写出渲染计划。

用法:
    python3 vp_plan.py --analysis analysis.json \\
        --pick "11.25-17.75,27.88-38.38,148.88-168.88" \\
        --out plan.json --trim-silence

不传 --pick 就用整条视频（只做停顿精简）。
"""

import argparse
import json
import os


def parse_pick(s, duration):
    if not s:
        return [[0.0, duration]]
    out = []
    for part in s.replace("，", ",").split(","):
        part = part.strip()
        if not part:
            continue
        a, b = part.split("-")
        out.append([float(a), float(b)])
    return out


def intersect(picks, keeps, min_len):
    """把选段和『非静音段』求交集，得到实际保留的小片段。"""
    out = []
    for gi, (ps, pe) in enumerate(picks):
        subs = []
        for ks, ke in keeps:
            a, b = max(ps, ks), min(pe, ke)
            if b - a >= min_len:
                subs.append([round(a, 3), round(b, 3)])
        if not subs:
            subs = [[round(ps, 3), round(pe, 3)]]
        # 相隔很近的小片段合并回去，避免过碎
        merged = [subs[0]]
        for s, e in subs[1:]:
            if s - merged[-1][1] < 0.12:
                merged[-1][1] = e
            else:
                merged.append([s, e])
        for s, e in merged:
            out.append({"start": s, "end": e, "group": gi})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--pick", default="")
    ap.add_argument("--out", default="plan.json")
    ap.add_argument("--input", default=None)
    ap.add_argument("--output", default="out.mp4")
    ap.add_argument("--subtitles", default="subs.ass")
    ap.add_argument("--trim-silence", action="store_true")
    ap.add_argument("--min-len", type=float, default=0.35)
    ap.add_argument("--zooms", default="1.0,1.06",
                    help="镜头变焦循环值，逐段轮换，制造多机位错觉")
    ap.add_argument("--size", default="1080x1920")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--crop", default=None, help="w:h:x:y，默认用 analysis.json 的建议值")
    ap.add_argument("--fonts-dir", default=None)
    ap.add_argument("--progress-bar", action="store_true")
    args = ap.parse_args()

    an = json.load(open(args.analysis, encoding="utf-8"))
    picks = parse_pick(args.pick, an["duration"])

    if args.trim_silence:
        segs = intersect(picks, an.get("keep_suggestion") or [[0, an["duration"]]], args.min_len)
    else:
        segs = [{"start": round(a, 3), "end": round(b, 3), "group": i}
                for i, (a, b) in enumerate(picks)]

    zooms = [float(z) for z in args.zooms.split(",")]
    for s in segs:
        s["zoom"] = zooms[s["group"] % len(zooms)]

    if args.crop:
        w, h, x, y = (int(v) for v in args.crop.split(":"))
        crop = {"w": w, "h": h, "x": x, "y": y}
    else:
        crop = an.get("crop_suggestion")
        if not crop:
            raise SystemExit("analysis.json 里没有裁切建议，请用 --crop 手动指定")
        crop = {k: crop[k] for k in ("w", "h", "x", "y")}

    W, H = (int(v) for v in args.size.lower().split("x"))
    plan = {
        "input": args.input or an["input"],
        "output": args.output,
        "size": [W, H],
        "fps": args.fps,
        "source_crop": crop,
        "segments": [{"start": s["start"], "end": s["end"], "zoom": s["zoom"]} for s in segs],
        "look": {"denoise": "2:1:3:3", "sharpen": 0.55, "brightness": 0.025,
                 "contrast": 1.10, "saturation": 1.10},
        "audio": {"highpass": 85, "denoise": True, "presence": 3.0,
                  "compress": True, "lufs": -14.0},
        "subtitle_style": {"font": "VP Sans SC", "size": int(H * 0.040),
                           "margin_v": int(H * 0.225), "accent": "#FFD400",
                           "max_chars": 12, "pop": True},
        "subtitles": args.subtitles,
        "overlays": [],
        "cover": {"at": 0.8, "path": "cover.jpg"},
        "crf": 18,
    }
    if args.fonts_dir:
        plan["fonts_dir"] = args.fonts_dir
    if args.progress_bar:
        plan["progress_bar"] = True

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=1)

    total = sum(s["end"] - s["start"] for s in segs)
    picked = sum(b - a for a, b in picks)
    print(f"选段 {len(picks)} 组 / 实际片段 {len(segs)} 个")
    print(f"选段总长 {picked:.2f}s → 剔除停顿后 {total:.2f}s（省 {picked-total:.2f}s）")
    print(f"裁切 crop={crop['w']}:{crop['h']}:{crop['x']}:{crop['y']} → {W}x{H}")
    print(f"计划 -> {os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()
