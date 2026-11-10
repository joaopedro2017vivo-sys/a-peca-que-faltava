"""Cenários. BG(nome) devolve imagem 1920x1080; INFO[nome] diz onde fica o chão e se o elenco flutua."""
import math, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from gfx import *
import bgs_old as O
from bgs_old import vgrad, vignette, stars, nebula, draw_earth, draw_moon

INFO = {  # chão (y dos pés), flutua?, ambiente sonoro
    'space': (900, True, 'none'), 'space_plain': (900, True, 'none'), 'spaceship': (890, True, 'hum'),
    'control': (1000, False, 'room'), 'ocean': (900, False, 'waves'), 'studio': (900, False, 'none'),
    'lab': (960, False, 'room'), 'office': (960, False, 'room'), 'workshop': (960, False, 'room'),
    'city_day': (960, False, 'city'), 'city_night': (960, False, 'city'), 'countryside': (960, False, 'wind'),
    'classroom': (960, False, 'room'), 'desert': (960, False, 'wind'), 'house': (960, False, 'room'),
    'construction': (960, False, 'city'),
}
ALIASES = {'space': 'space', 'space_plain': 'plain', 'spaceship': 'cabin', 'control': 'houston',
           'ocean': 'ocean', 'studio': 'co2bg'}
NAMES = list(INFO)


def floor_band(c, y, col1, col2, lines=True):
    c.poly([(0, y), (W, y), (W, H), (0, H)], fill=col1, ol=None)
    if lines:
        for x in range(-300, W + 300, 120):
            c.line([(x, y), (x + (x - W / 2) * 0.5, H)], fill=col2, w=3)
    c.line([(0, y), (W, y)], fill=col2, w=5)


def window(c, x0, y0, x1, y1, sky=((120, 180, 235, 255)), frame=(236, 236, 240, 255)):
    c.rr(x0, y0, x1, y1, 6, fill=sky, w=5)
    c.line([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], fill=frame, w=10)
    c.line([(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], fill=frame, w=10)
    c.rr(x0, y0, x1, y1, 6, fill=None, ol=frame, w=14)
    c.rr(x0, y0, x1, y1, 6, fill=None, w=4)


def shelf_items(c, x0, y, x1, seed):
    rnd = random.Random(seed)
    x = x0
    while x < x1 - 30:
        w = rnd.randint(18, 40); h = rnd.randint(50, 90)
        col = rnd.choice([(200, 70, 60, 255), (60, 120, 200, 255), (230, 180, 60, 255), (80, 160, 100, 255), (150, 90, 170, 255)])
        c.rr(x, y - h, x + w, y, 3, fill=col, w=3)
        x += w + rnd.randint(2, 10)


def building(c, x, w, h, base, col, lit, seed, night=False):
    rnd = random.Random(seed)
    c.rr(x, base - h, x + w, base + 10, 4, fill=col, w=4)
    for yy in range(int(base - h + 26), int(base - 30), 46):
        for xx in range(int(x + 18), int(x + w - 30), 40):
            on = rnd.random() < (0.55 if night else 0.0)
            c.rr(xx, yy, xx + 22, yy + 28, 3, fill=(255, 220, 120, 255) if on else lit, ol=None)


@lru_cache(None)
def BG(name):
    if name in ALIASES:
        return O.BG(ALIASES[name])
    c = Cv(0, 0, W, H, 1)
    if name in ('lab', 'office', 'classroom', 'house', 'workshop'):
        wall = {'lab': ((214, 228, 232), (186, 204, 210)), 'office': ((226, 222, 212), (198, 192, 180)),
                'classroom': ((236, 222, 190), (210, 192, 158)), 'house': ((230, 214, 196), (206, 186, 164)),
                'workshop': ((150, 140, 128), (118, 108, 98))}[name]
        base = vgrad(wall[0], wall[1])
        floor = {'lab': ((178, 186, 192, 255), (150, 158, 166, 255)), 'office': ((150, 112, 80, 255), (128, 94, 66, 255)),
                 'classroom': ((164, 120, 84, 255), (140, 100, 70, 255)), 'house': ((170, 124, 86, 255), (146, 104, 72, 255)),
                 'workshop': ((96, 96, 100, 255), (80, 80, 84, 255))}[name]
        if name == 'lab':
            window(c, 120, 140, 520, 470)
            c.rr(1180, 180, 1800, 420, 8, fill=(250, 250, 252, 255), w=5)
            for i, (x, col) in enumerate(((1240, (90, 200, 120, 255)), (1340, (80, 160, 230, 255)), (1440, (230, 120, 80, 255)), (1540, (200, 90, 200, 255)), (1640, (240, 210, 70, 255)))):
                c.rr(x, 260, x + 40, 380, 10, fill=(235, 245, 250, 255), w=4)
                c.rr(x + 4, 320, x + 36, 376, 8, fill=col, ol=None)
            c.rr(600, 640, 1900, 700, 6, fill=(236, 240, 244, 255), w=5)
            c.rr(620, 700, 1880, 900, 6, fill=(200, 208, 216, 255), w=5)
            c.ell(1500, 600, 40, 40, fill=(200, 230, 250, 255), w=4); c.rr(1490, 520, 1510, 570, 4, fill=(200, 230, 250, 255), w=4)
            c.rr(900, 540, 1060, 640, 8, fill=(60, 66, 80, 255), w=5); c.rr(912, 552, 1048, 628, 4, fill=(90, 200, 220, 255), ol=None)
        elif name == 'office':
            window(c, 1300, 120, 1820, 520, sky=(150, 200, 240, 255))
            c.rr(120, 140, 520, 420, 6, fill=(246, 246, 240, 255), w=5)
            for k in range(4):
                c.rr(160, 180 + k * 55, 160 + 90 + k * 60, 210 + k * 55, 3, fill=[(230, 90, 80, 255), (90, 150, 230, 255), (240, 190, 70, 255), (100, 190, 120, 255)][k], ol=None)
            c.rr(620, 200, 1100, 230, 4, fill=(120, 86, 60, 255), w=4); shelf_items(c, 640, 200, 1090, 3)
            c.rr(620, 360, 1100, 390, 4, fill=(120, 86, 60, 255), w=4); shelf_items(c, 640, 360, 1090, 4)
            c.ell(1700, 860, 60, 30, fill=(70, 120, 70, 255), w=4); c.rr(1660, 860, 1740, 960, 10, fill=(190, 110, 70, 255), w=4)
        elif name == 'classroom':
            c.rr(360, 120, 1560, 560, 10, fill=(40, 80, 60, 255), ol=(150, 110, 70, 255), w=18)
            c.text(960, 230, 'E = mc²', 64, fill=(240, 240, 230, 255), path=FB)
            c.line([(520, 360), (720, 300), (900, 420), (1100, 330), (1380, 440)], fill=(240, 240, 230, 255), w=5)
            c.ell(1700, 240, 90, 90, fill=(250, 250, 250, 255), w=6); c.line([(1700, 240), (1700, 180)], w=6); c.line([(1700, 240), (1740, 260)], w=6)
        elif name == 'house':
            window(c, 140, 140, 560, 520, sky=(150, 200, 240, 255))
            c.rr(1200, 220, 1500, 420, 6, fill=(240, 220, 170, 255), ol=(140, 100, 60, 255), w=14)
            c.ell(1350, 320, 60, 50, fill=(120, 170, 220, 255), ol=None)
            c.rr(700, 700, 1300, 820, 40, fill=(180, 80, 70, 255), w=5); c.rr(680, 640, 1320, 720, 30, fill=(200, 96, 84, 255), w=5)
            c.ell(1700, 860, 70, 34, fill=(70, 130, 70, 255), w=4); c.rr(1655, 860, 1745, 960, 10, fill=(90, 90, 100, 255), w=4)
        elif name == 'workshop':
            c.rr(120, 120, 900, 520, 6, fill=(110, 90, 70, 255), w=5)
            for i in range(6):
                x = 170 + i * 120
                c.line([(x, 160), (x, 250)], fill=(60, 60, 66, 255), w=6)
                c.rr(x - 22, 250, x + 22, 290 + (i % 3) * 20, 6, fill=[(200, 60, 50, 255), (60, 110, 200, 255), (230, 180, 50, 255)][i % 3], w=4)
            c.rr(1100, 620, 1880, 680, 6, fill=(150, 110, 70, 255), w=5); c.rr(1120, 680, 1860, 900, 6, fill=(120, 86, 56, 255), w=5)
            for i in range(3):
                c.ell(1260 + i * 200, 580, 50, 50, fill=(170, 176, 186, 255), w=5); c.ell(1260 + i * 200, 580, 18, 18, fill=(90, 96, 106, 255), w=4)
            c.rr(1200, 140, 1800, 460, 8, fill=(70, 70, 76, 255), w=5)
        floor_band(c, 930, floor[0], floor[1], lines=name != 'house')
        base.alpha_composite(c.done()[0])
        return vignette(base, 0.35)
    if name in ('city_day', 'city_night', 'construction'):
        night = name == 'city_night'
        base = vgrad((24, 30, 70), (70, 60, 110)) if night else vgrad((120, 186, 240), (210, 230, 246))
        if night:
            stars(c, 140, 5, 0, 0, W, 500); draw_moon(c, 1650, 170, 70)
        else:
            c.soft('ell', 1600, 180, 160, 160, fill=(255, 250, 220, 70), ol=None); c.ell(1600, 180, 60, 60, fill=(255, 236, 170, 255), ol=None)
            for cx, cy in ((300, 150), (900, 110), (1250, 210)):
                for i in range(5):
                    c.ell(cx + (i - 2) * 50, cy + (i % 2) * 14, 60, 40, fill=(255, 255, 255, 240), ol=None)
        rnd = random.Random(8)
        x = -40
        while x < W:
            w = rnd.randint(160, 280); h = rnd.randint(260, 560)
            col = (54, 60, 96, 255) if night else rnd.choice([(170, 180, 200, 255), (196, 186, 170, 255), (150, 166, 186, 255), (210, 200, 190, 255)])
            lit = (40, 46, 70, 255) if night else (150, 200, 235, 255)
            if name == 'construction' and 700 < x < 1300:
                x += w; continue
            building(c, x, w, h, 860, col, lit, rnd.randint(0, 999), night)
            x += w + rnd.randint(10, 40)
        if name == 'construction':
            c.line([(980, 860), (980, 160)], fill=(240, 190, 40, 255), w=18)
            c.line([(700, 180), (1500, 180)], fill=(240, 190, 40, 255), w=16)
            c.line([(1400, 180), (1400, 420)], fill=(60, 60, 60, 255), w=4); c.rr(1370, 420, 1430, 470, 6, fill=(120, 120, 130, 255), w=4)
            for k in range(4):
                c.rr(760, 860 - (k + 1) * 110, 1220, 860 - k * 110, 2, fill=None, ol=(150, 150, 160, 255), w=8)
        floor_band(c, 860, (90, 92, 100, 255) if not night else (40, 42, 56, 255), (200, 200, 200, 255) if not night else (80, 84, 100, 255), lines=False)
        c.poly([(0, 900), (W, 900), (W, H), (0, H)], fill=(170, 170, 170, 255) if not night else (70, 72, 86, 255), ol=None)
        base.alpha_composite(c.done()[0])
        return vignette(base, 0.3)
    if name in ('countryside', 'desert'):
        desert = name == 'desert'
        base = vgrad((110, 180, 240), (240, 220, 190)) if not desert else vgrad((130, 190, 240), (250, 220, 170))
        c.ell(300, 180, 70, 70, fill=(255, 236, 170, 255), ol=None)
        if desert:
            c.poly([(0, 760), (400, 600), (800, 720), (1300, 560), (1920, 740), (1920, 1080), (0, 1080)], fill=(226, 180, 110, 255), ol=None)
            c.poly([(0, 880), (600, 800), (1300, 880), (1920, 820), (1920, 1080), (0, 1080)], fill=(236, 196, 128, 255), ol=None)
            for x in (420, 1500):
                c.rr(x - 18, 700, x + 18, 900, 16, fill=(70, 140, 80, 255), w=4)
                c.rr(x - 70, 760, x - 40, 820, 12, fill=(70, 140, 80, 255), w=4); c.rr(x + 40, 740, x + 70, 800, 12, fill=(70, 140, 80, 255), w=4)
        else:
            c.poly([(0, 700), (500, 560), (1000, 680), (1500, 540), (1920, 660), (1920, 1080), (0, 1080)], fill=(110, 170, 90, 255), ol=None)
            c.poly([(0, 860), (700, 780), (1400, 860), (1920, 800), (1920, 1080), (0, 1080)], fill=(130, 190, 100, 255), ol=None)
            for x, s in ((250, 1.0), (1650, 1.2), (1420, 0.8)):
                c.rr(x - 14 * s, 780 - 120 * s, x + 14 * s, 880, 6, fill=(120, 80, 50, 255), w=4)
                c.ell(x, 720 - 120 * s, 90 * s, 80 * s, fill=(70, 140, 70, 255), w=4)
        base.alpha_composite(c.done()[0])
        return vignette(base, 0.25)
    raise KeyError(name)


# ------------------------------------------------------------ ícones para as legendas visuais
@lru_cache(None)
def icon(name, sc=1.0):
    c = Cv(-120, -120, 120, 120, sc)
    if name == 'bulb':
        c.ell(0, -20, 70, 70, fill=(255, 220, 80, 255), w=6)
        c.rr(-30, 40, 30, 90, 8, fill=(170, 176, 186, 255), w=5)
        c.line([(-20, -10), (0, 20), (20, -10)], fill=(200, 140, 30, 255), w=5)
    elif name == 'gear':
        for k in range(8):
            a = k * math.pi / 4
            c.rr(-16 + 80 * math.cos(a) - 0, -16 + 80 * math.sin(a), 16 + 80 * math.cos(a), 16 + 80 * math.sin(a), 6, fill=(150, 160, 176, 255), w=5)
        c.ell(0, 0, 76, 76, fill=(150, 160, 176, 255), w=6); c.ell(0, 0, 28, 28, fill=(60, 66, 80, 255), w=5)
    elif name == 'warning':
        c.poly([(0, -90), (-95, 75), (95, 75)], fill=(250, 200, 50, 255), w=7)
        c.text(0, 20, '!', 110, fill=(30, 30, 30, 255), path=FBL)
    elif name == 'check':
        c.ell(0, 0, 90, 90, fill=(70, 190, 110, 255), w=6); c.line([(-40, 0), (-10, 32), (45, -30)], fill=(255, 255, 255, 255), w=16)
    elif name == 'cross':
        c.ell(0, 0, 90, 90, fill=(230, 70, 70, 255), w=6)
        c.line([(-35, -35), (35, 35)], fill=(255, 255, 255, 255), w=16); c.line([(35, -35), (-35, 35)], fill=(255, 255, 255, 255), w=16)
    elif name == 'question':
        c.ell(0, 0, 90, 90, fill=(80, 140, 230, 255), w=6); c.text(0, 4, '?', 120, fill=(255, 255, 255, 255), path=FBL)
    elif name == 'clock':
        c.ell(0, 0, 90, 90, fill=(250, 250, 250, 255), w=7); c.line([(0, 0), (0, -55)], w=8); c.line([(0, 0), (40, 18)], w=8)
    elif name == 'money':
        c.rr(-100, -55, 100, 55, 12, fill=(110, 190, 110, 255), w=6); c.ell(0, 0, 36, 36, fill=(80, 160, 90, 255), w=5); c.text(0, 2, '$', 52, fill=(255, 255, 255, 255), path=FBL)
    elif name == 'globe':
        c.ell(0, 0, 90, 90, fill=(70, 140, 220, 255), w=6)
        c.ell(-20, -20, 40, 28, fill=(90, 180, 100, 255), ol=None); c.ell(30, 30, 30, 22, fill=(90, 180, 100, 255), ol=None)
        c.ell(0, 0, 90, 90, fill=None, w=6)
    elif name == 'rocket':
        c.poly([(0, -100), (40, -20), (40, 60), (-40, 60), (-40, -20)], fill=(240, 240, 245, 255), w=6)
        c.ell(0, -10, 18, 18, fill=(80, 150, 230, 255), w=5)
        c.poly([(-40, 20), (-75, 75), (-40, 60)], fill=(230, 70, 70, 255), w=5); c.poly([(40, 20), (75, 75), (40, 60)], fill=(230, 70, 70, 255), w=5)
        c.poly([(-24, 60), (0, 110), (24, 60)], fill=(255, 170, 50, 255), w=4)
    elif name == 'book':
        c.rr(-90, -60, 0, 70, 8, fill=(200, 70, 60, 255), w=5); c.rr(0, -60, 90, 70, 8, fill=(220, 90, 70, 255), w=5)
        for y in (-30, 0, 30): c.line([(-70, y), (-20, y)], fill=(255, 230, 220, 255), w=4); c.line([(20, y), (70, y)], fill=(255, 230, 220, 255), w=4)
    elif name == 'heart':
        c.ell(-36, -20, 46, 44, fill=(230, 70, 90, 255), ol=None); c.ell(36, -20, 46, 44, fill=(230, 70, 90, 255), ol=None)
        c.poly([(-80, 0), (80, 0), (0, 90)], fill=(230, 70, 90, 255), ol=None)
    elif name == 'bridge':
        c.line([(-110, 40), (110, 40)], w=12); c.arc(0, 60, 100, 90, 180, 360, w=10)
        for x in (-60, -20, 20, 60): c.line([(x, 40), (x, -10 - 40 * (1 - abs(x) / 100))], w=5)
    elif name == 'building':
        c.rr(-60, -100, 60, 100, 6, fill=(170, 180, 200, 255), w=6)
        for y in range(-80, 80, 36):
            for x in (-38, 0, 38): c.rr(x - 12, y, x + 12, y + 22, 3, fill=(120, 190, 240, 255), ol=None)
    elif name == 'atom':
        for a in (0, 60, 120):
            im = Image.new('RGBA', c.im.size, (0, 0, 0, 0))
        c.ell(0, 0, 100, 36, fill=None, ol=(90, 160, 240, 255), w=6); c.ell(0, 0, 36, 100, fill=None, ol=(90, 160, 240, 255), w=6)
        c.ell(0, 0, 16, 16, fill=(230, 80, 80, 255), w=4)
    else:
        c.ell(0, 0, 80, 80, fill=(200, 200, 210, 255), w=6)
    return c.done()


ICONS = ['bulb', 'gear', 'warning', 'check', 'cross', 'question', 'clock', 'money', 'globe', 'rocket', 'book', 'heart', 'bridge', 'building', 'atom']
