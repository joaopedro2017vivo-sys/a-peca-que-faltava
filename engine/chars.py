import math
from functools import lru_cache
from PIL import Image, ImageFilter, ImageChops
import numpy as np
from gfx import Cv, OUT, comp, place

SUIT = (236, 240, 246, 255)
CHARS = {
    'L': dict(kind='astro', color=(52, 122, 232), skin=(241, 198, 162), hair=(96, 64, 40)),
    'S': dict(kind='astro', color=(244, 132, 40), skin=(236, 190, 152), hair=(214, 168, 86)),
    'H': dict(kind='astro', color=(56, 176, 96), skin=(222, 168, 128), hair=(52, 40, 34)),
    'C1': dict(kind='eng', color=(206, 52, 64), skin=(216, 162, 122), hair=(70, 46, 30), glasses=True),
    'C2': dict(kind='eng', color=(46, 96, 178), skin=(150, 98, 68), hair=(28, 24, 24), glasses=False),
}
ARM_L = 106


def register(cid, spec):
    CHARS[cid] = spec
    sprites.cache_clear(); face.cache_clear(); head_img.cache_clear()


def C(c, a=255): return (c[0], c[1], c[2], a)


def shade(spr, depth=0.10, dark=0.42, hl=0.55, light=(-0.7, -1.0)):
    """dá volume: escurece a borda oposta à luz e acende a borda do lado da luz."""
    im, anc = spr
    w, h = im.size
    a = np.asarray(im.getchannel('A')).astype(np.float32) / 255
    o = max(2, int(min(w, h) * depth))
    def shifted_blur(dx, dy):
        m = Image.fromarray((a * 255).astype(np.uint8))
        m = ImageChops.offset(m, int(dx), int(dy))
        m = m.filter(ImageFilter.GaussianBlur(o * 0.8))
        return np.asarray(m).astype(np.float32) / 255
    lx, ly = light
    sh = 1 - shifted_blur(lx * o, ly * o)            # longe da luz -> sombra
    hi = 1 - shifted_blur(-lx * o * 0.5, -ly * o * 0.5)  # perto da luz -> brilho
    rgb = np.asarray(im.convert('RGB')).astype(np.float32)
    f = 1 - dark * np.clip(sh, 0, 1)
    rgb = rgb * f[..., None]
    rim = np.clip(hi, 0, 1)[..., None] * hl * np.array([255, 246, 228], np.float32)
    rgb = rgb + (255 - rgb) * (rim / 255) * 0.9
    # leve gradiente vertical (topo mais claro)
    g = np.linspace(1.06, 0.9, h, dtype=np.float32)[:, None, None]
    rgb = np.clip(rgb * g, 0, 255).astype(np.uint8)
    out = Image.fromarray(rgb).convert('RGBA'); out.putalpha(im.getchannel('A'))
    return out, anc


@lru_cache(None)
def sprites(cid, sc):
    s = CHARS[cid]; col = C(s['color']); skin = C(s['skin']); hair = C(s['hair'])
    astro = s['kind'] == 'astro'
    sp = {}
    # ---- corpo
    c = Cv(-125, -250, 125, 10, sc)
    if astro:
        c.rr(-94, -208, 94, -92, 24, fill=(160, 168, 184, 255))           # mochila
        c.rr(-56, -88, -6, -6, 18, fill=SUIT); c.rr(6, -88, 56, -6, 18, fill=SUIT)
        c.rr(-62, -34, -1, 3, 14, fill=(86, 94, 114, 255)); c.rr(1, -34, 62, 3, 14, fill=(86, 94, 114, 255))
        c.rr(-78, -220, 78, -62, 48, fill=SUIT)
        c.rr(-78, -96, 78, -80, 7, fill=(146, 154, 172, 255))
        c.rr(-40, -186, 40, -122, 12, fill=(74, 84, 108, 255))
        c.ell(-20, -164, 8, 8, fill=(238, 72, 72, 255), w=3)
        c.ell(0, -164, 8, 8, fill=(252, 210, 60, 255), w=3)
        c.ell(20, -164, 8, 8, fill=col, w=3)
        c.rr(-28, -144, 28, -134, 4, fill=(140, 220, 255, 255), ol=None)
        c.rr(-60, -230, 60, -206, 11, fill=col)                           # anel do pescoço
        c.rr(-74, -200, -48, -178, 5, fill=col, w=3)                     # emblema no ombro
    else:
        outfit = s.get('outfit', 'shirt')
        shirt = C(s.get('shirt', (246, 246, 242)))
        pants = C(s.get('pants', (44, 52, 76)))
        c.rr(-54, -90, -6, -10, 12, fill=pants); c.rr(6, -90, 54, -10, 12, fill=pants)
        c.rr(-62, -24, -2, 3, 12, fill=(30, 30, 36, 255)); c.rr(2, -24, 62, 3, 12, fill=(30, 30, 36, 255))
        c.rr(-48, -232, 48, -206, 12, fill=skin)
        if s.get('dress'):
            c.poly([(-70, -150), (70, -150), (96, -40), (-96, -40)], fill=col)
        c.rr(-76, -214, 76, -70, 42, fill=shirt if outfit != 'suit' else col)
        if outfit == 'suit':
            c.poly([(-26, -214), (26, -214), (0, -150)], fill=(246, 246, 242, 255), w=3)
            c.poly([(0, -204), (-9, -190), (-6, -150), (0, -140), (6, -150), (9, -190)], fill=(200, 40, 50, 255), w=3)
            c.line([(-26, -214), (-6, -120)], w=4); c.line([(26, -214), (6, -120)], w=4)
            c.ell(0, -108, 5, 5, fill=(230, 230, 230, 255), w=2); c.ell(0, -88, 5, 5, fill=(230, 230, 230, 255), w=2)
        elif outfit == 'lab':
            c.rr(-76, -214, 76, -30, 40, fill=(250, 250, 252, 255))
            c.poly([(-26, -214), (26, -214), (0, -160)], fill=shirt, w=3)
            c.line([(-26, -214), (-4, -150), (-4, -36)], w=4); c.line([(26, -214), (4, -150)], w=4)
            c.rr(30, -170, 58, -140, 4, fill=(240, 240, 240, 255), w=3)
            c.line([(38, -180), (38, -156)], fill=col, w=4)
            c.rr(-62, -100, -30, -70, 4, fill=(240, 240, 240, 255), w=3)
        elif outfit == 'worker':
            c.poly([(-76, -200), (-24, -214), (-14, -74), (-76, -74)], fill=(250, 130, 30, 255), w=4)
            c.poly([(76, -200), (24, -214), (14, -74), (76, -74)], fill=(250, 130, 30, 255), w=4)
            for yy in (-150, -112):
                c.rr(-74, yy, -18, yy + 10, 3, fill=(225, 228, 235, 255), ol=None)
                c.rr(18, yy, 74, yy + 10, 3, fill=(225, 228, 235, 255), ol=None)
        else:
            c.rr(-76, -90, 76, -74, 5, fill=(78, 56, 40, 255))
            if s.get('tie', True):
                c.poly([(0, -206), (-13, -192), (-9, -112), (0, -98), (9, -112), (13, -192)], fill=col, w=3)
            c.poly([(-30, -214), (0, -200), (-18, -186)], fill=shirt, w=3)
            c.poly([(30, -214), (0, -200), (18, -186)], fill=shirt, w=3)
            c.rr(28, -176, 56, -146, 4, fill=shirt, w=3)
            if s.get('badge', False):
                c.rr(-60, -160, -30, -140, 3, fill=(255, 255, 255, 255), w=3)
                c.rr(-60, -160, -30, -153, 2, fill=col, ol=None)
    sp['body'] = shade(c.done(), depth=0.09)
    # ---- braço (pivô no centro)
    L = ARM_L
    c = Cv(-L - 34, -L - 34, L + 34, L + 34, sc)
    if astro:
        c.rr(-21, -18, 21, L, 21, fill=SUIT)
        c.rr(-24, L - 40, 24, L - 26, 6, fill=col, w=4)
        c.ell(0, L + 4, 26, 26, fill=col)
        c.ell(-14, L + 10, 9, 12, fill=col, w=4)
    else:
        outfit = s.get('outfit', 'shirt')
        sleeve = {'suit': col, 'lab': (250, 250, 252, 255)}.get(outfit, C(s.get('shirt', (246, 246, 242))))
        longs = outfit in ('suit', 'lab') or s.get('long_sleeve')
        c.rr(-17, -14, 17, L, 17, fill=skin)
        c.rr(-23, -20, 23, (L - 6) if longs else 46, 21, fill=sleeve)
        c.ell(0, L + 4, 22, 22, fill=skin)
    sp['arm'] = shade(c.done(), depth=0.05, dark=0.35, hl=0.35)
    # ---- cabeça base
    c = Cv(-140, -140, 140, 140, sc)
    if astro:
        c.ell(0, 0, 108, 108, fill=(240, 244, 250, 255), w=6)
        c.ell(-109, 2, 16, 26, fill=col, w=4); c.ell(109, 2, 16, 26, fill=col, w=4)
        c.ell(0, 10, 85, 79, fill=(34, 46, 70, 255), w=5)
        c.ell(0, 12, 70, 68, fill=skin, ol=None)
        c.chord(0, -18, 64, 42, 180, 360, fill=hair, ol=None)
        c.soft('ell', -46, 26, 12, 7, fill=(240, 150, 150, 110), ol=None)
        c.soft('ell', 46, 26, 12, 7, fill=(240, 150, 150, 110), ol=None)
    else:
        hs = s.get('hairstyle', 'short')
        if hs == 'long':
            c.rr(-100, -60, 100, 110, 60, fill=hair)
        if hs != 'bald':
            c.ell(0, -22, 98, 76, fill=hair)
        c.ell(-86, 12, 18, 23, fill=skin); c.ell(86, 12, 18, 23, fill=skin)
        c.ell(0, 12, 85, 82, fill=skin)
        if hs in ('short', 'long'):
            c.chord(0, -26, 80, 50, 180, 360, fill=hair, ol=None)
        elif hs == 'bun':
            c.chord(0, -26, 80, 50, 180, 360, fill=hair, ol=None); c.ell(0, -100, 36, 30, fill=hair)
        elif hs == 'bald':
            c.ell(-84, -10, 16, 26, fill=C(s.get('hair', (90, 70, 60))), ol=None); c.ell(84, -10, 16, 26, fill=C(s.get('hair', (90, 70, 60))), ol=None)
        if s.get('beard'):
            c.chord(0, 40, 70, 52, 0, 180, fill=hair, ol=None)
        if s.get('hat') == 'hardhat':
            c.chord(0, -30, 98, 90, 180, 360, fill=(250, 205, 40, 255))
            c.rr(-112, -36, 112, -22, 7, fill=(250, 205, 40, 255))
        if s.get('headset'):
            c.arc(0, -8, 104, 104, 205, 335, fill=(58, 62, 72, 255), w=11)
            c.rr(-108, -14, -80, 36, 10, fill=(58, 62, 72, 255), w=4)
            c.line([(-94, 30), (-66, 62), (-34, 70)], fill=(58, 62, 72, 255), w=6)
            c.ell(-30, 70, 8, 8, fill=(30, 30, 36, 255), w=2)
        c.soft('ell', -48, 30, 12, 7, fill=(235, 140, 130, 100), ol=None)
        c.soft('ell', 48, 30, 12, 7, fill=(235, 140, 130, 100), ol=None)
    sp['head'] = shade(c.done(), depth=0.08, dark=0.38, hl=0.5)
    if astro:
        c = Cv(-140, -140, 140, 140, sc)
        c.ell(0, 10, 85, 79, fill=(150, 200, 255, 38), ol=None)
        c.arc(0, 10, 70, 64, 200, 245, fill=(255, 255, 255, 190), w=9)
        c.arc(0, 10, 70, 64, 254, 262, fill=(255, 255, 255, 160), w=9)
        sp['visor'] = c.done()
        c = Cv(-140, -140, 140, 140, sc)
        c.ell(0, 10, 85, 79, fill=(225, 238, 255, 95), ol=None)
        sp['fog'] = c.done()
    return sp


@lru_cache(maxsize=900)
def face(cid, sc, eyes, look, mouth, brows):
    s = CHARS[cid]
    c = Cv(-140, -140, 140, 140, sc)
    ey = 4
    dark = (24, 24, 34, 255)
    for sx in (-1, 1):
        x = sx * 27
        if eyes in ('open', 'wide'):
            rx, ry = (15, 19) if eyes == 'wide' else (13, 16)
            c.ell(x, ey, rx, ry, fill=(255, 255, 255, 255), w=3)
            pr = 6 if eyes == 'wide' else 8
            c.ell(x + look * 4, ey + 2, pr, pr + 1, fill=dark, ol=None)
            c.ell(x + look * 4 - 3, ey - 2, 2.6, 2.6, fill=(255, 255, 255, 255), ol=None)
        elif eyes == 'closed':
            c.arc(x, ey, 12, 7, 15, 165, w=4)
        elif eyes == 'happy':
            c.arc(x, ey + 7, 12, 11, 205, 335, w=5)
        # sobrancelhas
        bc = (60, 44, 34, 255) if s['kind'] == 'astro' else C(s['hair'])
        if brows == 'neutral':
            c.line([(x - 12, -20), (x + 12, -22)], fill=bc, w=5)
        elif brows == 'worried':
            c.line([(x + sx * 12, -17), (x - sx * 11, -29)], fill=bc, w=5)
        elif brows == 'determined':
            c.line([(x + sx * 12, -29), (x - sx * 11, -18)], fill=bc, w=5)
        elif brows == 'up':
            c.line([(x - 12, -30), (x + 12, -32)], fill=bc, w=5)
    if s.get('lashes'):
        for sx in (-1, 1):
            c.line([(sx * 27 + sx * 10, -12), (sx * 27 + sx * 18, -18)], w=3)
    if s.get('glasses'):
        for sx in (-1, 1):
            c.ell(sx * 27, 3, 22, 20, fill=None, ol=(40, 40, 50, 255), w=4)
        c.line([(-6, 0), (6, 0)], fill=(40, 40, 50, 255), w=4)
    my = 40
    red = (128, 34, 46, 255)
    if mouth == 'smile':
        c.arc(0, my - 8, 15, 10, 25, 155, w=5)
    elif mouth == 'frown':
        c.arc(0, my + 6, 13, 8, 205, 335, w=5)
    elif mouth == 'flat':
        c.line([(-10, my), (10, my)], w=5)
    elif mouth == 'grin':
        c.chord(0, my - 6, 20, 17, 0, 180, fill=red, w=4)
        c.chord(0, my - 6, 15, 7, 0, 180, fill=(255, 255, 255, 255), ol=None)
    elif mouth == 'O':
        c.ell(0, my, 9, 11, fill=red, w=4)
    elif mouth == 'chatter':
        c.rr(-14, my - 6, 14, my + 6, 4, fill=(255, 255, 255, 255), w=4)
        c.line([(-6, my - 6), (-6, my + 6)], w=2); c.line([(5, my - 6), (5, my + 6)], w=2)
    else:
        m = int(mouth)
        rx, ry = [(11, 4), (11, 6), (13, 10), (15, 14)][m]
        c.ell(0, my, rx, ry, fill=red, w=4)
        if m >= 2:
            c.ell(0, my + ry * 0.45, rx * 0.6, ry * 0.36, fill=(232, 112, 122, 255), ol=None)
    return c.done()


@lru_cache(maxsize=500)
def head_img(cid, sc, eyes, look, mouth, brows, fog=False, turn=0):
    sp = sprites(cid, sc)
    im, anc = sp['head']
    im = im.copy()
    fim = face(cid, sc, eyes, look, mouth, brows)[0]
    if turn:
        fim = ImageChops.offset(fim, int(turn * 11 * sc), 0)
    im.alpha_composite(fim)
    if 'visor' in sp:
        if fog: im.alpha_composite(sp['fog'][0])
        im.alpha_composite(sp['visor'][0])
    return im, anc


EXPR = {  # brows, mouth em repouso, olhos em repouso
    'neutral': ('neutral', 'smile', 'open'),
    'happy': ('up', 'grin', 'happy'),
    'worried': ('worried', 'frown', 'open'),
    'surprised': ('up', 'O', 'wide'),
    'determined': ('determined', 'flat', 'open'),
    'cold': ('worried', 'chatter', 'open'),
}


def gesture(g, t, talking, seed):
    s = math.sin
    k = 1.0 if talking else 0.35
    if g == 'idle':
        return 10 + 3 * s(t * 1.3 + seed), 10 + 3 * s(t * 1.1 + seed + 1)
    if g == 'talk':
        return (20 + 16 * k * s(t * 2.6 + seed) + 8 * k * s(t * 5.3),
                34 + 26 * k * s(t * 3.2 + seed + 2) + 10 * k * s(t * 6.1))
    if g == 'pointR':
        return 14 + 4 * s(t * 2), 98 + 6 * s(t * 3)
    if g == 'pointL':
        return 98 + 6 * s(t * 3), 14 + 4 * s(t * 2)
    if g == 'shrug':
        v = 58 + 14 * abs(s(t * 2.4))
        return v, v
    if g == 'cheer':
        return 152 + 12 * s(t * 9), 152 + 12 * s(t * 9 + 1.5)
    if g == 'hold':
        return 14 + 3 * s(t * 1.4), 64 + 5 * s(t * 2)
    if g == 'shiver':
        return 26 + 4 * s(t * 47), 26 + 4 * s(t * 43 + 1)
    if g == 'work':
        return 52 + 26 * s(t * 7 + seed), 52 + 26 * s(t * 7.6 + seed + 1.7)
    if g == 'wave':
        return 12, 148 + 24 * s(t * 8)
    if g == 'open':
        v = 70 + 12 * s(t * 2.2)
        return v, v
    return 10, 10


def draw_char(fr, cid, x, y, sc, P):
    """P: dict la, ra, tilt, eyes, look, mouth, brows, hold(prop sprite), fog."""
    sp = sprites(cid, sc)
    place(fr, sp['body'], x, y)
    hands = {}
    arm_im, (ax, ay) = sp['arm']
    for side, ang in ((-1, P['la']), (1, P['ra'])):
        sx = x + side * 72 * sc; sy = y - 196 * sc
        im = arm_im.rotate(side * ang, resample=Image.BICUBIC)
        comp(fr, im, sx - ax, sy - ay)
        a = math.radians(ang)
        hands[side] = (sx + side * (ARM_L + 4) * sc * math.sin(a), sy + (ARM_L + 4) * sc * math.cos(a))
    hx, hy = x, y - 300 * sc
    him, (hax, hay) = head_img(cid, sc, P['eyes'], P['look'], P['mouth'], P['brows'], P.get('fog', False), P.get('turn', 0))
    if abs(P.get('tilt', 0)) > 0.3:
        him = him.rotate(P['tilt'], resample=Image.BICUBIC)
    comp(fr, him, hx - hax, hy - hay)
    if P.get('hold'):
        place(fr, P['hold'], hands[1][0] + 10 * sc, hands[1][1] - 20 * sc, rot=-8)
    return {'top': (hx, hy - 112 * sc), 'hands': hands}


# ---------------- objetos
@lru_cache(None)
def prop(name, sc):
    if name == 'filter':
        c = Cv(-70, -70, 70, 70, sc)
        c.rr(-62, -62, 62, 62, 12, fill=(152, 158, 172, 255))
        c.rr(-48, -36, 48, 50, 6, fill=(106, 112, 128, 255))
        for yy in range(-26, 44, 13):
            c.rr(-38, yy, 38, yy + 6, 3, fill=(64, 70, 86, 255), ol=None)
        c.rr(-62, -62, 62, -40, 10, fill=(252, 196, 60, 255))
        c.text(0, -51, 'CM', 15, fill=(40, 40, 40, 255))
        return c.done()
    if name == 'socket':
        c = Cv(-100, -100, 100, 120, sc)
        c.rr(-86, 24, 86, 100, 12, fill=(150, 156, 170, 255))
        c.ell(0, 0, 82, 82, fill=(176, 182, 196, 255), w=6)
        c.ell(0, 0, 52, 52, fill=(36, 40, 52, 255))
        for i in range(8):
            a = i * math.pi / 4
            c.ell(68 * math.cos(a), 68 * math.sin(a), 5, 5, fill=(110, 116, 130, 255), w=2)
        c.rr(-30, 66, 30, 90, 6, fill=(120, 200, 255, 255), w=3)
        c.text(0, 78, 'LM', 15, fill=(20, 30, 50, 255))
        return c.done()
    if name == 'port':
        c = Cv(-80, -80, 80, 80, sc)
        c.ell(0, 0, 66, 66, fill=(156, 162, 176, 255), w=6)
        c.ell(0, 0, 44, 44, fill=(46, 50, 64, 255))
        c.ell(0, 0, 30, 30, fill=(30, 32, 42, 255), ol=None)
        for i in range(8):
            a = i * math.pi / 4 + 0.39
            c.ell(55 * math.cos(a), 55 * math.sin(a), 4.5, 4.5, fill=(110, 116, 130, 255), w=2)
        return c.done()
    if name == 'bag':
        c = Cv(-90, -90, 90, 90, sc)
        c.poly([(-60, -70), (60, -74), (70, 66), (-66, 70)], fill=(232, 240, 252, 175), ol=(150, 165, 190, 255), w=4)
        c.line([(-30, -50), (-16, 40)], fill=(170, 185, 210, 255), w=3)
        c.line([(20, -55), (32, 30)], fill=(170, 185, 210, 255), w=3)
        c.line([(-50, 10), (40, 0)], fill=(190, 200, 220, 255), w=3)
        return c.done()
    if name == 'card':
        c = Cv(-90, -80, 90, 80, sc)
        c.poly([(-72, -52), (72, -60), (76, 54), (-68, 60)], fill=(210, 172, 116, 255))
        c.line([(-2, -56), (4, 57)], fill=(160, 124, 78, 255), w=4)
        return c.done()
    if name == 'hose':
        c = Cv(-110, -80, 110, 80, sc)
        pts = [(-80 + i * 4, 24 * math.sin(i * 0.07) - 20 * math.sin(i * 0.035)) for i in range(41)]
        for i, (px, py) in enumerate(pts):
            c.ell(px, py, 18, 18, fill=(126, 134, 150, 255) if i % 2 else (98, 104, 120, 255), ol=OUT, w=2)
        for (px, py) in (pts[0], pts[-1]):
            c.ell(px, py, 22, 22, fill=(70, 120, 210, 255), w=4)
        return c.done()
    if name == 'tape':
        c = Cv(-100, -80, 100, 80, sc)
        c.poly([(36, 36), (92, 58), (86, 72), (30, 50)], fill=(190, 194, 202, 255), w=4)
        c.ell(0, 0, 58, 58, fill=(190, 194, 202, 255), w=5)
        c.ell(0, 0, 34, 34, fill=(150, 116, 80, 255), w=4)
        c.ell(0, 0, 26, 26, fill=(0, 0, 0, 0), ol=OUT, w=3)
        c.arc(0, 0, 47, 47, 200, 260, fill=(240, 242, 246, 255), w=4)
        return c.done()
    if name == 'co2':
        c = Cv(-70, -32, 70, 32, sc)
        c.line([(-40, 0), (40, 0)], fill=(80, 84, 96, 255), w=8)
        c.ell(-42, 0, 20, 20, fill=(236, 74, 74, 255), w=3)
        c.ell(42, 0, 20, 20, fill=(236, 74, 74, 255), w=3)
        c.ell(0, 0, 24, 24, fill=(52, 56, 68, 255), w=3)
        return c.done()
    if name == 'o2':
        c = Cv(-50, -30, 50, 30, sc)
        c.ell(-18, 0, 21, 21, fill=(236, 74, 74, 255), w=3)
        c.ell(18, 0, 21, 21, fill=(236, 74, 74, 255), w=3)
        return c.done()
    if name == 'lioh':
        c = Cv(-150, -170, 150, 170, sc)
        c.rr(-130, -150, 130, 150, 22, fill=(152, 158, 172, 255), w=6)
        c.rr(-104, -96, 104, 126, 10, fill=(100, 108, 124, 255))
        for yy in range(-80, 118, 22):
            c.rr(-88, yy, 88, yy + 10, 4, fill=(58, 64, 80, 255), ol=None)
        c.rr(-130, -150, 130, -112, 16, fill=(252, 196, 60, 255), w=6)
        c.text(0, -131, 'LiOH', 26, fill=(30, 30, 30, 255))
        return c.done()
    raise KeyError(name)


@lru_cache(None)
def adapter(stage, sc):
    """Adaptador montado em etapas. Origem no centro da caixa."""
    c = Cv(-150, -150, 150, 120, sc)
    if stage >= 1:
        c.rr(-62, -62, 62, 62, 12, fill=(152, 158, 172, 255))
        c.rr(-48, -36, 48, 50, 6, fill=(106, 112, 128, 255))
        for yy in range(-26, 44, 13):
            c.rr(-38, yy, 38, yy + 6, 3, fill=(64, 70, 86, 255), ol=None)
        c.rr(-62, -62, 62, -40, 10, fill=(252, 196, 60, 255))
    if stage >= 3:
        c.poly([(-66, -30), (66, -36), (70, 30), (-62, 34)], fill=(210, 172, 116, 255), w=4)
    if stage >= 2:
        c.soft('poly', [(-84, -84), (84, -88), (92, 84), (-90, 88)], fill=(232, 240, 252, 120), ol=(150, 165, 190, 255), w=4)
        c.soft('line', [(-40, -70), (-30, 60)], fill=(190, 200, 225, 200), w=3)
        c.soft('line', [(36, -72), (46, 50)], fill=(190, 200, 225, 200), w=3)
    if stage >= 3:
        for yy in (-60, 4, 64):
            c.poly([(-96, yy - 9), (96, yy - 13), (96, yy + 7), (-96, yy + 11)], fill=(186, 190, 198, 255), w=3)
    return c.done()
