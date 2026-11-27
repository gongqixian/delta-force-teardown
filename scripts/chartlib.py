# -*- coding: utf-8 -*-
"""用 PIL 画图表：白底黑线灰阶，适合印刷的拆解案插图"""
import io
import math
import os

from PIL import Image, ImageDraw, ImageFont

FONT_R = r'C:\Windows\Fonts\msyh.ttc'
FONT_B = r'C:\Windows\Fonts\msyhbd.ttc'


class Chart(object):
    W, H = 1600, 900

    def __init__(self, w=1600, h=900, bg=(255, 255, 255)):
        self.w, self.h = w, h
        self.img = Image.new('RGB', (w, h), bg)
        self.d = ImageDraw.Draw(self.img)
        self._font_cache = {}

    def f(self, size, bold=False):
        key = (size, bold)
        if key not in self._font_cache:
            self._font_cache[key] = ImageFont.truetype(FONT_B if bold else FONT_R, size)
        return self._font_cache[key]

    # ---------- 基础图元 ----------
    def text(self, xy, s, size=28, bold=False, fill=(26, 26, 26), anchor='la'):
        size = int(round(size * FSCALE))
        self.d.text(xy, s, font=self.f(size, bold), fill=fill, anchor=anchor)

    def line(self, pts, fill=(70, 70, 70), width=3):
        self.d.line(pts, fill=fill, width=width)

    def rect(self, box, fill=None, outline=(90, 90, 90), width=2):
        self.d.rectangle(box, fill=fill, outline=outline, width=width)

    def hline(self, y, x0, x1, fill=(180, 180, 180), width=1):
        self.d.line([(x0, y), (x1, y)], fill=fill, width=width)

    def vline(self, x, y0, y1, fill=(180, 180, 180), width=1):
        self.d.line([(x, y0), (x, y1)], fill=fill, width=width)

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.img.save(path, 'PNG')
        return path


def frame(c, title, sub=None, x0=170, y0=150, x1=None, y1=None):
    """画标题 + 坐标框，返回绘图区内框"""
    x1 = x1 or c.w - 90
    y1 = y1 or c.h - 150
    c.text((x0 - 100, 46), title, 38, True)
    if sub:
        c.text((x0 - 100, 100), sub, 24, False, (110, 110, 110))
    c.line([(x0, y1), (x0, y0)], (60, 60, 60), 3)
    c.line([(x0, y1), (x1, y1)], (60, 60, 60), 3)
    return x0, y0, x1, y1


def yaxis(c, lo, hi, x0, y0, y1, ticks=5, fmt='%.0f', unit=''):
    for i in range(ticks + 1):
        v = lo + (hi - lo) * i / ticks
        y = y1 - (y1 - y0) * i / ticks
        c.hline(int(y), x0, c.w - 90, (225, 225, 225), 1)
        lab = (fmt % v) + unit
        c.text((x0 - 16, y), lab, 22, False, (90, 90, 90), anchor='rm')


def xaxis_labels(c, labels, x0, x1, y1, size=22, rotate=0):
    n = len(labels)
    for i, lab in enumerate(labels):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        if rotate:
            tmp = Image.new('RGBA', (400, 60), (0, 0, 0, 0))
            dd = ImageDraw.Draw(tmp)
            dd.text((200, 30), lab, font=c.f(size), fill=(90, 90, 90), anchor='mm')
            tmp = tmp.rotate(rotate, expand=1, resample=Image.BICUBIC)
            c.img.paste(tmp, (int(x - tmp.width / 2), int(y1 + 12)), tmp)
        else:
            c.text((x, y1 + 16), lab, size, False, (90, 90, 90), anchor='ma')


FSCALE = 1.0
GRAY = [(38, 38, 38), (92, 92, 92), (140, 140, 140), (188, 188, 188), (222, 222, 222)]
ACC = (52, 52, 52)
