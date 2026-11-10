"""Motor de vídeo: roteiro JSON -> quadros (16:9 cinema ou 9:16)."""
import math, random, json, os, bisect
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from gfx import *
import chars
from chars import draw_char, gesture, EXPR
from bgs import BG, INFO, icon

FPS = 30
VO = 0.08
MODES = {'h': (1920, 1080), 'v': (1080, 1920)}
BAR = 132
NARR_COL = (150, 160, 180)


class Line: pass


class Story:
    def __init__(self, path, voice_dir):
        self.d = json.load(open(path))
        self.voice_dir = voice_dir
        for cid, spec in self.d['cast'].items():
            chars.register(cid, spec)
        vj = os.path.join(voice_dir, 'durs.json')
        self.voice = {int(k): v for k, v in json.load(open(vj)).items()} if os.path.exists(vj) else {}
        self.lines = []; self.scenes = []
        f = 0; i = 0
        for si, sc in enumerate(self.d['scenes']):
            sc = dict(sc); sc['i'] = si
            sc.setdefault('cast', []); sc.setdefault('mood', 'calm'); sc.setdefault('expr', 'neutral')
            n = len(sc['cast'])
            xs = {0: [], 1: [960], 2: [640, 1280], 3: [480, 960, 1440]}[min(n, 3)]
            gy, fl, _ = INFO[sc['bg']]
            sc['layout'] = [(cid, xs[k], gy - (20 if fl else 0), 1.0, fl) for k, cid in enumerate(sc['cast'][:3])]
            src_lines = sc['lines']; sc['lines'] = []
            for L in src_lines:
                ln = Line(); ln.i = i; ln.scene = sc; ln.spk = L['spk']; ln.text = L['text']; ln.ex = L
                ln.voice = self.voice.get(i)
                if ln.voice:
                    d = max(1.4, VO + ln.voice['dur'] + (0.22 if ln.spk == 'N' else 0.3))
                else:
                    d = max(2.2, len(ln.text) / (15 if ln.spk == 'N' else 13.5) + 0.6)
                if L.get('hold'): d += float(L['hold'])
                ln.f0 = f; ln.f1 = f + int(round(d * FPS)); f = ln.f1
                ln.start = ln.f0 / FPS; ln.dur = (ln.f1 - ln.f0) / FPS
                ln.sdur = ln.voice['dur'] if ln.voice else max(0.8, ln.dur - 0.6)
                self.lines.append(ln); sc['lines'].append(ln); i += 1
            self.scenes.append(sc)
        # cartão final
        ln = Line(); ln.i = i; ln.scene = self.scenes[-1]; ln.spk = 'END'; ln.text = ''; ln.ex = {'endcard': True}
        ln.voice = None; ln.f0 = f; ln.f1 = f + int(3.5 * FPS); ln.start = f / FPS; ln.dur = 3.5; ln.sdur = 0.5
        self.lines.append(ln); self.scenes[-1]['lines'].append(ln)
        self.total_f = ln.f1
        self.starts = [l.f0 for l in self.lines]
        for sc in self.scenes:
            sc['f0'] = sc['lines'][0].f0; sc['f1'] = sc['lines'][-1].f1

    def line_at(self, gf):
        k = bisect.bisect_right(self.starts, gf) - 1
        return self.lines[max(0, min(k, len(self.lines) - 1))]

    def col(self, spk):
        if spk in self.d['cast']: return tuple(self.d['cast'][spk]['color'])
        return NARR_COL


def word_time(ln, word):
    idx = ln.text.find(word)
    if idx < 0: return ln.start
    return ln.start + VO + ln.sdur * idx / max(1, len(ln.text))


VOW = set('aáàâãeéêoóôõ')


def mouth_level(ln, tl):
    if ln.voice:
        env = ln.voice['env']; k = int((tl - VO) * FPS)
        if k < 0 or k >= len(env): return 0
        v = max(env[k], 0.6 * env[min(k + 1, len(env) - 1)])
        return 3 if v > 0.2 else 2 if v > 0.12 else 1 if v > 0.045 else 0
    n = len(ln.text); i = min(n - 1, int(max(0, tl - VO) / ln.sdur * n)); ch = ln.text[i].lower(); q = int(tl * 13)
    if ch in VOW: return 3 if q % 3 else 2
    if ch.isalpha(): return 1 if q % 2 else 2
    return 0


def wrap(text, f, maxw):
    words = text.split(' '); out = []; cur = ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if f.getlength(t) <= maxw or not cur: cur = t
        else: out.append(cur); cur = w
    if cur: out.append(cur)
    return out


# ------------------------------------------------------------ pose do elenco
SEEDS = {}


def seed_of(cid):
    if cid not in SEEDS: SEEDS[cid] = (sum(map(ord, cid)) % 37) / 7.0
    return SEEDS[cid]


def act_for(cid, ln):
    sc = ln.scene; de = sc['expr']
    if ln.spk == cid: return (ln.ex.get('g', 'talk'), ln.ex.get('e', de))
    a = ln.ex.get('acts', {}).get(cid)
    if a: return tuple(a)
    if ln.ex.get('all_e'): return ('idle', ln.ex['all_e'])
    return ('idle', de)


def pose_for(S, ln, tl, t, cid, x, layout):
    seed = seed_of(cid)
    g, e = act_for(cid, ln)
    talking = ln.spk == cid and VO - 0.05 <= tl < VO + ln.sdur
    la, ra = gesture(g, t, talking, seed)
    prev = S.lines[ln.i - 1] if ln.i > 0 else None
    if prev is not None and prev.scene is ln.scene and tl < 0.35:
        pg, _ = act_for(cid, prev)
        if pg != g:
            pla, pra = gesture(pg, t, False, seed); k = ease(tl / 0.35)
            la, ra = lerp(pla, la, k), lerp(pra, ra, k)
    if e not in EXPR: e = 'neutral'
    brows, rmouth, reyes = EXPR[e]
    mouth = str(mouth_level(ln, tl)) if talking else rmouth
    eyes = reyes
    if talking and eyes == 'happy': eyes = 'open'
    if eyes in ('open', 'wide') and ((t + seed * 1.7) % 3.6) < 0.13: eyes = 'closed'
    xs = {c[0]: c[1] for c in layout}
    if ln.spk in xs and ln.spk != cid:
        look = 1 if xs[ln.spk] > x else -1
    else:
        others = sorted([(abs(x2 - x), x2) for c2, x2 in xs.items() if c2 != cid])
        if others:
            tgt = others[0][1] if (ln.spk == cid or int((t + seed) / 2.6) % 2 == 0) else others[-1][1]
            look = 1 if tgt > x else -1
        else:
            look = 0
    tilt = (3.2 * math.sin(t * 2.3 + seed)) if talking else 1.5 * math.sin(t * 0.8 + seed)
    return dict(la=la, ra=ra, tilt=tilt, eyes=eyes, look=look, mouth=mouth, brows=brows, turn=look,
                fog=False), g, talking


# ------------------------------------------------------------ câmera
@lru_cache(None)
def _shot(S_id, i, mode):
    S = _STORIES[S_id]; ln = S.lines[i]; sc = ln.scene
    lay = sc['layout']; ids = [c[0] for c in lay]
    same = sc['lines']
    R = dict(z0=1.0, z1=1.07, c0=(960, 540), c1=(960, 540), dof=0, ots=None)
    if ln.spk in ids:
        x, gy, s_, fl = [(c[1], c[2], c[3], c[4]) for c in lay if c[0] == ln.spk][0]
        hy = gy - 300 * s_
        cl = [l for l in same if l.spk in ids]
        j = cl.index(ln)
        others = [c for c in lay if c[0] != ln.spk]
        cy = hy + (60 if mode == 'h' else 120)
        if j % 2 == 0 or not others or mode == 'v':
            z = 1.95 if mode == 'h' else 2.7
            R.update(z0=z, z1=z * 1.05, c0=(x, cy), c1=(x, cy - 8), dof=5)
        else:
            lis = min(others, key=lambda c: abs(c[1] - x))
            side = -1 if lis[1] < x else 1
            z = 1.75; off = 0.13 * 1920 / z
            R.update(z0=z, z1=z * 1.04, c0=(x + side * off, cy), c1=(x + side * off, cy - 6), dof=5, ots=(lis[0], side))
    else:
        nl = [l for l in same if l.spk not in ids]
        j = nl.index(ln) if ln in nl else 0
        if lay:
            if j % 2 == 0:
                R.update(z0=1.0, z1=1.07, c0=(960, 560), c1=(960, 560))
            else:
                xs = [c[1] for c in lay]
                R.update(z0=1.3, z1=1.36, c0=(min(xs) + 100, 580), c1=(max(xs) - 100, 580), dof=2)
            if mode == 'v':
                c = lay[(j + 1) % len(lay)]
                hy = c[2] - 300 * c[3]
                R.update(c0=(c[1], hy + 120), c1=(c[1], hy + 110))
        else:
            pan = [(900, 540), (1020, 540)] if j % 2 else [(1020, 520), (900, 560)]
            R.update(z0=1.0, z1=1.1, c0=pan[0], c1=pan[1])
        if mode == 'v':
            R.update(z0=max(R['z0'], 1.79), z1=max(R['z1'], 1.86), dof=max(R['dof'], 2))
    return R


_STORIES = {}


def cam_at(S, ln, tl, mode):
    R = _shot(id(S), ln.i, mode)
    u = ease(clamp(tl / max(0.5, ln.dur)))
    z = lerp(R['z0'], R['z1'], u)
    cx = lerp(R['c0'][0], R['c1'][0], u); cy = lerp(R['c0'][1], R['c1'][1], u)
    t = ln.start + tl
    cx += 4 * math.sin(t * 0.7) + 2 * math.sin(t * 1.9); cy += 3 * math.sin(t * 0.9 + 1)
    OW, OH = MODES[mode]
    hw, hh = OW / (2 * z), OH / (2 * z)
    return z, clamp(cx, hw, W - hw), clamp(cy, hh, H - hh), R


def world_view(fr, z, cx, cy, mode, dof):
    OW, OH = MODES[mode]
    hw, hh = OW / (2 * z), OH / (2 * z)
    box = (cx - hw, cy - hh, cx + hw, cy + hh)
    if dof > 0:
        im = fr.resize((OW // 3, OH // 3), Image.BILINEAR, box=box).filter(ImageFilter.GaussianBlur(dof / 2.2))
        return im.resize((OW, OH), Image.BICUBIC)
    return fr.resize((OW, OH), Image.BICUBIC, box=box)


def q(v, step=0.025): return round(v / step) * step


@lru_cache(None)
def post_assets(mode):
    OW, OH = MODES[mode]
    yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
    d = np.sqrt(((xx - OW / 2) / (OW / 2)) ** 2 + ((yy - OH / 2) / (OH / 2)) ** 2) / 1.414
    vig = (1 - 0.36 * np.clip(d, 0, 1) ** 2.2).astype(np.float32)
    x = np.arange(256) / 255.0
    c = x * 0.7 + (x * x * (3 - 2 * x)) * 0.3
    lut = (np.stack([np.clip(c * 1.02 + 0.02 * c * c, 0, 1), c, np.clip(c * 0.95 + 0.05 * (1 - c) ** 2 + 0.01, 0, 1)], 1) * 255).astype(np.float32)
    rng = np.random.default_rng(1)
    grains = [rng.normal(0, 3.0, (OH, OW)).astype(np.float32) for _ in range(6)]
    return vig, lut, grains


# ------------------------------------------------------------ legendas
@lru_cache(None)
def _sub_layout(S_id, i, mode):
    S = _STORIES[S_id]; ln = S.lines[i]
    OW, OH = MODES[mode]
    size = 40 if mode == 'h' else 50
    f = font(FSB, size)
    ls = wrap(ln.text, f, 1640 if mode == 'h' else 940)
    lh = int(size * 1.25)
    widths = [f.getlength(s) for s in ls]
    top = (OH - BAR / 2 - lh * len(ls) / 2) if mode == 'h' else (290 - lh * len(ls) / 2)
    words = []; ci = 0; sp = f.getlength(' ')
    for k, s in enumerate(ls):
        x = (OW - widths[k]) / 2; y = top + k * lh + lh / 2
        for w in s.split(' '):
            idx = ln.text.find(w, ci); ci = idx + len(w)
            words.append((x, y, w, idx / max(1, len(ln.text))))
            x += f.getlength(w) + sp
    box = (min((OW - w_) / 2 for w_ in widths) - 30, top - 14, max((OW + w_) / 2 for w_ in widths) + 30, top + lh * len(ls) + 14)
    return words, f, box


def draw_sub(S, out, ln, tl, mode):
    if not ln.text: return
    words, f, box = _sub_layout(id(S), ln.i, mode)
    a = clamp(tl / 0.2) * clamp((ln.dur - tl) / 0.15)
    d = ImageDraw.Draw(out)
    if mode == 'v':
        lay = Image.new('RGBA', out.size, (0, 0, 0, 0))
        ImageDraw.Draw(lay).rounded_rectangle(box, radius=24, fill=(6, 10, 20, int(170 * a)))
        out.alpha_composite(lay)
    prog = (tl - VO) / ln.sdur + 0.02
    for (x, y, w, fr_) in words:
        col = (255, 255, 255, int(255 * a)) if prog >= fr_ else (150, 160, 182, int(235 * a))
        d.text((x, y), w, font=f, fill=col, anchor='lm', stroke_width=2 if mode == 'v' else 0, stroke_fill=(0, 0, 0, int(200 * a)))
    if ln.spk != 'N':
        x0 = box[0] + 6; y0 = (box[1] + box[3]) / 2
        d.rounded_rectangle([x0 - 22, y0 - 20, x0 - 12, y0 + 20], radius=5, fill=S.col(ln.spk) + (int(255 * a),))


# ------------------------------------------------------------ elementos gráficos (camada de interface)
@lru_cache(None)
def text_sprite(s, size, path=FXB, fill=(255, 255, 255, 255), shadow=True):
    f = font(path, size)
    bb = f.getbbox(s)
    w, h = bb[2] - bb[0] + 40, bb[3] - bb[1] + 40
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    if shadow:
        sh = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((20 - bb[0] + 4, 20 - bb[1] + 6), s, font=f, fill=(0, 0, 0, 170))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(im).text((20 - bb[0], 20 - bb[1]), s, font=f, fill=fill)
    return im, (w / 2, h / 2)


@lru_cache(None)
def pill(s, col, size=34, tcol=(255, 255, 255, 255)):
    f = font(FXB, size)
    tw = f.getbbox(s)[2]
    c = Cv(0, 0, tw + 60, size + 36, 1)
    c.rr(3, 3, tw + 57, size + 33, (size + 30) / 2, fill=col, w=4)
    c.d.text(c.P((tw + 60) / 2, (size + 36) / 2), s, font=font(FXB, size * SS), fill=tcol, anchor='mm')
    im, _ = c.done()
    return im, (im.width / 2, im.height / 2)


ACCENT = (226, 120, 40, 255)


def draw_shows(S, uil, ln, tl):
    shows = ln.ex.get('show')
    if not shows: return
    if isinstance(shows, dict): shows = [shows]
    t = ln.start + tl
    k = clamp((tl - 0.15) / 0.4); s = max(0.01, ease_out_back(k))
    big = not ln.scene['layout']          # cena só com narração: elementos grandes no centro
    y = 230 if big else 200
    for sh in shows:
        if 'title' in sh:
            place(uil, text_sprite(sh['title'].upper(), 170, FBL), W / 2, 420, scale=s)
            if sh.get('sub'):
                k2 = clamp((tl - 0.7) / 0.4)
                place(uil, text_sprite(sh['sub'].upper(), 52, FXB, fill=(255, 196, 80, 255)), W / 2, 560, alpha=k2)
        if 'pill' in sh:
            place(uil, pill(sh['pill'], tuple(sh.get('color', ACCENT[:3])) + (255,), 50 if big else 38), W / 2, y, scale=s); y += 120
        if 'year' in sh:
            place(uil, text_sprite(str(sh['year']), 240 if big else 150, FBL, fill=(255, 210, 90, 255)), W / 2, (480 if big else y + 40), scale=s); y += 180
        if 'big' in sh:
            place(uil, text_sprite(sh['big'], 120, FBL), W / 2, 440, scale=s)
        if 'icon' in sh:
            if big:
                place(uil, icon(sh['icon'], 2.2), W / 2 + sh.get('dx', 0), 520 + 12 * math.sin(t * 2.5), scale=s, rot=4 * math.sin(t * 1.3))
            else:
                place(uil, icon(sh['icon'], 1.1), W / 2 + sh.get('dx', 0), y + 110 + 10 * math.sin(t * 3), scale=s); y += 260
        if 'list' in sh:
            items = sh['list']; n = len(items)
            for j, it in enumerate(items):
                tj = 0.2 + j * (ln.sdur * 0.85) / n
                kj = clamp((tl - tj) / 0.3)
                if kj <= 0: continue
                if big:
                    place(uil, pill(it, (30, 40, 70, 255), 52), W / 2, 540 - (n - 1) * 75 + j * 150, scale=max(0.01, ease_out_back(kj)))
                else:
                    xx = W / 2 + (j - (n - 1) / 2) * min(420, 1600 / n)
                    place(uil, pill(it, (30, 40, 70, 255), 36), xx, y, scale=max(0.01, ease_out_back(kj)))
            y += 100
        if 'compare' in sh:
            a_, b_ = sh['compare']
            fs_ = 56 if big else 40; yy = 520 if big else y + 20
            place(uil, pill(a_, (40, 60, 110, 255), fs_), W / 2 - 380, yy, scale=s)
            place(uil, pill(b_, (40, 60, 110, 255), fs_), W / 2 + 380, yy, scale=s)
            place(uil, pill(sh.get('sym', '≠'), (220, 60, 60, 255), fs_ + 16), W / 2, yy, scale=s)
            y += 120


def draw_endcard(S, uil, fr, ln, tl):
    k = clamp(tl / 0.6)
    fr.alpha_composite(Image.new('RGBA', (W, H), (6, 8, 18, int(235 * k))))
    ch = S.d.get('channel', 'A Peça que Faltava')
    place(uil, text_sprite(ch.upper(), 120, FBL), W / 2, 380, scale=max(0.01, ease_out_back(clamp(tl / 0.6))))
    k3 = clamp((tl - 0.6) / 0.5)
    if k3 > 0:
        place(uil, pill('INSCREVA-SE PARA MAIS HISTÓRIAS', (226, 40, 40, 255), 44), W / 2, 560, scale=max(0.01, ease_out_back(k3)))
    if S.d.get('disclaimer', True):
        place(uil, text_sprite('Animação baseada em fatos reais · falas ilustrativas', 28, FSB, fill=(160, 170, 195, 255), shadow=False), W / 2, 700, alpha=clamp((tl - 1.0) / 0.5))


def compose_ui(out, uil, mode):
    if uil.getbbox() is None: return
    if mode == 'h':
        s = 0.86
        im = uil.resize((int(W * s), int(H * s)), Image.BICUBIC)
        out.alpha_composite(im, (int(960 - W * s / 2), int(600 - 600 * s)))
    else:
        s = 0.6
        im = uil.resize((int(W * s), int(H * s)), Image.BICUBIC)
        comp(out, im, 540 - W * s / 2, 470)


# ------------------------------------------------------------ quadro
def render_frame(S, gf, mode='h', fade_override=None):
    _STORIES[id(S)] = S
    ln = S.line_at(gf); sc = ln.scene
    t = gf / FPS; tl = t - ln.start
    OW, OH = MODES[mode]
    fr = BG(sc['bg']).copy()
    uil = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    lay = sc['layout']
    cast = []
    shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); shd = ImageDraw.Draw(shadow)
    for (cid, x, gy, s_, fl) in lay:
        P, g, talking = pose_for(S, ln, tl, t, cid, x, lay)
        seed = seed_of(cid); dx = dy = 0
        if fl: dy = 11 * math.sin(t * 1.1 + seed * 2); dx = 5 * math.sin(t * 0.6 + seed)
        if talking: dy -= 4 * abs(math.sin(t * 5.5))
        if g == 'shiver': dx += 2.5 * math.sin(t * 53)
        if g == 'cheer': dy -= 14 * abs(math.sin(t * 7))
        fy = INFO[sc['bg']][0] + (40 if fl else 4)
        hgt = max(0, fy - (gy + dy)); kk = 1 / (1 + hgt / 60); rw = 95 * s_ * (0.7 + 0.3 * kk)
        shd.ellipse([x + dx - rw, fy - 16, x + dx + rw, fy + 16], fill=(0, 0, 0, int(150 * kk)))
        cast.append((cid, x + dx, gy + dy, s_, P))
    if cast:
        fr.alpha_composite(shadow.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BILINEAR))
    if ln.ex.get('endcard'):
        draw_endcard(S, uil, fr, ln, tl)
    else:
        draw_shows(S, uil, ln, tl)
    z, cx, cy, R = cam_at(S, ln, tl, mode)
    if ln.ex.get('endcard'): z, cx, cy, R = 1.0 if mode == 'h' else 1.78, 960, 540, dict(dof=4, ots=None)
    out = world_view(fr, z, cx, cy, mode, R['dof']).convert('RGBA')
    if not ln.ex.get('endcard'):
        skip = R['ots'][0] if (R.get('ots') and mode == 'h') else None
        for (cid, x, y, s_, P) in sorted(cast, key=lambda c: c[2]):
            if cid == skip: continue
            X = (x - cx) * z + OW / 2; Y = (y - cy) * z + OH / 2
            if -400 < X < OW + 400: draw_char(out, cid, X, Y, q(s_ * z), P)
        if R.get('ots') and mode == 'h':
            lid, side = R['ots']
            for (cid, x, y, s_, P) in cast:
                if cid != lid: continue
                big = q(s_ * z * 1.45)
                layer = Image.new('RGBA', (OW, OH), (0, 0, 0, 0))
                PP = dict(P); PP['look'] = -side; PP['turn'] = -side
                if PP['mouth'] in ('0', '1', '2', '3'): PP['mouth'] = 'smile'
                draw_char(layer, cid, OW * (0.03 if side < 0 else 0.97), OH * 0.66 + 300 * big, big, PP)
                layer = layer.resize((OW // 4, OH // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3)).resize((OW, OH), Image.BICUBIC)
                out.alpha_composite(layer)
    compose_ui(out, uil, mode)
    arr = np.asarray(out.convert('RGB')).astype(np.float32)
    vig, lut, grains = post_assets(mode)
    for ch in range(3):
        arr[..., ch] = np.interp(arr[..., ch], np.arange(256), lut[:, ch])
    arr *= vig[..., None]
    arr += grains[gf % 6][..., None]
    if fade_override is not None:
        fade = fade_override
    else:
        fade = min(1.0, (gf - sc['f0'] + 1) / (0.3 * FPS), (sc['f1'] - gf) / (0.3 * FPS))
        if sc['i'] == 0: fade = min(1.0, (sc['f1'] - gf) / (0.3 * FPS), (gf + 1) / 8)
    arr *= max(0.0, min(1.0, fade))
    if mode == 'h':
        arr[:BAR] = 0; arr[OH - BAR:] = 0
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert('RGBA')
    draw_sub(S, out, ln, tl, mode)
    return np.asarray(out.convert('RGB'))
