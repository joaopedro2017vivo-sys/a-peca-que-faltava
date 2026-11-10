"""Sons: trilha gerada, efeitos e mixagem com as vozes."""
import math, random
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
rng = np.random.default_rng(7)
def mtof(n): return 440.0 * 2 ** ((n - 69) / 12)
def tarr(d): return np.arange(int(d * SR)) / SR


def add(buf, t0, x, gain=1.0, pan=0.0):
    if x.ndim == 1:
        l = math.cos((pan + 1) * math.pi / 4); r = math.sin((pan + 1) * math.pi / 4)
        x = np.stack([x * l * 1.414, x * r * 1.414], 1)
    i0 = int(t0 * SR)
    if i0 < 0: x = x[-i0:]; i0 = 0
    i1 = min(len(buf), i0 + len(x))
    if i1 > i0: buf[i0:i1] += x[:i1 - i0] * gain


def filt(x, kind, f, order=2):
    if kind == 'band':
        sos = signal.butter(order, [f[0] / (SR / 2), f[1] / (SR / 2)], 'bandpass', output='sos')
    else:
        sos = signal.butter(order, f / (SR / 2), kind, output='sos')
    return signal.sosfilt(sos, x)


def env(n, a, r):
    e = np.ones(n); na = max(1, int(a * SR)); nr = max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr)
    return e


def noise(d): return rng.standard_normal(int(d * SR))

CH = {
    'calm': [[57, 60, 64, 69], [53, 57, 60, 65], [48, 55, 60, 64], [55, 59, 62, 67]],
    'tense': [[50, 53, 57, 62], [46, 50, 53, 58], [43, 50, 55, 58], [45, 49, 52, 57]],
    'hope': [[53, 57, 60, 65], [55, 59, 62, 67], [57, 60, 64, 69], [48, 55, 60, 64]],
    'triumph': [[48, 55, 60, 64], [55, 59, 62, 67], [57, 60, 64, 69], [53, 57, 60, 65]],
}
BPM = 72; BEAT = 60 / BPM; BAR = BEAT * 4


def pad(notes, d):
    t = tarr(d); L = np.zeros(len(t)); R = np.zeros(len(t))
    for n in notes:
        f = mtof(n)
        for h in range(1, 7):
            a = 1 / h ** 1.5
            L += a * np.sin(2 * np.pi * f * h * 1.0023 * t + h)
            R += a * np.sin(2 * np.pi * f * h * 0.9977 * t + 2 * h)
    trem = 1 + 0.08 * np.sin(2 * np.pi * 0.25 * t)
    e = env(len(t), 0.9, 1.2) * trem
    return np.stack([L * e, R * e], 1) / (len(notes) * 2.5)


def pluck(f, d=0.9, bright=3):
    t = tarr(d)
    x = sum((1 / h ** 1.2) * np.sin(2 * np.pi * f * h * t) * np.exp(-t * (4 + h * bright)) for h in range(1, 5))
    return x * env(len(t), 0.004, 0.05)


def make_music(mood_at, TOTAL, N):
    global mus
    mus = np.zeros((N, 2))
    t = 0.0; bar = 0
    while t < TOTAL:
        m = mood_at(t + 0.1)
        ch = CH[m][bar % 4]
        add(mus, t, pad(ch, BAR + 1.3), 1.0)
        root = ch[0] - 12
        for b in range(0, 4, 2):
            tb = tarr(BEAT * 2)
            bass = np.sin(2 * np.pi * mtof(root) * tb) + 0.3 * np.sin(4 * np.pi * mtof(root) * tb)
            add(mus, t + b * BEAT, bass * np.exp(-tb * 1.2) * env(len(tb), 0.02, 0.2), 0.35)
        if m in ('hope', 'triumph', 'calm'):
            seq = [ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[2] + 12, ch[1] + 12, ch[3] + 12, ch[2] + 24, ch[3] + 12]
            step = BEAT / 2
            for k, n in enumerate(seq):
                g = 0.10 if m == 'calm' else 0.16
                add(mus, t + k * step, pluck(mtof(n)), g, pan=(-0.4 if k % 2 else 0.4))
        if m == 'tense':
            for b in range(4):
                tb = tarr(0.35)
                kick = np.sin(2 * np.pi * (48 + 40 * np.exp(-tb * 30)) * tb) * np.exp(-tb * 12)
                add(mus, t + b * BEAT, kick, 0.45)
                add(mus, t + b * BEAT + 0.22, kick, 0.25)
            tb = tarr(BAR)
            add(mus, t, filt(noise(BAR), 'band', (300, 900)) * 0.04 * env(len(tb), 1.5, 1.5), 1.0)
        if m == 'triumph':
            tb = tarr(BAR)
            bell = sum(np.sin(2 * np.pi * mtof(n + 12) * tb) for n in ch[1:]) * np.exp(-tb * 0.9)
            add(mus, t, bell * env(len(tb), 0.01, 0.3), 0.06)
        t += BAR; bar += 1
    
    # reverb simples
    ir_t = tarr(2.2)
    ir = rng.standard_normal((len(ir_t), 2)) * np.exp(-ir_t * 3.2)[:, None]
    ir[:, 0] = filt(ir[:, 0], 'low', 5000); ir[:, 1] = filt(ir[:, 1], 'low', 5000)
    wet = np.stack([signal.fftconvolve(mus[:, c], ir[:, c])[:N] for c in range(2)], 1)
    mus = mus + wet * 0.018
    mus /= np.max(np.abs(mus)) + 1e-9
    return mus

# ------------------------------------------------------------ efeitos
def whoosh(d=0.8):
    n = noise(d); tt = tarr(d)
    out = np.zeros(len(n))
    for k, fc in enumerate(np.linspace(300, 3000, 8)):
        seg = slice(int(k * len(n) / 8), int((k + 1) * len(n) / 8))
        out[seg] = filt(n, 'band', (fc * 0.7, fc * 1.3))[seg]
    return out * np.sin(np.pi * tt / d) ** 2


def pop(f0=500, f1=1100, d=0.12):
    tt = tarr(d)
    f = np.linspace(f0, f1, len(tt))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 28)


def tick():
    tt = tarr(0.06)
    return np.sin(2 * np.pi * 1800 * tt) * np.exp(-tt * 90) * 0.6 + filt(noise(0.06), 'high', 3000) * np.exp(-tt * 120) * 0.3


def boom(d=3.0):
    tt = tarr(d)
    low = np.sin(2 * np.pi * np.cumsum(30 + 70 * np.exp(-tt * 3)) / SR) * np.exp(-tt * 1.6)
    n = filt(noise(d), 'low', 900) * np.exp(-tt * 2.2) * 2.0
    crack = filt(noise(d), 'high', 1500) * np.exp(-tt * 9) * 0.8
    return np.tanh((low * 1.4 + n + crack) * 1.4)


def tone(f, d, a=0.005, r=0.02):
    tt = tarr(d); return np.sin(2 * np.pi * f * tt) * env(len(tt), a, r)


def alarm(n=3):
    out = []
    for i in range(n):
        out.append(np.concatenate([tone(760, 0.18) * 0.7 + tone(1520, 0.18) * 0.2, np.zeros(int(0.07 * SR)), tone(560, 0.18) * 0.7, np.zeros(int(0.25 * SR))]))
    return np.concatenate(out)


def static(d):
    tt = tarr(d)
    x = filt(noise(d), 'band', (700, 3500)) * 0.5
    cr = (rng.random(len(tt)) < 0.0015) * rng.standard_normal(len(tt)) * 3
    return (x + filt(cr, 'band', (500, 4000))) * env(len(tt), 0.05, 0.1)


def tape_rip(d=0.55):
    tt = tarr(d)
    n = filt(noise(d), 'band', (1200, 6000))
    am = (np.sin(2 * np.pi * 38 * tt) > 0.2) * 0.6 + 0.4
    cr = filt((rng.random(len(tt)) < 0.01) * rng.standard_normal(len(tt)) * 4, 'high', 2000)
    return (n * am + cr) * env(len(tt), 0.01, 0.12) * 0.8


def rustle(d=0.7):
    tt = tarr(d)
    n = filt(noise(d), 'band', (2000, 9000))
    am = np.abs(filt(noise(d), 'low', 18)) * 6
    return n * np.clip(am, 0, 1.5) * env(len(tt), 0.02, 0.15) * 0.6


def clunk():
    tt = tarr(0.6)
    return (np.sin(2 * np.pi * 110 * tt) * np.exp(-tt * 18) + 0.3 * np.sin(2 * np.pi * 740 * tt) * np.exp(-tt * 9)
            + 0.2 * np.sin(2 * np.pi * 1130 * tt) * np.exp(-tt * 12) + filt(noise(0.6), 'low', 1200) * np.exp(-tt * 40) * 0.6)


def chime(notes=(84, 88, 91, 96)):
    out = np.zeros(int(1.8 * SR))
    for k, n in enumerate(notes):
        x = pluck(mtof(n), 1.4, bright=1.5)
        i = int(k * 0.09 * SR); out[i:i + len(x)] += x
    return out


def thud():
    tt = tarr(0.3)
    return np.sin(2 * np.pi * (70 + 60 * np.exp(-tt * 25)) * tt) * np.exp(-tt * 14) + filt(noise(0.3), 'low', 600) * np.exp(-tt * 30) * 0.5


def buzz():
    tt = tarr(0.45)
    return signal.square(2 * np.pi * 110 * tt) * 0.35 * env(len(tt), 0.01, 0.06) + signal.square(2 * np.pi * 116 * tt) * 0.25 * env(len(tt), 0.01, 0.06)


def boing():
    tt = tarr(0.6)
    f = 220 + 300 * (1 - np.exp(-tt * 6))
    return np.sin(2 * np.pi * np.cumsum(f * (1 + 0.05 * np.sin(2 * np.pi * 14 * tt))) / SR) * np.exp(-tt * 4)


def splash():
    d = 2.4; tt = tarr(d)
    a = filt(noise(d), 'low', 2500) * np.exp(-tt * 2.5) * 1.6
    b = filt(noise(d), 'high', 2500) * np.exp(-tt * 4) * 0.5
    bub = np.zeros(len(tt))
    for k in range(18):
        i = int(rng.uniform(0.2, 1.8) * SR); bt = tarr(0.08); f = rng.uniform(500, 1200)
        bub[i:i + len(bt)] += np.sin(2 * np.pi * np.cumsum(np.linspace(f, f * 1.8, len(bt))) / SR) * np.exp(-bt * 40) * 0.3
    return np.tanh(a + b + bub)


def applause(d=4.0):
    tt = tarr(d)
    x = np.zeros(len(tt))
    idx = rng.integers(0, len(tt) - 2000, int(d * 220))
    for i in idx:
        x[i:i + 600] += rng.standard_normal(600) * np.exp(-np.arange(600) / 90)
    x = filt(x, 'band', (600, 5000)) * env(len(tt), 0.4, 1.6)
    return x / (np.max(np.abs(x)) + 1e-9)


def wind(d):
    tt = tarr(d)
    n = noise(d)
    out = filt(n, 'band', (250, 700)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.17 * tt)) + filt(n, 'band', (900, 1400)) * 0.25 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * tt + 1))
    return out * env(len(tt), 1.0, 1.0)


def hum(d):
    tt = tarr(d)
    return (np.sin(2 * np.pi * 60 * tt) * 0.4 + np.sin(2 * np.pi * 120 * tt) * 0.15 + filt(noise(d), 'low', 400) * 0.5) * env(len(tt), 0.8, 0.8)


def waves(d):
    tt = tarr(d)
    n = filt(noise(d), 'low', 1200)
    am = 0.35 + 0.65 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.16 * tt)) ** 2
    return n * am * env(len(tt), 0.8, 0.8)


def flutter(d):
    tt = tarr(d)
    return filt(noise(d), 'band', (200, 900)) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * tt)) * env(len(tt), 0.6, 0.6)


def quindar(f): return tone(f, 0.25) * 0.5

