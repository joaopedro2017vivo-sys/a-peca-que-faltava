"""Prepara falas geradas fora (ex.: voz clonada do dono pelo Speko) para o engine/pixel.py.
Uso: python3 engine/voz_externa.py out/ARQ fala_000.wav fala_001.wav ...   (um arquivo por fala, na ordem do roteiro)
Cria out/ARQ/voice/line_XXX.wav + durs.json; depois rode engine/pixel.py com o mesmo out/ARQ (ele pula a voz Piper)."""
import json, os, subprocess, sys
import numpy as np
from scipy.io import wavfile

out = sys.argv[1]; paths = sys.argv[2:]
vd = os.path.join(out, 'voice'); os.makedirs(vd, exist_ok=True)
CHAIN = ('aresample=48000:resampler=soxr,highpass=f=70,equalizer=f=2800:t=q:w=1.4:g=1.5,'
         'acompressor=threshold=-22dB:ratio=2.5:attack=8:release=120:makeup=2,'
         'silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse')
durs = {}
for i, p in enumerate(paths):
    fin = os.path.join(vd, f'line_{i:03d}.wav')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', p, '-af', CHAIN, '-ac', '1', fin], check=True)
    sr, x = wavfile.read(fin); x = x.astype(np.float32) / 32768
    act = x[np.abs(x) > 0.02]; x *= 0.16 / (np.sqrt(np.mean(act ** 2)) if len(act) else 0.1)
    pk = np.max(np.abs(x))
    if pk > 0.95: x *= 0.95 / pk
    wavfile.write(fin, sr, (x * 32767).astype(np.int16))
    hop = sr // 30
    durs[str(i)] = {'dur': len(x) / sr, 'env': [float(np.sqrt(np.mean(x[j:j + hop] ** 2))) for j in range(0, len(x), hop)]}
json.dump(durs, open(os.path.join(vd, 'durs.json'), 'w'))
print(f'{len(paths)} falas, {sum(v["dur"] for v in durs.values()):.1f} s')
