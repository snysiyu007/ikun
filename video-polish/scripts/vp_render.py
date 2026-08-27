#!/usr/bin/env python3
"""按 plan.json 渲染成片：分段裁切/变焦 → 拼接 → 调色 → 修音 → 烧字幕 → 导出。

用法:
    python3 vp_render.py plan.json [--dry-run] [--preview 12]

plan.json 结构见 SKILL.md。全部依赖只有 ffmpeg。
"""

import argparse
import json
import os
import shlex
import subprocess
import sys

from vp_common import esc_path, quantize

DEF_LOOK = {"denoise": "2:1:3:3", "sharpen": 0.55, "brightness": 0.025,
            "contrast": 1.10, "saturation": 1.10, "gamma": 1.0, "skin_smooth": 0.0}
DEF_AUDIO = {"highpass": 85, "denoise": True, "denoise_amount": 10,
             "presence": 3.0, "mud_cut": -2.0, "compress": True,
             "lufs": -14.0, "true_peak": -1.5, "fade_ms": 15}


def build_video_chain(look, seg_zoom, crop, size):
    """单个片段的画面链：裁切(含变焦) → 降噪 → 放大 → 锐化 → 调色。"""
    W, H = size
    cw, ch = crop["w"], crop["h"]
    cx, cy = crop["x"], crop["y"]
    z = max(1.0, float(seg_zoom or 1.0))
    zw, zh = int(cw / z), int(ch / z)
    zw -= zw % 2
    zh -= zh % 2
    # 变焦时保持人脸位置：水平居中不变，垂直方向偏上 40%（人脸在上半部）
    zx = cx + int((cw - zw) / 2)
    zy = cy + int((ch - zh) * 0.40)

    parts = [f"crop={zw}:{zh}:{zx}:{zy}"]
    if look.get("denoise"):
        parts.append(f"hqdn3d={look['denoise']}")
    if look.get("skin_smooth", 0) > 0:
        a = float(look["skin_smooth"])
        parts.append(f"smartblur=lr=2:ls={a:.2f}:lt=18:cr=1:cs=0:ct=0")
    parts.append(f"scale={W}:{H}:flags=lanczos")
    if look.get("sharpen", 0) > 0:
        parts.append(f"unsharp=5:5:{look['sharpen']}:5:5:0.0")
    eq = (f"eq=brightness={look.get('brightness',0)}:contrast={look.get('contrast',1)}"
          f":saturation={look.get('saturation',1)}:gamma={look.get('gamma',1)}")
    parts.append(eq)
    parts.append("setsar=1")
    return ",".join(parts)


def build_audio_chain(a):
    parts = []
    if a.get("highpass"):
        parts.append(f"highpass=f={a['highpass']}")
    if a.get("denoise"):
        parts.append(f"afftdn=nr={a.get('denoise_amount',10)}:nf=-32:tn=1")
    if a.get("mud_cut"):
        parts.append(f"equalizer=f=250:t=q:w=1.2:g={a['mud_cut']}")
    if a.get("presence"):
        parts.append(f"equalizer=f=3200:t=q:w=1.4:g={a['presence']}")
    if a.get("compress"):
        parts.append("acompressor=threshold=-20dB:ratio=3:attack=6:release=140:makeup=2")
    parts.append("deesser=i=0.35")
    if a.get("lufs") is not None:
        parts.append(f"loudnorm=I={a['lufs']}:TP={a.get('true_peak',-1.5)}:LRA=9")
    parts.append("alimiter=limit=0.97")
    parts.append("aresample=48000")
    return ",".join(parts)


def build_filtergraph(plan):
    size = plan.get("size", [1080, 1920])
    fps = plan.get("fps", 30)
    crop = plan["source_crop"]
    look = {**DEF_LOOK, **plan.get("look", {})}
    aud = {**DEF_AUDIO, **plan.get("audio", {})}
    segs = quantize(plan["segments"], fps)
    fade = aud.get("fade_ms", 15) / 1000.0

    g = []
    g.append(f"[0:v]fps={fps},format=yuv420p,split={len(segs)}"
             + "".join(f"[v{i}]" for i in range(len(segs))))
    g.append(f"[0:a]{build_audio_chain(aud)},asplit={len(segs)}"
             + "".join(f"[a{i}]" for i in range(len(segs))))

    for i, s in enumerate(segs):
        st, en = float(s["start"]), float(s["end"])
        dur = s["duration"]
        chain = build_video_chain(look, s.get("zoom", 1.0), crop, size)
        # 画面按帧号选，避免时间戳比较产生 ±1 帧的漂移
        sel = f"select='between(n\\,{s['frame_in']}\\,{s['frame_out']})'"
        g.append(f"[v{i}]{sel},setpts=PTS-STARTPTS,{chain}[vv{i}]")
        af = (f"atrim=start={st:.6f}:end={en:.6f},asetpts=PTS-STARTPTS,"
              f"afade=t=in:st=0:d={fade},afade=t=out:st={max(0.0,dur-fade):.3f}:d={fade}")
        g.append(f"[a{i}]{af}[aa{i}]")

    g.append("".join(f"[vv{i}][aa{i}]" for i in range(len(segs)))
             + f"concat=n={len(segs)}:v=1:a=1[vc][aout]")

    vlast = "vc"
    subs = plan.get("subtitles")
    if subs:
        fdir = plan.get("fonts_dir")
        opt = f"subtitles='{esc_path(subs)}'"
        if fdir:
            opt += f":fontsdir='{esc_path(fdir)}'"
        g.append(f"[{vlast}]{opt}[vs]")
        vlast = "vs"
    if plan.get("progress_bar"):
        h = max(4, int(size[1] * 0.004))
        g.append(f"[{vlast}]drawbox=x=0:y=ih-{h}:w='iw*t/{plan['_total']:.3f}':h={h}"
                 f":color={plan.get('progress_color','0xFFD400')}@0.95:t=fill[vp]")
        vlast = "vp"
    g.append(f"[{vlast}]format=yuv420p[vout]")
    return ";".join(g)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--preview", type=float, default=0, help="只渲染前 N 秒用于快速预览")
    ap.add_argument("--crf", type=int, default=None)
    args = ap.parse_args()

    plan = json.load(open(args.plan, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(args.plan))
    for k in ("input", "output", "subtitles"):
        if plan.get(k) and not os.path.isabs(plan[k]):
            plan[k] = os.path.join(base, plan[k])

    total = sum(s["duration"] for s in quantize(plan["segments"], plan.get("fps", 30)))
    plan["_total"] = total
    fg = build_filtergraph(plan)

    crf = args.crf if args.crf is not None else plan.get("crf", 18)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-i", plan["input"],
           "-filter_complex", fg, "-map", "[vout]", "-map", "[aout]",
           "-c:v", "libx264", "-preset", plan.get("preset", "slow"), "-crf", str(crf),
           "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p",
           "-x264-params", "keyint=60:min-keyint=30:scenecut=0",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
           "-movflags", "+faststart"]
    if args.preview:
        cmd += ["-t", str(args.preview)]
    cmd.append(plan["output"])

    if args.dry_run:
        print(" ".join(shlex.quote(c) for c in cmd))
        return

    print(f"片段 {len(plan['segments'])} 个，成片 {total:.2f} 秒 → {plan['output']}")
    r = subprocess.run(cmd)
    if r.returncode != 0:
        sys.exit(r.returncode)

    cover = plan.get("cover")
    if cover and not args.preview:
        at = float(cover.get("at", 1.0))
        path = cover.get("path", "cover.jpg")
        if not os.path.isabs(path):
            path = os.path.join(base, path)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(at), "-i", plan["output"],
                        "-frames:v", "1", "-q:v", "2", path], check=False)
        print(f"封面 -> {path}")

    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration,size", "-of", "default=nw=1", plan["output"]],
                         capture_output=True, text=True).stdout.strip()
    print(out)


if __name__ == "__main__":
    main()
