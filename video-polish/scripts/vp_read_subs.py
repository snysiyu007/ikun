#!/usr/bin/env python3
"""原片已经烧录了字幕时，把字幕带切成带序号的拼图，供人（或多模态模型）直接读出文案。

用法:
    python3 vp_read_subs.py 原片.mp4 --analysis analysis.json --out subsheets

产出:
    subsheets/runs.json   每条字幕的序号与起止时间（原片时间轴）
    subsheets/s00.jpg …   带序号的字幕拼图

读完图后，把文字按序号一行一条写进 texts.txt，再合并成 segments.json：

    python3 vp_read_subs.py --merge subsheets/runs.json texts.txt --out segments.json

只依赖 ffmpeg 和 Python 标准库。
"""

import argparse
import json
import os
import subprocess
import sys


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-show_entries", "stream=width,height",
                          "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", path],
                         capture_output=True, text=True).stdout.split()
    return int(out[0]), int(out[1]), float(out[2])


def band_from(args, H):
    if args.band:
        a, b = (float(v) for v in args.band.split(","))
        top, bot = (int(a), int(b)) if a > 1 else (int(a * H), int(b * H))
    else:
        an = json.load(open(args.analysis, encoding="utf-8"))
        b = an.get("burned_subtitle_band")
        if not b:
            sys.exit("analysis.json 里没有检测到烧录字幕带，请用 --band 顶,底 手动指定像素位置")
        top, bot = b["top_px"], b["bottom_px"]
    pad = int(H * 0.018)
    top = max(0, top - pad)
    bot = min(H, bot + pad)
    return top, bot - top


def detect_runs(path, crop, fps, gw=136, gh=32, bright=200, change=14, min_pix=12):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf",
                        f"{crop},fps={fps},scale={gw}:{gh},format=gray",
                        "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
    n = gw * gh
    total = len(p.stdout) // n
    if total < 4:
        sys.exit("抽帧失败，检查字幕带位置是否正确")

    masks, counts = [], []
    for i in range(total):
        fr = p.stdout[i * n:(i + 1) * n]
        m = bytes(1 if b > bright else 0 for b in fr)
        masks.append(m)
        counts.append(sum(m))

    def ham(a, b):
        return sum(x ^ y for x, y in zip(a, b))

    runs, start = [], 0
    for i in range(1, total):
        blank_flip = (counts[i] < min_pix) != (counts[i - 1] < min_pix)
        if ham(masks[i], masks[i - 1]) > change or blank_flip:
            runs.append((start, i - 1))
            start = i
    runs.append((start, total - 1))

    merged = []
    for a, b in runs:                       # 一两帧的过渡并回前一段
        if b - a < 1 and merged:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))

    out = []
    for a, b in merged:
        mid = (a + b) // 2
        if counts[mid] < min_pix:
            continue
        out.append({"i": len(out), "start": round(a / fps, 2),
                    "end": round((b + 1) / fps, 2), "mid": round((mid + 0.5) / fps, 2)})
    return out


def merge(runs_path, texts_path, out_path):
    """把读出来的文案按序号贴回时间轴。texts.txt 每行一条，空行表示这条不要字幕。"""
    runs = json.load(open(runs_path, encoding="utf-8"))
    lines = open(texts_path, encoding="utf-8").read().splitlines()
    if len(lines) != len(runs):
        print(f"警告：文案 {len(lines)} 行，字幕 {len(runs)} 条，数量对不上。"
              f"按较短的一边对齐，请核对序号。", file=sys.stderr)
    segs = []
    for r, t in zip(runs, lines):
        t = t.strip()
        if t:
            segs.append({"start": r["start"], "end": r["end"], "text": t})
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(segs, f, ensure_ascii=False, indent=1)
    print(f"合并 {len(segs)} 条 -> {out_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", nargs="?")
    ap.add_argument("--merge", nargs=2, metavar=("RUNS_JSON", "TEXTS_TXT"),
                    help="把 runs.json 和逐行文案合并成 segments.json")
    ap.add_argument("--analysis", default="analysis.json")
    ap.add_argument("--band", default=None, help="字幕带 顶,底（像素或 0~1 比例）")
    ap.add_argument("--out", default="subsheets")
    ap.add_argument("--fps", type=float, default=8.0)
    ap.add_argument("--per-sheet", type=int, default=10)
    ap.add_argument("--sheet-width", type=int, default=880)
    args = ap.parse_args()

    if args.merge:
        out = args.out if args.out != "subsheets" else "segments.json"
        return merge(args.merge[0], args.merge[1], out)
    if not args.video:
        sys.exit("用法：vp_read_subs.py 原片.mp4 --analysis analysis.json  "
                 "或  vp_read_subs.py --merge runs.json texts.txt --out segments.json")

    W, H, dur = probe(args.video)
    top, bh = band_from(args, H)
    crop = f"crop={W}:{bh}:0:{top}"
    print(f"字幕带 y={top}~{top+bh}px，抽帧 {args.fps}fps")

    runs = detect_runs(args.video, crop, args.fps)
    if not runs:
        sys.exit("没有检测到字幕变化，确认这条视频真的烧了字幕")
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "runs.json"), "w", encoding="utf-8") as f:
        json.dump(runs, f, ensure_ascii=False, indent=1)

    bands = os.path.join(args.out, "_bands")
    os.makedirs(bands, exist_ok=True)
    sel = "+".join(f"lt(abs(t-{r['mid']}),0.017)" for r in runs)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", args.video, "-vf",
                    f"{crop},select='{sel}'", "-vsync", "0", "-q:v", "2",
                    os.path.join(bands, "b%04d.jpg")], check=True)
    files = sorted(os.listdir(bands))
    print(f"字幕 {len(runs)} 条，抽出 {len(files)} 张")

    lw = 110
    bw = args.sheet_width - lw
    scaled_h = max(2, int(bh * bw / W) // 2 * 2)
    sheets = 0
    for s in range(0, len(files), args.per_sheet):
        rows = min(args.per_sheet, len(files) - s)
        vf = (f"scale={bw}:{scaled_h},pad={args.sheet_width}:{scaled_h+8}:{lw}:4:color=0x18181c,"
              f"drawtext=text='%{{eif\\:n+{s}\\:d}}':x=14:y=(h-th)/2:fontsize={max(20,scaled_h//4)}"
              f":fontcolor=0xFFD24A:borderw=2:bordercolor=black,"
              f"tile={1}x{rows}:padding=0:color=0x0e0e12")
        outp = os.path.join(args.out, f"s{sheets:02d}.jpg")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-start_number", str(s + 1),
                        "-i", os.path.join(bands, "b%04d.jpg"), "-vf", vf,
                        "-frames:v", "1", "-q:v", "3", outp], check=True)
        sheets += 1

    print(f"拼图 {sheets} 张 -> {args.out}/s00.jpg …")
    print("读图时按左侧黄色序号把文字写进 segments.json，时间从 runs.json 取。")


if __name__ == "__main__":
    main()
