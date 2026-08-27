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
| 字幕 | 重做大字号描边字幕，关键词高亮，自动避开平台底部 UI |
| 画质 | 压缩噪点抑制 → Lanczos 放大 → 锐化 → 调色 |
| 声音 | 高通、降噪、去浑浊、提人声、压缩、统一到 -14 LUFS |
| 交付 | 成片 mp4 + 封面 jpg |

## 需要装什么

只有 ffmpeg 一个。

```bash
# macOS
brew install ffmpeg
# Windows
winget install Gyan.FFmpeg
# Ubuntu/Debian
sudo apt install ffmpeg
```

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
#    原片已烧字幕的话，先切成拼图再照着抄：
python3 $VP/vp_read_subs.py 原片.mp4 --analysis analysis.json --out subsheets

# 3. 选段 + 剔停顿 + 分配变焦
python3 $VP/vp_plan.py --analysis analysis.json --trim-silence \
  --pick "11.25-17.75,27.88-38.38,148.88-168.88" \
  --input 原片.mp4 --output 成片.mp4 --subtitles 成片.ass --out plan.json

# 4. 生成字幕（时间轴自动对齐剪辑结果）
python3 $VP/vp_ass.py plan.json --segments segments.json --out 成片.ass

# 5. 渲染
python3 $VP/vp_render.py plan.json --preview 12   # 先看前 12 秒
python3 $VP/vp_render.py plan.json
```

## 文件说明

| 文件 | 作用 |
|------|------|
| `SKILL.md` | Skill 定义，给 Claude Code 看的完整流程和判断标准 |
| `scripts/vp_analyze.py` | 体检：探测参数、静音、烧录字幕带、主体位置、裁切建议 |
| `scripts/vp_read_subs.py` | 把原片烧录字幕切成带序号拼图，供读图抄文案 |
| `scripts/vp_plan.py` | 选段 → 剔停顿 → 分配变焦 → 生成 plan.json |
| `scripts/vp_ass.py` | 文案时间轴 → 竖屏风格 ASS 字幕，自动重新对时 |
| `scripts/vp_render.py` | 按 plan.json 渲染成片和封面 |

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
           "compress": true, "lufs": -14.0, "fade_ms": 15},
 "subtitle_style": {"font": "PingFang SC", "size": 76, "margin_v": 432,
                    "accent": "#FFD400", "max_chars": 12, "pop": true},
 "subtitles": "成片.ass",
 "overlays": [
  {"type": "title", "text": "标题第一行\n第二行【高亮词】", "start": 0.15, "end": 4.2},
  {"type": "cta", "text": "关注我\n每天一条 AI 实操", "start": 72.3, "end": 76.3}
 ],
 "cover": {"at": 1.6, "path": "cover.jpg"},
 "crf": 18
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

## 已知限制

- **原片已烧录的字幕去不掉**，只能靠裁切避开。裁切会损失画面宽度，源分辨率越低越吃亏。
  最好的办法是导出**没有烧字幕**的原片。
- 不做语音识别。文案来源是现成 srt、本地 `faster-whisper`，或读图抄烧录字幕。
- 不加背景音乐。BGM 建议发布时用平台自带曲库，避免版权风险。
- 变焦是逐段静态的，不做人脸跟踪推拉。
- 输出固定 H.264 + AAC + faststart，不支持 HDR 或竖屏以外的比例预设。

## License

MIT
