# -*- coding: utf-8 -*-
"""Builds the TMG A-H platform architecture diagram.

Emits the same design twice from one source: a standalone page (fonts get
embedded afterwards by embed_fonts.py) and the Main artboard of the design
canvas, plus the three alternative layout directions kept for reference.
"""
import pathlib, json

ROOT = pathlib.Path(__file__).resolve().parent
CANVAS = ROOT / 'canvas'
CANVAS.mkdir(exist_ok=True)

SCENES = ['行业销售','竞对控比','行业损益','行业用户','品类规划','商家复盘','新商新品','行业营销']
ROLES  = ['行业 GM','品类组长','渠道组长','品类小二','渠道小二','用户小二','营销小二']
EXPERTS= [('行业陈景润','数据分析子 Agent'),('行业藏书阁','知识管理子 Agent'),('行业猫头鹰','竞对监控子 Agent'),
          ('行业葛朗台','财务分析子 Agent'),('行业秘书处','组织协同子 Agent'),('行业王进喜','任务执行子 Agent')]
SKILLS = [('target-data','销售追踪'),('Kbsearch-tmg','知识调用'),('cmr-tmg','损益管理'),
          ('AI-data-qd','渠道取数'),('AI-data-pl','品类取数'),('Renwu-bj','任务找人'),
          ('Zhenduan','明确任务'),('category-scan','品类扫描'),('category-planning','品类规划'),
          ('category-opportunity','品类机会'),('category-bd','品类招商'),
          ('category-report','品类报告'),('category-meeting','品类会议'),
          ('kbase-learning','知识学习'),('kbase-wiki','知识 wiki 化')]
KB = [('L1','行业知识库','行业的通用信息，以对商文档为主'),
      ('L2','岗位知识库','行业的政策、资源扶持等核心内容'),
      ('L3','个人记忆画像','对应岗位的行业经验、商家判断、运营习惯等和个人意识相关的信息，由 Agent 使用中沉淀回流')]

TAGLINE = '把岗位职责变成可复用的 Agent，把个人经验沉淀成组织资产'

# violet = capability (scenes / agents / skills), indigo = knowledge
CSS = """
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:#0C0918;
       background-image:radial-gradient(1200px 560px at 50% -10%,rgba(124,58,237,.22),transparent 70%),
                        radial-gradient(900px 460px at 50% 112%,rgba(49,46,129,.28),transparent 72%);
       background-attachment:fixed;color:#F6F2FF;
       font-family:'Sora','Noto Sans SC',system-ui,-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;
       font-weight:500;line-height:1.45;-webkit-font-smoothing:antialiased}
  a{color:#C6B4F5}a:hover{color:#E6DBFF}
  .stage{width:1600px;max-width:100%;margin:0 auto;padding:26px 40px}
  .mast{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;flex-wrap:wrap;
        padding-bottom:13px;margin-bottom:12px;border-bottom:1px solid rgba(167,139,250,.26)}
  .brand{display:flex;align-items:center;gap:14px}
  .mark{flex:none;width:38px;height:38px}
  h1{font-size:28px;font-weight:700;letter-spacing:.01em;text-wrap:balance}
  .tag{margin-top:4px;font-size:12.5px;color:#9C8CCB;letter-spacing:.04em}
  .legend{display:flex;gap:16px;align-items:center;font-size:11.5px;color:#9C8CCB;letter-spacing:.04em}
  .legend span{display:flex;align-items:center;gap:6px}
  .key{width:20px;height:11px;border-radius:4px;display:block;
       background:linear-gradient(180deg,#9D55FF,#7A28E8)}
  .key.g{background:rgba(167,139,250,.09);border:1px dashed rgba(167,139,250,.5)}
  .panel{border:1px dashed rgba(167,139,250,.26);border-radius:15px;
         background:rgba(139,92,246,.045);padding:10px 15px 12px}
  .head{display:flex;align-items:baseline;gap:10px;margin-bottom:8px}
  .tier{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:10.5px;color:#C6B4F5;
        border:1px solid rgba(167,139,250,.5);border-radius:6px;padding:2px 7px;flex:none}
  h2{font-size:17px;font-weight:700;letter-spacing:.02em}
  .sub{font-size:12px;color:#9C8CCB}
  .grid{display:grid;gap:8px}
  .chip{border-radius:11px;padding:9px 11px;background:linear-gradient(180deg,#9D55FF,#7A28E8);
        border:1px solid rgba(255,255,255,.16);
        box-shadow:0 6px 16px rgba(74,20,140,.36),inset 0 1px 0 rgba(255,255,255,.24);
        transition:transform .18s ease,box-shadow .18s ease}
  .chip:hover{transform:translateY(-2px);box-shadow:0 12px 24px rgba(74,20,140,.48),inset 0 1px 0 rgba(255,255,255,.3)}
  .chip b{display:block;font-size:14.5px;font-weight:700}
  .chip i{display:block;font-style:normal;font-size:11.5px;color:rgba(255,255,255,.74);margin-top:2px}
  .chip.g{background:rgba(167,139,250,.09);border:1px dashed rgba(167,139,250,.5);box-shadow:none}
  .chip.g b{color:#C6B4F5}.chip.g i{color:#9C8CCB}
  .chip.g:hover{transform:none;box-shadow:none;background:rgba(167,139,250,.14)}
  .mono b{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:12.5px;font-weight:500}
  .arrow{display:flex;align-items:center;justify-content:center;gap:9px;height:15px;color:#C6B4F5}
  .arrow span{font-size:10.5px;letter-spacing:.1em;color:#9C8CCB}
  .kb{margin-top:12px;border:1px solid rgba(129,140,248,.45);border-radius:15px;
      background:rgba(67,56,202,.13);padding:10px 15px 12px}
  .kb .tier{color:#C7CCFF;border-color:rgba(165,180,252,.5)}
  .kb .grid{grid-template-columns:1fr 1fr 1.32fr;gap:12px}
  .kbcard{border-radius:11px;padding:10px 13px;display:flex;flex-direction:column;gap:6px;
          background:linear-gradient(180deg,#4C41C9,#2C2480);border:1px solid rgba(199,210,254,.26);
          box-shadow:0 6px 16px rgba(23,18,80,.5),inset 0 1px 0 rgba(255,255,255,.16)}
  .kbtop{display:flex;align-items:center;gap:9px}
  .kbcard b{font-size:15px;font-weight:700}
  .kbcard p{font-size:11.5px;line-height:1.6;color:rgba(255,255,255,.8)}
  .idx{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:10px;color:#D8DCFF;
       border:1px solid rgba(216,220,255,.42);border-radius:5px;padding:2px 6px;flex:none}
  @media (prefers-reduced-motion:reduce){.chip{transition:none}.chip:hover{transform:none}}
"""

MARK = ('<svg class="mark" viewBox="0 0 44 44" fill="none" aria-hidden="true">'
        '<rect x="4" y="5" width="36" height="8" rx="3" fill="#9D55FF"/>'
        '<rect x="9" y="17" width="26" height="8" rx="3" fill="#7A28E8"/>'
        '<rect x="14" y="29" width="16" height="8" rx="3" fill="#5B1BB0"/></svg>')

MAST = f"""<header class="mast">
  <div class="brand">{MARK}<div><h1>TMG保健行业A-H平台</h1><p class="tag">{TAGLINE}</p></div></div>
  <div class="legend"><span><i class="key"></i>已定义</span><span><i class="key g"></i>扩展位</span></div>
</header>"""

def head(tier, title, sub=''):
    s = f'<span class="sub">{sub}</span>' if sub else ''
    return f'<div class="head"><span class="tier">{tier}</span><h2>{title}</h2>{s}</div>'

def dn(label):
    return (f'<div class="arrow"><svg width="9" height="22" viewBox="0 0 9 22" fill="none" aria-hidden="true">'
            f'<path d="M4.5 0V16" stroke="currentColor" stroke-width="1.1"/>'
            f'<path d="M1 15L4.5 21L8 15Z" fill="currentColor"/></svg><span>{label}</span></div>')

def scene_rows():   # one per row, differentiator bold, shared suffix muted
    return ''.join(f'<div class="chip scene"><b>{s}</b><i>作战中心</i></div>' for s in SCENES)
def scene_cards():
    return ''.join(f'<div class="chip" style="text-align:center"><b>{s}</b><i>作战中心</i></div>' for s in SCENES)
def role_chips(center=True):
    st = ' style="text-align:center"' if center else ''
    return (''.join(f'<div class="chip"{st}><b>{r}</b></div>' for r in ROLES)
            + f'<div class="chip g"{st}><b>岗位 X…</b></div>')
def expert_chips():
    return (''.join(f'<div class="chip"><b>{n}</b><i>{r}</i></div>' for n, r in EXPERTS)
            + '<div class="chip g slot"><b>等等…</b><i>按场景扩充</i></div>')
def skill_chips():
    return (''.join(f'<div class="chip mono"><b>{k}</b><i>{v}</i></div>' for k, v in SKILLS)
            + '<div class="chip g mono"><b>Skill X…</b><i>扩展位</i></div>' * 3)
def kb_cards():
    return ''.join(f'<div class="kbcard"><div class="kbtop"><span class="idx">{i}</span><b>{n}</b></div>'
                   f'<p>{d}</p></div>' for i, n, d in KB)

def kb_band():
    return (f'<section class="kb">{head("KB","三层知识库","平台知识底座，服务全部工作场景与各层 Agent")}'
            f'<div class="grid">{kb_cards()}</div></section>')

# ============================================================ FINAL — 16:9
FINAL_CSS = """
  .body{display:grid;grid-template-columns:340px 1fr;gap:18px;align-items:stretch}
  .scenecol{display:flex;flex-direction:column}
  .scenecol .grid{flex:1;grid-template-rows:repeat(8,1fr);gap:8px}
  .scene{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:0 14px}
  .scene b{font-size:15px}
  .scene i{margin-top:0;font-size:11px}
  .roles .grid,.experts .grid{grid-template-columns:repeat(4,1fr);gap:10px}
  .experts .slot{grid-column:span 2}
  .skills .grid{grid-template-columns:repeat(6,1fr)}
  @media (max-width:1180px){
    .body{grid-template-columns:1fr}
    .scenecol .grid{grid-template-rows:none;grid-template-columns:repeat(4,1fr)}
    .roles .grid,.experts .grid,.skills .grid{grid-template-columns:repeat(4,1fr)}
    .experts .slot{grid-column:auto}
    .kb .grid{grid-template-columns:1fr}
  }
"""
FINAL_BODY = f"""<div class="stage">
{MAST}
<div class="body">
  <section class="panel scenecol">
    {head('01','工作场景')}
    <div class="grid">{scene_rows()}</div>
  </section>
  <div>
    <section class="panel roles">{head('02','岗位 Agent')}
      <div class="grid">{role_chips()}</div></section>
    {dn('拆解')}
    <section class="panel experts">{head('03','场景运营专家团','岗位 Agent 的子 Agent 组成')}
      <div class="grid">{expert_chips()}</div></section>
    {dn('配置')}
    <section class="panel skills">{head('04','运营专家团 Skill 配置')}
      <div class="grid">{skill_chips()}</div></section>
  </div>
</div>
{kb_band()}
</div>"""

def dc(extra_css, body):
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Noto+Sans+SC:wght@400;500;700&family=JetBrains+Mono:wght@500&display=swap">
  <style>{CSS}{extra_css}</style>
</helmet>
{body}
</x-dc>
</body>
</html>
"""

(ROOT/'tmg-a-h-platform.html').write_text(
    f'<title>TMG保健行业A-H平台</title>\n<style>\n/*@FONTS@*/\n{CSS}{FINAL_CSS}</style>\n\n{FINAL_BODY}\n',
    encoding='utf-8')
(CANVAS/'Main.dc.html').write_text(dc(FINAL_CSS, FINAL_BODY), encoding='utf-8')

# ==================================================== alternates (reference)
ENC_CSS = """
  .frame{position:relative;border:1px solid rgba(167,139,250,.45);border-radius:20px;
         background:rgba(139,92,246,.05);padding:30px 24px 24px}
  .frame-tag{position:absolute;top:-11px;left:24px;background:#0C0918;padding:0 12px;
             font-size:12px;color:#C6B4F5;letter-spacing:.08em}
  .band{margin-bottom:18px}
  .b1{grid-template-columns:repeat(4,1fr)}
  .b2{grid-template-columns:repeat(8,1fr)}
  .b3{grid-template-columns:repeat(7,1fr)}
  .b4{grid-template-columns:repeat(6,1fr)}
  .rule{height:1px;background:rgba(167,139,250,.24);margin:22px 0 18px}
  .kb{margin-top:0;border:none;background:none;padding:0}
"""
ENC_BODY = f"""<div class="stage">
{MAST}
<div class="frame">
  <span class="frame-tag">三层知识库 · 平台知识底座（框内全部内容都由它供给，并向 L3 回流）</span>
  <section class="band">{head('01','工作场景')}<div class="grid b1">{scene_cards()}</div></section>
  <section class="band">{head('02','岗位 Agent')}<div class="grid b2">{role_chips()}</div></section>
  <section class="band">{head('03','场景运营专家团','岗位 Agent 的子 Agent 组成')}
    <div class="grid b3">{expert_chips()}</div></section>
  <section class="band">{head('04','运营专家团 Skill 配置')}<div class="grid b4">{skill_chips()}</div></section>
  <div class="rule"></div>
  <section class="kb"><div class="grid">{kb_cards()}</div></section>
</div>
</div>"""
(CANVAS/'Enclosure.dc.html').write_text(dc(ENC_CSS, ENC_BODY), encoding='utf-8')

GRAN_CSS = """
  .lad{display:grid;grid-template-columns:78px 1fr}
  .tk{position:relative;border-right:1px solid rgba(167,139,250,.24);padding:2px 16px 0 0;
      text-align:right;font-size:11px;color:#9C8CCB;letter-spacing:.06em}
  .tk b{display:block;font-family:'JetBrains Mono',ui-monospace,monospace;font-size:10px;color:#C6B4F5;margin-bottom:2px}
  .tk:after{content:'';position:absolute;right:-4.5px;top:6px;width:8px;height:8px;border-radius:50%;
            background:#8B3FF3;box-shadow:0 0 0 4px rgba(139,63,243,.18)}
  .row{padding:0 0 20px 20px}
  .row:last-of-type{padding-bottom:0}
  .rh{display:flex;align-items:baseline;gap:10px;margin-bottom:10px}
  .rh h2{font-size:16px}
  .g1{grid-template-columns:repeat(4,1fr)}
  .g1 .chip{padding:17px 14px;text-align:center;background:linear-gradient(180deg,#B478FF,#8B3FF3)}
  .g1 .chip b{font-size:16px}
  .g2{grid-template-columns:repeat(8,1fr)}
  .g2 .chip{padding:12px 8px;text-align:center;background:linear-gradient(180deg,#9D55FF,#7A28E8)}
  .g3{grid-template-columns:repeat(7,1fr)}
  .g3 .chip{padding:10px 11px;background:linear-gradient(180deg,#7C34DF,#5A1BB4)}
  .g3 .chip b{font-size:13.5px}
  .g4{grid-template-columns:repeat(6,1fr);gap:8px}
  .g4 .chip{padding:8px 11px;background:rgba(109,40,217,.28);border:1px solid rgba(167,139,250,.34);
            box-shadow:none;border-radius:8px}
  .g4 .chip b{font-size:12px}
  .g4 .chip i{font-size:10.5px;color:#B9A9E8}
  .kb{margin-top:20px}
"""
def ladrow(n, label, title, cls, chips, sub=''):
    sb = f'<span class="sub">{sub}</span>' if sub else ''
    return (f'<div class="tk"><b>{n}</b>{label}</div>'
            f'<section class="row"><div class="rh"><h2>{title}</h2>{sb}</div>'
            f'<div class="grid {cls}">{chips}</div></section>')
GRAN_BODY = f"""<div class="stage">
{MAST}
<div class="lad">
  {ladrow('01','场景','工作场景','g1', scene_cards())}
  {ladrow('02','岗位','岗位 Agent','g2', role_chips())}
  {ladrow('03','专家','场景运营专家团','g3', expert_chips(),'岗位 Agent 的子 Agent')}
  {ladrow('04','Skill','运营专家团 Skill 配置','g4', skill_chips())}
</div>
{kb_band()}
</div>"""
(CANVAS/'Granularity.dc.html').write_text(dc(GRAN_CSS, GRAN_BODY), encoding='utf-8')

RAIL_CSS = """
  .rail{display:grid;grid-template-columns:1fr 54px 1fr 54px 1fr 54px 1fr;align-items:start}
  .col{display:flex;flex-direction:column;padding:14px 14px 15px}
  .col h2{font-size:15.5px}
  .duo{display:grid;grid-template-columns:repeat(2,1fr);gap:7px;align-content:start}
  .duo .chip{padding:8px 10px;border-radius:9px}
  .duo .chip b{font-size:13px}
  .duo .chip i{font-size:10.5px;margin-top:1px}
  .rcell{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:7px;
         align-self:center;min-height:170px}
  .rcell span{font-size:10px;color:#9C8CCB;letter-spacing:.08em}
  .kb{margin-top:18px}
  .kb .kbcard{padding:11px 14px}
  .kb .kbcard p{font-size:11px}
"""
def rcol(tier, title, inner):
    return (f'<section class="col panel"><div class="head"><span class="tier">{tier}</span>'
            f'<h2>{title}</h2></div><div class="duo">{inner}</div></section>')
def rarrow(label):
    return (f'<div class="rcell"><span>{label}</span>'
            f'<svg width="26" height="9" viewBox="0 0 26 9" fill="none" aria-hidden="true">'
            f'<path d="M0 4.5H20" stroke="#C6B4F5" stroke-width="1.1"/>'
            f'<path d="M19 1L25 4.5L19 8Z" fill="#C6B4F5"/></svg></div>')
RAIL_BODY = f"""<div class="stage">
{MAST}
<div class="rail">
  {rcol('01','工作场景', scene_rows())}
  {rarrow('承接')}
  {rcol('02','岗位 Agent', role_chips(center=False))}
  {rarrow('拆解')}
  {rcol('03','场景运营专家团', expert_chips())}
  {rarrow('配置')}
  {rcol('04','Skill 配置', skill_chips())}
</div>
{kb_band()}
</div>"""
(CANVAS/'Rail.dc.html').write_text(dc(RAIL_CSS, RAIL_BODY), encoding='utf-8')


# ==================================================== 汇报页 A — 能力复用矩阵
# 列按覆盖场景数降序：基础四天然排在前面，外圈自然形成递减的尾巴
EXPERT_COLS = [
    ('组织协同子 Agent', '行业秘书处', 'base'), ('任务执行子 Agent', '行业王进喜', 'base'),
    ('数据分析子 Agent',   '行业陈景润', 'base'), ('知识管理子 Agent',   '行业藏书阁', 'base'),
    ('品类洞察子 Agent', '待命名',     'scene'), ('竞对监控子 Agent', '行业猫头鹰', 'scene'),
    ('用户增长子 Agent', '待命名',     'scene'), ('财务分析子 Agent',   '行业葛朗台', 'scene'),
    ('外部咨询子 Agent', '待命名',     'scene'), ('营销创意子 Agent', '待命名',     'scene'),
]
# 来自勾选页的实际配置
PICKS = {
    '行业销售': ['组织协同子 Agent','任务执行子 Agent','数据分析子 Agent','知识管理子 Agent'],
    '竞对控比': ['组织协同子 Agent','任务执行子 Agent','数据分析子 Agent','知识管理子 Agent','竞对监控子 Agent','品类洞察子 Agent'],
    '行业损益': ['组织协同子 Agent','任务执行子 Agent','数据分析子 Agent','财务分析子 Agent'],
    '行业用户': ['组织协同子 Agent','任务执行子 Agent','数据分析子 Agent','知识管理子 Agent','用户增长子 Agent'],
    '品类规划': ['组织协同子 Agent','任务执行子 Agent','数据分析子 Agent','知识管理子 Agent','竞对监控子 Agent','外部咨询子 Agent','品类洞察子 Agent'],
    '商家复盘': ['组织协同子 Agent','任务执行子 Agent','数据分析子 Agent','知识管理子 Agent','竞对监控子 Agent','财务分析子 Agent','用户增长子 Agent','品类洞察子 Agent'],
    '新商新品': ['组织协同子 Agent','任务执行子 Agent','数据分析子 Agent','知识管理子 Agent'],
    '行业营销': ['组织协同子 Agent','任务执行子 Agent','知识管理子 Agent','营销创意子 Agent','用户增长子 Agent','品类洞察子 Agent'],
}
OWNERS = {'行业销售':'行业 GM','竞对控比':'行业 GM','行业损益':'行业 GM','行业用户':'行业 GM',
          'x品类规划':'', '品类规划':'品类组长','商家复盘':'品类小二','新商新品':'品类组长','行业营销':'营销小二'}
MATRIX_ROWS = [(sc, OWNERS[sc], {e: 1 for e in PICKS[sc]}) for sc in PICKS]
EXPERT_SKILLS = {   # 来自勾选页
    '组织协同子 Agent': ['Renwu-bj', 'Zhenduan'],
    '任务执行子 Agent': ['Renwu-bj'],
    '数据分析子 Agent':   ['target-data', 'AI-data-qd', 'AI-data-pl', 'category-meeting'],
    '知识管理子 Agent':   ['Kbsearch-tmg', 'kbase-learning', 'kbase-wiki'],
    '品类洞察子 Agent': ['target-data', 'Kbsearch-tmg', 'AI-data-pl', 'category-planning',
                'category-opportunity', 'category-bd', 'category-meeting'],
    '竞对监控子 Agent': ['category-scan', 'category-opportunity', 'category-report'],
    '用户增长子 Agent': ['Kbsearch-tmg', 'AI-data-pl', 'category-planning'],
    '财务分析子 Agent':   ['cmr-tmg'],
    '外部咨询子 Agent': ['AI-data-pl', 'Zhenduan', 'category-opportunity'],
    '营销创意子 Agent': ['Kbsearch-tmg', 'Renwu-bj', 'Zhenduan', 'category-opportunity'],
}
SKILL_CN = dict(SKILLS)
DOMAINS = [
    ('取数类', '把各系统的数拿回来', ['target-data', 'AI-data-qd', 'AI-data-pl']),
    ('知识类', '调政策、规则与历史打法', ['Kbsearch-tmg', 'kbase-learning', 'kbase-wiki']),
    ('财务类', '算账与投产比', ['cmr-tmg']),
    ('任务类', '把结论变成派得下去的活', ['Renwu-bj', 'Zhenduan']),
    ('品类类', '品类经营的专属动作', ['category-scan', 'category-planning', 'category-opportunity',
                                     'category-bd', 'category-report', 'category-meeting']),
]
SKILL_USERS = {k: [e for e, ks in EXPERT_SKILLS.items() if k in ks] for k in SKILL_CN}
CALLS = sum(len(u) for u in SKILL_USERS.values())
ASSIGNED = sum(1 for u in SKILL_USERS.values() if u)
REUSE = {fn: sum(1 for sc in PICKS if fn in PICKS[sc]) for fn, _c, _k in EXPERT_COLS}
FILLED = sum(len(v) for v in PICKS.values())
AVG = round(FILLED / len(EXPERT_COLS), 1)

MATRIX_CSS = """
  .deck-mast{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;
             padding-bottom:14px;margin-bottom:16px;border-bottom:1px solid rgba(167,139,250,.26)}
  .deck-mast h1{font-size:26px}
  .claim{margin-top:6px;font-size:14px;color:#D9CCFF;letter-spacing:.02em}
  .mx{display:grid;grid-template-columns:236px repeat(10,1fr);gap:0 6px;align-items:stretch}
  .mx-h{display:flex;flex-direction:column;justify-content:flex-end;align-items:center;gap:2px;
        padding:0 4px 9px;text-align:center;border-bottom:1px solid rgba(167,139,250,.26)}
  .mx-h b{font-size:12.5px;font-weight:700;letter-spacing:.01em;white-space:nowrap}
  .mx-h u{display:block;text-decoration:none;font-size:9.5px;color:#B9A9E8;letter-spacing:.02em;
          margin-top:1px}
  .mx-h span{font-size:9.5px;color:#9C8CCB;letter-spacing:.04em}
  .mx-h.base{background:rgba(139,92,246,.10);border-radius:9px 9px 0 0}
  .mx-h.corner{border-bottom:1px solid rgba(167,139,250,.26);align-items:flex-start;padding-left:2px}
  .mx-h.corner b{font-size:11px;color:#9C8CCB;font-weight:500;letter-spacing:.1em}
  .mx-r{display:flex;flex-direction:column;justify-content:center;gap:4px;padding:0 10px 0 2px;
       border-bottom:1px solid rgba(167,139,250,.13)}
  .mx-r b{font-size:15px;font-weight:700}
  .mx-r span{font-size:10.5px;color:#C6B4F5;border:1px solid rgba(167,139,250,.42);
             border-radius:999px;padding:1px 8px;align-self:flex-start}
  .mx-c{display:flex;align-items:center;justify-content:center;min-height:65px;
      border-bottom:1px solid rgba(167,139,250,.13)}
  .mx-c.base{background:rgba(139,92,246,.10)}
  .m{width:22px;height:22px;border-radius:7px;display:block;
     background:linear-gradient(180deg,#9D55FF,#7A28E8);
     box-shadow:0 3px 10px rgba(74,20,140,.45),inset 0 1px 0 rgba(255,255,255,.28)}
  .m.t{background:none;border:1px dashed rgba(167,139,250,.62);box-shadow:none}
  .mx-c.ft,.mx-r.ft{border-bottom:none;min-height:46px}
  .mx-c.ft{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:15px;font-weight:700;color:#C6B4F5}
  .mx-c.ft.base{border-radius:0 0 9px 9px}
  .mx-r.ft{justify-content:center;font-size:11px;color:#9C8CCB;letter-spacing:.06em;padding-top:4px}
  .mx-foot{display:flex;align-items:flex-end;justify-content:space-between;gap:30px;margin-top:16px;
           padding-top:14px;border-top:1px solid rgba(167,139,250,.26)}
  .take{font-size:14.5px;color:#F6F2FF;line-height:1.6;max-width:1240px;text-wrap:pretty}
  .take em{font-style:normal;color:#C08BFF;font-weight:700}
  .mlegend{display:flex;gap:18px;align-items:center;font-size:11.5px;color:#9C8CCB;white-space:nowrap}
  .mlegend span{display:flex;align-items:center;gap:7px}
  .mlegend i{width:16px;height:16px;border-radius:5px;display:block;
             background:linear-gradient(180deg,#9D55FF,#7A28E8)}
  .mlegend i.t{background:none;border:1px dashed rgba(167,139,250,.62)}
  .note{margin-top:9px;font-size:11.5px;color:#9C8CCB}
"""

def matrix_body():
    cells = ['<div class="mx-h corner"><b>作战中心 / 主导岗位</b></div>']
    for name, nick, kind in EXPERT_COLS:
        head_, _, _tail = name.partition('子 Agent')
        suffix = '<u>子 Agent</u>' if _tail == '' and '子 Agent' in name else ''
        cells.append(f'<div class="mx-h {kind}"><b>{head_}</b>{suffix}'
                     f'<span>{nick}</span></div>')
    for scene, owner, marks in MATRIX_ROWS:
        cells.append(f'<div class="mx-r"><b>{scene}</b><span>{owner} 主导</span></div>')
        for name, _, kind in EXPERT_COLS:
            v = marks.get(name)
            mark = '' if not v else f'<i class="m{"" if v == 1 else " t"}"></i>'
            cells.append(f'<div class="mx-c {kind}">{mark}</div>')
    cells.append('<div class="mx-r ft">被几个作战中心复用</div>')
    for name, _, kind in EXPERT_COLS:
        cells.append(f'<div class="mx-c ft {kind}">{REUSE[name]}</div>')
    return f"""<div class="stage">
<header class="deck-mast">
  <div class="brand">{MARK}<div><h1>场景 × 专家团 能力矩阵</h1>
    <p class="claim">同一组专家反复复用在 8 个作战中心上——不是 8 套烟囱，是 1 套能力</p></div></div>
  <div class="mlegend"><span><i></i>该场景配置了这位专家，空格为不配置</span></div>
</header>
<div class="mx">{''.join(cells)}</div>
<div class="mx-foot">
  <div><p class="take">8 个作战中心、{FILLED} 个配置，全部由 <em>10 个专家</em>承担——
    平均每个专家被 <em>{AVG} 个场景复用</em>；组织协同、任务执行两位 8 场景全覆盖。
    新增一个作战中心，平均只要补 <em>1–2 个专属专家</em>。</p>
    <p class="note">底色四列为基础专家；空格表示该场景暂不配置该专家。每个专家配哪些 Skill 见下一页。</p></div>
</div>
</div>"""

MATRIX_BODY = matrix_body()
(ROOT/'tmg-matrix.html').write_text(
    f'<title>场景 × 专家团 能力矩阵</title>\n<style>\n/*@FONTS@*/\n{CSS}{MATRIX_CSS}</style>\n\n{MATRIX_BODY}\n',
    encoding='utf-8')
(CANVAS/'Matrix.dc.html').write_text(dc(MATRIX_CSS, MATRIX_BODY), encoding='utf-8')

# ============================================ 汇报页 B — 行业销售端到端
TODAY = ['BI 按历史出目标','人工每日盯盘','逐级同步数据与风险','拉会一起补缺口',
         '人工翻可用资源','人工写商家建议','商家执行']
LEVELS = [
    ('L1','行业 GM Agent','看行业整体达成与缺口，把目标按品类 / 渠道拆成任务',
     ['target-data'], 'A2A 派单', ''),
    ('L2','品类组长 Agent · 渠道组长 Agent','接到任务自动下钻，定位问题品类与问题渠道，找出小二级的机会',
     ['AI-data-pl','AI-data-qd'], 'A2A 派单', ''),
    ('L3','品类小二 Agent · 渠道小二 Agent','下钻到商家 × 渠道，结合知识库找出可给的政策与资源',
     ['AI-data-pl','AI-data-qd','Kbsearch-tmg','Zhenduan'], '生成动作', 'kb'),
    ('L4','商家 × 渠道 运营动作','每个商家一套具体动作建议，AI 直接触达商家',
     ['Renwu-bj'], '', 'out'),
]

FLOW_CSS = """
  .deck-mast{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;
             padding-bottom:12px;margin-bottom:14px;border-bottom:1px solid rgba(167,139,250,.26)}
  .deck-mast h1{font-size:26px}
  .claim{margin-top:6px;font-size:14px;color:#D9CCFF}
  .today{display:flex;align-items:center;gap:9px;flex-wrap:wrap;
         border:1px dashed rgba(180,150,120,.32);border-radius:13px;padding:12px 14px;margin-bottom:16px;
         background:rgba(120,90,60,.07)}
  .today .lb{font-size:11.5px;color:#D8A657;letter-spacing:.1em;font-weight:700;flex:none}
  .today .st{font-size:11.5px;color:#BCAF9E;background:rgba(255,255,255,.045);
             border:1px solid rgba(180,150,120,.22);border-radius:7px;padding:5px 9px;white-space:nowrap}
  .today .sep{color:#7A6A55;font-size:11px}
  .today .pain{margin-left:auto;font-size:11.5px;color:#D8A657;white-space:nowrap}
  .casc{display:flex;align-items:stretch;gap:10px}
  .rail{position:relative;width:32px;flex:none;display:flex;flex-direction:column;
        align-items:center;justify-content:center}
  .rail:before{content:'';position:absolute;left:50%;top:0;bottom:6px;width:1px;
               background:repeating-linear-gradient(180deg,rgba(167,139,250,.5) 0 5px,transparent 5px 10px)}
  .rail:after{content:'';position:absolute;top:-1px;left:calc(50% - 4.5px);width:0;height:0;
              border-left:4.5px solid transparent;border-right:4.5px solid transparent;
              border-bottom:8px solid rgba(167,139,250,.6)}
  .rail span{position:relative;z-index:1;writing-mode:vertical-rl;
             font-size:10.5px;color:#9C8CCB;letter-spacing:.12em;white-space:nowrap;
             background:#0C0918;padding:10px 0}
  .cbody{flex:1;display:grid;grid-template-columns:46px 1fr;gap:0 10px;align-content:start}
  .bdg{display:flex;align-items:center;justify-content:center;
       font-family:'JetBrains Mono',ui-monospace,monospace;font-size:11px;color:#C6B4F5;
       border:1px solid rgba(167,139,250,.5);border-radius:8px;height:34px;align-self:center}
  .lv{border:1px solid rgba(167,139,250,.3);border-radius:13px;background:rgba(139,92,246,.06);
      padding:21px 16px;display:grid;grid-template-columns:1fr 300px 78px;gap:14px;align-items:center}
  .lv b{font-size:15.5px;font-weight:700;display:block}
  .lv p{font-size:13px;color:#C6B4F5;margin-top:4px;line-height:1.55}
  .kbnote{margin-top:9px;font-size:11.5px;color:#C7CCFF;border-left:2px solid rgba(129,140,248,.65);
          padding:2px 0 2px 9px;letter-spacing:.02em}
  .lv.out{border-color:rgba(196,141,255,.55);background:linear-gradient(180deg,rgba(157,85,255,.20),rgba(122,40,232,.12))}
  .lv.kb{border-color:rgba(129,140,248,.45)}
  .sk{display:flex;flex-wrap:wrap;gap:6px;justify-content:flex-end}
  .sk i{font-style:normal;font-family:'JetBrains Mono',ui-monospace,monospace;font-size:10.5px;
        color:#E4D8FF;background:rgba(139,63,243,.30);border:1px solid rgba(167,139,250,.34);
        border-radius:6px;padding:4px 7px;text-align:center;line-height:1.3}
  .sk i u{display:block;text-decoration:none;font-family:'Sora','Noto Sans SC',sans-serif;
          font-size:9.5px;color:#C6B4F5;margin-top:1px}
  .sk i.kbs{background:rgba(76,65,201,.42);border-color:rgba(165,180,252,.45);color:#DDE2FF}
  .a2a{display:flex;align-items:center;gap:9px;height:30px;padding-left:2px;color:#C6B4F5}
  .a2a span{font-size:10.5px;letter-spacing:.1em;color:#9C8CCB}
  .hitl{font-size:10.5px;color:#C6B4F5;border:1px dashed rgba(167,139,250,.5);border-radius:999px;
        padding:4px 0;text-align:center;letter-spacing:.04em}
  .gain{display:grid;grid-template-columns:1fr 1fr 1.15fr;gap:12px;margin-top:18px}
  .gcard{border:1px solid rgba(167,139,250,.34);border-radius:13px;padding:17px 18px;
         background:rgba(139,92,246,.07)}
  .gcard .k{font-size:11px;color:#9C8CCB;letter-spacing:.08em}
  .gcard .v{display:flex;align-items:baseline;gap:10px;margin-top:5px}
  .gcard .was{font-size:14px;color:#8E7FBF;text-decoration:line-through}
  .gcard .now{font-size:23px;font-weight:700;color:#F6F2FF;letter-spacing:.01em}
  .gcard .x{font-size:12px;color:#C08BFF;font-weight:700}
  .gcard.qual .v{margin-top:7px}
  .gcard.qual .now{font-size:16px;line-height:1.5}
"""

def flow_body():
    today = ''.join(
        (f'<span class="st">{s}</span>' + ('<span class="sep">→</span>' if i < len(TODAY)-1 else ''))
        for i, s in enumerate(TODAY))
    rows = []
    for tag, name, desc, skills, arrow, kind in LEVELS:
        sk = ''.join(f'<i class="{"kbs" if k == "Kbsearch-tmg" else ""}">{k}'
                     f'<u>{SKILL_CN.get(k, "")}</u></i>' for k in skills)
        hitl = '' if kind == 'out' else '<span class="hitl">人确认</span>'
        kbn = ('<div class="kbnote">三层知识库注入 · 行业政策 / 资源扶持 / 商家档案</div>'
               if kind == 'kb' else '')
        rows.append(f'<div class="bdg">{tag}</div>'
                    f'<div class="lv {kind}"><div><b>{name}</b><p>{desc}</p>{kbn}</div>'
                    f'<div class="sk">{sk}</div>{hitl or "<span></span>"}</div>')
        if arrow:
            rows.append('<div></div><div class="a2a">'
                        '<svg width="9" height="20" viewBox="0 0 9 20" fill="none" aria-hidden="true">'
                        '<path d="M4.5 0V14" stroke="currentColor" stroke-width="1.1"/>'
                        '<path d="M1 13L4.5 19L8 13Z" fill="currentColor"/></svg>'
                        f'<span>{arrow}</span></div>')
    return f"""<div class="stage">
<header class="deck-mast">
  <div class="brand">{MARK}<div><h1>行业销售作战中心 · 端到端跑通</h1>
    <p class="claim">一个行业目标，逐级下钻到 100+ 个商家的当日动作</p></div></div>
  <div class="mlegend"><span>每一级派单后，Agent 先出结论与建议，人确认或与 Agent 对话调整</span></div>
</header>
<div class="today"><span class="lb">今天怎么干</span>{today}
  <span class="pain">只有数字没有知识 · 靠人传话易遗漏 · 4 小时只覆盖 3–5 个头部商家</span></div>
<div class="casc">
  <div class="rail"><span>当日动作汇总回流 · 成为行业每日行动</span></div>
  <div class="cbody">{''.join(rows)}</div>
</div>
<div class="gain">
  <div class="gcard"><div class="k">单次跑完耗时</div>
    <div class="v"><span class="was">4 小时</span><span class="now">1 小时</span><span class="x">÷4</span></div></div>
  <div class="gcard"><div class="k">覆盖商家数</div>
    <div class="v"><span class="was">3–5 个头部</span><span class="now">100+ 个核心</span><span class="x">×20+</span></div></div>
  <div class="gcard qual"><div class="k">质变</div>
    <div class="v"><span class="now">从「只有数字」到「数字 × 知识 × 动作」——抓手不再靠人传话，不遗漏、可复用到长尾商家</span></div></div>
</div>
</div>"""

FLOW_BODY = flow_body()
(ROOT/'tmg-sales-flow.html').write_text(
    f'<title>行业销售作战中心 · 端到端</title>\n<style>\n/*@FONTS@*/\n{CSS}{MATRIX_CSS}{FLOW_CSS}</style>\n\n{FLOW_BODY}\n',
    encoding='utf-8')
(CANVAS/'SalesFlow.dc.html').write_text(dc(MATRIX_CSS + FLOW_CSS, FLOW_BODY), encoding='utf-8')

# ============================================ 汇报页 · Skill（按专家组织）
SHELF_CSS = """
  .chain{display:flex;align-items:center;gap:12px;margin-bottom:16px}
  .cn{border:1px dashed rgba(167,139,250,.4);border-radius:11px;padding:9px 16px;
      display:flex;align-items:baseline;gap:9px;background:rgba(139,92,246,.04)}
  .cn b{font-size:14.5px;font-weight:700;color:#C6B4F5}
  .cn em{font-style:normal;font-family:'JetBrains Mono',ui-monospace,monospace;
         font-size:12px;color:#9C8CCB}
  .cn.here{border-style:solid;border-color:rgba(255,255,255,.18);
           background:linear-gradient(180deg,#9D55FF,#7A28E8);
           box-shadow:0 6px 16px rgba(74,20,140,.36),inset 0 1px 0 rgba(255,255,255,.24)}
  .cn.here b{color:#fff}
  .cn.here em{color:rgba(255,255,255,.78)}
  .cn.here i{font-style:normal;font-size:11px;color:rgba(255,255,255,.72);margin-left:2px}
  .ca{font-size:10.5px;color:#9C8CCB;letter-spacing:.1em;display:flex;align-items:center;gap:7px}
  .egrid{display:grid;grid-template-columns:repeat(5,1fr);gap:13px}
  .ec{border:1px solid rgba(167,139,250,.3);border-radius:14px;background:rgba(139,92,246,.05);
      padding:0 0 12px;display:flex;flex-direction:column}
  .ec-h{padding:14px 14px 13px;border-bottom:1px solid rgba(167,139,250,.22)}
  .ec-h b{display:block;font-size:16px;font-weight:700}
  .ec-h span{display:block;font-size:10.5px;color:#9C8CCB;margin-top:2px}
  .ec-h i{display:inline-block;font-style:normal;margin-top:7px;font-size:10.5px;color:#C6B4F5;
          border:1px solid rgba(167,139,250,.42);border-radius:999px;padding:1px 8px}
  .ec-s{display:flex;flex-direction:column;gap:7px;padding:13px 12px 0;flex:1}
  .ec-s .slot,.ec-s .more{background:none;border:1px dashed rgba(167,139,250,.34);
        justify-content:center;color:#7B6CA6;font-size:11px;letter-spacing:.04em}
  .ec-s .more{border-style:solid;border-color:rgba(167,139,250,.26);
        background:rgba(167,139,250,.07);color:#C6B4F5}
  .ec-s div{display:flex;align-items:baseline;gap:7px;border-radius:8px;padding:8px 9px;
            background:linear-gradient(180deg,rgba(157,85,255,.34),rgba(122,40,232,.24));
            border:1px solid rgba(167,139,250,.3)}
  .ec-s b{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:10.5px;font-weight:500;
          color:#EFE6FF;letter-spacing:-.02em}
  .ec-s em{font-style:normal;font-size:11.5px;color:#F6F2FF;font-weight:700;white-space:nowrap}
  .ec-s u{margin-left:auto;text-decoration:none;font-family:'JetBrains Mono',ui-monospace,monospace;
          font-size:10px;color:#B9A9E8}
  .sfoot{display:flex;align-items:flex-end;justify-content:space-between;gap:30px;margin-top:18px;
         padding-top:15px;border-top:1px solid rgba(167,139,250,.26)}
  .sfoot .take{max-width:1080px}
  .stats{display:flex;gap:22px;white-space:nowrap}
  .stats div{text-align:right}
  .stats b{display:block;font-family:'JetBrains Mono',ui-monospace,monospace;font-size:22px;
           font-weight:700;color:#F6F2FF}
  .stats span{font-size:10.5px;color:#9C8CCB;letter-spacing:.04em}
"""

def arrow_r(label):
    return (f'<div class="ca"><span>{label}</span>'
            f'<svg width="22" height="9" viewBox="0 0 22 9" fill="none" aria-hidden="true">'
            f'<path d="M0 4.5H16" stroke="#9C8CCB" stroke-width="1.1"/>'
            f'<path d="M15 1L21 4.5L15 8Z" fill="#9C8CCB"/></svg></div>')

def shelf_body():
    cards = []
    ROWS = 4
    for fn, code, _kind in EXPERT_COLS:
        ks = sorted(EXPERT_SKILLS.get(fn) or [], key=lambda k: -len(SKILL_USERS[k]))
        shown = ks[:ROWS - 1] if len(ks) > ROWS else ks
        lines = ''.join(
            f'<div><b>{k}</b><em>{SKILL_CN[k]}</em><u>×{len(SKILL_USERS[k])}</u></div>' for k in shown)
        if len(ks) > ROWS:
            lines += f'<div class="more">… 还有 {len(ks) - len(shown)} 个</div>'
        else:
            lines += '<div class="slot">＋ 扩展位</div>' * (ROWS - len(ks))
        cards.append(f'<div class="ec"><div class="ec-h"><b>{fn}</b><span>{code}</span>'
                     f'<i>{REUSE[fn]} 个作战中心在用</i></div>'
                     f'<div class="ec-s">{lines}</div></div>')
    return f"""<div class="stage">
<header class="deck-mast">
  <div class="brand">{MARK}<div><h1>每位专家手上的标准动作</h1>
    <p class="claim">Skill 挂在专家身上，专家是岗位 Agent 的子 Agent——同一个动作被不同专家反复调用</p></div></div>
  <div class="mlegend"><span>动作后的 ×N＝有几位专家在用同一个动作；卡内按复用次数排序，每张最多列 4 个</span></div>
</header>
<div class="chain">
  <div class="cn"><b>岗位 Agent</b><em>7</em></div>
  {arrow_r('拆解为')}
  <div class="cn"><b>场景运营专家团</b><em>10</em></div>
  {arrow_r('配置')}
  <div class="cn here"><b>Skill</b><em>{len(SKILL_CN)}</em><i>本页</i></div>
</div>
<div class="egrid">{''.join(cards)}</div>
<div class="sfoot">
  <p class="take"><em>Skill 不是员工技能，是岗位动作的最小可复用单元。</em>
    能力不再长在某个人身上——{len(SKILL_CN)} 个动作被 10 位专家调用 {CALLS} 次，
    新增一个作战中心，多数时候只是把现成的动作重新组合一次。</p>
  <div class="stats">
    <div><b>{len(SKILL_CN)}</b><span>标准动作</span></div>
    <div><b>{CALLS}</b><span>被专家调用次数</span></div>
    <div><b>{round(CALLS / len(SKILL_CN), 1)}</b><span>平均每个动作复用</span></div>
  </div>
</div>
</div>"""

SHELF_BODY = shelf_body()
(ROOT/'tmg-skill-shelf.html').write_text(
    f'<title>专家的标准动作</title>\n<style>\n/*@FONTS@*/\n{CSS}{MATRIX_CSS}{SHELF_CSS}</style>\n\n{SHELF_BODY}\n',
    encoding='utf-8')
(CANVAS/'Shelf.dc.html').write_text(dc(MATRIX_CSS + SHELF_CSS, SHELF_BODY), encoding='utf-8')

# ============================================ 汇报页 · 三层知识库
import math

KB_TIERS = [
    ('L1', '行业知识库', '行业的通用信息，以对商文档为主',
     ['8 月大促节奏时间及玩法规则', '大促节奏和去年对标的时间'],
     [('来源', '大促白皮书 · 内部群信息'), ('体量', '300 篇'), ('更新', '每天'),
      ('维护', '行业运营 ＋ 岗位 Agent 自动蒸馏'), ('可见', '全行业')], []),
    ('L2', '岗位知识库', '行业的政策、资源扶持等核心内容',
     ['2026 年 8 月百补资源补贴政策', '百补的不同玩法及补贴'],
     [('来源', '大促资源政策文档'), ('体量', '20 篇'), ('更新', '大促前 ＋ 每月'),
      ('维护', '渠道小二 ＋ 岗位 Agent 蒸馏'), ('可见', '按岗位')], []),
    ('L3', '个人记忆画像', '对应岗位的行业经验、商家判断、运营习惯',
     ['Swisse 不参加百补、秒杀渠道', 'WHC 不参加淘客渠道'],
     [('来源', '日常与 Agent 的交流 · 小二主动输入'), ('体量', '持续增加'), ('更新', '不定时'),
      ('维护', '岗位小二'), ('可见', '本人及上级')],
     ['商家判断', '运营习惯', '常用数据口径', '沟通偏好', '踩过的坑']),
]
WHEEL = [
    ('采集', '白皮书 · 内部群 · Agent 交流'),
    ('Agent 蒸馏', '自动结构化入库', 'kbase-wiki · kbase-learning'),
    ('分层供给', '按权限分发到三层'),
    ('Agent 调用', '在作战中心里被用起来'),
    ('回流沉淀', '写回个人记忆画像'),
]

KB_CSS = """
  .kbwrap{display:grid;grid-template-columns:1fr 520px;gap:26px;align-items:center}
  .tiers{display:flex;flex-direction:column;gap:17px}
  .kbt{border:1px solid rgba(129,140,248,.45);border-radius:15px;background:rgba(67,56,202,.12);
        padding:17px 20px 18px}
  .kbt-h{display:flex;align-items:baseline;gap:11px;flex-wrap:wrap;margin-bottom:14px}
  .kbt-h b{font-size:17.5px;font-weight:700}
  .kbt-h em{font-style:normal;font-size:12.5px;color:#9C8CCB}
  .kidx{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:10.5px;color:#D8DCFF;
        border:1px solid rgba(216,220,255,.42);border-radius:5px;padding:2px 7px;flex:none}
  .ex{display:grid;grid-template-columns:1fr 1fr;gap:9px}
  .ex div{border-radius:11px;padding:14px 16px;font-size:15px;font-weight:700;
          background:linear-gradient(180deg,#4C41C9,#2C2480);border:1px solid rgba(199,210,254,.26);
          box-shadow:0 5px 14px rgba(23,18,80,.45),inset 0 1px 0 rgba(255,255,255,.14)}
  .ex div:before{content:'「';color:rgba(216,220,255,.5)}
  .ex div:after{content:'」';color:rgba(216,220,255,.5)}
  .gov{display:flex;flex-wrap:wrap;gap:7px 18px;margin-top:14px;font-size:11.5px;color:#9C8CCB}
  .gov span b{font-weight:500;color:#C7CCFF;margin-right:5px}
  .gov span i{font-style:normal;color:#E2E4FF}
  .memchips{display:flex;flex-wrap:wrap;gap:7px;margin-top:12px}
  .memchips i{font-style:normal;font-size:11px;color:#DDE2FF;background:rgba(76,65,201,.34);
              border:1px solid rgba(165,180,252,.34);border-radius:999px;padding:3px 10px}
  .wheel{position:relative;width:520px;height:520px;margin:0 auto}
  .wheel svg{position:absolute;inset:0}
  .wn{position:absolute;transform:translate(-50%,-50%);width:172px;text-align:center;
      border-radius:11px;padding:9px 8px;background:rgba(67,56,202,.30);
      border:1px solid rgba(165,180,252,.42);backdrop-filter:blur(2px)}
  .wn b{display:block;font-size:13px;font-weight:700}
  .wn em{display:block;font-style:normal;font-size:10px;color:#B9BEEB;margin-top:2px;line-height:1.45}
  .wn s{display:block;text-decoration:none;font-family:'JetBrains Mono',ui-monospace,monospace;
        font-size:9px;color:rgba(255,255,255,.72);margin-top:3px;letter-spacing:-.01em}
  .wn.key{background:linear-gradient(180deg,#6D6BE0,#3B32A6);border-color:rgba(255,255,255,.24);
          box-shadow:0 6px 18px rgba(23,18,80,.5)}
  .wn.key em{color:rgba(255,255,255,.78)}
  .wc{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);text-align:center;width:170px}
  .wc b{display:block;font-size:21px;font-weight:700}
  .wc em{display:block;font-style:normal;font-size:11.5px;color:#B9BEEB;margin-top:5px;line-height:1.5}
  .wa{position:absolute;transform-origin:center;color:#8B90D8}
  .kbfoot{margin-top:15px;padding-top:14px;border-top:1px solid rgba(129,140,248,.3)}
  .chainrow{display:grid;grid-template-columns:repeat(5,1fr);gap:0 8px;align-items:stretch}
  .ch{border-radius:11px;padding:11px 13px;position:relative}
  .ch b{display:block;font-size:13px;font-weight:700}
  .ch em{display:block;font-style:normal;font-size:11.5px;margin-top:4px;line-height:1.5}
  .ch.d{background:linear-gradient(180deg,rgba(157,85,255,.30),rgba(122,40,232,.20));
        border:1px solid rgba(167,139,250,.45)}
  .ch.d em{color:#D9CCFF}
  .ch.k{background:rgba(67,56,202,.26);border:1px solid rgba(165,180,252,.42)}
  .ch.k b{color:#C7CCFF}
  .ch.k em{color:#DDE2FF}
  .ch.a{background:linear-gradient(180deg,#9D55FF,#7A28E8);border:1px solid rgba(255,255,255,.18);
        box-shadow:0 6px 16px rgba(74,20,140,.4)}
  .ch.a em{color:rgba(255,255,255,.82)}
  .ch:not(:last-child):after{content:'';position:absolute;right:-8px;top:50%;
        transform:translateY(-50%);width:0;height:0;border-top:5px solid transparent;
        border-bottom:5px solid transparent;border-left:7px solid rgba(165,180,252,.7)}
  .chtag{font-size:10.5px;color:#9C8CCB;letter-spacing:.1em;margin-bottom:8px;display:block}
  .kbfoot .take{margin-top:13px;font-size:13.5px}
"""

def kb_body():
    tiers = ''
    for tag, name, desc, exs, gov, chips in KB_TIERS:
        ex = ''.join(f'<div>{e}</div>' for e in exs)
        gv = ''.join(f'<span><b>{k}</b><i>{v}</i></span>' for k, v in gov)
        mc = ('<div class="memchips">' + ''.join(f'<i>{c}</i>' for c in chips) + '</div>') if chips else ''
        tiers += (f'<section class="kbt"><div class="kbt-h"><span class="kidx">{tag}</span>'
                  f'<b>{name}</b><em>{desc}</em></div>'
                  f'<div class="ex">{ex}</div>{mc}<div class="gov">{gv}</div></section>')

    C, R = 260, 175
    nodes = ''
    for i, item in enumerate(WHEEL):
        t, sub = item[0], item[1]
        code = f'<s>{item[2]}</s>' if len(item) > 2 else ''
        a = math.radians(-90 + i * 72)
        x, y = C + R * math.cos(a), C + R * math.sin(a)
        key = ' key' if t == 'Agent 蒸馏' else ''
        nodes += (f'<div class="wn{key}" style="left:{x:.0f}px;top:{y:.0f}px">'
                  f'<b>{t}</b><em>{sub}</em>{code}</div>')
    arrows = ''
    for i in range(5):
        a = math.radians(-90 + i * 72 + 36)
        x, y = C + R * math.cos(a), C + R * math.sin(a)
        rot = -90 + i * 72 + 36 + 90
        arrows += (f'<div class="wa" style="left:{x:.0f}px;top:{y:.0f}px;'
                   f'transform:translate(-50%,-50%) rotate({rot:.0f}deg)">'
                   f'<svg width="13" height="13" viewBox="0 0 13 13" fill="none">'
                   f'<path d="M1 1L11 6.5L1 12Z" fill="currentColor"/></svg></div>')

    return f"""<div class="stage">
<header class="deck-mast">
  <div class="brand">{MARK}<div><h1>三层知识库 · 让数据诊断落到运营动作</h1>
    <p class="claim">没有它，Agent 只能告诉你哪里跌了；有了它，才能告诉你这个商家该给什么、怎么给</p></div></div>
  <div class="mlegend"><span>「」内为知识库里的真实条目</span></div>
</header>
<div class="kbwrap">
  <div class="tiers">{tiers}</div>
  <div class="wheel">
    <svg viewBox="0 0 520 520" fill="none" aria-hidden="true">
      <circle cx="260" cy="260" r="175" stroke="rgba(165,180,252,.32)" stroke-width="1.4"
              stroke-dasharray="7 7"/>
    </svg>
    <div class="wc"><b>知识飞轮</b><em>用得越多，沉淀越厚，判断越准</em></div>
    {arrows}{nodes}
  </div>
</div>
<div class="kbfoot">
  <span class="chtag">一条真实的串联 · 示例</span>
  <div class="chainrow">
    <div class="ch d"><b>数据诊断</b><em>某商家 8 月销售出现缺口</em></div>
    <div class="ch k"><b>L1 行业知识库</b><em>现在正处在 8 月大促节奏</em></div>
    <div class="ch k"><b>L2 岗位知识库</b><em>有百补资源与补贴政策可给</em></div>
    <div class="ch k"><b>L3 个人记忆画像</b><em>但 Swisse 不参加百补</em></div>
    <div class="ch a"><b>运营动作</b><em>换其它资源触达，不空耗百补名额</em></div>
  </div>
  <p class="take"><em>没有知识库，Agent 只能说哪里跌了；有了它，才能说这个商家该给什么。</em>
    三层按权限隔离——行业通用全行业共享、岗位政策按岗位可见、个人判断只对本人与上级开放；人走了，判断留下来。</p>
</div>
</div>"""

KB_BODY = kb_body()
(ROOT/'tmg-kb.html').write_text(
    f'<title>三层知识库</title>\n<style>\n/*@FONTS@*/\n{CSS}{MATRIX_CSS}{SHELF_CSS}{KB_CSS}</style>\n\n{KB_BODY}\n',
    encoding='utf-8')
(CANVAS/'KB.dc.html').write_text(dc(MATRIX_CSS + SHELF_CSS + KB_CSS, KB_BODY), encoding='utf-8')

canvas = {
 "pages":[{"id":"page-1","name":"汇报页"},{"id":"page-2","name":"其它排版方向"}],
 "artboards":[
  {"file":"Main.dc.html","title":"P1 · 平台总架构","page":"page-1","x":0,"y":0,"w":1600,"h":900},
  {"file":"Matrix.dc.html","title":"P2 · 场景 × 专家团","page":"page-1","x":1760,"y":0,"w":1600,"h":900},
  {"file":"Shelf.dc.html","title":"P3 · 专家的标准动作","page":"page-1","x":3520,"y":0,"w":1600,"h":900},
  {"file":"SalesFlow.dc.html","title":"P4 · 行业销售端到端","page":"page-1","x":5280,"y":0,"w":1600,"h":900},
  {"file":"KB.dc.html","title":"P5 · 三层知识库","page":"page-1","x":7040,"y":0,"w":1600,"h":900},
  {"file":"Enclosure.dc.html","title":"方向二 · 环抱式","page":"page-2","x":0,"y":0,"w":1600,"h":935},
  {"file":"Granularity.dc.html","title":"方向三 · 粒度阶梯","page":"page-2","x":1760,"y":0,"w":1600,"h":950},
  {"file":"Rail.dc.html","title":"方向四 · 横向流水线","page":"page-2","x":3520,"y":0,"w":1600,"h":925}
 ],
 "annotations":[
  {"id":"note-p5","page":"page-1","x":7040,"y":-160,"w":520,
   "text":"P5 全部用你填的真实内容。质量指标你留空了，所以没画那一块。\\n品牌名我规范成了 Swisse / WHC。"},
  {"id":"note-alts","page":"page-2","x":0,"y":-120,"w":460,
   "text":"没有选中的三个排版方向，留作参考。"}
 ],
 "launch":{"view":"canvas","page":"page-1"}
}
(CANVAS/'canvas.json').write_text(json.dumps(canvas, ensure_ascii=False, indent=1), encoding='utf-8')
print('built KB page')
