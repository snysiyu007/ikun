# -*- coding: utf-8 -*-
"""P2 / P3 文案编辑页：字段预填当前值，保存后写回页面自身，Claude 直接读。"""
import pathlib, json

ROOT = pathlib.Path(__file__).resolve().parent

TEXTS_P2 = [
    ('p2.h1', '标题', '场景 × 专家团 能力矩阵'),
    ('p2.claim', '标题下的主旨句', '同一组专家反复复用在 8 个作战中心上——不是 8 套烟囱，是 1 套能力'),
    ('p2.legend', '右上角图例说明', '该场景配置了这位专家，空格为不配置'),
    ('p2.rowlabel', '左上角表头', '作战中心 / 主导岗位'),
    ('p2.ftlabel', '底部统计行的名字', '被几个作战中心复用'),
    ('p2.take', '页脚论述（数字会自动算，改了就变成写死的）',
     '8 个作战中心、44 个配置，全部由 10 个专家承担——平均每个专家被 4.4 个场景复用；'
     '组织协同、任务执行 8 场景全覆盖。新增一个作战中心，平均只要补 1–2 个专属专家。'),
    ('p2.note', '页脚小字', '底色四列为基础专家；空格表示该场景暂不配置该专家。每个专家配哪些 Skill 见下一页。'),
]
TEXTS_P3 = [
    ('p3.h1', '标题', '每位专家手上的标准动作'),
    ('p3.claim', '标题下的主旨句', 'Skill 挂在专家身上，专家是岗位 Agent 的子 Agent——同一个动作被不同专家反复调用'),
    ('p3.legend', '右上角图例说明', '动作后的 ×N＝有几位专家在用同一个动作；卡内按复用次数排序，每张最多列 4 个'),
    ('p3.chain1', '链路条 第 1 节', '岗位 Agent'),
    ('p3.arrow1', '链路条 第 1 个箭头', '拆解为'),
    ('p3.chain2', '链路条 第 2 节', '场景运营专家团'),
    ('p3.arrow2', '链路条 第 2 个箭头', '配置'),
    ('p3.chain3', '链路条 第 3 节（本页）', 'Skill'),
    ('p3.rows', '每张卡最多列几个动作', '4'),
    ('p3.badge', '卡片头部徽标的措辞', 'N 个作战中心在用'),
    ('p3.take', '页脚论述（数字会自动算，改了就变成写死的）',
     'Skill 不是员工技能，是岗位动作的最小可复用单元。能力不再长在某个人身上——'
     '13 个动作被 10 位专家调用 29 次，新增一个作战中心，多数时候只是把现成的动作重新组合一次。'),
]
SCENES = [('行业销售','行业 GM'), ('竞对控比','行业 GM'), ('行业损益','行业 GM'), ('行业用户','行业 GM'),
          ('品类规划','品类组长'), ('商家复盘','品类小二'), ('新商新品','品类组长'), ('行业营销','营销小二')]
EXPERTS = [('组织协同','行业秘书处'), ('任务执行','行业王进喜'), ('数据官','行业陈景润'), ('知识官','行业藏书阁'),
           ('品类洞察','待命名'), ('竞对情报','行业猫头鹰'), ('用户增长','待命名'), ('财务官','行业葛朗台'),
           ('外部咨询','待命名'), ('营销创意','待命名')]
SKILLS = [('target-data','销售追踪'), ('Kbsearch-tmg','知识调用'), ('cmr-tmg','损益管理'),
          ('AI-data-qd','渠道取数'), ('AI-data-pl','品类取数'), ('Renwu-bj','任务找人'),
          ('Zhenduan','明确任务'), ('category-scan','品类扫描'), ('category-planning','品类规划'),
          ('category-opportunity','品类机会'), ('category-bd','品类招商'),
          ('category-report','品类报告'), ('category-meeting','品类会议')]

def tblock(items):
    out = ''
    for k, label, val in items:
        long = len(val) > 40
        tag = 'textarea' if long else 'input'
        inner = (f'<textarea data-k="{k}" rows="2">{val}</textarea>' if long
                 else f'<input data-k="{k}" value="{val}">')
        out += f'<label class="f"><span>{label}</span>{inner}</label>'
    return out

def rows(items, kind, c1, c2):
    out = ''
    for a, b in items:
        out += (f'<div class="row"><span class="orig">{a}</span>'
                f'<input data-k="{kind}.{a}.1" value="{a}" aria-label="{c1}">'
                f'<input data-k="{kind}.{a}.2" value="{b}" aria-label="{c2}">'
                f'<label class="hide"><input type="checkbox" data-c="{kind}:{a}">'
                f'<span class="box"></span>不显示</label></div>')
    return out

HTML = f"""<title>P2 / P3 文案编辑</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Noto+Sans+SC:wght@400;500;700&family=JetBrains+Mono:wght@500&display=swap">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0C0918;background-image:radial-gradient(1200px 560px at 50% -10%,rgba(124,58,237,.20),transparent 70%);
     color:#F6F2FF;font-family:'Sora','Noto Sans SC',system-ui,-apple-system,'PingFang SC',sans-serif;
     font-weight:500;line-height:1.5;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:1180px;margin:0 auto;padding:34px 26px 60px}}
h1{{font-size:26px;font-weight:700}}
.lead{{margin-top:8px;font-size:14px;color:#C6B4F5;line-height:1.7;max-width:880px}}
.lead em{{font-style:normal;color:#F6F2FF;font-weight:700}}
h2{{font-size:16px;font-weight:700;margin:32px 0 6px}}
h2 b{{font-family:'JetBrains Mono',monospace;font-size:11px;color:#C6B4F5;border:1px solid rgba(167,139,250,.5);
     border-radius:6px;padding:2px 7px;margin-right:9px;font-weight:500;vertical-align:middle}}
.hint{{font-size:12px;color:#9C8CCB;margin-bottom:12px}}
.card{{border:1px solid rgba(167,139,250,.3);border-radius:14px;background:rgba(139,92,246,.05);padding:16px 18px}}
.fs{{display:grid;gap:11px}}
.f{{display:flex;flex-direction:column;gap:5px}}
.f span{{font-size:11.5px;color:#9C8CCB}}
input,textarea{{width:100%;background:rgba(139,92,246,.08);border:1px solid rgba(167,139,250,.32);
     border-radius:9px;padding:9px 12px;color:#F6F2FF;font-family:inherit;font-size:13.5px;line-height:1.6}}
textarea{{resize:vertical}}
input:focus,textarea:focus{{outline:none;border-color:rgba(196,181,253,.85);background:rgba(139,92,246,.15)}}
.row{{display:grid;grid-template-columns:104px 1fr 1fr 96px;gap:10px;align-items:center;
     padding:7px 0;border-bottom:1px solid rgba(167,139,250,.12)}}
.row:last-child{{border-bottom:none}}
.orig{{font-size:11.5px;color:#7B6CA6;font-family:'JetBrains Mono',monospace;overflow:hidden;text-overflow:ellipsis}}
.chead{{display:grid;grid-template-columns:104px 1fr 1fr 96px;gap:10px;font-size:11px;color:#9C8CCB;
       padding-bottom:8px;border-bottom:1px solid rgba(167,139,250,.26);letter-spacing:.04em}}
.hide{{display:flex;align-items:center;gap:7px;font-size:11.5px;color:#9C8CCB;cursor:pointer}}
.hide input{{position:absolute;opacity:0;width:0;height:0}}
.box{{width:16px;height:16px;border-radius:5px;border:1px dashed rgba(167,139,250,.6);display:block;
     position:relative;flex:none}}
.hide input:checked+.box{{background:linear-gradient(180deg,#9D55FF,#7A28E8);border:1px solid rgba(255,255,255,.2)}}
.hide input:checked+.box:after{{content:'';position:absolute;left:5px;top:2px;width:4px;height:8px;
     border:solid #fff;border-width:0 2px 2px 0;transform:rotate(42deg)}}
.bar{{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:28px 0 12px}}
button{{font-family:inherit;font-size:13.5px;font-weight:700;border-radius:10px;padding:11px 20px;cursor:pointer;
       border:1px solid rgba(255,255,255,.16);color:#fff;background:linear-gradient(180deg,#9D55FF,#7A28E8);
       box-shadow:0 6px 16px rgba(74,20,140,.36)}}
button.ghost{{background:rgba(167,139,250,.09);border:1px solid rgba(167,139,250,.45);color:#C6B4F5;box-shadow:none}}
button:hover{{filter:brightness(1.08)}}
#msg{{font-size:12.5px;color:#9C8CCB}}
pre{{background:rgba(139,92,246,.07);border:1px solid rgba(167,139,250,.3);border-radius:12px;padding:16px 18px;
    font-family:'JetBrains Mono','Noto Sans SC',monospace;font-size:12.5px;line-height:1.8;color:#E4D8FF;
    white-space:pre-wrap;user-select:all;max-height:340px;overflow:auto}}
@media (max-width:760px){{.row,.chead{{grid-template-columns:1fr}}}}
</style>

<script type="application/json" id="edit-state">{{"fields":{{}},"hidden":[]}}</script>

<div class="wrap">
  <h1>P2 / P3 文案编辑</h1>
  <p class="lead">所有字段<em>已经预填成图上现在的内容</em>，改哪个动哪个，不动的保持原样。改完点「保存」，
    我这边读到之后重画 P2、P3。<em>「谁配谁」的关系不在这页</em>——那个还在原来的勾选页改。</p>

  <h2><b>P2</b>页面文案</h2>
  <div class="card"><div class="fs">{tblock(TEXTS_P2)}</div></div>

  <h2><b>P2</b>作战中心<span></span></h2>
  <p class="hint">左边灰字是当前的名字（我用它对应回原数据，别管它）；改中间两栏即可。</p>
  <div class="card">
    <div class="chead"><span>当前</span><span>作战中心名称</span><span>主导岗位</span><span></span></div>
    {rows(SCENES, 'scene', '作战中心名称', '主导岗位')}
  </div>

  <h2><b>P2 P3</b>专家</h2>
  <p class="hint">「待命名」那四个是新增专家，还没有代号——你们的命名规律是「行业 + 人名/物名」，这里可以直接起名。</p>
  <div class="card">
    <div class="chead"><span>当前</span><span>职能名（图上大字）</span><span>代号（图上小字）</span><span></span></div>
    {rows(EXPERTS, 'expert', '职能名', '代号')}
  </div>

  <h2><b>P3</b>Skill</h2>
  <div class="card">
    <div class="chead"><span>当前</span><span>代号</span><span>中文动作名</span><span></span></div>
    {rows(SKILLS, 'skill', '代号', '中文动作名')}
  </div>

  <h2><b>P3</b>页面文案</h2>
  <div class="card"><div class="fs">{tblock(TEXTS_P3)}</div></div>

  <h2>还想改什么</h2>
  <div class="card"><textarea data-k="note" rows="3" placeholder="例：P2 想把行业营销挪到第一行；P3 的卡片想按专家名笔画排…"></textarea></div>

  <div class="bar">
    <button id="save">保存修改</button>
    <button class="ghost" id="copy">复制改动清单</button>
    <span id="msg">改动会自动记在这台设备上；点保存才会同步给我。</span>
  </div>
  <pre id="out"></pre>
</div>

<script>
(function () {{
  var PRISTINE = document.documentElement.outerHTML;
  var LS = 'tmg-editor-v1';
  var fs = Array.prototype.slice.call(document.querySelectorAll('[data-k]'));
  var cs = Array.prototype.slice.call(document.querySelectorAll('[data-c]'));
  var out = document.getElementById('out'), msg = document.getElementById('msg');
  var BASE = {{}};
  fs.forEach(function (el) {{ BASE[el.dataset.k] = el.value; }});

  function state() {{
    var f = {{}};
    fs.forEach(function (el) {{ f[el.dataset.k] = el.value; }});
    return {{ fields: f, hidden: cs.filter(function (c) {{ return c.checked; }})
                                  .map(function (c) {{ return c.dataset.c; }}) }};
  }}
  function apply(s) {{
    if (!s) return;
    fs.forEach(function (el) {{ if (s.fields && s.fields[el.dataset.k] !== undefined) el.value = s.fields[el.dataset.k]; }});
    if (s.hidden) cs.forEach(function (c) {{ c.checked = s.hidden.indexOf(c.dataset.c) >= 0; }});
  }}
  function text() {{
    var s = state(), L = [];
    Object.keys(s.fields).forEach(function (k) {{
      if (s.fields[k] !== BASE[k]) L.push('改 ' + k + '：' + BASE[k] + '  →  ' + s.fields[k]);
    }});
    s.hidden.forEach(function (h) {{ L.push('隐藏 ' + h); }});
    return L.length ? L.join('\\n') : '（还没有改动）';
  }}
  function refresh() {{
    out.textContent = text();
    try {{ localStorage.setItem(LS, JSON.stringify(state())); }} catch (e) {{}}
  }}
  try {{
    var v = localStorage.getItem(LS);
    if (v) apply(JSON.parse(v));
    else {{
      var st = JSON.parse(document.getElementById('edit-state').textContent);
      if (st && st.fields && Object.keys(st.fields).length) apply(st);
    }}
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
          /(<script type="application\\/json" id="edit-state">)[\\s\\S]*?(<\\/script>)/,
          function (m, a, b) {{ return a + JSON.stringify(state()) + b; }});
        return art.publish('<!doctype html>\\n' + body);
      }})
      .then(function () {{ msg.textContent = '已保存，我这边可以读到了。'; }})
      .catch(function (e) {{
        var c = (e && e.code) || '';
        msg.textContent = (c === 'not_writer' || c === 'not_granted')
          ? '这个视图没有写权限，点「复制改动清单」贴给我一样。'
          : '保存没成功（' + (c || '未知') + '），点「复制改动清单」贴给我。';
      }});
  }});
}})();
</script>
"""
(ROOT / 'tmg-editor.html').write_text(HTML, encoding='utf-8')
print('wrote tmg-editor.html', len(HTML))
