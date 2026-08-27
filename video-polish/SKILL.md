---
name: video-polish
description: 把一条原始口播视频剪成竖屏短视频成片。当用户给出 mp4/mov 文件并提到"剪辑""美化""做成抖音/视频号/小红书""加字幕""调色""去停顿""拆成多条"时触发。零素材依赖，只用原片本身。
---

# 口播视频 → 竖屏短视频成片

面向不会剪辑、也没有额外素材的人。所有"素材"都从原片派生：重新构图、变焦制造多机位、
重做字幕、修音、调色。全流程只依赖 `ffmpeg`。

## 触发条件

- 用户提供视频文件并想要剪辑 / 美化 / 发抖音、视频号、小红书、B 站
- 用户说"帮我加字幕""画面太暗""声音太小""太长了拆一下"
- 用户使用 `/video-polish <文件路径>`

## 前置检查

```bash
ffmpeg -version >/dev/null 2>&1 || echo "需要先装 ffmpeg"
```

没有 ffmpeg 时告诉用户：macOS `brew install ffmpeg`，Windows `winget install Gyan.FFmpeg`。

脚本目录（下文用 `$VP` 指代）：`~/.claude/skills/video-polish/scripts`

## Step 1: 体检原片

```bash
python3 $VP/vp_analyze.py 原片.mp4 --json analysis.json --headroom-trim 0.04
```

输出 `analysis.json`，并打印：分辨率、响度、本底噪声、停顿分布、**已烧录字幕带位置**、
**建议的竖屏裁切框**、以及需要提醒用户的问题。

关键判断：

- `burned_subtitle_band` 不为 null → 原片已经烧死了字幕。裁切建议会自动避开它，
  这样才能重做更大更醒目的字幕。**务必告诉用户这一点**，因为这决定了画面要裁多少。
- 分辨率低于 1080x1920 或码率低于 2Mbps → 提醒用户下次别用微信/QQ 转发过的版本，
  要用手机相册里的原片。
- `--headroom-trim` 控制从顶部裁掉多少头顶留白，口播一般 0.03~0.06 之间。

## Step 2: 拿到文案时间轴

渲染字幕需要 `segments.json`：

```json
[{"start": 11.25, "end": 13.5, "text": "可能会【取代】人的工作"}]
```

时间是**原片**时间轴，`【】`包住的词会高亮成主题色。按下面顺序找文案来源：

1. **用户已有字幕文件**（剪映可以导出 srt）→ 直接转成上面的格式。
2. **本地语音识别**：装了 `faster-whisper` 就用它
   ```bash
   pip install faster-whisper
   ```
   ```python
   from faster_whisper import WhisperModel
   m = WhisperModel("medium", device="cpu", compute_type="int8")
   segs, _ = m.transcribe("原片.mp4", language="zh", vad_filter=True)
   ```
3. **原片已烧录字幕**：用 `vp_read_subs.py` 把字幕带切成拼图，然后**直接看图读出文字**
   ——这比 OCR 准，也不需要额外依赖。
   ```bash
   python3 $VP/vp_read_subs.py 原片.mp4 --analysis analysis.json --out subsheets
   ```
   生成 `subsheets/s00.jpg …` 和 `subsheets/runs.json`（每条字幕的起止时间）。
   逐张读图，把文字**按序号一行一条**写进 `texts.txt`（读不到内容的那条留空行），再合并：
   ```bash
   python3 $VP/vp_read_subs.py --merge subsheets/runs.json texts.txt --out segments.json
   ```
   行数必须和 `runs.json` 条数一致，否则脚本会告警并按较短一边对齐。

**读文案时顺手做三件事**：
- 记下口误、重复、跑题的时间段，Step 3 要剪掉；
- 记下事实性错误（比如把蒸汽机说成第四次工业革命），单独提醒用户；
- 记下 ASR 明显听错的专有名词（Claude Code 被听成 "cloud code" 之类），在文案里改对。

## Step 3: 定剪辑结构

这是最影响数据的一步，要真的动脑子，不要只做"去停顿"。

竖屏短视频的结构原则：

- **前 3 秒必须是钩子**。开场寒暄、"今天想跟大家聊聊"、"现在几点了"这类全部删掉，
  直接从痛点或结论开始。
- **一条只讲一件事**。原片超过 100 秒就考虑拆成多条，每条 60~90 秒。
- **金句放结尾**能提升完播和评论；如果开头实在弱，也可以把金句前置做冷开场。
- **删掉**：口吃重复、说错重说、"然后""就是""那个"堆叠、与主线无关的展开。

把选定的片段写成 `起-止` 列表交给 `vp_plan.py`：

```bash
python3 $VP/vp_plan.py --analysis analysis.json --trim-silence \
  --pick "11.25-17.75,27.88-38.38,148.88-168.88" \
  --input 原片.mp4 --output 成片.mp4 --subtitles 成片.ass \
  --out plan.json --zooms "1.0,1.07,1.0,1.05"
```

- `--trim-silence` 会在每个选段**内部**再自动剔除停顿，通常还能压掉 10%~15% 时长。
- `--zooms` 是逐段轮换的变焦值。单机位口播靠它制造"多机位"错觉，是零素材条件下
  最有效的一招。幅度控制在 1.00~1.08，超过就会因为放大而糊。
- `--crop` 可覆盖自动裁切框，格式 `w:h:x:y`。

## Step 4: 加标题和片尾引导

编辑 `plan.json` 的 `overlays`：

```json
"overlays": [
 {"type": "title", "text": "AI 不会淘汰你\n淘汰你的是【不用 AI 的人】", "start": 0.15, "end": 4.2},
 {"type": "cta",   "text": "关注我\n每天一条 AI 实操", "start": 72.3, "end": 76.3}
]
```

标题要给出**信息增量**，不要和第一句字幕重复。`\n` 换行，`【】`高亮。

## Step 5: 生成字幕

```bash
python3 $VP/vp_ass.py plan.json --segments segments.json --out 成片.ass
```

时间轴会自动按 `plan.json` 保留的片段重新对齐，不需要手工算。
样式参数在 `plan.json` 的 `subtitle_style` 里：`font` / `fill` / `margin_v` / `accent` / `max_chars`。

**字号是自动实测的**：libass 按字体 hhea 度量缩放，同一个 `size` 数字在不同中文字体下
实际字面能差三成。脚本会先渲染一帧探针量出真实墨迹宽度，再反推字号，让满一行正好占
画面宽度的 `fill`（默认 0.78）。换字体不用重调数字；要手动锁死就传 `--size 96`。

字体按平台选，取第一个装了的：
- macOS：`PingFang SC`
- Windows：`微软雅黑` 或 `Microsoft YaHei`
- Linux：`Noto Sans SC` / `WenQuanYi Zen Hei`

`margin_v` 默认是画面高度的 22.5%，用来避开抖音底部的按钮和文案区。

## Step 6: 渲染

```bash
python3 $VP/vp_render.py plan.json --preview 12   # 先看前 12 秒
python3 $VP/vp_render.py plan.json                # 确认后出全片
```

渲染顺序：分段裁切+变焦 → 降噪 → 放大 → 锐化 → 调色 → 拼接 → 烧字幕 → 修音 → 编码。
同时导出 `cover.jpg` 作为封面备选。

**渲染完必须自查**，抽几帧看：

```bash
ffmpeg -y -v error -i 成片.mp4 -vf "fps=1/8,scale=360:-2,tile=4x3" -frames:v 1 检查.jpg
ffmpeg -hide_banner -nostats -i 成片.mp4 -af ebur128=peak=true -f null - 2>&1 | grep -E "I:|Peak:"
```

- 字幕有没有被裁掉、有没有和原片烧录字幕重叠
- 响度应落在 -14 LUFS 附近，真峰值不超过 -1 dBFS
- 切点有没有切在字中间

## 音画默认值与调整

`plan.json` 里的 `look` 和 `audio`，多数素材不用改：

| 参数 | 默认 | 什么时候调 |
|------|------|-----------|
| `look.brightness` | 0.025 | 画面偏暗加到 0.05；过曝调负 |
| `look.contrast` | 1.10 | 画面发灰加到 1.18 |
| `look.sharpen` | 0.55 | 放大倍数大时加到 0.8；超过 1.0 会有毛边 |
| `look.skin_smooth` | 0 | 需要磨皮设 0.4~0.6，再高会像塑料 |
| `audio.denoise` | true | 环境很安静可关掉，避免人声发闷 |
| `audio.lufs` | -14 | 抖音/视频号/小红书都用 -14；B 站可用 -16 |
| `audio.presence` | 3.0 | 声音发闷加到 5；齿音重降到 1 |
| `crf` | 20 | 要更小的文件调到 23（几乎看不出差别）；源片码率本来就低时，低于 18 是浪费 |

## 异常处理

- **ffmpeg 报 "No such filter"**：版本太老，需要 ffmpeg 5 以上。
- **字幕不显示或变成方块**：`subtitle_style.font` 写的字体没装。用 `fc-list`（macOS/Linux）
  或系统字体册确认，换成实际装了的中文字体名。字体没装时实测会退回名义字号，
  终端会打印"字体宽度实测失败"，看到这句就说明字体名写错了。
- **切点有爆音**：调大 `audio.fade_ms`（默认 15，可以到 25）。
- **画面糊**：源码率太低，降低 `--headroom-trim` 少裁一点，或直接输出 720x1280。
- **找不到烧录字幕带**：`--no-scan` 跳过扫描，用 `--crop` 手动给裁切框。

## 交付时告诉用户

1. 成片路径、时长、分辨率、响度
2. 剪掉了什么、为什么（尤其是删掉的开场和口误）
3. 内容上发现的问题（事实错误、逻辑跳跃）
4. 下次拍摄可以改进的地方（原片分辨率、麦克风、头顶留白、光线）
