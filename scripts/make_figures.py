# -*- coding: utf-8 -*-
"""
生成 6 张分析图。只读 data/ 下的聚合数据，不依赖任何游戏文件。

用法：
    python scripts/make_figures.py

依赖：Pillow。中文用 Windows 自带字体；Linux/macOS 请改 fonts() 里的路径。
"""
import collections
import csv
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chartlib
chartlib.FSCALE = 1.20
from chartlib import Chart, frame, yaxis, xaxis_labels

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
DATA = os.path.join(ROOT, 'data')
FIG = os.path.join(ROOT, 'figures')
os.makedirs(FIG, exist_ok=True)


def out(name):
    return os.path.join(FIG, name)


def jload(name):
    with io.open(os.path.join(DATA, name), encoding='utf-8') as f:
        return json.load(f)


def weapons():
    p = os.path.join(DATA, 'weapons.csv')
    with io.open(p, encoding='utf-8') as f:
        return list(csv.DictReader(f))


# ============================================================ 图 1
def fig_dps_by_class():
    """按枪族看理论秒伤的分布：粗线=该类最低到最高，方点=中位。"""
    by = collections.defaultdict(list)
    for r in weapons():
        by[r['category']].append(float(r['dps_theoretical']))
    rows = sorted(by.items(), key=lambda kv: -sorted(kv[1])[len(kv[1]) // 2])
    n = len(rows)
    hi = 900.0

    c = Chart(1600, 900)
    x0, y0, x1, y1 = frame(
        c, u'秒伤把六十九把枪分成三层：五百、四百、四百以下',
        u'横轴＝理论每秒伤害（肉体伤害 × 射速 × 弹丸数）；粗线为该类最低到最高，方点为中位',
        x0=260, y0=280, y1=790)
    for i in range(7):
        v = hi * i / 6
        x = x0 + (x1 - x0) * i / 6
        c.vline(int(x), y0, y1, (233, 233, 233), 1)
        c.text((x, y1 + 10), '%.0f' % v, 22, False, (90, 90, 90), anchor='ma')
    c.text(((x0 + x1) // 2, y1 + 58), u'理论每秒伤害（未计护甲与命中分布）', 24, False,
           (80, 80, 80), anchor='ma')

    gap = (y1 - y0) / float(n)
    for i, (cat, vals) in enumerate(rows):
        vals = sorted(vals)
        med = vals[len(vals) // 2]
        yy = y0 + gap * (i + 0.5)
        xa = x0 + (x1 - x0) * vals[0] / hi
        xb = x0 + (x1 - x0) * vals[-1] / hi
        c.line([(xa, yy), (xb, yy)], (150, 150, 150), 6)
        c.line([(xa, yy - 14), (xa, yy + 14)], (120, 120, 120), 3)
        c.line([(xb, yy - 14), (xb, yy + 14)], (120, 120, 120), 3)
        xm = x0 + (x1 - x0) * med / hi
        c.rect([xm - 7, yy - 17, xm + 7, yy + 17], fill=(52, 52, 52), outline=None, width=0)
        c.text((x0 - 20, yy), u'%s（%d）' % (cat, len(vals)), 24, False, (40, 40, 40), anchor='rm')
        if i == n - 1:
            c.text((xm + 16, yy), u'%.0f' % med, 22, True, (30, 30, 30), anchor='lm')
        else:
            c.text((xm, yy - 30), u'%.0f' % med, 22, True, (30, 30, 30), anchor='mb')

    c.text((x0, 158),
           u'狙击的中位只有五十七，全场最低——但它一百点基础伤害意味着一枪结束交火。',
           19, False, (40, 40, 40))
    c.text((x0, 188),
           u'秒伤衡量持续输出，不衡量爆发。真正的分层在连发武器之间：', 19, False, (40, 40, 40))
    c.text((x0, 218),
           u'霰弹枪与轻机枪五百、冲锋枪四百五、突击步枪三百九、精确射手三百二。',
           19, False, (40, 40, 40))
    return c.save(out('01-dps-by-class.png'))


# ============================================================ 图 2
def fig_sound_bands():
    """枪声只有 7 个档位，每档基本就是一个枪族。"""
    band = collections.defaultdict(list)
    for r in weapons():
        if r['sound_radius_m'] == '':
            continue
        band[int(r['sound_radius_m'])].append(r['category'])
    bands = sorted(band.keys(), reverse=True)

    c = Chart(1600, 900)
    x0, y0, x1, y1 = frame(
        c, u'六十八把枪只用了七个枪声档位，每一档基本就是一个枪族',
        u'横轴＝该档位的枪械数量；右侧列出该档位包含的枪族',
        x0=250, y0=270, y1=790)
    XMAX = 40.0
    for i in range(6):
        v = XMAX * i / 5
        x = x0 + (x1 - x0) * i / 5
        c.vline(int(x), y0, y1, (233, 233, 233), 1)
        c.text((x, y1 + 10), '%.0f' % v, 22, False, (90, 90, 90), anchor='ma')
    c.text((x0 + (x1 - x0) * 0.12, y1 + 56), u'枪械数量（把）', 24, False, (80, 80, 80),
           anchor='ma')

    gap = (y1 - y0) / float(len(bands))
    TXT_X = x0 + (x1 - x0) * 0.63
    for i, b in enumerate(bands):
        cats = band[b]
        yy = y0 + gap * (i + 0.5)
        bw = (x1 - x0) * len(cats) / XMAX
        c.rect([x0, yy - gap * 0.28, x0 + max(bw, 4), yy + gap * 0.28],
               fill=(150, 150, 150), outline=(70, 70, 70), width=2)
        c.text((x0 - 18, yy), u'%d 米' % b, 25, True, (35, 35, 35), anchor='rm')
        c.text((x0 + bw + 12, yy), u'%d 把' % len(cats), 22, True, (60, 60, 60), anchor='lm')
        uniq = []
        for x in cats:
            if x not in uniq:
                uniq.append(x)
        c.text((TXT_X, yy), u'、'.join(uniq), 20, False, (55, 55, 55), anchor='lm')

    c.text((x0, 160),
           u'枪声不是一把枪的可调项，而是枪族的标签：冲锋枪与手枪三百米，多数突击步枪五百米，',
           19, False, (40, 40, 40))
    c.text((x0, 190),
           u'战斗步枪、精确射手与轻机枪六百米。九成三的枪落在这三档里。', 19, False, (40, 40, 40))
    c.text((x0, 220),
           u'玩家选枪时枪声是被动接受的，不是拿来比较的。', 19, False, (40, 40, 40))
    return c.save(out('02-sound-radius-bands.png'))


# ============================================================ 图 3
def fig_duration():
    """时长段局数 + 该段撤离率；第八分钟画一道门。"""
    d = jload('player-sample.json')
    buckets = d['by_duration_bucket']

    c = Chart(1600, 900)
    x0, y0, x1, y1 = frame(
        c, u'第八分钟是一道门：此前进得去出不来',
        u'灰柱＝该时长段的局数（左轴）；折线＝该段的撤离率（右轴）',
        x0=170, y0=180, y1=790)
    yaxis(c, 0, 70, x0, y0, y1, ticks=7, fmt='%.0f', unit=u' 局')

    n = len(buckets)
    w = x1 - x0
    bw = w / float(n) * 0.56
    rate_pts = []
    for i, b in enumerate(buckets):
        cx = x0 + w * (i + 0.5) / n
        h = (y1 - y0) * b['n'] / 70.0
        c.rect([cx - bw / 2, y1 - h, cx + bw / 2, y1], fill=(205, 205, 205),
               outline=(120, 120, 120), width=2)
        c.text((cx, y1 - h - 12), str(b['n']), 22, True, (60, 60, 60), anchor='mb')
        ry = y1 - (y1 - y0) * b['exfil_rate'] / 1.0
        rate_pts.append((cx, ry))

    c.line(rate_pts, (20, 20, 20), 4)
    last = len(rate_pts) - 1
    for k, ((x, y), b) in enumerate(zip(rate_pts, buckets)):
        c.d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(20, 20, 20))
        if k == last:
            c.text((x - 22, y), u'%.0f%%' % (b['exfil_rate'] * 100), 24, True, (20, 20, 20),
                   anchor='rm')
        else:
            c.text((x + 22, y), u'%.0f%%' % (b['exfil_rate'] * 100), 24, True, (20, 20, 20),
                   anchor='lm')

    xaxis_labels(c, [b['bucket'] for b in buckets], x0, x1, y1, 23)
    gx = x0 + w * 3
    c.line([(gx, y0 - 10), (gx, y1)], (20, 20, 20), 3)
    c.text((gx + 12, y0 + 2), u'第八分钟', 24, True, (20, 20, 20))
    c.text((x0, 142),
           u'第八分钟之前共 143 局，只有 1 局撤离成功——零点七个百分点。', 23, False, (40, 40, 40))
    return c.save(out('03-duration-vs-exfil-rate.png'))


# ============================================================ 图 4
def fig_map_economy():
    """四张图的收益结构：只有一张是正期望。"""
    d = jload('player-sample.json')
    # 每一类图的名称标签放哪一侧（避免互相压住）
    HOW = {
        u'零号大坝·机密': 'above',
        u'航天基地·绝密': 'left',
        u'AZ3·机密': 'right',
        u'巴克什·机密': 'above',
        u'航天基地·机密': 'right',
    }
    pts = [(m['map'], m['exfil_rate'] * 100, m['net_per_hour_wan'], m['n'],
            HOW.get(m['map'], 'above')) for m in d['by_map']]

    LO, HI = -400.0, 200.0
    c = Chart(1600, 940)
    x0, y0, x1, y1 = frame(
        c, u'四张图的收益结构：只有一张是正期望',
        u'横轴＝撤离率；纵轴＝每小时净收益（万哈弗币）；圆面积＝样本量',
        y0=200, y1=790)
    yaxis(c, LO, HI, x0, y0, y1, 6, '%.0f')
    for i in range(6):
        v = i * 20
        x = x0 + (x1 - x0) * v / 100.0
        c.vline(int(x), y0, y1, (233, 233, 233), 1)
        c.text((x, y1 + 10), '%d%%' % v, 22, False, (90, 90, 90), anchor='ma')
    c.text(((x0 + x1) // 2, y1 + 58), u'撤离率', 24, False, (80, 80, 80), anchor='ma')
    zy = y1 - (y1 - y0) * (0 - LO) / (HI - LO)
    c.line([(x0, zy), (x1, zy)], (60, 60, 60), 3)
    c.text((x0 + 8, zy - 8), u'零线', 21, False, (90, 90, 90), anchor='lb')

    for nm, esc, net, cnt, how in pts:
        x = x0 + (x1 - x0) * esc / 100.0
        y = y1 - (y1 - y0) * (net - LO) / (HI - LO)
        r = 12 + (cnt ** 0.5) * 3.4
        c.d.ellipse([x - r, y - r, x + r, y + r],
                    fill=(205, 205, 205), outline=(40, 40, 40), width=3)
        money = (u'%+.0f 万/时' % net)
        if how == 'above':
            c.text((x, y - r - 30), nm, 23, True, (30, 30, 30), anchor='mb')
            c.text((x, y - r - 6), money, 21, False, (95, 95, 95), anchor='mb')
        elif how == 'right':
            c.text((x + r + 10, y - 14), nm, 23, True, (30, 30, 30), anchor='lm')
            c.text((x + r + 10, y + 14), money, 21, False, (95, 95, 95), anchor='lm')
        else:
            c.text((x - r - 10, y - 14), nm, 23, True, (30, 30, 30), anchor='rm')
            c.text((x - r - 10, y + 14), money, 21, False, (95, 95, 95), anchor='rm')

    c.text((x0 + 14, y0 + 4), u'零线以上是正期望。', 23, False, (40, 40, 40))
    c.text((x0 + 14, y0 + 40), u'巴克什撤离率只有一成，', 23, False, (40, 40, 40))
    c.text((x0 + 14, y0 + 76), u'每小时亏三百八十八万。', 23, False, (40, 40, 40))
    return c.save(out('04-map-economy-scatter.png'))


# ============================================================ 图 5
def fig_sensitivity():
    """14 个参数变体的效力。"""
    d = jload('parameter-sensitivity.json')
    rows = [(r['variant'], r['cross_one_shot'] * 100) for r in d['rows']]
    rows.sort(key=lambda x: x[1])

    c = Chart(1600, 960)
    x0, y0, x1, y1 = frame(
        c, u'十四个参数的效力：改哪个数会改变结果',
        u'横轴＝结果受影响的场景比例（共 2,898 个场景）',
        x0=390, y0=200, y1=850)
    n = len(rows)
    gap = (y1 - y0) / float(n)
    hi = 70.0
    for i, (lab, v) in enumerate(rows):
        yy = y1 - gap * (i + 0.55)
        h = gap * 0.52
        bw = (x1 - x0) * v / hi
        fill = (38, 38, 38) if v >= 20 else ((125, 125, 125) if v >= 10 else (205, 205, 205))
        c.rect([x0, yy - h / 2, x0 + max(bw, 3), yy + h / 2], fill=fill, outline=None, width=0)
        c.text((x0 - 16, yy), lab, 22, False, (40, 40, 40), anchor='rm')
        c.text((x0 + bw + 10, yy), u'%.2f%%' % v, 21, True, (40, 40, 40), anchor='lm')
    for i in range(8):
        v = 10 * i
        x = x0 + (x1 - x0) * v / hi
        c.vline(int(x), y0, y1, (233, 233, 233), 1)
        c.text((x, y1 + 10), '%d%%' % v, 22, False, (90, 90, 90), anchor='ma')
    c.text((x0, 146),
           u'最后两行几乎是空的：三级甲耐久 85 砍到 60，只有 0.79% 的场景会多打一发。',
           23, False, (40, 40, 40))
    return c.save(out('05-parameter-sensitivity.png'))


# ============================================================ 图 6
def fig_armor_tiers():
    """穿透系数的四个台阶。"""
    tiers = [(u'-2', 0.0, u'打不动'), (u'-1', 0.0, u'打不动'),
             (u'+0', 0.50, u''), (u'+1', 0.75, u''),
             (u'+2', 1.00, u''), (u'+3', 1.00, u'')]

    c = Chart(1600, 820)
    x0, y0, x1, y1 = frame(
        c, u'穿透系数：穿甲等级减去护甲等级，决定这一发打多少血',
        u'纵轴＝肉体伤害系数（占基础伤害的比例）；横轴＝穿甲等级 − 护甲等级',
        x0=170, y0=180, y1=700)
    yaxis(c, 0, 1.1, x0, y0, y1, ticks=5, fmt='%.1f')

    n = len(tiers)
    w = x1 - x0
    bw = w / float(n) * 0.5
    for i, (lab, v, note) in enumerate(tiers):
        cx = x0 + w * (i + 0.5) / n
        h = (y1 - y0) * v / 1.1
        fill = (38, 38, 38) if v >= 1.0 else ((190, 190, 190) if v > 0 else (238, 238, 238))
        c.rect([cx - bw / 2, y1 - h, cx + bw / 2, y1], fill=fill, outline=(60, 60, 60), width=3)
        c.text((cx, y1 - h - 12), '%.2f' % v, 24, True, (20, 20, 20), anchor='mb')
        c.text((cx, y1 + 14), lab, 24, True, (40, 40, 40), anchor='ma')
        if note:
            c.text((cx, y1 + 48), note, 20, False, (120, 120, 120), anchor='ma')
    c.text(((x0 + x1) // 2, y1 + 96), u'穿甲等级 − 护甲等级', 24, False, (80, 80, 80),
           anchor='ma')
    c.text((x0, 142),
           u'四个台阶，没有第五个：高两级吃满，低一级砍半，低两级不掉血。', 23, False, (40, 40, 40))
    return c.save(out('06-armor-penetration-tiers.png'))


if __name__ == '__main__':
    for fn in (fig_dps_by_class, fig_sound_bands, fig_duration,
               fig_map_economy, fig_sensitivity, fig_armor_tiers):
        print(fn())
    print('\nok ->', FIG)
