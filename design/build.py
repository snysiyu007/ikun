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

SCENES = ['行业销售','竞对对比','行业损益','行业用户','品类规划','商家复盘','新商新品','行业营销']
ROLES  = ['行业 GM','品类组长','渠道组长','品类小二','渠道小二','用户小二','营销小二']
EXPERTS= [('行业陈景润','数据官'),('行业藏书阁','知识库'),('行业猫头鹰','监视竞对'),
          ('行业葛朗台','财务官'),('行业秘书处','组织协同'),('行业王进喜','任务执行')]
SKILLS = [('target-data','销售追踪'),('Kbsearch-tmg','知识调用'),('cmr-tmg','损益管理'),
          ('AI-data-qd','渠道取数'),('AI-data-pl','品类取数'),('Renwu-bj','任务找人'),
          ('Zhenduan','明确任务')]
KB = [('L1','行业知识库','行业的通用信息，以对商文档为主'),
      ('L2','岗位知识库','行业的政策、资源扶持等核心内容'),
      ('L3','个人记忆画像','对应岗位的行业经验、商家判断、运营习惯等和个人意识相关的信息，由 Agent 使用中沉淀回流')]

TAGLINE = '以三层知识库为底座，叠加岗位 Agent 能力，把行业运营的工作做得更好'

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
  .stage{width:1600px;max-width:100%;margin:0 auto;padding:30px 40px}
  .mast{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;flex-wrap:wrap;
        padding-bottom:14px;margin-bottom:14px;border-bottom:1px solid rgba(167,139,250,.26)}
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
         background:rgba(139,92,246,.045);padding:12px 15px 14px}
  .head{display:flex;align-items:baseline;gap:10px;margin-bottom:10px}
  .tier{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:10.5px;color:#C6B4F5;
        border:1px solid rgba(167,139,250,.5);border-radius:6px;padding:2px 7px;flex:none}
  h2{font-size:17px;font-weight:700;letter-spacing:.02em}
  .sub{font-size:12px;color:#9C8CCB}
  .grid{display:grid;gap:9px}
  .chip{border-radius:11px;padding:10px 12px;background:linear-gradient(180deg,#9D55FF,#7A28E8);
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
  .arrow{display:flex;align-items:center;justify-content:center;gap:9px;height:18px;color:#C6B4F5}
  .arrow span{font-size:10.5px;letter-spacing:.1em;color:#9C8CCB}
  .kb{margin-top:14px;border:1px solid rgba(129,140,248,.45);border-radius:15px;
      background:rgba(67,56,202,.13);padding:12px 15px 14px}
  .kb .tier{color:#C7CCFF;border-color:rgba(165,180,252,.5)}
  .kb .grid{grid-template-columns:1fr 1fr 1.32fr;gap:12px}
  .kbcard{border-radius:11px;padding:11px 14px;display:flex;flex-direction:column;gap:6px;
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
            + ''.join(f'<div class="chip g mono"><b>Skill {i}</b><i>xxx</i></div>' for i in range(1, 6)))
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

canvas = {
 "pages":[{"id":"page-1","name":"最终版"},{"id":"page-2","name":"其它方向"}],
 "artboards":[
  {"file":"Main.dc.html","title":"最终版 · 双栏底座 16:9","page":"page-1","x":0,"y":0,"w":1600,"h":900},
  {"file":"Enclosure.dc.html","title":"方向二 · 环抱式","page":"page-2","x":0,"y":0,"w":1600,"h":900},
  {"file":"Granularity.dc.html","title":"方向三 · 粒度阶梯","page":"page-2","x":1760,"y":0,"w":1600,"h":900},
  {"file":"Rail.dc.html","title":"方向四 · 横向流水线","page":"page-2","x":3520,"y":0,"w":1600,"h":830}
 ],
 "annotations":[
  {"id":"note-final","page":"page-1","x":0,"y":-150,"w":460,
   "text":"最终版：方向一的构图，锁 16:9（1600×900）。\\n知识库换成靛蓝，和紫色的能力层分成两种物质；层级数量标注已去掉；专家团补齐了扩展位。"},
  {"id":"note-alts","page":"page-2","x":0,"y":-150,"w":460,
   "text":"没有选中的三个方向，留作参考。"}
 ],
 "launch":{"view":"canvas","page":"page-1"}
}
(CANVAS/'canvas.json').write_text(json.dumps(canvas, ensure_ascii=False, indent=1), encoding='utf-8')
print('built:', ', '.join(sorted(p.name for p in CANVAS.iterdir())), '+ tmg-a-h-platform.html')
