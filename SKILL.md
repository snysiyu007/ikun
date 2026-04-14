---
name: wechat-article
description: 抓取微信公众号文章并总结到Obsidian。当用户发送 mp.weixin.qq.com 链接、提到"微信文章"、"公众号文章"、或想要总结/学习某篇微信文章时触发。
---

# 微信公众号文章抓取与总结

将微信公众号文章抓取、提取、总结，并保存到 Obsidian 笔记库。

## 触发条件

- 用户发送包含 `mp.weixin.qq.com/s/` 的链接
- 用户提到想学习/总结/阅读某篇微信公众号文章
- 用户使用 `/wechat-article <url>`

## 流程

### Step 1: 抓取文章 HTML

微信公众号有反爬机制，需要用微信内置浏览器的 User-Agent 绕过。用 curl 下载原始 HTML：

```bash
curl -sL \
  -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.34(0x16082222) NetType/WIFI Language/zh_CN" \
  "<文章URL>" \
  -o /tmp/wechat_article_raw.html
```

如果 curl 返回的 HTML 中包含"验证码"或"环境异常"，说明 UA 伪装被识别，需要告知用户手动复制文章内容。

### Step 2: 提取文章内容

用提取脚本解析 HTML，获取标题、公众号名称、作者、发布日期和正文：

```bash
python3 ~/.claude/skills/wechat-article/scripts/wechat_extract.py /tmp/wechat_article_raw.html --json
```

脚本会输出 JSON 格式的结构化数据。如果标题为空，可能是抓取失败，检查 HTML 内容判断原因。

### Step 3: 生成总结

基于提取的文章正文，生成一份结构化的中文总结。总结要求：

**文件头部信息：**
- 标题
- 公众号名称
- 作者（如有）
- 发布日期
- 原文链接

**正文总结结构：**
1. 一句话概括（文章核心观点）
2. 文章结构与章节划分
3. 每个章节/段落的核心要点（详细列出，用 bullet points）
4. 关键工具/方法/资源汇总（如有）
5. 作者的核心观点与建议
6. 可直接参考的实用信息提炼

总结要足够详细，让读者不需要回看原文就能获取主要价值。

### Step 4: 保存到 Obsidian

将总结保存为 Markdown 文件到用户 Obsidian Vault 下的 `wechat-articles/` 目录。
默认路径为：

```
~/Documents/Obsidian Vault/wechat-articles/
```

如果用户指定了其他路径，以用户指定的为准。
如果目标文件夹不存在，自动创建。

文件命名格式：`{文章标题简写}-{公众号名称}.md`

- 标题过长时适当缩短，保留核心关键词
- 去除标题中的特殊字符（冒号、问号等替换为空或横线）
- 例如：`Figma与Pencil接入Claude Code做前端设计-鲁工.md`

### Step 5: 确认

告知用户：
- 文件已保存的完整路径
- 文章的核心内容概览（3-5个要点）

## 异常处理

- **抓取失败（验证码/空内容）**：告知用户 UA 伪装被拦截，建议手动复制文章内容粘贴过来
- **文章内容过短（<200字）**：可能抓取不完整，提示用户确认
- **提取脚本报错**：回退到手动用 python3 解析 HTML，或请用户提供文章内容
- **目标文件夹不存在**：自动创建

## 注意事项

- 微信 UA 伪装方法可能随时失效，如果微信更新了反爬策略需要调整 UA 字符串
- 文章中的图片无法提取，总结中如涉及图片内容用文字描述补充
- 如果同一篇文章已有总结文件，询问用户是否覆盖
