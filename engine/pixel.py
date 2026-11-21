"""Motor "pixel": apresentador em pixel art conversando com quem assiste (formato de notícia de games).
Uso: python3 engine/pixel.py stories/ARQ.json out/ARQ
Saídas: video_16x9.mp4, short_9x16.mp4, thumb.jpg, legendas.srt, folha_16x9.jpg, folha_9x16.jpg, qa.json
Roteiro: {"slug","title","thumb_text","avatar":{...},"youtube":{...},"fontes":[...],"pronounce":[...],
          "scenes":[{"bg":"neon|room|stats|news","lines":[{"text":"...","show":{...},"sfx":"pop","e":"happy"}]}],"short":[...]}
show: {"title","sub"} {"big","sub"} {"pill"} {"list":[...]} {"compare":[a,b]}
"""
import os, sys, json, math, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make as M
import synth as Y

FPS = 30
FONT = '/usr/share/fonts/opentype/inter/Inter-Black.otf'
FONTB = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
FONTX = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'


def fnt(p, s): return ImageFont.truetype(p, s)


# ------------------------------------------------------------------ paleta / utilidades
def mix(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
def dark(c, f=0.7): return tuple(int(v * f) for v in c[:3])
def light(c, f=0.25): return tuple(int(v + (255 - v) * f) for v in c[:3])

BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def grad(w, h, stops, bands=10):
    """Gradiente vertical em faixas com dithering (cara de 16 bits)."""
    img = np.zeros((h, w, 3), np.uint8)
    ys = np.arange(h) / max(1, h - 1)
    for y in range(h):
        t = ys[y] * (len(stops) - 1); i = min(int(t), len(stops) - 2); f = t - i
        q = f * bands
        for x in range(w):
            ff = (math.floor(q) + (1 if (q % 1) > BAYER[y % 4, x % 4] else 0)) / bands
            img[y, x] = mix(stops[i], stops[i + 1], min(1, ff))
    return img


# ------------------------------------------------------------------ avatar
def avatar_frames(A):
    """Desenha o busto em pixel art (40x56). Devolve dict de sprites RGBA por estado (boca, olho)."""
    skin = tuple(A.get('skin', [214, 160, 120])); hair = tuple(A.get('hair', [40, 28, 20]))
    shirt = tuple(A.get('shirt', [40, 160, 140])); eye = tuple(A.get('eyes', [40, 26, 18]))
    style = A.get('hairstyle', 'short'); beard = A.get('beard'); glasses = A.get('glasses'); headset = A.get('headset', True)
    out = {}
    for mouth in ('closed', 'mid', 'open'):
        for eyes in ('open', 'blink'):
            W, H = 40, 56
            im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
            P = lambda x, y, c: d.point((x, y), fill=c + (255,))
            R = lambda x0, y0, x1, y1, c: d.rectangle((x0, y0, x1, y1), fill=c + (255,))
            # tronco (moletom)
            d.rounded_rectangle((3, 36, 36, 60), 8, fill=shirt + (255,))
            R(26, 38, 35, 55, dark(shirt, 0.82))
            R(14, 34, 25, 38, dark(shirt, 0.75))                  # gola/capuz
            R(16, 39, 16, 46, (235, 235, 235)); R(23, 39, 23, 46, (235, 235, 235))   # cordões
            if A.get('logo', True):
                R(17, 48, 22, 51, light(shirt, 0.5))
            # pescoço
            R(16, 30, 23, 35, dark(skin, 0.85))
            # orelhas
            R(8, 17, 9, 21, skin); R(30, 17, 31, 21, skin); P(9, 19, dark(skin, 0.8)); P(30, 19, dark(skin, 0.8))
            # cabeça
            d.rounded_rectangle((10, 6, 29, 31), 6, fill=skin + (255,))
            R(26, 12, 29, 28, dark(skin, 0.9))                    # sombra lateral
            # cabelo
            if style == 'short':
                d.rounded_rectangle((9, 3, 30, 12), 5, fill=hair + (255,)); R(9, 8, 11, 17, hair); R(28, 8, 30, 15, hair)
                for x in range(12, 28, 3): P(x, 12, hair)
            elif style == 'curly':
                for cx in range(10, 31, 4):
                    d.ellipse((cx - 3, 1, cx + 3, 9), fill=hair + (255,))
                R(9, 5, 30, 11, hair); R(9, 8, 11, 17, hair); R(28, 8, 30, 17, hair)
            elif style == 'buzz':
                d.rounded_rectangle((10, 5, 29, 10), 4, fill=dark(hair, 0.9) + (255,)); R(10, 8, 11, 14, dark(hair, 0.9)); R(28, 8, 29, 14, dark(hair, 0.9))
            elif style == 'long':
                d.rounded_rectangle((8, 3, 31, 12), 5, fill=hair + (255,)); R(7, 8, 11, 34, hair); R(28, 8, 32, 34, hair)
            elif style == 'bald':
                pass
            if style != 'bald':
                for x in range(13, 27, 4): P(x, 5, light(hair, 0.18))   # brilho
            # sobrancelhas
            R(13, 14, 16, 14, dark(hair, 0.9)); R(23, 14, 26, 14, dark(hair, 0.9))
            # olhos
            if eyes == 'open':
                R(14, 17, 15, 18, eye); R(24, 17, 25, 18, eye); P(14, 17, (255, 255, 255)); P(24, 17, (255, 255, 255))
            else:
                R(13, 18, 16, 18, dark(skin, 0.6)); R(23, 18, 26, 18, dark(skin, 0.6))
            # nariz
            P(19, 21, dark(skin, 0.75)); P(20, 22, dark(skin, 0.75))
            # barba
            if beard:
                bc = dark(hair, 1.0)
                R(11, 23, 12, 29, bc); R(27, 23, 28, 29, bc); R(12, 27, 27, 31, bc); R(15, 23, 24, 24, bc)
            # boca
            mc = (90, 30, 30)
            if mouth == 'closed':
                R(17, 26, 22, 26, mc)
            elif mouth == 'mid':
                R(17, 25, 22, 27, mc); R(18, 27, 21, 27, (200, 90, 90))
            else:
                R(17, 25, 22, 28, mc); R(18, 25, 21, 25, (245, 245, 245)); R(18, 28, 21, 28, (200, 90, 90))
            # óculos
            if glasses:
                gc = (25, 25, 30)
                d.rectangle((12, 16, 17, 20), outline=gc + (255,)); d.rectangle((22, 16, 27, 20), outline=gc + (255,)); R(18, 17, 21, 17, gc)
            # headset gamer
            if headset:
                hc = (30, 30, 36); ac = tuple(A.get('accent', [255, 70, 160]))
                d.arc((7, 0, 32, 26), 180, 360, fill=hc + (255,), width=2)
                R(6, 14, 9, 23, hc); R(30, 14, 33, 23, hc); R(7, 16, 8, 21, ac); R(31, 16, 32, 21, ac)
                R(10, 23, 11, 24, hc); R(12, 25, 14, 25, hc); R(14, 26, 15, 27, ac)    # microfone
            # contorno
            a = np.array(im); al = a[..., 3] > 0
            edge = np.zeros_like(al)
            edge[1:, :] |= al[:-1, :]; edge[:-1, :] |= al[1:, :]; edge[:, 1:] |= al[:, :-1]; edge[:, :-1] |= al[:, 1:]
            edge &= ~al
            a[edge] = (20, 16, 28, 255)
            out[(mouth, eyes)] = Image.fromarray(a)
    return out


# ------------------------------------------------------------------ cenários (pixel art original, nada de marca)
def bg_neon(w, h, t):
    img = Image.fromarray(grad(w, int(h * 0.62), [(36, 14, 70), (150, 40, 120), (255, 120, 90), (255, 200, 120)]))
    base = Image.new('RGB', (w, h), (20, 10, 40)); base.paste(img, (0, 0)); d = ImageDraw.Draw(base)
    hz = int(h * 0.62)
    # sol com listras
    cx, cy, r = int(w * 0.62), int(h * 0.46), int(h * 0.2)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 210, 110))
    for k in range(5):
        yy = cy + 4 + k * 6; d.rectangle((cx - r, yy, cx + r, yy + k // 2 + 1), fill=mix((150, 40, 120), (255, 120, 90), 0.6))
    # prédios
    rng = np.random.default_rng(7); x = 0
    while x < w:
        bw = int(rng.integers(12, 26)); bh = int(rng.integers(int(h * 0.12), int(h * 0.38)))
        col = (28 + int(rng.integers(0, 14)), 16, 52)
        d.rectangle((x, hz - bh, x + bw - 2, hz), fill=col)
        for wy in range(hz - bh + 3, hz - 2, 4):
            for wx in range(x + 2, x + bw - 4, 3):
                on = (hash((wx, wy)) + int(t * 0.7)) % 7 == 0 or (hash((wx, wy)) % 3 == 0)
                if on: d.point((wx, wy), fill=(255, 220, 140) if (wx + wy) % 5 else (120, 240, 255))
        x += bw
    # mar com reflexo
    d.rectangle((0, hz, w, h), fill=(24, 18, 60))
    for k in range(0, h - hz, 3):
        yy = hz + k; ww = max(2, int(r * (1 - k / (h - hz)) * 1.2)); off = int(2 * math.sin(t * 2 + k))
        d.line((cx - ww + off, yy, cx + ww + off, yy), fill=(255, 150, 120) if k % 2 == 0 else (200, 90, 130))
    # coqueiros
    for px, ph in ((int(w * 0.08), int(h * 0.55)), (int(w * 0.9), int(h * 0.6)), (int(w * 0.97), int(h * 0.42))):
        sway = int(1.5 * math.sin(t * 1.3 + px))
        for k in range(ph):
            xx = px + int(6 * math.sin(k / ph * 1.6)) + (sway if k > ph * 0.7 else 0)
            d.rectangle((xx, h - k, xx + 2, h - k), fill=(12, 6, 24))
        tx, ty = px + 5 + sway, h - ph
        for ang in range(0, 360, 45):
            for s in range(14):
                a = math.radians(ang); d.point((tx + int(math.cos(a) * s), ty + int(math.sin(a) * s * 0.55) + s * s // 40), fill=(12, 6, 24))
    return base


def bg_room(w, h, t):
    base = Image.new('RGB', (w, h), (34, 26, 54)); d = ImageDraw.Draw(base)
    for y in range(0, h, 2):
        d.line((0, y, w, y), fill=(38, 30, 60) if (y // 2) % 2 else (34, 26, 54))
    # janela noturna
    wx0, wy0, wx1, wy1 = int(w * 0.62), int(h * 0.08), int(w * 0.92), int(h * 0.48)
    d.rectangle((wx0, wy0, wx1, wy1), fill=(14, 12, 40)); d.rectangle((wx0, wy0, wx1, wy1), outline=(70, 60, 100), width=2)
    rng = np.random.default_rng(3)
    for _ in range(18):
        sx, sy = int(rng.integers(wx0 + 3, wx1 - 3)), int(rng.integers(wy0 + 3, wy1 - 3))
        if (int(t * 2) + sx) % 9: d.point((sx, sy), fill=(230, 230, 255))
    d.ellipse((wx1 - 18, wy0 + 5, wx1 - 8, wy0 + 15), fill=(250, 240, 200))
    d.line(((wx0 + wx1) // 2, wy0, (wx0 + wx1) // 2, wy1), fill=(70, 60, 100), width=2)
    # fita de LED
    hue = t * 0.25
    for x in range(0, w, 2):
        c = tuple(int(127 + 127 * math.sin(hue * 6.28 + x / 30 + k * 2.1)) for k in range(3))
        d.point((x, 2), fill=c); d.point((x + 1, 2), fill=c)
    # prateleira com caixinhas genéricas
    d.rectangle((int(w * 0.06), int(h * 0.3), int(w * 0.36), int(h * 0.32)), fill=(90, 60, 40))
    for k, c in enumerate([(220, 70, 70), (70, 160, 230), (240, 200, 60), (120, 210, 120), (200, 120, 220)]):
        x = int(w * 0.07) + k * 9; d.rectangle((x, int(h * 0.3) - 10 - k % 2 * 3, x + 6, int(h * 0.3) - 1), fill=c)
    # mesa + monitor
    d.rectangle((0, int(h * 0.78), w, h), fill=(60, 40, 30)); d.line((0, int(h * 0.78), w, int(h * 0.78)), fill=(90, 62, 44))
    mx0, my0, mx1, my1 = int(w * 0.6), int(h * 0.52), int(w * 0.95), int(h * 0.76)
    d.rectangle((mx0 - 2, my0 - 2, mx1 + 2, my1 + 2), fill=(18, 18, 22))
    scr = Image.fromarray(grad(mx1 - mx0, my1 - my0, [(255, 120, 90), (150, 40, 120), (40, 20, 80)], 6)); base.paste(scr, (mx0, my0))
    d.rectangle(((mx0 + mx1) // 2 - 3, my1 + 2, (mx0 + mx1) // 2 + 3, int(h * 0.78)), fill=(18, 18, 22))
    # brilho do monitor pulsando
    return base


def bg_stats(w, h, t):
    base = Image.new('RGB', (w, h), (16, 14, 30)); d = ImageDraw.Draw(base)
    off = int(t * 8) % 12
    for x in range(-12 + off, w, 12): d.line((x, 0, x, h), fill=(30, 26, 56))
    for y in range(-12 + off, h, 12): d.line((0, y, w, y), fill=(30, 26, 56))
    return base


def bg_news(w, h, t):
    base = Image.fromarray(grad(w, h, [(20, 30, 80), (60, 30, 110), (20, 16, 40)], 8)); d = ImageDraw.Draw(base)
    for k in range(6):
        x = int((k * 70 + t * 20) % (w + 80)) - 40
        d.polygon([(x, 0), (x + 20, 0), (x - 30, h), (x - 50, h)], fill=(70, 40, 130))
    d.rectangle((0, int(h * 0.8), w, h), fill=(30, 22, 60)); d.line((0, int(h * 0.8), w, int(h * 0.8)), fill=(255, 70, 160), width=2)
    return base


BGS = {'neon': bg_neon, 'room': bg_room, 'stats': bg_stats, 'news': bg_news}


# ------------------------------------------------------------------ elementos gráficos (desenhados em alta resolução)
ACC = (255, 70, 160); YEL = (255, 214, 80); CYAN = (90, 230, 255)


def box(d, xy, fill, border, s):
    x0, y0, x1, y1 = xy
    d.rectangle((x0 + s, y0 + s, x1 + s, y1 + s), fill=(0, 0, 0))          # sombra dura
    d.rectangle(xy, fill=fill); d.rectangle(xy, outline=border, width=max(2, s // 2))


def draw_show(img, show, k, area, s):
    """k: progresso 0..1 da entrada; area: (x0,y0,x1,y1) onde o gráfico pode ficar; s: escala de pixel."""
    if not show: return
    d = ImageDraw.Draw(img); x0, y0, x1, y1 = area; cx = (x0 + x1) // 2; W = x1 - x0
    pop = min(1.0, k * 1.6)
    dy = int((1 - pop) * 20 * s)
    def ctext(y, txt, f, col, maxw):
        while f.getlength(txt) > maxw and f.size > 14: f = fnt(f.path, int(f.size * 0.9))
        tw = f.getlength(txt); d.text((cx - tw / 2 + s, y + s), txt, font=f, fill=(0, 0, 0)); d.text((cx - tw / 2, y), txt, font=f, fill=col)
        return f.size
    if 'big' in show:
        sz = ctext(y0 + dy, show['big'], fnt(FONT, int(30 * s)), YEL, W * 0.95)
        if show.get('sub'): ctext(y0 + dy + int(sz * 1.15), show['sub'], fnt(FONTX, int(9 * s)), (255, 255, 255), W * 0.95)
    elif 'title' in show:
        f = fnt(FONT, int(20 * s)); sz = ctext(y0 + dy, show['title'], f, (255, 255, 255), W * 0.95)
        if show.get('sub'):
            f2 = fnt(FONTX, int(8 * s)); t = show['sub']; tw = f2.getlength(t)
            yy = y0 + dy + int(sz * 1.2)
            box(d, (cx - tw / 2 - 5 * s, yy - 2 * s, cx + tw / 2 + 5 * s, yy + f2.size + 3 * s), ACC, (255, 255, 255), s)
            d.text((cx - tw / 2, yy), t, font=f2, fill=(255, 255, 255))
    elif 'pill' in show:
        f = fnt(FONTX, int(10 * s)); t = show['pill']
        while f.getlength(t) > W * 0.85 and f.size > 14: f = fnt(FONTX, int(f.size * 0.9))
        tw = f.getlength(t)
        box(d, (cx - tw / 2 - 6 * s, y0 + dy, cx + tw / 2 + 6 * s, y0 + dy + f.size + 6 * s), (30, 20, 60), YEL, s)
        d.text((cx - tw / 2, y0 + dy + 2 * s), t, font=f, fill=YEL)
    elif 'list' in show:
        f = fnt(FONTX, int(9 * s)); items = show['list']
        while max(f.getlength(t) for t in items) > W * 0.8 and f.size > 14: f = fnt(FONTX, int(f.size * 0.9))
        lh = f.size + 8 * s; tot = lh * len(items)
        for j, t in enumerate(items):
            kk = max(0.0, min(1.0, k * len(items) * 1.4 - j))
            if kk <= 0: continue
            tw = f.getlength(t); yy = y0 + j * lh + int((1 - kk) * 10 * s)
            box(d, (cx - tw / 2 - 6 * s, yy, cx + tw / 2 + 6 * s, yy + f.size + 5 * s), (30, 20, 60), CYAN if j % 2 else ACC, s)
            d.text((cx - tw / 2, yy + 2 * s), t, font=f, fill=(255, 255, 255))
    elif 'compare' in show:
        a, b = show['compare']; f = fnt(FONTX, int(8 * s))
        while max(f.getlength(a), f.getlength(b)) > W * 0.42 and f.size > 12: f = fnt(FONTX, int(f.size * 0.9))
        bw = int(W * 0.45); hgt = f.size * 3
        for j, (t, col) in enumerate(((a, (90, 90, 120)), (b, ACC))):
            kk = max(0.0, min(1.0, k * 2.2 - j * 0.7))
            if kk <= 0: continue
            bx = x0 + j * (W - bw); yy = y0 + int((1 - kk) * 12 * s)
            box(d, (bx, yy, bx + bw, yy + hgt), col, (255, 255, 255), s)
            tw = f.getlength(t); d.text((bx + bw / 2 - tw / 2, yy + hgt / 2 - f.size / 2), t, font=f, fill=(255, 255, 255))
        fv = fnt(FONT, int(10 * s)); d.text((cx - fv.getlength('VS') / 2, y0 + hgt / 2 - fv.size / 2), 'VS', font=fv, fill=YEL)


def wrap(text, f, maxw):
    words = text.split(); lines = []; cur = ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if f.getlength(t) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines


def draw_caption(img, text, prog, cx, y, maxw, fs, s, bottom=True):
    """Legenda karaokê: palavras já faladas em branco, próximas em cinza."""
    d = ImageDraw.Draw(img); f = fnt(FONTB, fs)
    lines = wrap(text, f, maxw)
    # mostra no máximo 2 linhas por vez, acompanhando o progresso
    nw = len(text.split()); spoken = int(prog * nw + 0.5)
    groups = [lines[i:i + 2] for i in range(0, len(lines), 2)]
    cnt = 0; gi = 0
    for i, g in enumerate(groups):
        n = sum(len(l.split()) for l in g)
        if spoken <= cnt + n or i == len(groups) - 1: gi = i; break
        cnt += n
    g = groups[gi]; lh = int(fs * 1.3)
    y0 = y - lh * len(g) if bottom else y
    wmax = max(f.getlength(l) for l in g)
    d.rounded_rectangle((cx - wmax / 2 - fs * 0.5, y0 - fs * 0.25, cx + wmax / 2 + fs * 0.5, y0 + lh * len(g) + fs * 0.1), int(fs * 0.3), fill=(10, 8, 20))
    wi = cnt
    for j, l in enumerate(g):
        x = cx - f.getlength(l) / 2
        for w in l.split():
            col = (255, 255, 255) if wi < spoken else (150, 150, 170)
            d.text((x, y0 + j * lh), w, font=f, fill=col); x += f.getlength(w + ' '); wi += 1


# ------------------------------------------------------------------ montagem
def load(story_path, out):
    d = json.load(open(story_path))
    lines = []
    for si, sc in enumerate(d['scenes']):
        for L in sc['lines']:
            lines.append(dict(L, bg=sc['bg'], scene=si))
    # vozes: reaproveita o motor principal (todas as falas pelo "narrador" = voz do apresentador)
    tmp = dict(d); tmp['narrator'] = d.get('voice', {'voice': 'cadu-medium', 'speed': 0.88})
    tmp['scenes'] = [{'bg': 'studio', 'lines': [{'spk': 'N', 'text': L['text']} for L in sc['lines']]} for sc in d['scenes']]
    tp = os.path.join(out, '_voz.json'); json.dump(tmp, open(tp, 'w'), ensure_ascii=False)
    vdir = os.path.join(out, 'voice')
    if not os.path.exists(os.path.join(vdir, 'durs.json')):
        M.log('vozes'); M.make_voices(tp, out)
    durs = json.load(open(os.path.join(vdir, 'durs.json')))
    t = 0.6
    for i, L in enumerate(lines):
        L['i'] = i; L['wav'] = os.path.join(vdir, f'line_{i:03d}.wav')
        L['dur'] = durs[str(i)]['dur']; L['env'] = durs[str(i)]['env']
        L['t0'] = t; t += L['dur'] + L.get('pause', 0.25) + (0.35 if i + 1 < len(lines) and lines[i + 1]['scene'] != L['scene'] else 0)
    total = t + 1.2
    return d, lines, total


def timeline(lines, sel=None):
    """Reposiciona as falas (para o Short). Devolve lista de (linha, t0_novo) e duração."""
    seq = []; t = 0.3
    for L in lines:
        if sel is not None and L['i'] not in sel: continue
        seq.append((L, t)); t += L['dur'] + min(L.get('pause', 0.25), 0.3)
    return seq, t + 0.9


def make_audio(seq, total, path, sfx_on=True):
    sr = 48000; n = int(total * sr) + sr
    voice = np.zeros(n, np.float32); fx = np.zeros(n, np.float32)
    for L, t0 in seq:
        s_, x = wavfile.read(L['wav']); x = x.astype(np.float32) / 32768
        a = int(t0 * sr); voice[a:a + len(x)] += x[:n - a]
        if sfx_on and L.get('sfx'):
            fn = {'pop': lambda: Y.pop(), 'whoosh': lambda: Y.whoosh(), 'chime': lambda: Y.chime(), 'boing': lambda: Y.boing(),
                  'applause': lambda: Y.applause(2.5), 'buzz': lambda: Y.buzz(), 'thud': lambda: Y.thud()}.get(L['sfx'])
            if fn:
                z = np.asarray(fn(), np.float32)
                if z.ndim > 1: z = z.mean(axis=1)
                if Y.SR != sr: z = np.interp(np.arange(0, len(z), Y.SR / sr), np.arange(len(z)), z).astype(np.float32)
                b = int((t0 + L.get('sfx_at', 0.0)) * sr); fx[b:b + len(z)] += z[:max(0, n - b)] * 0.35
    # trilha chiptune original (onda quadrada + baixo + bumbo), em loop de 4 acordes
    tt = np.arange(n) / sr; bpm = 104; beat = 60 / bpm
    chords = [(57, 60, 64), (53, 57, 60), (60, 64, 67), (55, 59, 62)]
    mus = np.zeros(n, np.float32)
    step = beat / 2; nsteps = int(total / step) + 1
    for k in range(nsteps):
        ch = chords[(k // 8) % 4]; note = ch[[0, 1, 2, 1][k % 4]] + 12
        a = int(k * step * sr); b = min(n, a + int(step * 0.9 * sr))
        if a >= n: break
        tl = np.arange(b - a) / sr; f = 440 * 2 ** ((note - 69) / 12)
        sq = np.sign(np.sin(2 * np.pi * f * tl)) * np.exp(-tl * 7) * 0.05
        mus[a:b] += sq
        if k % 2 == 0:
            fb = 440 * 2 ** ((ch[0] - 24 - 69) / 12); bb = min(n, a + int(step * 1.8 * sr)); tb = np.arange(bb - a) / sr
            mus[a:bb] += (2 * ((fb * tb) % 1) - 1) * 0.045 * np.exp(-tb * 2.5)
        if k % 4 == 0:
            kb = min(n, a + int(0.18 * sr)); tk = np.arange(kb - a) / sr
            mus[a:kb] += np.sin(2 * np.pi * (110 * np.exp(-tk * 25) + 45) * tk) * np.exp(-tk * 18) * 0.22
        if k % 4 == 2:
            hb = min(n, a + int(0.05 * sr)); mus[a:hb] += np.random.default_rng(k).standard_normal(hb - a).astype(np.float32) * 0.03
    # ducking: música abaixa quando tem voz
    envv = np.convolve(np.abs(voice), np.ones(4800) / 4800, mode='same')
    duck = 1.0 - 0.55 * np.clip(envv / 0.04, 0, 1)
    fade = np.clip(np.minimum(tt / 1.0, (total - tt) / 1.5), 0, 1)
    mixd = voice + fx + mus * duck * fade * 0.9
    mixd = mixd[:int(total * sr)]
    wav = path + '.tmp.wav'; wavfile.write(wav, sr, (np.clip(mixd, -1, 1) * 32767).astype(np.int16))
    M.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ar', '48000', path])
    os.remove(wav)


def render(d, seq, total, path, audio, vertical=False):
    A = avatar_frames(d.get('avatar', {}))
    cw, ch = (180, 320) if vertical else (320, 180)
    S = 6; W, H = cw * S, ch * S
    cache = {}
    def bgimg(name, t):
        key = (name, int(t * 4))                      # cenário anima a 4 fps (jeitão retrô)
        if key not in cache:
            if len(cache) > 40: cache.clear()
            cache[key] = BGS[name](cw, ch, t)
        return cache[key]
    nf = int(total * FPS)
    proc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                             '-i', '-', '-i', audio, '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
                             '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', path], stdin=subprocess.PIPE)
    rng = np.random.default_rng(5); blinks = set()
    tb = 1.0
    while tb < total:
        blinks.update(range(int(tb * FPS), int(tb * FPS) + 4)); tb += float(rng.uniform(2.2, 5.0))
    for fi in range(nf):
        t = fi / FPS
        cur = None; nxt = None
        for L, t0 in seq:
            if t0 <= t: cur = (L, t0)
            elif nxt is None: nxt = (L, t0)
        if cur is None: cur = seq[0]
        L, t0 = cur; lt = t - t0
        canvas = bgimg(L['bg'], t).copy()
        # boca pelo envelope da voz
        ei = int(lt * FPS); amp = L['env'][ei] if 0 <= ei < len(L['env']) else 0.0
        mouth = 'open' if amp > 0.09 else 'mid' if amp > 0.035 else 'closed'
        eyes = 'blink' if fi in blinks else 'open'
        spr = A[(mouth, eyes)]
        sc = 2 if not vertical else 2
        bob = 1 if (amp > 0.12 and (fi // 4) % 2) else 0
        breath = int(math.sin(t * 2.2) > 0.6)
        sp = spr.resize((spr.width * sc, spr.height * sc), Image.NEAREST)
        if vertical:
            ax, ay = (cw - sp.width) // 2, ch - sp.height + 6
        else:
            ax, ay = (8 if L['bg'] != 'room' else 24), ch - sp.height + 8
        canvas.paste(sp, (ax, ay - bob - breath), sp)
        big = canvas.resize((W, H), Image.NEAREST)
        # gráficos
        k = min(1.0, lt / 0.5)
        if vertical:
            area = (int(W * 0.06), int(H * 0.12), int(W * 0.94), int(H * 0.45))
        else:
            area = (int(W * 0.36), int(H * 0.1), int(W * 0.96), int(H * 0.62))
        draw_show(big, L.get('show'), k, area, S)
        # legenda
        prog = min(1.0, max(0.0, lt / max(0.1, L['dur'])))
        if vertical:
            draw_caption(big, L['text'], prog, W // 2, int(H * 0.5), int(W * 0.86), 52, S, bottom=False)
        else:
            draw_caption(big, L['text'], prog, int(W * 0.62), int(H * 0.95), int(W * 0.68), 40, S)
        # marca discreta do canal
        dd = ImageDraw.Draw(big); fm = fnt(FONTX, 26 if not vertical else 30)
        dd.text((W - fm.getlength(d['channel']) - 24, 18), d['channel'], font=fm, fill=(255, 255, 255, 160))
        proc.stdin.write(big.tobytes())
        if fi % 600 == 0: M.log(f'  {os.path.basename(path)} {fi}/{nf}')
    proc.stdin.close(); proc.wait()


def thumbnail(d, path):
    A = avatar_frames(d.get('avatar', {}))
    cw, ch = 320, 180; S = 4
    c = bg_neon(cw, ch, 3.0)
    sp = A[('open', 'open')]; sp = sp.resize((sp.width * 3, sp.height * 3), Image.NEAREST)
    c.paste(sp, (6, ch - sp.height + 18), sp)
    big = c.resize((cw * S, ch * S), Image.NEAREST); dr = ImageDraw.Draw(big)
    words = d['thumb_text'].upper(); f = fnt(FONT, 92)
    if d.get('thumb_lines'):
        lines = [l.upper() for l in d['thumb_lines']]
        while max(f.getlength(l) for l in lines) > 780: f = fnt(FONT, int(f.size * 0.92))
    else:
        lines = wrap(words, f, 760)
        while len(lines) > 3: f = fnt(FONT, int(f.size * 0.9)); lines = wrap(words, f, 760)
    y = 70
    for j, l in enumerate(lines):
        x = 1280 - 40 - f.getlength(l)
        for ox, oy in ((-6, 0), (6, 0), (0, -6), (0, 6), (8, 8)): dr.text((x + ox, y + oy), l, font=f, fill=(20, 10, 30))
        dr.text((x, y), l, font=f, fill=YEL if j == 0 else (255, 255, 255)); y += int(f.size * 1.12)
    big.convert('RGB').save(path, quality=92)


def srt(seq, path):
    def ts(x): h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60; return f'{h:02d}:{m:02d}:{int(s):02d},{int((s % 1) * 1000):03d}'
    with open(path, 'w') as f:
        for n, (L, t0) in enumerate(seq, 1): f.write(f"{n}\n{ts(t0)} --> {ts(t0 + L['dur'])}\n{L['text']}\n\n")


def main():
    sp = os.path.abspath(sys.argv[1]); out = os.path.abspath(sys.argv[2]); os.makedirs(out, exist_ok=True)
    d, lines, total = load(sp, out)
    seq = [(L, L['t0']) for L in lines]
    M.log(f'duração {total:.1f} s')
    a1 = os.path.join(out, 'audio_16x9.m4a'); make_audio(seq, total, a1)
    v1 = os.path.join(out, 'video_16x9.mp4'); render(d, seq, total, v1, a1)
    sseq, stot = timeline(lines, set(d.get('short', [])) or None)
    a2 = os.path.join(out, 'audio_9x16.m4a'); make_audio(sseq, stot, a2)
    v2 = os.path.join(out, 'short_9x16.mp4'); render(d, sseq, stot, v2, a2, vertical=True)
    srt(seq, os.path.join(out, 'legendas.srt')); thumbnail(d, os.path.join(out, 'thumb.jpg'))
    M.contact_sheet(v1, os.path.join(out, 'folha_16x9.jpg')); M.contact_sheet(v2, os.path.join(out, 'folha_9x16.jpg'))
    class _S: pass
    S = _S(); S.d = d; S.lines = []
    r = M.qa(S, out, [('video_16x9', v1, total), ('short_9x16', v2, stot)])
    for L in lines:
        if L['dur'] < 0.4: r['problemas'].append(f"fala {L['i']} sem voz")
    r['ok'] = not r['problemas']; json.dump(r, open(os.path.join(out, 'qa.json'), 'w'), ensure_ascii=False, indent=1)
    M.log('QA', 'OK' if r['ok'] else 'PROBLEMAS: ' + '; '.join(r['problemas']))
    print(json.dumps(r, ensure_ascii=False))


if __name__ == '__main__':
    main()
