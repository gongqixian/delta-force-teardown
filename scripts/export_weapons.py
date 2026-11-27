# -*- coding: utf-8 -*-
"""导出 69 把枪的对比表（含枪声半径），供仓库里的画图脚本直接读取。

注意：这里输出的是**每把枪的两个基础伤害值、射速、弹丸数、由此算出的理论秒伤，
以及枪声半径**——都是聚合/推导量，不含配置表原文。
"""
import collections
import csv
import io
import json
import os

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
REF = os.path.join(WS, 'output', 'df', 'ref')
OUT = os.path.join(WS, 'repos', 'delta-force-teardown', 'data')


def jload(p):
    with io.open(p, encoding='utf-8-sig') as f:
        return json.load(f)


w = jload(os.path.join(REF, 'dfttk', 'v3', 'catalog', 'weapons.json'))['objects']
idx = jload(os.path.join(REF, 'index.json'))

# 两个数据源的 id 格式不同（一边是数字 id，一边是 m4a1 这类 slug），
# 用「肉体伤害 + 护甲伤害 + 射速」三元组做连接——这三项同时相同的枪极少。
keyed = {}
for grp in idx.get('weapons', []):
    for it in grp.get('weapons', []):
        k = (it.get('baseDamage'), it.get('armorDamage'), it.get('fireRate'))
        keyed.setdefault(k, it)

CAT = {
    'assaultRifle': u'突击步枪', 'submachineGun': u'冲锋枪',
    'marksmanRifle': u'精确射手步枪', 'pistol': u'手枪',
    'sniperRifle': u'狙击步枪', 'lightMachineGun': u'轻机枪',
    'specialWeapon': u'特殊武器',
}

rows = []
matched = 0
for wid, obj in w.items():
    sol = (obj.get('combatSummaryByMode') or {}).get('sol') or {}
    flesh = sol.get('baseFleshDamage')
    armor = sol.get('baseArmorDamage')
    rpm = sol.get('fireRateRpm')
    pellets = sol.get('projectileCount') or 1
    if flesh is None or rpm is None:
        continue
    dps = flesh * (rpm / 60.0) * pellets
    cat = obj.get('categoryId')
    m = keyed.get((flesh, armor, round(rpm)))
    if m is None:
        m = keyed.get((flesh, armor, rpm))
    if m:
        matched += 1
    rows.append({
        'weapon_id': wid,
        'name': (m or {}).get('name', ''),
        'category': CAT.get(cat, u'霰弹枪'),
        'base_flesh_damage': flesh,
        'base_armor_damage': armor,
        'fire_rate_rpm': round(rpm, 2),
        'pellets': pellets,
        'dps_theoretical': round(dps, 1),
        'sound_radius_m': (m or {}).get('soundRadius', ''),
        'caliber': (m or {}).get('caliber', ''),
    })

print('matched %d / %d' % (matched, len(rows)))

rows.sort(key=lambda r: -r['dps_theoretical'])
p = os.path.join(OUT, 'weapons.csv')
with io.open(p, 'w', encoding='utf-8', newline='') as f:
    wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    wr.writeheader()
    wr.writerows(rows)
print('%s  %d rows  %d B' % ('weapons.csv', len(rows), os.path.getsize(p)))

# 枪声档位分布（画图要用）
band = collections.Counter()
for r in rows:
    if r['sound_radius_m'] != '':
        band[r['sound_radius_m']] += 1
print('sound bands:', dict(sorted(band.items())))
