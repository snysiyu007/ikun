#!/usr/bin/env python3
"""体检原始视频：分辨率、响度、停顿、烧录字幕位置、主体位置，并给出竖屏裁切建议。

用法:
    python3 vp_analyze.py 原片.mp4 [--json analysis.json] [--aspect 9:16]

只依赖 ffmpeg/ffprobe 和 Python 标准库。
"""

import argparse
import json
import re
import subprocess
import sys


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def probe(path):
    out = run(["ffprobe", "-v", "error", "-print_format", "json",
               "-show_format", "-show_streams", path]).stdout
    data = json.loads(out)
    v = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    if v is None:
        sys.exit("错误：文件里没有视频轨。")
    num, den = (v.get("r_frame_rate") or "30/1").split("/")
    return {
        "width": int(v["width"]),
        "height": int(v["height"]),
        "fps": round(int(num) / max(1, int(den)), 3),
        "duration": round(float(data["format"]["duration"]), 2),
        "v_bitrate": int(v.get("bit_rate") or 0),
        "total_bitrate": int(data["format"].get("bit_rate") or 0),
        "has_audio": a is not None,
        "a_channels": int(a["channels"]) if a else 0,
        "a_rate": int(a["sample_rate"]) if a else 0,
    }


def loudness(path):
    err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
               "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    tail = err[err.rfind("Summary:"):] if "Summary:" in err else ""

    def grab(pat):
        m = re.search(pat, tail)
        return float(m.group(1)) if m else None

    return {
        "integrated_lufs": grab(r"I:\s*(-?[\d.]+) LUFS"),
        "lra": grab(r"LRA:\s*(-?[\d.]+) LU"),
        "true_peak_dbfs": grab(r"Peak:\s*(-?[\d.]+) dBFS"),
    }


def noise_floor(path):
    """读取本底噪声，用来自适应静音阈值（不同设备/环境差异很大）。"""
    err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
               "-af", "astats=metadata=1:reset=0", "-f", "null", "-"]).stderr
    vals = [float(m.group(1)) for m in re.finditer(r"Noise floor dB: (-?[\d.]+)", err)]
    vals = [v for v in vals if v > -120]
    return round(sum(vals) / len(vals), 2) if vals else None


def auto_noise_db(floor):
    """本底噪声之上留 18dB 余量：太严会漏掉带底噪的停顿，太松会切掉气口。"""
    if floor is None:
        return -30.0
    return round(max(-40.0, min(-20.0, floor + 18.0)), 1)


def silences(path, noise_db, min_dur):
    err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
               "-af", f"silencedetect=noise={noise_db}dB:d={min_dur}",
               "-f", "null", "-"]).stderr
    spans, start = [], None
    for m in re.finditer(r"silence_(start|end): (-?[\d.]+)", err):
        kind, t = m.group(1), float(m.group(2))
        if kind == "start":
            start = t
        elif start is not None:
            spans.append([round(max(0.0, start), 3), round(t, 3)])
            start = None
    return spans


def keep_from_silences(spans, duration, pad, drop_shorter_than):
    """把静音段反转成保留段，两端各留 pad 秒呼吸感。"""
    keep, cursor = [], 0.0
    for s, e in spans:
        if e - s < drop_shorter_than:
            continue
        end = min(s + pad, duration)
        if end - cursor > 0.25:
            keep.append([round(cursor, 3), round(end, 3)])
        cursor = max(cursor, e - pad)
    if duration - cursor > 0.25:
        keep.append([round(cursor, 3), round(duration, 3)])
    return keep


def gray_frames(path, vf, w, h, fps):
    """抽取低分辨率灰度帧，返回逐帧 bytes。"""
    chain = f"{vf},fps={fps},scale={w}:{h},format=gray" if vf else f"fps={fps},scale={w}:{h},format=gray"
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", chain,
                        "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
    n = w * h
    return [p.stdout[i * n:(i + 1) * n] for i in range(len(p.stdout) // n)]


def _std(vals):
    if not vals:
        return 0.0
    mean = sum(vals) / len(vals)
    return (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5


def detect_burned_subs(path, duration, gw=96, gh=170, fps=2.0):
    """找出烧录字幕带：字幕行的『亮像素数量』随时间剧烈变化，白墙/灯光则基本不变。

    返回 (band_top_ratio, band_bottom_ratio) 或 None。
    """
    fps = min(fps, 400.0 / max(duration, 1.0))
    frames = gray_frames(path, None, gw, gh, fps)
    if len(frames) < 8:
        return None
    per_row = [[] for _ in range(gh)]
    for fr in frames:
        for y in range(gh):
            row = fr[y * gw:(y + 1) * gw]
            per_row[y].append(sum(1 for b in row if b > 200))
    scores = [_std(per_row[y]) for y in range(gh)]
    lo = int(gh * 0.55)                       # 只在画面下半部分找
    window, best, best_y = max(3, gh // 25), 0.0, None
    for y in range(lo, gh - window):
        s = sum(scores[y:y + window]) / window
        if s > best:
            best, best_y = s, y
    baseline = sorted(scores)[len(scores) // 2] + 1e-6
    if best_y is None or best < max(1.5, baseline * 3.0):
        return None
    top, bot = best_y, best_y + window
    while top > lo and scores[top - 1] > baseline * 2.0:
        top -= 1
    while bot < gh - 1 and scores[bot] > baseline * 2.0:
        bot += 1
    return (round(top / gh, 4), round(bot / gh, 4))


def subject_center(path, duration, gw=96, gh=170, fps=2.0):
    """用逐列亮度时间方差估计说话人水平位置（人在动，背景不动）。"""
    fps = min(fps, 400.0 / max(duration, 1.0))
    frames = gray_frames(path, None, gw, gh, fps)
    if len(frames) < 8:
        return 0.5, 0.0
    top, bot = int(gh * 0.10), int(gh * 0.72)   # 只看人脸/上半身区域
    prev, energy = None, [0.0] * gw
    for fr in frames:
        cols = [0] * gw
        for y in range(top, bot):
            base = y * gw
            for x in range(gw):
                cols[x] += fr[base + x]
        if prev is not None:
            for x in range(gw):
                energy[x] += abs(cols[x] - prev[x])
        prev = cols
    total = sum(energy)
    if total <= 0:
        return 0.5, 0.0
    cx = sum(x * energy[x] for x in range(gw)) / total
    peak = max(energy)
    conf = round(min(1.0, (peak * gw) / (total * 3.0)), 3)
    return round((cx + 0.5) / gw, 4), conf


def suggest_crop(info, sub_band, cx_ratio, aspect, headroom_trim):
    aw, ah = (int(x) for x in aspect.split(":"))
    W, H = info["width"], info["height"]
    top = int(H * headroom_trim)
    bottom = int(H * (sub_band[0] - 0.006)) if sub_band else H
    bottom = max(top + 64, min(bottom, H))
    avail_h = bottom - top
    w = int(avail_h * aw / ah)
    if w > W:                                   # 高度富余，改由宽度决定
        w, avail_h = W, int(W * ah / aw)
        top = max(0, min(top, bottom - avail_h))
    x = int(cx_ratio * W - w / 2)
    x = max(0, min(x, W - w))
    w -= w % 2
    avail_h -= avail_h % 2
    return {"w": w, "h": avail_h, "x": x - x % 2, "y": top - top % 2,
            "removes_burned_subs": bool(sub_band)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--json", default="analysis.json")
    ap.add_argument("--aspect", default="9:16")
    ap.add_argument("--noise-db", type=float, default=None,
                    help="静音判定阈值 dB，默认按本底噪声自动计算")
    ap.add_argument("--min-silence", type=float, default=0.32)
    ap.add_argument("--pad", type=float, default=0.10)
    ap.add_argument("--headroom-trim", type=float, default=0.0,
                    help="从画面顶部裁掉的比例，用来压缩头顶留白（0.05 = 5%%）")
    ap.add_argument("--no-scan", action="store_true", help="跳过画面扫描（更快）")
    args = ap.parse_args()

    info = probe(args.video)
    res = {"input": args.video, **info}
    res["loudness"] = loudness(args.video) if info["has_audio"] else {}

    floor = noise_floor(args.video) if info["has_audio"] else None
    noise_db = args.noise_db if args.noise_db is not None else auto_noise_db(floor)
    res["noise_floor_db"] = floor
    res["silence_threshold_db"] = noise_db
    sil = silences(args.video, noise_db, args.min_silence) if info["has_audio"] else []
    keep = keep_from_silences(sil, info["duration"], args.pad, args.min_silence)
    res["silence"] = sil
    res["keep_suggestion"] = keep
    kept = sum(b - a for a, b in keep)
    res["cut_summary"] = {
        "silence_count": len(sil),
        "kept_seconds": round(kept, 2),
        "saved_seconds": round(info["duration"] - kept, 2),
    }

    if args.no_scan:
        res["burned_subtitle_band"] = None
        res["subject"] = {"cx_ratio": 0.5, "confidence": 0.0}
    else:
        band = detect_burned_subs(args.video, info["duration"])
        cx, conf = subject_center(args.video, info["duration"])
        res["burned_subtitle_band"] = (
            {"top_ratio": band[0], "bottom_ratio": band[1],
             "top_px": int(band[0] * info["height"]),
             "bottom_px": int(band[1] * info["height"])} if band else None)
        res["subject"] = {"cx_ratio": cx, "confidence": conf}
        res["crop_suggestion"] = suggest_crop(
            info, band, cx if conf > 0.02 else 0.5, args.aspect, args.headroom_trim)

    notes = []
    if info["width"] * info["height"] < 1080 * 1920:
        notes.append(f"分辨率只有 {info['width']}x{info['height']}，低于 1080x1920。"
                     "尽量用手机相册里的原片，不要用微信/QQ 转发压缩过的版本。")
    if info["v_bitrate"] and info["v_bitrate"] < 2_000_000:
        notes.append(f"视频码率仅 {info['v_bitrate']//1000} kbps，画面细节已被压掉，放大后会偏软。")
    li = res["loudness"].get("integrated_lufs")
    if li is not None and li < -16:
        notes.append(f"整体响度 {li} LUFS，比短视频平台常用的 -14 LUFS 偏小，需要提响度。")
    if info["duration"] > 100:
        notes.append(f"时长 {int(info['duration'])} 秒，对竖屏短视频偏长，建议拆成 60~90 秒的多条。")
    if res.get("burned_subtitle_band"):
        b = res["burned_subtitle_band"]
        notes.append(f"检测到已烧录的字幕带在 y={b['top_px']}~{b['bottom_px']}px。"
                     "裁切建议已避开它，这样可以重做更醒目的字幕。")
    res["notes"] = notes

    with open(args.json, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)

    print(f"分辨率 {info['width']}x{info['height']}  {info['fps']}fps  时长 {info['duration']}s")
    if res["loudness"]:
        print(f"响度 {res['loudness']['integrated_lufs']} LUFS  真峰值 {res['loudness']['true_peak_dbfs']} dBFS")
    print(f"本底噪声 {floor} dB，静音阈值取 {noise_db} dB")
    print(f"停顿 {len(sil)} 处，剪掉可省 {res['cut_summary']['saved_seconds']} 秒")
    if res.get("crop_suggestion"):
        c = res["crop_suggestion"]
        print(f"建议裁切 crop={c['w']}:{c['h']}:{c['x']}:{c['y']}"
              + ("（已避开烧录字幕）" if c["removes_burned_subs"] else ""))
    for n in notes:
        print("· " + n)
    print(f"\n完整结果 -> {args.json}")


if __name__ == "__main__":
    main()
