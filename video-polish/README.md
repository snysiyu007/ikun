# video-polish

一个 Claude Code Skill：把一条原始口播视频，剪成能直接发抖音 / 视频号 / 小红书的竖屏成片。

为**不会剪辑、也没有任何额外素材**的人写的。所有"素材"都从原片本身派生。

## 它做什么

| 环节 | 做的事 |
|------|--------|
| 体检 | 分辨率、码率、响度、本底噪声、停顿分布、**自动定位已烧录的字幕带** |
| 构图 | 按 9:16 重新裁切，压掉头顶留白，自动避开原片烧录字幕 |
| 结构 | 删掉开场寒暄和口误，钩子前置，超长视频拆条 |
| 节奏 | 自动剔除段内停顿，通常压掉 10%~15% 时长 |
| 镜头 | 逐段轮换变焦，单机位口播也有"多机位"感 |
| 配图 | 把关键概念做成整屏图卡切进去，矢量图标 + 无头浏览器排版，零素材 |
| 背景 | 人像抠像后把背景做景深虚化（首选），或整个换掉 |
| 字幕 | 重做大字号描边字幕，关键词高亮，自动避开平台底部 UI |
| 画质 | 压缩噪点抑制 → Lanczos 放大 → 锐化 → 调色 |
| 声音 | 高通、降噪、去浑浊、提人声、压缩、统一到 -14 LUFS |
| 交付 | 成片 mp4 + 封面 jpg |

## 需要装什么

ffmpeg 是必须的；再有一个 Chrome / Chromium / Edge 就能生成配图卡（没有也能跑，只是没配图）。

```bash
# macOS
brew install ffmpeg
# Windows
winget install Gyan.FFmpeg
# Ubuntu/Debian
sudo apt install ffmpeg
```

配图卡用无头浏览器排版，macOS 上一般已经装了 Chrome，不用额外装。

脚本本身零第三方依赖，Python 3.8+ 标准库即可。

## 安装

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/snysiyu007/ikun.git /tmp/ikun-skills
cp -r /tmp/ikun-skills/video-polish ~/.claude/skills/video-polish
```

## 使用

在 Claude Code 里直接说：

```
帮我把 ~/Desktop/口播.mp4 剪成抖音版
```

或者 `/video-polish ~/Desktop/口播.mp4`。

Claude 会依次跑体检 → 读文案 → 定结构 → 出字幕 → 渲染，并在每一步告诉你它的判断。

## 手动跑（不用 Claude Code）

```bash
VP=~/.claude/skills/video-polish/scripts

# 1. 体检，拿到裁切建议和停顿分布
python3 $VP/vp_analyze.py 原片.mp4 --json analysis.json --headroom-trim 0.04

# 2. 准备 segments.json（文案时间轴）
#    原片已烧字幕的话，先切成拼图再照着抄，然后按序号合并：
python3 $VP/vp_read_subs.py 原片.mp4 --analysis analysis.json --out subsheets
python3 $VP/vp_read_subs.py --merge subsheets/runs.json texts.txt --out segments.json

# 3. 选段 + 剔停顿 + 分配变焦
python3 $VP/vp_plan.py --analysis analysis.json --trim-silence \
  --pick "11.25-17.75,27.88-38.38,148.88-168.88" \
  --input 原片.mp4 --output 成片.mp4 --subtitles 成片.ass --out plan.json

# 4. 生成配图卡（可选，但这是画面不枯燥的关键）
python3 $VP/vp_cards.py cards.json --out cards
#    然后把 {"image":"cards/xx.png","start":6.8,"end":9.9} 写进 plan.json 的 inserts

# 5. 生成字幕（时间轴自动对齐剪辑结果）
python3 $VP/vp_ass.py plan.json --segments segments.json --out 成片.ass

# 6. 渲染
python3 $VP/vp_render.py plan.json --preview 12   # 先看前 12 秒
python3 $VP/vp_render.py plan.json
```

## 文件说明

| 文件 | 作用 |
|------|------|
| `SKILL.md` | Skill 定义，给 Claude Code 看的完整流程和判断标准 |
| `scripts/vp_analyze.py` | 体检：探测参数、静音、烧录字幕带、主体位置、裁切建议 |
| `scripts/vp_read_subs.py` | 把原片烧录字幕切成带序号拼图；`--merge` 再把读出的文案贴回时间轴 |
| `scripts/vp_plan.py` | 选段 → 剔停顿 → 分配变焦 → 生成 plan.json |
| `scripts/vp_cards.py` | 概念描述 → 整屏配图卡 PNG（无头浏览器排版） |
| `scripts/vp_backdrop.py` | 生成换背景用的背景图（书架 / 棚拍 / 网格） |
| `scripts/vp_bg.py` | 人像抠像 + 背景替换 |
| `scripts/vp_icons.py` | 配图卡用的矢量图标库 |
| `scripts/vp_ass.py` | 文案时间轴 → 竖屏风格 ASS 字幕，自动重新对时 |
| `scripts/vp_render.py` | 按 plan.json 渲染成片和封面 |
| `scripts/vp_common.py` | 渲染与字幕共用的帧对齐时间轴 |

## plan.json

所有渲染参数集中在这一个文件，改完重跑 `vp_render.py` 即可。

```json
{
 "input": "原片.mp4",
 "output": "成片.mp4",
 "size": [1080, 1920],
 "fps": 30,
 "source_crop": {"w": 384, "h": 684, "x": 72, "y": 38},
 "segments": [{"start": 11.25, "end": 17.75, "zoom": 1.0}],
 "look": {"denoise": "2:1:3:3", "sharpen": 0.55, "brightness": 0.025,
          "contrast": 1.10, "saturation": 1.10, "skin_smooth": 0},
 "audio": {"highpass": 85, "denoise": true, "presence": 3.0,
           "compress": true, "lufs": -14.0, "fade_ms": 15, "bitrate": "192k"},
 "subtitle_style": {"font": "PingFang SC", "fill": 0.78, "margin_v": 432,
                    "accent": "#FFD400", "max_chars": 12, "pop": true},
 "subtitles": "成片.ass",
 "inserts": [
  {"image": "cards/steam.png", "start": 6.8, "end": 9.9, "motion": "up"},
  {"image": "我自己的截图.png", "start": 21.4, "end": 24.7, "motion": "down"}
 ],
 "overlays": [
  {"type": "title", "text": "标题第一行\n第二行【高亮词】", "start": 0.15, "end": 4.2},
  {"type": "cta", "text": "关注我\n每天一条 AI 实操", "start": 72.3, "end": 76.3}
 ],
 "cover": {"at": 1.6, "path": "cover.jpg"},
 "crf": 20
}
```

## 下次拍摄怎么拍，成片会好很多

剪辑能补救的有限，源头质量决定上限。按影响从大到小：

1. **导出原片，不要用转发过的版本**。微信/QQ 转发会把视频压到几百 kbps、分辨率砍半，
   细节一旦丢了任何算法都补不回来。直接从相册导出，或用「原视频」选项发送。
2. **别让平台先把字幕烧进画面**。烧录字幕会逼着裁掉画面下部，白白损失构图空间。
   录完先存一份无字幕的原片。
3. **头顶留白留 5%~10% 就够**。手机架高一点、镜头稍微俯一点，人物占比大，天然更有镜头感。
4. **收音比画质更值得投入**。一支几十块的领夹麦，效果远超任何后期降噪。
5. **光源放在脸前方**，不要在背后。窗边正对窗户拍，或买一盏补光灯。
6. **开头三句话直接进主题**。"大家好""今天想聊聊""现在几点了"这类开场，后期只能删掉。
7. **一条只讲一件事**，控制在 60~90 秒。素材长了可以拆，但一条里塞三个主题救不回来。

## 关于输出分辨率

默认 `1080x1920`。但源片只有 544x960 这种情况，放大近 3 倍只是把糊的地方放大，
输出 `720x1280`（`vp_plan.py --size 720x1280`）通常更好：同样的文件大小，
每个像素分到的码率更多，画面反而更干净。字号会按输出分辨率自动重算。

## 关于码率

`crf` 越小画质越好、文件越大。默认 20，1080x1920 的口播大约 2.5~3 Mbps。

源片本身码率就低（比如微信压缩过的几百 kbps）时，把 crf 压到 18 以下没有意义——
多出来的码率都花在编码压缩噪点上。需要更小的文件（微信传输、平台上传限制）就往上调，
23 左右肉眼几乎看不出差别，27 开始能看出画面变软。

## 关于字号

`subtitle_style.size` 是名义字号，**不等于**屏幕上的实际字面大小——libass 按字体的
hhea 度量缩放，同一个数字在 PingFang SC、微软雅黑、Noto Sans SC 下能差三成。

所以 `vp_ass.py` 默认会先渲染一帧探针、实测墨迹宽度，再反推字号，让"满一行"正好占
画面宽度的 `fill`（默认 0.78，竖屏短视频的常见比例）。换字体不用重新调数字。

想手动锁死字号就传 `--size 96`，或加 `--no-autofit`。

## 背景处理

拍摄环境不好看时，**先试景深虚化，别急着换背景**：

```bash
pip install mediapipe            # 只有这个功能需要
python3 $VP/vp_bg.py 原片.mp4 --blur 30 --sharpen 0.6 --out 虚化.mp4
```

背景是真实房间、真实光线，只是失焦，没有任何合成痕迹；主体再锐一点，
浅景深的对比就出来了，观感接近正经机器拍的。

合成背景很难不假——光比、透视、噪点、色温任一项对不上，边缘立刻露馅。
只有原背景实在没法看才换：

```bash
python3 $VP/vp_backdrop.py --style bookshelf --size 1080x1920 --out backdrop.png
python3 $VP/vp_bg.py 原片.mp4 --bg backdrop.png --out 换背景.mp4
```

自带的 `bookshelf` / `studio` / `grid` 是矢量排版，**不是照片**。要照片级效果，
用即梦或 Midjourney 生成一张再喂给 `--bg`，并让它的亮度接近原素材。

## 配图卡

口播视频最劝退的地方是全程一张脸。`vp_cards.py` 把关键概念渲染成整屏图卡，
按时间切进成片，图标是矢量画的，排版走无头浏览器，完全不需要额外素材。

五种版式：`statement`（一个观点）、`versus`（两者对比）、`flow`（分步发生）、
`stat`（一个数字）、`chips`（一排并列项）。写法见 SKILL.md。

排时间三条规矩：单张 2.5~4 秒；总占比 25%~35%；每张必须压在**对应那句话**上，
排完要拿字幕文件核对，别凭感觉。

卡片烧在字幕**下层**，切到配图时字幕照常可读。

有自己的素材（产品截图、AI 生成图、录屏）时，直接把图片路径写进 `inserts`，
和配图卡同一条通道，会等比裁切到画幅、不变形。

## 已知限制

- **原片已烧录的字幕去不掉**，只能靠裁切避开。裁切会损失画面宽度，源分辨率越低越吃亏。
  最好的办法是导出**没有烧字幕**的原片。
- 不做语音识别。文案来源是现成 srt、本地 `faster-whisper`，或读图抄烧录字幕。
- 不加背景音乐。BGM 建议发布时用平台自带曲库，避免版权风险。
- 不生成写实图片/AI 绘图。配图卡是排版和矢量图标，要照片级素材得自己用即梦、
  Midjourney 之类生成好再放进 `inserts` 或 `vp_bg.py --bg`。
- 不做换脸、改体型、往手里加物体这类生成式修改。换背景是抠像替换，不是重绘画面。
- 变焦是逐段静态的，不做人脸跟踪推拉。
- 输出固定 H.264 + AAC + faststart，不支持 HDR 或竖屏以外的比例预设。

## License

MIT
