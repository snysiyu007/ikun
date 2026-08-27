#!/usr/bin/env python3
"""处理口播视频的背景：抠出人像，把背景虚化，或者整个换掉。

用法:
    python3 vp_bg.py 原片.mp4 --blur 26 --out 虚化.mp4      # 景深虚化（推荐）
    python3 vp_bg.py 原片.mp4 --bg 背景.png --out 换背景.mp4  # 整个换掉

**优先用 --blur**。背景是真实房间、真实光线，只是失焦，看不出后期痕迹；
换成一张合成图，只要光比、透视、颗粒对不上，一眼就假。除非原背景实在没法看，
否则不要换。

依赖 ffmpeg + mediapipe（只有这个功能需要 mediapipe，其余脚本不需要）:
    pip install mediapipe
模型会自动下到 ~/.cache/video-polish/，约 250KB。

抠像本身只解决"背景是什么"，解决不了"手里多一样东西"——凭空加物体需要生成模型，
这里做不到，也不建议硬做。
"""

import argparse
import os
import subprocess
import sys
import urllib.request

MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/image_segmenter/"
             "selfie_segmenter/float16/latest/selfie_segmenter.tflite")
CACHE = os.path.expanduser("~/.cache/video-polish")


def ensure_model(path=None):
    if path:
        return path
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, "selfie_segmenter.tflite")
    if not os.path.exists(p):
        print("首次运行，下载抠像模型（约 250KB）…")
        urllib.request.urlretrieve(MODEL_URL, p)
    return p


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-show_entries", "stream=width,height,r_frame_rate,nb_frames",
                          "-of", "default=nw=1:nk=1", path],
                         capture_output=True, text=True).stdout.split()
    w, h = int(out[0]), int(out[1])
    num, den = out[2].split("/")
    return w, h, int(num) / max(1, int(den))


def load_bg(path, W, H):
    """把背景图等比裁切到画幅大小，返回 float32 数组。"""
    import numpy as np
    from PIL import Image
    im = Image.open(path).convert("RGB")
    s = max(W / im.width, H / im.height)
    im = im.resize((max(W, int(im.width * s + 0.5)), max(H, int(im.height * s + 0.5))),
                   Image.LANCZOS)
    left, top = (im.width - W) // 2, (im.height - H) // 2
    return np.asarray(im.crop((left, top, left + W, top + H))).astype(np.float32)


def box_blur(a, r):
    """用积分图做的均值模糊，只为了羽化边缘，不需要高斯那么讲究。"""
    import numpy as np
    if r < 1:
        return a
    k = 2 * r + 1
    pad = np.pad(a, ((r + 1, r), (r + 1, r)), mode="edge")
    ii = pad.cumsum(0).cumsum(1)
    ii = np.pad(ii, ((1, 0), (1, 0)), mode="constant")
    H, W = a.shape
    ys, xs = np.arange(H), np.arange(W)
    y0, y1 = ys[:, None], ys[:, None] + k
    x0, x1 = xs[None, :], xs[None, :] + k
    return (ii[y1, x1] - ii[y0, x1] - ii[y1, x0] + ii[y0, x0]) / (k * k)


def big_blur(a, r, ds=4):
    """大半径模糊降到 1/ds 分辨率上做——反正结果是糊的，看不出差别，但快十几倍。"""
    import numpy as np
    from PIL import Image
    if r < ds * 2:
        return box_blur(a, r)
    H, W = a.shape
    sw, sh = max(2, W // ds), max(2, H // ds)
    small = np.asarray(Image.fromarray(a).resize((sw, sh), Image.BILINEAR))
    small = box_blur(small, max(1, r // ds))
    small = box_blur(small, max(1, r // (ds * 2)))      # 叠两次，接近高斯
    return np.asarray(Image.fromarray(small).resize((W, H), Image.BILINEAR))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--bg", default=None, help="换成这张背景图")
    ap.add_argument("--blur", type=int, default=0,
                    help="景深虚化半径（像素）。720 宽的素材 22~30 比较自然")
    ap.add_argument("--dim", type=float, default=0.12,
                    help="背景压暗比例，让主体更突出（0~0.4）")
    ap.add_argument("--desat", type=float, default=0.18,
                    help="背景降饱和比例（0~0.5）")
    ap.add_argument("--sharpen", type=float, default=0.55,
                    help="主体锐化强度，源片偏软时有用（0~1.2，超过 1.2 会有毛边）")
    ap.add_argument("--out", default="bg_replaced.mp4")
    ap.add_argument("--model", default=None)
    ap.add_argument("--feather", type=int, default=3, help="边缘羽化半径，像素")
    ap.add_argument("--erode", type=float, default=0.06,
                    help="向内收边，去掉原背景残留的一圈亮边（0~0.2）")
    ap.add_argument("--smooth", type=float, default=0.55,
                    help="掩码时间平滑系数，越大越稳但跟手越慢（0~0.9）")
    ap.add_argument("--bg-blur", type=int, default=0, help="背景额外模糊半径，制造景深")
    ap.add_argument("--crf", type=int, default=20)
    ap.add_argument("--preset", default="medium")
    args = ap.parse_args()

    try:
        import numpy as np
        import mediapipe as mp
        from mediapipe.tasks import python as mpp
        from mediapipe.tasks.python import vision
    except ImportError:
        sys.exit("需要 mediapipe：pip install mediapipe")

    if not args.bg and not args.blur:
        sys.exit("要么 --blur 半径（虚化真实背景，推荐），要么 --bg 图片（整个换掉）")

    W, H, fps = probe(args.video)
    bg = None
    if args.bg:
        bg = load_bg(args.bg, W, H)
        if args.bg_blur:
            for c in range(3):
                bg[..., c] = box_blur(bg[..., c], args.bg_blur)

    seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
        base_options=mpp.BaseOptions(model_asset_path=ensure_model(args.model)),
        running_mode=vision.RunningMode.IMAGE, output_confidence_masks=True))

    dec = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", args.video, "-f", "rawvideo",
         "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", f"{fps}", "-i", "-", "-i", args.video,
         "-map", "0:v", "-map", "1:a?", "-c:v", "libx264", "-preset", args.preset,
         "-crf", str(args.crf), "-pix_fmt", "yuv420p", "-c:a", "copy",
         "-movflags", "+faststart", "-shortest", args.out], stdin=subprocess.PIPE)

    fsize = W * H * 3
    prev = None
    n = 0
    try:
        while True:
            raw = dec.stdout.read(fsize)
            if len(raw) < fsize:
                break
            frame = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
            res = seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=frame))
            m = np.array(res.confidence_masks[0].numpy_view(), copy=True).reshape(H, W)

            if args.erode:                      # 收边：把 0.5 的判定门槛往前景推
                m = np.clip((m - args.erode) / (1 - args.erode), 0, 1)
            if args.feather:
                m = box_blur(m, args.feather)
            if prev is not None and args.smooth:  # 时间平滑，压掉逐帧抖动
                m = args.smooth * prev + (1 - args.smooth) * m
            prev = m

            a = m[..., None]
            f = frame.astype(np.float32)
            if args.sharpen > 0:
                # 主体锐化：背景已经糊了，人再锐一点，"浅景深"的感觉才立得住
                soft = np.stack([box_blur(f[..., c], 2) for c in range(3)], axis=-1)
                f = np.clip(f + args.sharpen * (f - soft), 0, 255)
            if bg is not None:
                back = bg
            else:
                # 归一化卷积：只用背景像素做模糊，否则人物颜色会向外糊出一圈光晕
                bgm = 1.0 - m
                den = big_blur(bgm, args.blur) + 1e-4
                back = np.stack([big_blur(f[..., c] * bgm, args.blur) / den
                                 for c in range(3)], axis=-1)
                if args.desat:
                    g = back.mean(axis=2, keepdims=True)
                    back = back * (1 - args.desat) + g * args.desat
                if args.dim:
                    back *= (1 - args.dim)
            out = f * a + back * (1 - a)
            enc.stdin.write(np.clip(out, 0, 255).astype(np.uint8).tobytes())
            n += 1
            if n % 60 == 0:
                print(f"\r  已处理 {n} 帧", end="", flush=True)
    finally:
        try:
            enc.stdin.close()
        except OSError:
            pass
        dec.wait()
        enc.wait()

    print(f"\r抠像换背景完成：{n} 帧 -> {args.out}")
    os._exit(0)          # mediapipe 的 C 绑定在解释器退出时会报无害的清理错误


if __name__ == "__main__":
    main()
