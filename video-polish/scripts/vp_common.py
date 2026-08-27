#!/usr/bin/env python3
"""渲染与字幕共用的时间轴处理和路径转义。"""


def esc_path(p):
    """ffmpeg 滤镜里的路径要转义反斜杠、冒号和单引号。"""
    return p.replace("\\", "/").replace(":", r"\:").replace("'", r"\'")


def quantize(segments, fps):
    """把片段起止对齐到帧号，并返回每段的精确时长。

    画面按帧号 select、声音按时间 atrim，两边都落在同一组帧边界上，
    每段时长精确等于 (m-n)/fps。这样字幕用的时间轴和渲染出来的时间轴一致；
    否则片段一多，每段不到一帧的误差累积起来，片尾字幕会明显对不上口型。
    """
    out = []
    for s in segments:
        n = int(round(float(s["start"]) * fps))
        m = int(round(float(s["end"]) * fps))
        if m <= n:
            m = n + 1
        out.append({
            **s,
            "start": n / fps,
            "end": m / fps,
            "frame_in": n,
            "frame_out": m - 1,
            "duration": (m - n) / fps,
        })
    return out


def timeline(segments, fps):
    """返回 (原片起, 原片止, 输出起点) 列表和成片总时长。"""
    q = quantize(segments, fps)
    rows, acc = [], 0.0
    for s in q:
        rows.append((s["start"], s["end"], acc))
        acc += s["duration"]
    return rows, acc
