#!/usr/bin/env python3
"""Extract title, author, and body text from a WeChat article HTML file."""

import re
import html
import sys
import json
from datetime import datetime


def extract(html_path: str) -> dict:
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Title
    title_match = re.search(r'var msg_title = "(.+?)";', content)
    if not title_match:
        title_match = re.search(r'var msg_title\s*=\s*"(.+?)"\s*;', content)
    title = html.unescape(title_match.group(1).strip()) if title_match else ""

    # Author / nickname (the WeChat official account name)
    nick_match = re.search(r'var nickname\s*=\s*"(.+?)"\s*;', content)
    nickname = html.unescape(nick_match.group(1).strip()) if nick_match else ""

    # Author name inside the article (if different from account name)
    author_match = re.search(
        r'id="js_author_name"[^>]*>([^<]+)<', content
    )
    author_name = html.unescape(author_match.group(1).strip()) if author_match else ""

    # Publish timestamp
    ct_match = re.search(r'var ct\s*=\s*"(\d+)"', content)
    pub_ts = int(ct_match.group(1)) if ct_match else 0
    pub_date = datetime.fromtimestamp(pub_ts).strftime("%Y-%m-%d") if pub_ts else ""

    # Body: extract js_content div
    body_match = re.search(
        r'id="js_content"[^>]*>(.*?)</div>\s*<(?:script|div\s+class="ct_mpda_wrp")',
        content,
        re.DOTALL,
    )
    body_html = body_match.group(1) if body_match else ""

    # Convert HTML to rough markdown
    text = body_html
    # Headings
    text = re.sub(r"<h([1-6])[^>]*>", lambda m: "\n" + "#" * int(m.group(1)) + " ", text)
    text = re.sub(r"</h[1-6]>", "\n\n", text)
    # Paragraphs and line breaks
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"</p>", "\n", text)
    text = re.sub(r"<p[^>]*>", "\n", text)
    # Lists
    text = re.sub(r"<li[^>]*>", "- ", text)
    text = re.sub(r"</li>", "\n", text)
    # Bold
    text = re.sub(r"<strong[^>]*>", "**", text)
    text = re.sub(r"</strong>", "**", text)
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode entities
    text = html.unescape(text)
    # Clean whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = text.strip()

    return {
        "title": title,
        "nickname": nickname,
        "author_name": author_name,
        "pub_date": pub_date,
        "pub_ts": pub_ts,
        "body": text,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 wechat_extract.py <html_file> [--json]", file=sys.stderr)
        sys.exit(1)

    result = extract(sys.argv[1])

    if "--json" in sys.argv:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"标题: {result['title']}")
        print(f"公众号: {result['nickname']}")
        if result["author_name"]:
            print(f"作者: {result['author_name']}")
        print(f"发布日期: {result['pub_date']}")
        print(f"正文字数: {len(result['body'])}")
        print("---")
        print(result["body"])
