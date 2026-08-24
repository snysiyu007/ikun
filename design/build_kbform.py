# -*- coding: utf-8 -*-
"""知识库页素材填写：字段值保存回页面自身，Claude 直接读。"""
import pathlib, json

ROOT = pathlib.Path(__file__).resolve().parent

LAYERS = [
    ('l1', 'L1', '行业知识库', '行业的通用信息，以对商文档为主',
     ['例：2026 春季大促招商规则', '例：保健行业类目结构与定义', '']),
    ('l2', 'L2', '岗位知识库', '行业的政策、资源扶持等核心内容',
     ['例：新商扶持政策 v3（流量包 / 佣金减免）', '例：品类小二的商家分层标准', '']),
    ('l3', 'L3', '个人记忆画像', '对应岗位的行业经验、商家判断、运营习惯，由 Agent 使用中沉淀回流',
     ['例：张三对 A 商家的判断：库存响应慢，需提前 3 天打招呼', '', '']),
]
META = [('src', '来源 / 从哪来', '例：对商文档库、政策发文系统'),
        ('size', '大致体量', '例：约 800 篇 / 1.2 万条'),
        ('freq', '多久更新一次', '例：大促前每周、日常每月'),
        ('owner', '谁维护', '例：行业运营 + 秘书处 Agent 自动归档')]
MEMFIELDS = ['商家判断', '运营习惯', '常用数据口径', '历史决策与结果',
             '沟通偏好', '关注的品类 / 商家', '踩过的坑']

def field(k, label, ph, wide=False):
    return (f'<label class="f{" w" if wide else ""}"><span>{label}</span>'
            f'<input data-k="{k}" placeholder="{ph}"></label>')

cards = ''
for pre, tag, name, desc, exs in LAYERS:
    ex = ''.join(field(f'{pre}.ex{i+1}', f'条目样例 {i+1}', e or '再补一条（可留空）', True)
                 for i, e in enumerate(exs))
    meta = ''.join(field(f'{pre}.{k}', lb, ph) for k, lb, ph in META)
    cards += (f'<section class="lc"><div class="lc-h"><span class="idx">{tag}</span>'
              f'<b>{name}</b><em>{desc}</em></div>'
              f'<div class="fs">{ex}</div><div class="fs two">{meta}</div></section>')

mem = ''.join(f'<label class="ck"><input type="checkbox" data-c="{m}"><span class="box"></span>{m}</label>'
              for m in MEMFIELDS)

HTML = f"""<title>知识库素材 · 填写</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Noto+Sans+SC:wght@400;500;700&family=JetBrains+Mono:wght@500&display=swap">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0C0918;background-image:radial-gradient(1200px 560px at 50% -10%,rgba(67,56,202,.22),transparent 70%);
     color:#F6F2FF;font-family:'Sora','Noto Sans SC',system-ui,-apple-system,'PingFang SC',sans-serif;
     font-weight:500;line-height:1.5;-webkit-font-smoothing:antialiased}}
a{{color:#C6B4F5}}
.wrap{{max-width:1240px;margin:0 auto;padding:34px 26px 60px}}
h1{{font-size:26px;font-weight:700}}
.lead{{margin-top:8px;font-size:14px;color:#C6B4F5;line-height:1.7;max-width:880px}}
.lead em{{font-style:normal;color:#F6F2FF;font-weight:700}}
h2{{font-size:15px;font-weight:700;margin:30px 0 12px}}
h2 span{{font-size:12px;font-weight:500;color:#9C8CCB;margin-left:10px}}
.lc{{border:1px solid rgba(129,140,248,.42);border-radius:14px;background:rgba(67,56,202,.10);
    padding:16px 18px 18px;margin-bottom:14px}}
.lc-h{{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:14px}}
.lc-h b{{font-size:17px;font-weight:700}}
.lc-h em{{font-style:normal;font-size:12px;color:#9C8CCB}}
.idx{{font-family:'JetBrains Mono',monospace;font-size:10.5px;color:#D8DCFF;
     border:1px solid rgba(216,220,255,.42);border-radius:5px;padding:2px 7px}}
.fs{{display:grid;gap:9px}}
.fs.two{{grid-template-columns:repeat(2,1fr);margin-top:9px}}
.f{{display:flex;flex-direction:column;gap:5px}}
.f span{{font-size:11.5px;color:#9C8CCB;letter-spacing:.03em}}
input[data-k],textarea{{width:100%;background:rgba(139,92,246,.07);border:1px solid rgba(167,139,250,.32);
     border-radius:9px;padding:10px 12px;color:#F6F2FF;font-family:inherit;font-size:13.5px;line-height:1.6}}
input::placeholder,textarea::placeholder{{color:#6F6194}}
input[data-k]:focus,textarea:focus{{outline:none;border-color:rgba(196,181,253,.8);background:rgba(139,92,246,.14)}}
textarea{{min-height:80px;resize:vertical}}
.cks{{display:flex;flex-wrap:wrap;gap:9px}}
.ck{{display:flex;align-items:center;gap:8px;cursor:pointer;font-size:13.5px;
    border:1px dashed rgba(167,139,250,.4);border-radius:10px;padding:9px 13px}}
.ck input{{position:absolute;opacity:0;width:0;height:0}}
.box{{width:18px;height:18px;border-radius:6px;border:1px dashed rgba(167,139,250,.6);
     display:block;position:relative;flex:none}}
.ck input:checked+.box{{background:linear-gradient(180deg,#6D6BE0,#4038B0);border:1px solid rgba(255,255,255,.2)}}
.ck input:checked+.box:after{{content:'';position:absolute;left:6px;top:2.5px;width:4px;height:9px;
     border:solid #fff;border-width:0 2px 2px 0;transform:rotate(42deg)}}
.grid3{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}
.bar{{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:26px 0 12px}}
button{{font-family:inherit;font-size:13.5px;font-weight:700;border-radius:10px;padding:11px 20px;
       cursor:pointer;border:1px solid rgba(255,255,255,.16);color:#fff;
       background:linear-gradient(180deg,#6D6BE0,#4038B0);box-shadow:0 6px 16px rgba(23,18,80,.4)}}
button.ghost{{background:rgba(167,139,250,.09);border:1px solid rgba(167,139,250,.45);color:#C6B4F5;box-shadow:none}}
button:hover{{filter:brightness(1.1)}}
#msg{{font-size:12.5px;color:#9C8CCB}}
pre{{background:rgba(67,56,202,.10);border:1px solid rgba(129,140,248,.34);border-radius:12px;
    padding:16px 18px;font-family:'JetBrains Mono','Noto Sans SC',monospace;font-size:12.5px;
    line-height:1.85;color:#DDE2FF;white-space:pre-wrap;user-select:all}}
@media (max-width:780px){{.fs.two,.grid3{{grid-template-columns:1fr}}}}
</style>

<script type="application/json" id="kb-state">{{"fields":{{}},"checks":[]}}</script>

<div class="wrap">
  <h1>知识库素材 · 填写</h1>
  <p class="lead">这页填完我就能画 P5。<em>最要紧的是每层 2–3 条真实条目样例</em>（脱敏就行，是虚构还是真实一眼能看出来）——
    没有样例，「知识库」三个字在老板眼里是空的。其余字段能填多少填多少，留空我就不画那块。</p>

  <h2>三层内容<span>条目样例 = 里面到底装了什么货</span></h2>
  {cards}

  <h2>个人记忆画像沉淀什么<span>决定飞轮那一环怎么画</span></h2>
  <div class="cks">{mem}</div>
  <div style="margin-top:10px">{field('mem.extra', '还沉淀别的？', '例：商家的历史响应时长', True)}</div>

  <h2>权限隔离<span>老板一定会问「谁能看到什么」</span></h2>
  <div class="grid3">
    {field('perm.l1', 'L1 行业知识库 谁可见', '例：全行业可见')}
    {field('perm.l2', 'L2 岗位知识库 谁可见', '例：按岗位可见')}
    {field('perm.l3', 'L3 个人记忆画像 谁可见', '例：仅本人 + 其上级')}
  </div>

  <h2>质量指标<span>有就填，没有留空——比编一个强</span></h2>
  <div class="grid3">
    {field('m.cover', '覆盖率', '例：核心品类文档覆盖 85%')}
    {field('m.acc', '准确率 / 有效率', '例：知识引用准确率 92%')}
    {field('m.calls', '调用量', '例：日均被 Agent 调用 3000+ 次')}
  </div>

  <h2>还有什么要放进这页的<span>随便写</span></h2>
  <textarea data-k="note" placeholder="例：知识库是和某某团队共建的；某类知识暂时还进不来，原因是…"></textarea>

  <div class="bar">
    <button id="save">保存填写内容</button>
    <button class="ghost" id="copy">复制下方文字</button>
    <span id="msg">改动会自动记在这台设备上；点保存才会同步给我。</span>
  </div>
  <pre id="out"></pre>
</div>

<script>
(function () {{
  var PRISTINE = document.documentElement.outerHTML;
  var LS = 'tmg-kb-form-v1';
  var fs = Array.prototype.slice.call(document.querySelectorAll('[data-k]'));
  var cs = Array.prototype.slice.call(document.querySelectorAll('[data-c]'));
  var out = document.getElementById('out'), msg = document.getElementById('msg');

  function state() {{
    var f = {{}};
    fs.forEach(function (el) {{ var v = el.value.trim(); if (v) f[el.dataset.k] = v; }});
    return {{ fields: f, checks: cs.filter(function (c) {{ return c.checked; }})
                                 .map(function (c) {{ return c.dataset.c; }}) }};
  }}
  function apply(s) {{
    if (!s) return;
    fs.forEach(function (el) {{ if (s.fields && s.fields[el.dataset.k]) el.value = s.fields[el.dataset.k]; }});
    if (s.checks) cs.forEach(function (c) {{ c.checked = s.checks.indexOf(c.dataset.c) >= 0; }});
  }}
  function text() {{
    var s = state(), L = [];
    Object.keys(s.fields).forEach(function (k) {{ L.push(k + '：' + s.fields[k]); }});
    if (s.checks.length) L.push('个人记忆画像沉淀：' + s.checks.join(' / '));
    return L.length ? L.join('\\n') : '（还没填）';
  }}
  function refresh() {{
    out.textContent = text();
    try {{ localStorage.setItem(LS, JSON.stringify(state())); }} catch (e) {{}}
  }}
  try {{
    var v = localStorage.getItem(LS);
    apply(v ? JSON.parse(v) : JSON.parse(document.getElementById('kb-state').textContent));
  }} catch (e) {{}}
  refresh();
  fs.concat(cs).forEach(function (el) {{ el.addEventListener('input', refresh); }});

  document.getElementById('copy').addEventListener('click', function () {{
    var t = text();
    if (navigator.clipboard) {{
      navigator.clipboard.writeText(t).then(
        function () {{ msg.textContent = '已复制，粘贴给我就行。'; }},
        function () {{ msg.textContent = '复制被挡了，手动选中下面的文字。'; }});
    }} else {{ msg.textContent = '手动选中下面的文字复制。'; }}
  }});
  document.getElementById('save').addEventListener('click', function () {{
    msg.textContent = '保存中…';
    (window.claude && window.claude.use ? window.claude.use('artifact') : Promise.resolve(null))
      .then(function (art) {{
        if (!art || !art.publish) throw {{ code: 'not_granted' }};
        var body = PRISTINE.replace(
          /(<script type="application\\/json" id="kb-state">)[\\s\\S]*?(<\\/script>)/,
          function (m, a, b) {{ return a + JSON.stringify(state()) + b; }});
        return art.publish('<!doctype html>\\n' + body);
      }})
      .then(function () {{ msg.textContent = '已保存，我这边可以读到了。'; }})
      .catch(function (e) {{
        var c = (e && e.code) || '';
        msg.textContent = (c === 'not_writer' || c === 'not_granted')
          ? '这个视图没有写权限，点「复制下方文字」贴给我一样。'
          : '保存没成功（' + (c || '未知') + '），点「复制下方文字」贴给我。';
      }});
  }});
}})();
</script>
"""
(ROOT / 'tmg-kb-form.html').write_text(HTML, encoding='utf-8')
print('wrote tmg-kb-form.html', len(HTML))
