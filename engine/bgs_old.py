import math, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from gfx import *
from chars import prop

def vgrad(c1, c2, w=W, h=H):
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(c1, float)[None, None, :] * (1 - t) + np.array(c2, float)[None, None, :] * t
    a = np.repeat(a, w, axis=1)
    rgb = np.clip(a, 0, 255).astype(np.uint8)
    im = Image.fromarray(rgb, 'RGB').convert('RGBA')
    return im


def vignette(im, strength=0.45):
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 1.414
    f = 1 - strength * np.clip(d, 0, 1) ** 2
    a = np.asarray(im.convert('RGB')).astype(float) * f[..., None]
    return Image.fromarray(a.astype(np.uint8)).convert('RGBA')


def stars(c, n, seed, x0=0, y0=0, x1=W, y1=H, inside=None):
    rnd = random.Random(seed)
    k = 0
    while k < n:
        x = rnd.uniform(x0, x1); y = rnd.uniform(y0, y1)
        if inside and not inside(x, y): continue
        k += 1
        r = rnd.choice([1.0, 1.2, 1.5, 1.8, 2.4, 3.2]) * (1 if rnd.random() < 0.9 else 1.5)
        b = rnd.randint(150, 255)
        col = (b, b, min(255, b + 20), 255) if rnd.random() < 0.7 else (255, rnd.randint(200, 240), 180, 255)
        c.ell(x, y, r, r, fill=col, ol=None)


def nebula(base, seed, cols):
    rnd = random.Random(seed)
    lay = Image.new('RGBA', (W // 4, H // 4), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(14):
        x = rnd.uniform(0, W / 4); y = rnd.uniform(0, H / 4); r = rnd.uniform(40, 120)
        col = rnd.choice(cols)
        d.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=col + (rnd.randint(18, 40),))
    lay = lay.filter(ImageFilter.GaussianBlur(28)).resize((W, H), Image.BICUBIC)
    base.alpha_composite(lay)


def draw_earth(c, cx, cy, r, seed=3):
    rnd = random.Random(seed)
    c.soft('ell', cx, cy, r + 26, r + 26, fill=(90, 160, 255, 40), ol=None)
    c.soft('ell', cx, cy, r + 12, r + 12, fill=(110, 180, 255, 60), ol=None)
    c.ell(cx, cy, r, r, fill=(38, 108, 206, 255), ol=None)
    for i in range(16):
        a = rnd.uniform(0, 2 * math.pi); d = rnd.uniform(0, r * 0.75)
        rr_ = rnd.uniform(r * 0.08, r * 0.22)
        c.ell(cx + d * math.cos(a), cy + d * math.sin(a), rr_ * 1.4, rr_, fill=(72, 164, 92, 255), ol=None)
    for i in range(14):
        a = rnd.uniform(0, 2 * math.pi); d = rnd.uniform(0, r * 0.82)
        c.soft('ell', cx + d * math.cos(a), cy + d * math.sin(a), rnd.uniform(r * .1, r * .25), rnd.uniform(r * .03, r * .07),
               fill=(255, 255, 255, 150), ol=None)
    c.ell(cx, cy, r, r, fill=None, ol=(150, 210, 255, 255), w=6)


def draw_moon(c, cx, cy, r, seed=5):
    rnd = random.Random(seed)
    c.ell(cx, cy, r, r, fill=(206, 206, 212, 255), ol=None)
    for i in range(9):
        a = rnd.uniform(0, 2 * math.pi); d = rnd.uniform(0, r * 0.7); rr_ = rnd.uniform(r * .08, r * .2)
        c.ell(cx + d * math.cos(a), cy + d * math.sin(a), rr_, rr_, fill=(176, 176, 186, 255), ol=(160, 160, 170, 255), w=2)
    c.ell(cx, cy, r, r, fill=None, ol=(240, 240, 248, 255), w=4)


@lru_cache(None)
def BG(name):
    if name in ('space', 'plain', 'alone', 'crew', 'endbg'):
        base = vgrad((5, 7, 20), (16, 20, 48))
        nebula(base, 11, [(90, 60, 180), (40, 90, 200), (160, 60, 140)])
        c = Cv(0, 0, W, H, 1)
        stars(c, 520, 7)
        if name == 'space':
            draw_earth(c, 230, 990, 330)
            draw_moon(c, 1680, 200, 105)
        if name == 'alone':
            draw_earth(c, 210, 880, 70)
        if name == 'crew':
            for x in (560, 960, 1360):
                c.soft('ell', x, 962, 190, 34, fill=(140, 180, 255, 60), ol=None)
        base.alpha_composite(c.done()[0])
        if name == 'endbg':
            base = Image.blend(base, Image.new('RGBA', (W, H), (0, 0, 0, 255)), 0.25)
        return vignette(base, 0.35)
    if name in ('cabin', 'cold'):
        base = vgrad((58, 68, 90), (30, 36, 52))
        c = Cv(0, 0, W, H, 1)
        c.rr(-20, -20, W + 20, 50, 0, fill=(44, 50, 66, 255), w=4)
        for y in (22, 38):
            c.line([(0, y), (W, y)], fill=(90, 98, 116, 255), w=8)
        # janelas triangulares
        for pts in ([(560, 92), (900, 92), (770, 352)], [(1020, 92), (1360, 92), (1150, 352)]):
            c.poly(pts, fill=(6, 8, 24, 255), ol=None)
        stars(c, 70, 21, 560, 92, 1360, 352,
              inside=lambda x, y: (y > 96 and y < 345 and ((560 < x < 900 and (x - 560) / 340 > (y - 92) / 260 * 0.62 and (900 - x) / 340 > (y - 92) / 260 * 0.38)
                                                         or (1020 < x < 1360 and (x - 1020) / 340 > (y - 92) / 260 * 0.38 and (1360 - x) / 340 > (y - 92) / 260 * 0.62))))
        for pts in ([(560, 92), (900, 92), (770, 352)], [(1020, 92), (1360, 92), (1150, 352)]):
            c.poly(pts, fill=None, ol=(126, 134, 152, 255), w=18)
            c.poly(pts, fill=None, ol=OUT, w=4)
        # painéis
        def panel(x0, y0, x1, y1, seed):
            rnd = random.Random(seed)
            c.rr(x0, y0, x1, y1, 10, fill=(74, 84, 106, 255), w=4)
            for yy in range(int(y0) + 26, int(y1) - 20, 44):
                for xx in range(int(x0) + 26, int(x1) - 20, 40):
                    k = rnd.random()
                    if k < 0.45:
                        c.rr(xx - 8, yy - 12, xx + 8, yy + 12, 4, fill=(40, 46, 60, 255), w=2)
                        c.rr(xx - 4, yy - 12 + (0 if rnd.random() < .5 else 12), xx + 4, yy + (0 if rnd.random() < .5 else 12), 2, fill=(200, 204, 214, 255), ol=None)
                    elif k < 0.7:
                        c.ell(xx, yy, 11, 11, fill=(40, 46, 60, 255), w=2)
                    else:
                        c.rr(xx - 13, yy - 9, xx + 13, yy + 9, 3, fill=(30, 36, 30, 255), w=2)
        panel(30, 470, 330, 900, 1)
        panel(1600, 600, 1890, 900, 2)
        panel(380, 400, 520, 640, 3); panel(1400, 400, 1540, 640, 4)
        c.rr(1640, 330, 1900, 590, 18, fill=(84, 94, 116, 255), w=4)
        c.rr(1720, 336, 1820, 362, 6, fill=(120, 200, 255, 255), w=3)
        c.text(1770, 349, 'LM', 15, fill=(20, 30, 50, 255))
        # piso
        c.poly([(0, 930), (W, 930), (W, H), (0, H)], fill=(36, 40, 54, 255), ol=None)
        for x in range(-200, W + 200, 90):
            c.line([(x, 930), (x + (x - W / 2) * 0.4, H)], fill=(46, 52, 68, 255), w=3)
        c.line([(0, 930), (W, 930)], fill=(90, 98, 120, 255), w=5)
        base.alpha_composite(c.done()[0])
        place(base, prop('port', 1.0), 1770, 470)
        base = vignette(base, 0.5)
        if name == 'cold':
            base = Image.blend(base, Image.new('RGBA', (W, H), (40, 90, 160, 255)), 0.28)
            fr = Image.new('RGBA', (W // 4, H // 4), (0, 0, 0, 0)); d = ImageDraw.Draw(fr)
            rnd = random.Random(4)
            for i in range(60):
                side = rnd.choice(['l', 'r', 't', 'b'])
                x = {'l': 0, 'r': W / 4}.get(side, rnd.uniform(0, W / 4)); y = {'t': 0, 'b': H / 4}.get(side, rnd.uniform(0, H / 4))
                r = rnd.uniform(10, 40)
                d.ellipse([x - r, y - r, x + r, y + r], fill=(230, 245, 255, 120))
            fr = fr.filter(ImageFilter.GaussianBlur(10)).resize((W, H), Image.BICUBIC)
            base.alpha_composite(fr)
        return base
    if name in ('houston', 'tablebg'):
        base = vgrad((28, 40, 50), (14, 20, 28))
        c = Cv(0, 0, W, H, 1)
        c.rr(520, 60, 1400, 410, 14, fill=(8, 18, 16, 255), ol=(70, 76, 88, 255), w=14)
        for x in range(560, 1380, 60): c.line([(x, 76), (x, 394)], fill=(20, 48, 36, 255), w=2)
        for y in range(90, 400, 50): c.line([(536, y), (1384, y)], fill=(20, 48, 36, 255), w=2)
        pts = []
        for i in range(181):
            a = i / 180 * 2 * math.pi
            x = 960 + 330 * math.sin(a) ; y = 250 + 90 * math.sin(2 * a)
            pts.append((x, y))
        c.line(pts[45:136] , fill=(60, 220, 120, 255), w=4)
        c.line(pts[136:] + pts[:46], fill=(60, 220, 120, 255), w=4)
        c.ell(630, 250, 34, 34, fill=(40, 110, 210, 255), w=3)
        c.ell(1290, 250, 22, 22, fill=(200, 200, 206, 255), w=3)
        c.text(960, 92, 'CONTROLE DA MISSÃO · HOUSTON', 20, fill=(90, 230, 140, 255), path=FB)
        for (x0, x1) in ((80, 440), (1480, 1840)):
            c.rr(x0, 100, x1, 340, 10, fill=(10, 20, 18, 255), ol=(70, 76, 88, 255), w=10)
        rnd = random.Random(2)
        for i in range(8):
            ww = rnd.randint(120, 300)
            c.rr(1500, 124 + i * 26, 1500 + ww, 134 + i * 26, 3, fill=(60, 200, 120, 255), ol=None)
        c.rr(-10, 640, W + 10, 830, 14, fill=(196, 190, 172, 255), w=5)
        for x in range(60, W, 260):
            c.rr(x, 560, x + 200, 660, 10, fill=(60, 64, 70, 255), w=4)
            c.rr(x + 14, 572, x + 186, 648, 4, fill=(10, 26, 20, 255), ol=None)
            for j in range(4):
                c.rr(x + 24, 584 + j * 15, x + 24 + rnd.randint(50, 150), 590 + j * 15, 2, fill=(70, 210, 130, 255), ol=None)
            for j in range(6):
                c.ell(x + 30 + j * 28, 700, 7, 7, fill=rnd.choice([(230, 80, 70, 255), (250, 200, 60, 255), (120, 200, 255, 255), (220, 220, 220, 255)]), w=2)
        c.poly([(0, 830), (W, 830), (W, H), (0, H)], fill=(56, 58, 66, 255), ol=None)
        base.alpha_composite(c.done()[0])
        base = vignette(base, 0.4)
        if name == 'tablebg':
            base = base.filter(ImageFilter.GaussianBlur(9))
            base = Image.blend(base, Image.new('RGBA', (W, H), (10, 14, 22, 255)), 0.35)
            c = Cv(0, 0, W, H, 1)
            c.poly([(0, 700), (W, 700), (W, H), (0, H)], fill=(146, 102, 64, 255), ol=None)
            rnd = random.Random(9)
            for i in range(26):
                y = rnd.uniform(712, H); c.line([(0, y), (W, y + rnd.uniform(-8, 8))], fill=(126, 86, 52, 255), w=rnd.uniform(2, 5))
            c.line([(0, 700), (W, 700)], fill=(186, 140, 96, 255), w=10)
            base.alpha_composite(c.done()[0])
        return base
    if name == 'ocean':
        base = vgrad((96, 170, 236), (250, 214, 176), h=H)
        c = Cv(0, 0, W, H, 1)
        c.soft('ell', 1500, 560, 260, 260, fill=(255, 240, 200, 60), ol=None)
        c.ell(1500, 560, 80, 80, fill=(255, 236, 170, 255), ol=None)
        rnd = random.Random(3)
        for cx, cy, s in ((300, 200, 1.2), (900, 140, 0.9), (1600, 230, 1.0), (1250, 330, 0.7)):
            for i in range(6):
                c.ell(cx + rnd.uniform(-90, 90) * s, cy + rnd.uniform(-20, 20) * s, rnd.uniform(40, 70) * s, rnd.uniform(30, 46) * s, fill=(255, 255, 255, 235), ol=None)
        c.poly([(0, 720), (W, 720), (W, H), (0, H)], fill=(30, 96, 156, 255), ol=None)
        c.poly([(0, 860), (W, 860), (W, H), (0, H)], fill=(22, 78, 134, 255), ol=None)
        c.poly([(1440, 718), (1460, 690), (1560, 690), (1570, 670), (1600, 670), (1610, 690), (1700, 690), (1720, 718)], fill=(110, 120, 136, 255), ol=None)
        c.line([(0, 720), (W, 720)], fill=(170, 210, 240, 255), w=3)
        base.alpha_composite(c.done()[0])
        return base
    if name == 'co2bg':
        base = vgrad((20, 46, 60), (10, 18, 28))
        c = Cv(0, 0, W, H, 1)
        for x in range(0, W, 64):
            for y in range(0, H, 64):
                c.ell(x, y, 2, 2, fill=(40, 80, 96, 255), ol=None)
        base.alpha_composite(c.done()[0])
        return vignette(base, 0.4)
    if name == 'radio':
        base = Image.new('RGBA', (W, H))
        base.paste(BG('houston').crop((480, 0, 1440, H)), (0, 0))
        base.paste(BG('cabin').crop((480, 0, 1440, H)), (960, 0))
        c = Cv(0, 0, W, H, 1)
        c.rr(950, -10, 970, H + 10, 0, fill=(240, 244, 250, 255), ol=OUT, w=4)
        for x, txt, col in ((40, 'HOUSTON', (206, 52, 64, 255)), (1000, 'APOLLO 13', (244, 132, 40, 255))):
            c.rr(x, 30, x + 260, 86, 14, fill=col, w=4)
            c.text(x + 130, 58, txt, 26)
        base.alpha_composite(c.done()[0])
        return base
    raise KeyError(name)


