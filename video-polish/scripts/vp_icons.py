#!/usr/bin/env python3
"""配图卡用的矢量图标。全部是几何化的剪影，宁可简单也不要画得半写实。"""

# viewBox 统一 0 0 120 120，画面重心居中
ICONS = {
    # 齿轮：生产力 / 工具。齿用 dasharray 打断的粗描边画，比手写 16 段路径干净
    "gear": '<circle cx="60" cy="60" r="44" fill="none" stroke-width="17" '
            'stroke-dasharray="15 19.56"/>'
            '<circle cx="60" cy="60" r="29" fill="none" stroke-width="13"/>',
    # 火车头：锅炉 + 烟囱 + 驾驶室 + 蒸汽。比抽象的"蒸汽机"好认得多
    "steam": '<rect x="14" y="56" width="60" height="30" rx="8"/>'
             '<rect x="74" y="34" width="30" height="52" rx="5"/>'
             '<rect x="20" y="30" width="17" height="28" rx="2"/>'
             '<path d="M14 24h29l-4 8H18z"/>'
             '<rect x="8" y="86" width="104" height="9" rx="4"/>'
             '<circle cx="30" cy="106" r="13"/><circle cx="62" cy="108" r="10"/>'
             '<circle cx="92" cy="106" r="13"/>'
             '<circle cx="28" cy="18" r="7" opacity=".5"/>'
             '<circle cx="45" cy="10" r="5" opacity=".32"/>',
    # 马车：靠大辐条轮和长车辕跟汽车区分开
    "carriage": '<path d="M30 50h44a6 6 0 016 6v22H24V56a6 6 0 016-6z"/>'
                '<path d="M30 32h30v18H30z" opacity=".45"/>'
                '<path d="M80 62h20l14-14" fill="none" stroke-width="6" stroke-linecap="round"/>'
                '<circle cx="76" cy="92" r="21" fill="none" stroke-width="7"/>'
                '<path d="M76 71v42M55 92h42M61 77l30 30M91 77l-30 30" stroke-width="4" fill="none"/>'
                '<circle cx="28" cy="100" r="13" fill="none" stroke-width="6"/>'
                '<path d="M28 87v26M15 100h26" stroke-width="4" fill="none"/>',
    # 汽车：侧面剪影
    "car": '<path d="M14 84V70l10-4 12-20a10 10 0 018-4h32a10 10 0 018 5l11 19 11 4v14a6 6 0 01-6 6h-6'
           'a14 14 0 00-28 0H54a14 14 0 00-28 0h-6a6 6 0 01-6-6z"/>'
           '<path d="M44 48h-6l-8 14h14zm10 0h14v14H54zm24 0h-6v14h14z" fill="#0B0E13"/>'
           '<circle cx="40" cy="90" r="10"/><circle cx="82" cy="90" r="10"/>',
    # 漏斗：筛选
    "filter": '<path d="M16 20h88L70 64v34l-20 12V64z"/>',
    # 人：单人 / 岗位
    "person": '<circle cx="60" cy="34" r="18"/>'
              '<path d="M24 108a36 36 0 0172 0 6 6 0 01-6 6H30a6 6 0 01-6-6z"/>',
    # 两个人：团队 / 员工
    "people": '<circle cx="42" cy="36" r="16"/><circle cx="86" cy="42" r="13"/>'
              '<path d="M10 104a32 32 0 0164 0 5 5 0 01-5 5H15a5 5 0 01-5-5z"/>'
              '<path d="M78 109a38 38 0 00-8-23 26 26 0 0142 18 5 5 0 01-5 5z" opacity=".55"/>',
    # 闪电：效率跃迁
    "bolt": '<path d="M68 6L26 68h26l-8 46 44-64H62z"/>',
    # 雾中开车：车 + 灯锥 + 雾线
    "fog": '<path d="M8 88V78l8-3 9-15a8 8 0 017-4h26a8 8 0 016 4l9 15 8 3v10a5 5 0 01-5 5h-4'
           'a11 11 0 00-22 0H39a11 11 0 00-22 0h-4a5 5 0 01-5-5z"/>'
           '<circle cx="30" cy="93" r="8"/><circle cx="64" cy="93" r="8"/>'
           '<path d="M78 66l36-16v42l-36-14z" opacity=".3"/>'
           '<path d="M20 30h58M34 46h56M8 14h52" stroke-width="6" stroke-linecap="round" '
           'fill="none" opacity=".35"/>',
    # 向上箭头：提升
    "up": '<path d="M60 10l38 40H76v60H44V50H22z"/>',
    # 问号：疑问 / 担忧
    "question": '<path d="M60 8a34 34 0 00-34 34h20a14 14 0 1114 14c-6 0-10 4-10 10v14h20v-8'
                'a34 34 0 00-10-64z"/><circle cx="60" cy="104" r="11"/>',
    # 时钟：时效
    "clock": '<path d="M60 8a52 52 0 100 104A52 52 0 0060 8zm0 16a36 36 0 110 72 36 36 0 010-72z"/>'
             '<path d="M56 34h8v28h22v8H56z"/>',
    # 岔路：两条路 + 箭头，用来表示"选哪条"
    "fork": '<path d="M54 118V78L20 44v-6h12l34 34v46z" opacity=".55"/>'
            '<path d="M54 118V78l34-34h12v6L66 84v34z"/>'
            '<path d="M8 46V22h24v12H20v12z"/><path d="M112 46V22H88v12h12v12z"/>',
}


def svg(name, color="#FFD400", size=200):
    body = ICONS.get(name)
    if not body:
        return ""
    return (f'<svg class="icon" viewBox="0 0 120 120" width="{size}" height="{size}" '
            f'fill="{color}" stroke="{color}">{body}</svg>')
