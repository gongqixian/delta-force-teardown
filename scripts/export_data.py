# -*- coding: utf-8 -*-
"""
把 workspace 里的分析产物导出成仓库用的聚合数据。

原则：
- 只导出**聚合统计**与**推导结果**，不含任何游戏原始资源（配置表原文、Lua 字节码、pak 内容）。
- 所有数字都可以由 scripts/ 里的脚本重新算出来（脚本读的是本地游戏目录，不在仓库里）。
"""
import io
import json
import os

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
LOGS = os.path.join(WS, 'output', 'df', 'logs')
OUT = os.path.join(WS, 'repos', 'delta-force-teardown', 'data')
os.makedirs(OUT, exist_ok=True)


def rd(name):
    with io.open(os.path.join(LOGS, name), encoding='utf-8') as f:
        return json.load(f)


def wjson(name, obj):
    p = os.path.join(OUT, name)
    with io.open(p, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print('%-32s %d B' % (name, os.path.getsize(p)))


# ---------------------------------------------------------------- 1. 六张地图的几何真值
# 点位数量取自地图内图例（官方标注），不是从坐标点数量反推——两者偶尔不等。
MAP_META = {
    u'零号大坝': (u'map_article.js', 811, 810, u'常规 / 机密', 14, 8),
    u'长弓溪谷': (u'map_cgxg.js', 1128, 1128, u'常规 / 机密', 22, 9),
    u'航天基地': (u'map_htjd.js', 654, 654, u'机密 / 绝密', 8, 3),
    u'巴克什':   (u'map_bks.js', 600, 600, u'常规 / 机密 / 绝密', 11, 6),
    u'潮汐监狱': (u'map_cxjy.js', 366, 366, u'未标注', 14, 5),
    u'AZ3':      (u'map_az3.js', 810, 808, u'常规 / 机密', 14, 16),
}

geo = {}
for row in rd('map_geometry2.json'):
    geo[row['name']] = row

maptool = rd('maptool_data.json')

maps = []
for name, (src, w, h, diff, sp, ex) in MAP_META.items():
    g = geo.get(name, {})
    t = maptool.get(name) or {}
    floor = t.get('floor') or {}
    counts = floor.get('counts') or {}
    diag = (w * w + h * h) ** 0.5
    dmin = round(g.get('near', 0), 1)
    dmed = round(g.get('med', 0), 1)
    dmax = round(g.get('far', 0), 1)
    # 个别撤离点坐标落在图幅之外（坐标系不同源），这类极值不可用，置空
    outlier = dmax > diag * 1.05
    maps.append({
        u'name': name,
        u'source_file': src,
        u'size_m': [w, h],
        u'diagonal_m': round(diag, 1),
        u'spawn_points': sp,
        u'exfil_points': ex,
        u'difficulty_tiers': diff,
        u'dist_to_nearest_exfil_m': {
            u'min': dmin,
            u'median': dmed,
            u'max': None if outlier else dmax,
        },
        u'loot_nodes': sum(counts.values()) if counts else None,
        u'loot_node_kinds': len(counts) if counts else None,
    })

wjson('map-geometry.json', {
    u'note': u'尺寸与点位数量取自官方地图工具的公开点位表；距离为出生点到最近撤离点的直线距离，'
             u'按地图坐标系折算为米。',
    u'maps': maps,
})


# ---------------------------------------------------------------- 2. 图例：十种撤离点
wjson('exfil-types.json', {
    u'note': u'六张图合计 47 个撤离点。只有"常规撤离点"是走到即可用，其余九类都要求玩家先做一件事。',
    u'total': 47,
    u'free_ratio': 0.213,
    u'types': [
        {u'type': u'常规撤离点', u'count': 10, u'condition': u'自由使用，走到即走'},
        {u'type': u'概率撤离点', u'count': 8, u'condition': u'每局随机开启，不一定可用'},
        {u'type': u'条件撤离点', u'count': 10, u'condition': u'需持有特定道具或完成特定动作'},
        {u'type': u'拉闸撤离点', u'count': 8, u'condition': u'需先到别处合闸，闸是公开位置'},
        {u'type': u'付费撤离点', u'count': 3, u'condition': u'花游戏币开启'},
        {u'type': u'行动撤离点', u'count': 2, u'condition': u'需接取并完成对应行动'},
        {u'type': u'丢包撤离点', u'count': 2, u'condition': u'需交出部分背包内容'},
        {u'type': u'列车撤离点', u'count': 1, u'condition': u'按时刻表发车'},
        {u'type': u'电梯撤离点', u'count': 2, u'condition': u'限时开启'},
        {u'type': u'延迟撤离点', u'count': 1, u'condition': u'进入后需等待倒计时'},
    ],
})


# ---------------------------------------------------------------- 3. 玩家行为聚合
wjson('player-sample.json', {
    u'note': u'一名玩家的搜打撤对局逐局结算，用于观察经济期望与时长结构。只保留聚合统计。',
    u'battles': 247,
    u'exfil_rate': 0.275,
    u'breakeven_exfil_rate': 0.32,
    u'cumulative_net': -7_820_000,
    u'duration_minutes': {
        u'median': 6.4, u'p10': 1.5, u'p25': 3.0, u'p75': 10.9, u'p90': 19.6, u'max': 29.9,
        u'death_median': 4.3, u'exfil_median': 11.5,
    },
    u'by_duration_bucket': [
        {u'bucket': u'0-3 min',  u'n': 63, u'exfil_rate': 0.000, u'net_median': -433000, u'loot_per_min': 0.176, u'kills_avg': 0.95},
        {u'bucket': u'3-5 min',  u'n': 34, u'exfil_rate': 0.000, u'net_median': -240000, u'loot_per_min': 0.236, u'kills_avg': 2.32},
        {u'bucket': u'5-8 min',  u'n': 39, u'exfil_rate': 0.026, u'net_median': -294000, u'loot_per_min': 0.149, u'kills_avg': 3.00},
        {u'bucket': u'8-12 min', u'n': 59, u'exfil_rate': 0.644, u'net_median':  364000, u'loot_per_min': 0.114, u'kills_avg': 4.24},
        {u'bucket': u'12-18 min', u'n': 21, u'exfil_rate': 0.286, u'net_median':  185000, u'loot_per_min': 0.074, u'kills_avg': 4.81},
        {u'bucket': u'18+ min',  u'n': 31, u'exfil_rate': 0.742, u'net_median':  411000, u'loot_per_min': 0.050, u'kills_avg': 5.94},
    ],
    u'by_map': [
        {u'map': u'零号大坝·机密',   u'n': 42,  u'exfil_rate': 0.381, u'net_per_hour_wan': 117.9, u'median_min': 6.7, u'payback_ratio': 1.16},
        {u'map': u'航天基地·绝密',   u'n': 113, u'exfil_rate': 0.319, u'net_per_hour_wan': 39.5,  u'median_min': 9.0, u'payback_ratio': 0.74},
        {u'map': u'AZ3·机密',        u'n': 42,  u'exfil_rate': 0.286, u'net_per_hour_wan': -61.0, u'median_min': 6.5, u'payback_ratio': 0.36},
        {u'map': u'巴克什·机密',     u'n': 39,  u'exfil_rate': 0.103, u'net_per_hour_wan': -388.1, u'median_min': 3.2, u'payback_ratio': 0.20},
        {u'map': u'航天基地·机密',   u'n': 9,   u'exfil_rate': 0.000, u'net_per_hour_wan': -140.1, u'median_min': 6.0, u'payback_ratio': 0.0},
    ],
})


# ---------------------------------------------------------------- 4. 参数敏感度
wjson('parameter-sensitivity.json', {
    u'note': u'十四个参数变体各跑一遍 2,898 个交火场景（69 把枪 x 7 个护甲等级 x 6 个距离），'
             u'统计"击杀所需发数"发生变化的场景占比。离散的 TTK 让玩家只感知到"少打/多打一发"。',
    u'scenarios': 2898,
    u'baseline_median_shots': 4.0,
    u'rows': [
        {u'variant': u'基础肉体伤害 x0.85',   u'cross_one_shot': 0.6280, u'median_after': 5.0, u'mean_delta':  0.655},
        {u'variant': u'基础肉体伤害 x0.90',   u'cross_one_shot': 0.4379, u'median_after': 5.0, u'mean_delta':  0.438},
        {u'variant': u'基础肉体伤害 x1.15',   u'cross_one_shot': 0.3696, u'median_after': 4.0, u'mean_delta': -0.370},
        {u'variant': u'耐久吸收率统一 0.6',   u'cross_one_shot': 0.2833, u'median_after': 5.0, u'mean_delta':  0.644},
        {u'variant': u'基础肉体伤害 x1.10',   u'cross_one_shot': 0.2315, u'median_after': 4.0, u'mean_delta': -0.232},
        {u'variant': u'基础护甲伤害 x0.85',   u'cross_one_shot': 0.2153, u'median_after': 5.0, u'mean_delta':  0.259},
        {u'variant': u'衰减边界 x1.2',        u'cross_one_shot': 0.1705, u'median_after': 4.0, u'mean_delta': -0.222},
        {u'variant': u'基础护甲伤害 x1.15',   u'cross_one_shot': 0.1712, u'median_after': 4.0, u'mean_delta': -0.189},
        {u'variant': u'穿透系数表改陡',       u'cross_one_shot': 0.1432, u'median_after': 5.0, u'mean_delta':  0.154},
        {u'variant': u'穿透系数表改平',       u'cross_one_shot': 0.1342, u'median_after': 4.0, u'mean_delta': -0.122},
        {u'variant': u'耐久吸收率统一 1.0',   u'cross_one_shot': 0.1153, u'median_after': 4.0, u'mean_delta': -0.154},
        {u'variant': u'衰减边界 x0.8',        u'cross_one_shot': 0.0711, u'median_after': 5.0, u'mean_delta':  0.090},
        {u'variant': u'三级甲耐久 85 -> 110', u'cross_one_shot': 0.0121, u'median_after': 4.0, u'mean_delta':  0.012},
        {u'variant': u'三级甲耐久 85 -> 60',  u'cross_one_shot': 0.0079, u'median_after': 4.0, u'mean_delta': -0.008},
    ],
})

print('\ndone ->', OUT)
