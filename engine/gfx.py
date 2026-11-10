import math, random
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080
SS = 3
OUT = (26, 30, 46, 255)
FB = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
FXB = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
FSB = '/usr/share/fonts/opentype/inter/Inter-SemiBold.otf'
FBL = '/usr/share/fonts/opentype/inter/Inter-Black.otf'


@lru_cache(None)
def font(path, size):
    return ImageFont.truetype(path, int(size))


def lerp(a, b, t): return a + (b - a) * t
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(t):
    t = clamp(t); return t * t * (3 - 2 * t)
def ease_out_back(t):
    t = clamp(t); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def mix(c1, c2, t): return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


class Cv:
    """Canvas em unidades, desenhado em supersample e reduzido (bordas suaves)."""
    def __init__(self, x0, y0, x1, y1, sc):
        self.x0, self.y0, self.sc = x0, y0, sc
        self.k = sc * SS
        self.w = int((x1 - x0) * sc) + 2; self.h = int((y1 - y0) * sc) + 2
        self.im = Image.new('RGBA', (self.w * SS, self.h * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def P(self, x, y): return ((x - self.x0) * self.k, (y - self.y0) * self.k)
    def Wd(self, w): return max(1, int(round(w * self.k)))

    def ell(self, cx, cy, rx, ry, fill=None, ol=OUT, w=5):
        self.d.ellipse([self.P(cx - rx, cy - ry), self.P(cx + rx, cy + ry)], fill=fill,
                       outline=ol, width=self.Wd(w) if ol else 0)

    def rr(self, x0, y0, x1, y1, r, fill=None, ol=OUT, w=5):
        self.d.rounded_rectangle([self.P(x0, y0), self.P(x1, y1)], radius=r * self.k, fill=fill,
                                 outline=ol, width=self.Wd(w) if ol else 0)

    def poly(self, pts, fill=None, ol=OUT, w=5):
        p = [self.P(*q) for q in pts]
        if fill: self.d.polygon(p, fill=fill)
        if ol: self.line(pts + [pts[0]], ol, w)

    def line(self, pts, fill=OUT, w=5):
        p = [self.P(*q) for q in pts]
        ww = self.Wd(w)
        self.d.line(p, fill=fill, width=ww, joint='curve')
        r = ww / 2
        for (cx, cy) in p:
            self.d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)

    def arc(self, cx, cy, rx, ry, a0, a1, fill=OUT, w=5):
        self.d.arc([self.P(cx - rx, cy - ry), self.P(cx + rx, cy + ry)], a0, a1, fill=fill, width=self.Wd(w))
        # pontas arredondadas
        r = self.Wd(w) / 2
        for a in (a0, a1):
            x = cx + (rx - w / 2) * math.cos(math.radians(a)); y = cy + (ry - w / 2) * math.sin(math.radians(a))
            px, py = self.P(x, y); self.d.ellipse([px - r, py - r, px + r, py + r], fill=fill)

    def chord(self, cx, cy, rx, ry, a0, a1, fill, ol=OUT, w=4):
        self.d.chord([self.P(cx - rx, cy - ry), self.P(cx + rx, cy + ry)], a0, a1, fill=fill,
                     outline=ol, width=self.Wd(w) if ol else 0)

    def soft(self, fn, *a, **k):
        """desenha com mistura (para cores translúcidas por cima de outras)."""
        lay = Image.new('RGBA', self.im.size, (0, 0, 0, 0))
        old_im, old_d = self.im, self.d
        self.im, self.d = lay, ImageDraw.Draw(lay)
        getattr(self, fn)(*a, **k)
        self.im, self.d = old_im, old_d
        self.im.alpha_composite(lay)

    def text(self, x, y, s, size, fill=(255, 255, 255, 255), path=FXB):
        self.d.text(self.P(x, y), s, font=font(path, size * self.k), fill=fill, anchor='mm')

    def done(self):
        im = self.im.resize((self.w, self.h), Image.LANCZOS)
        return im, (-self.x0 * self.sc, -self.y0 * self.sc)


def comp(base, im, x, y):
    x = int(round(x)); y = int(round(y))
    w, h = im.size; bw, bh = base.size
    if x >= bw or y >= bh or x + w <= 0 or y + h <= 0: return
    cx0 = max(0, -x); cy0 = max(0, -y); cx1 = min(w, bw - x); cy1 = min(h, bh - y)
    if (cx0, cy0, cx1, cy1) != (0, 0, w, h):
        im = im.crop((cx0, cy0, cx1, cy1))
    base.alpha_composite(im, (x + cx0, y + cy0))


def place(base, spr, x, y, rot=0, alpha=1.0, scale=1.0):
    im, (ax, ay) = spr
    if scale != 1.0:
        nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
        im = im.resize((nw, nh), Image.BICUBIC); ax *= scale; ay *= scale
    if rot:
        # gira em torno da âncora: expande e recalcula
        w, h = im.size
        cx, cy = w / 2, h / 2
        im2 = im.rotate(rot, resample=Image.BICUBIC, expand=True)
        dx, dy = ax - cx, ay - cy
        r = math.radians(-rot)
        ndx = dx * math.cos(r) - dy * math.sin(r); ndy = dx * math.sin(r) + dy * math.cos(r)
        ax, ay = im2.width / 2 + ndx, im2.height / 2 + ndy
        im = im2
    if alpha < 1.0:
        im = im.copy(); a = im.getchannel('A').point(lambda v: int(v * alpha)); im.putalpha(a)
    comp(base, im, x - ax, y - ay)


def fade_img(im, a):
    if a >= 1: return im
    im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * a))); return im
