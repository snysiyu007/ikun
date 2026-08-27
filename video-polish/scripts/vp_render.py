#!/usr/bin/env python3
"""按 plan.json 渲染成片：分段裁切/变焦 → 拼接 → 调色 → 修音 → 烧字幕 → 导出。

用法:
    python3 vp_render.py plan.json [--dry-run] [--preview 12]

plan.json 结构见 SKILL.md。全部依赖只有 ffmpeg。
"""

import argparse
import json
import os
import re
import shlex
import subprocess
import sys

from vp_common import esc_path, quantize

DEF_LOOK = {"denoise": "2:1:3:3", "sharpen": 0.55, "brightness": 0.025,
            "contrast": 1.10, "saturation": 1.10, "gamma": 1.0, "skin_smooth": 0.0}
DEF_AUDIO = {"highpass": 85, "denoise": True, "denoise_amount": 10,
             "presence": 3.0, "mud_cut": -2.0, "compress": True,
             "lufs": -14.0, "true_peak": -1.5, "fade_ms": 15, "bitrate": "192k"}


def source_time(segs, t_out):
    """把成片时间换算回原片时间。"""
    acc = 0.0
    for s in segs:
        if t_out < acc + s["duration"]:
            return s["start"] + (t_out - acc)
        acc += s["duration"]
    return segs[-1]["end"] - 1e-3


def title_only_ass(ass_path, t_out, out_path):
    """抽出成片 t_out 时刻的标题层，重新计时到 0，供封面单帧使用。

    封面只要标题，不要正文字幕；正文字幕已经烧进成片，所以封面得从原片重渲一帧。
    """
    try:
        raw = open(ass_path, encoding="utf-8").read()
    except OSError:
        return None
    head, events = raw.split("[Events]", 1)
    fmt, picked = "", None
    for line in events.splitlines():
        if line.startswith("Format:"):
            fmt = line
        elif line.startswith("Dialogue:"):
            f = line.split(",", 9)
            if len(f) < 10 or f[3].strip() not in ("Title", "CTA"):
                continue
            def secs(v):
                h, m, sec = v.strip().split(":")
                return int(h) * 3600 + int(m) * 60 + float(sec)
            if secs(f[1]) <= t_out < secs(f[2]):
                body = re.sub(r"\{\\fad\([^)]*\)\}", "", f[9])
                picked = ",".join(f[:1] + ["0:00:00.00", "0:00:10.00"] + f[3:9] + [body])
    if not picked:
        return None
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(head + "[Events]\n" + fmt + "\n" + picked + "\n")
    return out_path


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


def insert_branches(plan, size, fps, first_input=1):
    """把配图卡做成叠在成片上的分支，返回 (滤镜片段, 额外输入参数, 叠加指令)。

    卡片放在字幕【下面】，这样切到配图时字幕仍然可读。
    """
    W, H = size
    fil, inputs, overlays = [], [], []
    for k, ins in enumerate(plan.get("inserts", [])):
        path = ins["image"]
        if not os.path.isabs(path):
            path = os.path.join(plan["_base"], path)
        if not os.path.exists(path):
            sys.exit(f"配图卡不存在：{path}")
        a, b = float(ins["start"]), float(ins["end"])
        dur = max(0.2, b - a)
        fade = min(float(ins.get("fade", 0.14)), dur / 3)
        idx = first_input + k
        inputs += ["-loop", "1", "-t", f"{dur:.3f}", "-i", path]

        chain = ["format=rgba"]
        if ins.get("mode", "cutaway") == "banner":
            chain.append(f"scale={W}:-1")
            x, y = 0, int(ins.get("y", H * 0.06))
        else:
            # 竖向缓慢位移：静止的整屏卡片在快节奏里会显得发闷
            m = ins.get("motion", "up")
            over = int(H * 0.04) // 2 * 2
            # 等比放大再裁切：直接拉伸会让卡片（或用户自己的图）变形
            chain.append(f"scale={W}:{H + over}:force_original_aspect_ratio=increase")
            if m == "none":
                chain.append(f"crop={W}:{H}:(iw-ow)/2:(ih-oh)/2")
            else:
                prog = f"t/{dur:.3f}" if m == "up" else f"(1-t/{dur:.3f})"
                chain.append(f"crop={W}:{H}:(iw-ow)/2:'(ih-oh)*(1-{prog})'")
            x, y = 0, 0
        chain.append(f"fade=t=in:st=0:d={fade:.3f}:alpha=1")
        chain.append(f"fade=t=out:st={dur - fade:.3f}:d={fade:.3f}:alpha=1")
        chain.append(f"setpts=PTS+{a:.3f}/TB")
        fil.append(f"[{idx}:v]{','.join(chain)}[ins{k}]")
        overlays.append((f"ins{k}", x, y, a, b))
    return fil, inputs, overlays


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
        # trim 负责让这一路尽早 EOF（否则 concat 会等到整条流读完，
        # 前面的分支把整段输出堆在缓冲里，片段一多就卡死）；
        # select 再按秒级时间精确取帧，半帧的判定余量远大于时间戳误差，
        # 不会像 trim 单独用那样出现 ±1 帧的漂移。
        lo, hi = (s["frame_in"] - 0.5) / fps, (s["frame_out"] + 0.5) / fps
        cut = (f"trim=start={max(0.0,(s['frame_in']-1)/fps):.6f}:end={(s['frame_out']+2)/fps:.6f},"
               f"select='between(t\\,{lo:.6f}\\,{hi:.6f})'")
        g.append(f"[v{i}]{cut},setpts=PTS-STARTPTS,{chain}[vv{i}]")
        af = (f"atrim=start={st:.6f}:end={en:.6f},asetpts=PTS-STARTPTS,"
              f"afade=t=in:st=0:d={fade},afade=t=out:st={max(0.0,dur-fade):.3f}:d={fade}")
        g.append(f"[a{i}]{af}[aa{i}]")

    g.append("".join(f"[vv{i}][aa{i}]" for i in range(len(segs)))
             + f"concat=n={len(segs)}:v=1:a=1[vc][aout]")

    vlast = "vc"
    ins_fil, ins_inputs, ins_overlays = insert_branches(plan, size, fps)
    g.extend(ins_fil)
    for j, (lbl, x, y, a, b) in enumerate(ins_overlays):
        g.append(f"[{vlast}][{lbl}]overlay={x}:{y}:eof_action=pass:repeatlast=0"
                 f":enable='between(t,{a:.3f},{b:.3f})'[ov{j}]")
        vlast = f"ov{j}"
    plan["_insert_inputs"] = ins_inputs

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
    plan["_base"] = base
    fg = build_filtergraph(plan)

    crf = args.crf if args.crf is not None else plan.get("crf", 18)
    cmd = (["ffmpeg", "-y", "-hide_banner", "-i", plan["input"]]
           + plan.get("_insert_inputs", [])
           + ["-filter_complex", fg, "-map", "[vout]", "-map", "[aout]",
           "-c:v", "libx264", "-preset", plan.get("preset", "slow"), "-crf", str(crf),
           "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p",
           "-x264-params", "keyint=60:min-keyint=30:scenecut=0",
           "-c:a", "aac", "-ar", "48000", "-ac", "2",
           "-b:a", str({**DEF_AUDIO, **plan.get("audio", {})}["bitrate"]),
           "-movflags", "+faststart"])
    if args.preview:
        cmd += ["-t", str(args.preview)]
    cmd.append(plan["output"])

    if args.dry_run:
        print(" ".join(shlex.quote(c) for c in cmd))
        return

    n_ins = len(plan.get("inserts", []))
    ins_t = sum(float(i["end"]) - float(i["start"]) for i in plan.get("inserts", []))
    print(f"片段 {len(plan['segments'])} 个，配图卡 {n_ins} 张（占 {ins_t:.1f}s / {100*ins_t/total:.0f}%），"
          f"成片 {total:.2f} 秒 → {plan['output']}")
    r = subprocess.run(cmd)
    if r.returncode != 0:
        sys.exit(r.returncode)

    cover = plan.get("cover")
    if cover and not args.preview:
        at = float(cover.get("at", 1.0))
        path = cover.get("path", "cover.jpg")
        if not os.path.isabs(path):
            path = os.path.join(base, path)
        segs = quantize(plan["segments"], plan.get("fps", 30))
        src_t = source_time(segs, min(at, total - 0.05))
        chain = build_video_chain({**DEF_LOOK, **plan.get("look", {})},
                                  1.0, plan["source_crop"], plan.get("size", [1080, 1920]))
        tmp_ass = os.path.join(base, ".vp_cover.ass")
        if plan.get("subtitles") and title_only_ass(plan["subtitles"], at, tmp_ass):
            chain += f",subtitles='{esc_path(tmp_ass)}'"
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{src_t:.3f}",
                            "-i", plan["input"], "-vf", chain,
                            "-frames:v", "1", "-q:v", "2", path], check=False)
        if os.path.exists(tmp_ass):
            os.remove(tmp_ass)
        if r.returncode == 0:
            print(f"封面（只带标题）-> {path}")
        else:
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(at), "-i", plan["output"],
                            "-frames:v", "1", "-q:v", "2", path], check=False)
            print(f"封面 -> {path}")

    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration,size", "-of", "default=nw=1", plan["output"]],
                         capture_output=True, text=True).stdout.strip()
    print(out)


if __name__ == "__main__":
    main()
