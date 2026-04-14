# wechat-article

一个 Claude Code Skill，自动抓取微信公众号文章，AI 总结后归档到 Obsidian。

## 功能

- 输入公众号文章链接，自动抓取 HTML 内容
- 提取标题、公众号名称、作者、发布日期、正文
- AI 生成结构化总结（一句话概括、章节要点、关键工具、实用信息）
- 自动保存到 Obsidian Vault 的 Markdown 笔记

## 效果

```
你: https://mp.weixin.qq.com/s/xxxxx

Claude Code: (自动触发)
  → 抓取 HTML → 提取结构化内容 → AI 总结 → 写入 Obsidian
  → 已保存到 ~/Documents/Obsidian Vault/wechat-articles/xxx.md
  → 核心要点：
    1. ...
    2. ...
    3. ...
```

## 安装

### 方式一：一键安装脚本

```bash
# 克隆到本地 Claude Code skills 目录
mkdir -p ~/.claude/skills
git clone https://github.com/YOUR_USERNAME/wechat-article.git ~/.claude/skills/wechat-article
```

### 方式二：手动复制

1. 将 `SKILL.md` 放到 `~/.claude/skills/wechat-article/SKILL.md`
2. 将 `scripts/` 目录放到 `~/.claude/skills/wechat-article/scripts/`

## 使用

在 Claude Code 对话中：

1. 直接粘贴公众号文章链接，自动触发
2. 或输入 `/wechat-article https://mp.weixin.qq.com/s/xxxxx`

### 自定义 Obsidian 路径

默认保存到 `~/Documents/Obsidian Vault/wechat-articles/`

如需修改，在对话中告诉 Claude Code 你的实际 Vault 路径即可。

## 技术细节

| 组件 | 说明 |
|------|------|
| `SKILL.md` | Claude Code Skill 定义，包含完整流程指令 |
| `scripts/wechat_extract.py` | 纯 Python 标准库，零依赖，从微信 HTML 提取结构化数据 |
| UA 伪装 | 使用微信内置浏览器 UA 绕过反爬 |

## 限制

- 微信 UA 可能失效，需要不定期更新 SKILL.md 中的 UA 字符串
- 文章中的图片无法提取
- 部分被反爬拦截的文章需要手动复制内容

## License

MIT
