# -*- coding: utf-8 -*-
"""专家团配置勾选页：用户在页面上勾，保存后状态写回页面自身，Claude 直接读。"""
import pathlib, json

ROOT = pathlib.Path(__file__).resolve().parent

# 职能全称 / 代号 / 一句话说明 / 是否基础专家
EXPERTS = [
    ('数据官',   '行业陈景润', '取数、算达成与缺口、做归因',        1),
    ('知识官',   '行业藏书阁', '调行业政策、资源规则、历史打法',    1),
    ('组织协同', '行业秘书处', '拉通角色、派任务、跟进度',          1),
    ('任务执行', '行业王进喜', '落地动作、生成话术、触达商家',      1),
    ('竞对情报', '行业猫头鹰', '盯竞对动作、价格与新品',            0),
    ('财务官',   '行业葛朗台', '算损益、投产比、费用与折扣',        0),
    ('外部咨询', '待命名',     '引入外部行业研究与专家观点',        0),
    ('营销创意', '待命名',     '出活动主题、创意与内容',            0),
    ('用户增长', '待命名',     '拉新、复购、人群运营',              0),
    ('品类洞察', '待命名',     '看品类结构、趋势与机会点',          0),
]
BASE = [e[0] for e in EXPERTS if e[3]]
SCENES = [
    ('行业销售', '行业 GM',  1), ('竞对控比', '行业 GM',  1),
    ('行业损益', '行业 GM',  1), ('行业用户', '行业 GM',  1),
    ('品类规划', '品类组长', 1), ('商家复盘', '品类小二', 1),
    ('新商新品', '品类组长', 1), ('行业营销', '营销小二', 0),
]
PRESET = {
    '行业销售': ['组织协同','任务执行','数据官','知识官'],
    '竞对控比': ['组织协同','任务执行','数据官','知识官','竞对情报','品类洞察'],
    '行业损益': ['组织协同','任务执行','数据官','财务官'],
    '行业用户': ['组织协同','任务执行','数据官','知识官','用户增长'],
    '品类规划': ['组织协同','任务执行','数据官','知识官','竞对情报','外部咨询','品类洞察'],
    '商家复盘': ['组织协同','任务执行','数据官','知识官','竞对情报','财务官','用户增长','品类洞察'],
    '新商新品': ['组织协同','任务执行','数据官','知识官'],
    '行业营销': ['组织协同','任务执行','知识官','营销创意','用户增长','品类洞察'],
}
SKILLS = [('target-data','销售追踪'), ('Kbsearch-tmg','知识调用'), ('cmr-tmg','损益管理'),
          ('AI-data-qd','渠道取数'), ('AI-data-pl','品类取数'), ('Renwu-bj','任务找人'),
          ('Zhenduan','明确任务'), ('category-scan','品类扫描'), ('category-planning','品类规划'),
          ('category-opportunity','品类机会'), ('category-bd','品类招商'),
          ('category-report','品类报告'), ('category-meeting','品类会议')]
SKPRESET = {   # 已按你上次勾的回填
    '数据官': ['target-data','AI-data-qd','AI-data-pl'], '知识官': ['Kbsearch-tmg'],
    '组织协同': ['Renwu-bj','Zhenduan'], '任务执行': ['Renwu-bj'], '竞对情报': [],
    '财务官': ['cmr-tmg'], '外部咨询': ['AI-data-pl','Zhenduan'],
    '营销创意': ['Kbsearch-tmg','Renwu-bj','Zhenduan'], '用户增长': ['Kbsearch-tmg','AI-data-pl'],
    '品类洞察': ['target-data','Kbsearch-tmg','AI-data-pl'],
}

def sid(s): return 's' + str([x[0] for x in SCENES].index(s))
def eid(e): return 'e' + str([x[0] for x in EXPERTS].index(e))

gloss = ''.join(
    f'<div class="gx{" b" if base else ""}"><b>{fn}</b><span>{code}</span><p>{desc}</p></div>'
    for fn, code, desc, base in EXPERTS)

heads = ''.join(
    f'<div class="hc{" b" if base else ""}"><b>{fn}</b><span>{code}</span></div>'
    for fn, code, _, base in EXPERTS)

skheads = ''.join(f'<div class="hc"><b>{c}</b><span>{d}</span></div>' for c, d in SKILLS)
skrows = []
for fn, code, _d, base in EXPERTS:
    cs = ''.join(
        f'<label class="cell"><input type="checkbox" data-owner="{fn}" data-skill="{c}"'
        f'{" checked" if c in SKPRESET.get(fn, []) else ""}><span class="box"></span></label>'
        for c, _n in SKILLS)
    skrows.append(f'<div class="rl"><b>{fn}</b><span>{code}</span></div>' + cs)

rows = []
for scene, owner, _ in SCENES:
    cells = []
    for fn, _c, _d, base in EXPERTS:
        on = ' checked' if fn in PRESET[scene] else ''
        cells.append(
            f'<label class="cell{" b" if base else ""}">'
            f'<input type="checkbox" data-scene="{scene}" data-exp="{fn}"{on}>'
            f'<span class="box"></span></label>')
    rows.append(f'<div class="rl"><b>{scene}</b><span>{owner} 主导</span></div>' + ''.join(cells))

HTML = f"""<title>专家团配置 · 勾选</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Noto+Sans+SC:wght@400;500;700&family=JetBrains+Mono:wght@500&display=swap">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0C0918;background-image:radial-gradient(1200px 560px at 50% -10%,rgba(124,58,237,.20),transparent 70%);
     color:#F6F2FF;font-family:'Sora','Noto Sans SC',system-ui,-apple-system,'PingFang SC',sans-serif;
     font-weight:500;line-height:1.5;-webkit-font-smoothing:antialiased}}
a{{color:#C6B4F5}}a:hover{{color:#E6DBFF}}
.wrap{{max-width:1460px;margin:0 auto;padding:34px 28px 60px}}
h1{{font-size:26px;font-weight:700}}
.lead{{margin-top:8px;font-size:14px;color:#C6B4F5;line-height:1.7;max-width:940px}}
.lead em{{font-style:normal;color:#F6F2FF;font-weight:700}}
h2{{font-size:15px;font-weight:700;margin:30px 0 12px;letter-spacing:.02em}}
h2 span{{font-size:12px;font-weight:500;color:#9C8CCB;margin-left:10px}}
.gloss{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}}
.gx{{border:1px dashed rgba(167,139,250,.3);border-radius:12px;padding:11px 13px;background:rgba(139,92,246,.04)}}
.gx.b{{border-style:solid;border-color:rgba(167,139,250,.45);background:rgba(139,92,246,.12)}}
.gx b{{font-size:14.5px;font-weight:700;display:block}}
.gx span{{font-size:11px;color:#C6B4F5;font-family:'JetBrains Mono',monospace}}
.gx p{{margin-top:6px;font-size:11.5px;color:#9C8CCB;line-height:1.6}}
.scroll{{overflow-x:auto;padding-bottom:4px}}
.mx{{display:grid;grid-template-columns:186px repeat(10,minmax(96px,1fr));gap:0 4px;min-width:1180px}}
.mx2{{display:grid;grid-template-columns:180px repeat(13,minmax(104px,1fr));gap:0 4px;min-width:1600px}}
.mx2 .hc b{{font-family:'JetBrains Mono',monospace;font-size:12px}}
.mx2 .rl span{{font-family:'JetBrains Mono',monospace}}
.hc{{display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:2px;
    padding:10px 4px 10px;text-align:center;border-bottom:1px solid rgba(167,139,250,.26)}}
.hc.b{{background:rgba(139,92,246,.12);border-radius:10px 10px 0 0}}
.hc b{{font-size:13px;font-weight:700}}
.hc span{{font-size:10px;color:#9C8CCB}}
.corner{{border-bottom:1px solid rgba(167,139,250,.26);display:flex;align-items:flex-end;
        padding:0 0 12px 2px;font-size:11px;color:#9C8CCB;letter-spacing:.08em}}
.rl{{display:flex;flex-direction:column;justify-content:center;gap:3px;padding:0 10px 0 2px;
    border-bottom:1px solid rgba(167,139,250,.13);position:sticky;left:0;background:#0C0918;z-index:1}}
.rl b{{font-size:15px;font-weight:700}}
.rl span{{font-size:10.5px;color:#C6B4F5;border:1px solid rgba(167,139,250,.42);border-radius:999px;
         padding:1px 8px;align-self:flex-start}}
.cell{{display:flex;align-items:center;justify-content:center;min-height:62px;cursor:pointer;
      border-bottom:1px solid rgba(167,139,250,.13)}}
.cell.b{{background:rgba(139,92,246,.12)}}
.cell:hover .box{{border-color:rgba(196,181,253,.9);background:rgba(167,139,250,.16)}}
.cell input{{position:absolute;opacity:0;width:0;height:0}}
.box{{width:26px;height:26px;border-radius:8px;border:1px dashed rgba(167,139,250,.55);
     display:block;position:relative;transition:all .12s ease}}
.cell input:checked+.box{{background:linear-gradient(180deg,#9D55FF,#7A28E8);border:1px solid rgba(255,255,255,.2);
     box-shadow:0 3px 10px rgba(74,20,140,.45),inset 0 1px 0 rgba(255,255,255,.28)}}
.cell input:checked+.box:after{{content:'';position:absolute;left:9px;top:4.5px;width:6px;height:12px;
     border:solid #fff;border-width:0 2px 2px 0;transform:rotate(42deg)}}
.cell input:focus-visible+.box{{outline:2px solid #C6B4F5;outline-offset:2px}}
.extra{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:14px}}
.extra input{{width:100%;background:rgba(139,92,246,.06);border:1px dashed rgba(167,139,250,.4);
     border-radius:10px;padding:11px 13px;color:#F6F2FF;font-family:inherit;font-size:13.5px}}
.extra input::placeholder{{color:#7B6CA6}}
.extra input:focus{{outline:none;border-color:rgba(196,181,253,.8);background:rgba(139,92,246,.12)}}
.bar{{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:26px 0 12px}}
button{{font-family:inherit;font-size:13.5px;font-weight:700;border-radius:10px;padding:11px 20px;
       cursor:pointer;border:1px solid rgba(255,255,255,.16);color:#fff;
       background:linear-gradient(180deg,#9D55FF,#7A28E8);
       box-shadow:0 6px 16px rgba(74,20,140,.36),inset 0 1px 0 rgba(255,255,255,.24)}}
button.ghost{{background:rgba(167,139,250,.09);border:1px solid rgba(167,139,250,.45);color:#C6B4F5;box-shadow:none}}
button:hover{{filter:brightness(1.08)}}
#msg{{font-size:12.5px;color:#9C8CCB}}
pre{{background:rgba(139,92,246,.07);border:1px solid rgba(167,139,250,.3);border-radius:12px;
    padding:16px 18px;font-family:'JetBrains Mono','Noto Sans SC',monospace;font-size:12.5px;
    line-height:1.85;color:#E4D8FF;white-space:pre-wrap;user-select:all}}
@media (max-width:900px){{.gloss{{grid-template-columns:repeat(2,1fr)}}.extra{{grid-template-columns:1fr}}}}
</style>

<script type="application/json" id="picks-state">{json.dumps({"picks": PRESET, "extra": ["", "", ""], "skills": {fn: list(SKPRESET.get(fn, [])) for fn, _c, _d, _b in EXPERTS}, "skillExtra": ["", "", ""]}, ensure_ascii=False)}</script>

<div class="wrap">
  <h1>专家团配置 · 请勾选</h1>
  <p class="lead">两张表：上面是<em>作战中心需要哪些专家</em>（已按你上次勾的结果回填），下面是
    <em>每个专家配哪些 Skill</em>（我按职能先勾了一部分，不对就改）。改完点「保存勾选结果」，我这边直接读。</p>

  <h2>专家说明<span>后 4 位是新增的，还没有代号；说明是我按名字先写的，不对就改</span></h2>
  <div class="gloss">{gloss}</div>

  <h2>作战中心 × 专家<span>点格子切换；带底色的四列是基础专家</span></h2>
  <div class="scroll"><div class="mx">
    <div class="corner">作战中心 / 主导岗位</div>{heads}
    {''.join(rows)}
  </div></div>

  <h2>每个专家配哪些 Skill<span>已按你上次勾的回填；新加的 6 个 category-* 还没分配，麻烦勾一下（表格可以左右滑）</span></h2>
  <div class="scroll"><div class="mx2">
    <div class="corner">专家 / 代号</div>{skheads}
    {''.join(skrows)}
  </div></div>

  <div class="extra">
    <input id="k0" placeholder="补充 Skill 1，例如：huodong-tmg（活动报名）">
    <input id="k1" placeholder="补充 Skill 2">
    <input id="k2" placeholder="补充 Skill 3">
  </div>

  <h2>还缺哪些专家？<span>填了会一起带给我</span></h2>
  <div class="extra">
    <input id="x0" placeholder="补充专家 1，例如：物流履约官">
    <input id="x1" placeholder="补充专家 2">
    <input id="x2" placeholder="补充专家 3">
  </div>

  <div class="bar">
    <button id="save">保存勾选结果</button>
    <button class="ghost" id="copy">复制下方文字</button>
    <span id="msg">改动会自动记在这台设备上；点保存才会同步给我。</span>
  </div>
  <pre id="out"></pre>
</div>

<script>
(function () {{
  var PRISTINE = document.documentElement.outerHTML;
  var LS = 'tmg-expert-picks-v1';
  var boxes = Array.prototype.slice.call(document.querySelectorAll('input[data-scene]'));
  var sboxes = Array.prototype.slice.call(document.querySelectorAll('input[data-owner]'));
  var xs = [document.getElementById('x0'), document.getElementById('x1'), document.getElementById('x2')];
  var ks = [document.getElementById('k0'), document.getElementById('k1'), document.getElementById('k2')];
  var out = document.getElementById('out'), msg = document.getElementById('msg');

  function state() {{
    var picks = {{}};
    boxes.forEach(function (b) {{
      if (!picks[b.dataset.scene]) picks[b.dataset.scene] = [];
      if (b.checked) picks[b.dataset.scene].push(b.dataset.exp);
    }});
    var skills = {{}};
    sboxes.forEach(function (b) {{
      if (!skills[b.dataset.owner]) skills[b.dataset.owner] = [];
      if (b.checked) skills[b.dataset.owner].push(b.dataset.skill);
    }});
    return {{ picks: picks, extra: xs.map(function (i) {{ return i.value.trim(); }}),
             skills: skills, skillExtra: ks.map(function (i) {{ return i.value.trim(); }}) }};
  }}
  function apply(s) {{
    if (!s || !s.picks) return;
    boxes.forEach(function (b) {{
      var list = s.picks[b.dataset.scene];
      if (list) b.checked = list.indexOf(b.dataset.exp) >= 0;
    }});
    if (s.skills) sboxes.forEach(function (b) {{
      var l = s.skills[b.dataset.owner];
      if (l) b.checked = l.indexOf(b.dataset.skill) >= 0;
    }});
    (s.extra || []).forEach(function (v, i) {{ if (xs[i]) xs[i].value = v || ''; }});
    (s.skillExtra || []).forEach(function (v, i) {{ if (ks[i]) ks[i].value = v || ''; }});
  }}
  function text() {{
    var s = state(), lines = [];
    Object.keys(s.picks).forEach(function (k) {{
      lines.push(k + '｜' + (s.picks[k].length ? s.picks[k].join('  ') : '（未勾选）'));
    }});
    var ex = s.extra.filter(Boolean);
    if (ex.length) lines.push('补充专家：' + ex.join(' / '));
    lines.push('');
    lines.push('—— 专家 × Skill ——');
    Object.keys(s.skills).forEach(function (k) {{
      lines.push(k + '｜' + (s.skills[k].length ? s.skills[k].join('  ') : '（待配）'));
    }});
    var kx = s.skillExtra.filter(Boolean);
    if (kx.length) lines.push('补充 Skill：' + kx.join(' / '));
    return lines.join('\\n');
  }}
  function refresh() {{
    out.textContent = text();
    try {{ localStorage.setItem(LS, JSON.stringify(state())); }} catch (e) {{}}
  }}

  try {{
    var saved = localStorage.getItem(LS);
    if (saved) apply(JSON.parse(saved));
    else apply(JSON.parse(document.getElementById('picks-state').textContent));
  }} catch (e) {{}}
  refresh();
  boxes.concat(sboxes, xs, ks).forEach(function (el) {{ el.addEventListener('input', refresh); }});

  document.getElementById('copy').addEventListener('click', function () {{
    var t = text();
    if (navigator.clipboard) {{
      navigator.clipboard.writeText(t).then(
        function () {{ msg.textContent = '已复制，粘贴给我就行。'; }},
        function () {{ msg.textContent = '复制被浏览器挡了，手动选中下面的文字复制。'; }});
    }} else {{ msg.textContent = '手动选中下面的文字复制。'; }}
  }});

  document.getElementById('save').addEventListener('click', function () {{
    msg.textContent = '保存中…';
    (window.claude && window.claude.use ? window.claude.use('artifact') : Promise.resolve(null))
      .then(function (art) {{
        if (!art || !art.publish) throw {{ code: 'not_granted' }};
        var body = PRISTINE.replace(
          /(<script type="application\\/json" id="picks-state">)[\\s\\S]*?(<\\/script>)/,
          function (m, a, b) {{ return a + JSON.stringify(state()) + b; }});
        return art.publish('<!doctype html>\\n' + body);
      }})
      .then(function () {{ msg.textContent = '已保存，我这边可以读到了。'; }})
      .catch(function (e) {{
        var c = (e && e.code) || '';
        msg.textContent = (c === 'not_writer' || c === 'not_granted')
          ? '这个视图没有写权限，点「复制下方文字」贴给我一样快。'
          : '保存没成功（' + (c || '未知') + '），点「复制下方文字」贴给我。';
      }});
  }});
}})();
</script>
"""
(ROOT / 'tmg-expert-picker.html').write_text(HTML, encoding='utf-8')
print('wrote tmg-expert-picker.html', len(HTML), 'bytes')
