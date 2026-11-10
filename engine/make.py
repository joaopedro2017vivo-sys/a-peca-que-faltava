"""Gera um episódio completo a partir de um roteiro JSON.

uso: python3 make.py roteiro.json pasta_saida [--skip-video]
Saídas: video_16x9.mp4, short_9x16.mp4, thumb.jpg, legendas.srt, qa.json, folha.jpg
"""
import os, sys, json, re, subprocess, shutil, time
import numpy as np
from scipy.io import wavfile
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
VOICES = os.environ.get('CANAL_VOICES', os.path.expanduser('~/.cache/canal'))
PIPER = os.path.join(VOICES, 'piper', 'piper')
FPS = 30
NARRADOR = {'voice': 'cadu-medium', 'speed': 0.9, 'pitch': 0.0}


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def run(cmd, inp=None, env=None):
    r = subprocess.run(cmd, input=inp, capture_output=True, env=env)
    if r.returncode:
        raise RuntimeError(' '.join(cmd[:3]) + ' -> ' + r.stderr.decode(errors='ignore')[-600:])
    return r


# ------------------------------------------------------------ vozes
SUBS_DEFAULT = [('...', ', '), ('…', ', '), ('CO₂', 'cê ó dois'), ('H₂O', 'agá dois ó'), ('km/h', 'quilômetros por hora'),
                ('%', ' por cento'), ('—', ', '), ('–', ', ')]


def speech_text(t, extra):
    for a, b in list(extra) + SUBS_DEFAULT:
        t = t.replace(a, b)
    t = re.sub(r'^[,\s]+', '', t)
    return t.strip()


def make_voices(story_path, out):
    d = json.load(open(story_path))
    vdir = os.path.join(out, 'voice'); os.makedirs(vdir, exist_ok=True)
    extra = [tuple(x) for x in d.get('pronounce', [])]
    import bgs
    durs = {}; i = 0
    env = dict(os.environ, LD_LIBRARY_PATH=os.path.dirname(PIPER))
    for sc in d['scenes']:
        amb = bgs.INFO[sc['bg']][2]
        for L in sc['lines']:
            spk = L['spk']
            v = dict(NARRADOR); v.update(d.get('narrator', {}))
            if spk != 'N': v.update({k: d['cast'][spk][k] for k in ('voice', 'speed', 'pitch') if k in d['cast'][spk]})
            model = os.path.join(VOICES, f"vits-piper-pt_BR-{v['voice']}", f"pt_BR-{v['voice']}.onnx")
            raw = os.path.join(vdir, f'raw_{i:03d}.wav'); fin = os.path.join(vdir, f'line_{i:03d}.wav')
            run([PIPER, '--model', model, '--config', model + '.json', '--output_file', raw, '--length_scale', str(v['speed']),
                 '--noise_scale', '0.55', '--noise_w', '0.6', '--sentence_silence', '0.12'], speech_text(L['text'], extra).encode(), env)
            chain = ['aresample=48000:resampler=soxr', 'afftdn=nf=-32:tn=1', 'agate=threshold=0.012:ratio=3:attack=3:release=120']
            if v.get('pitch'):
                chain.append(f"rubberband=pitch={2 ** (v['pitch'] / 12):.4f}:pitchq=quality:formant=preserved")
            chain += ['highpass=f=70', 'lowpass=f=10500', 'equalizer=f=220:t=q:w=1:g=1.5', 'equalizer=f=2800:t=q:w=1.4:g=2',
                      'equalizer=f=6500:t=q:w=1.5:g=-2', 'acompressor=threshold=-22dB:ratio=2.5:attack=8:release=120:makeup=2']
            if spk == 'N':
                chain.append('bass=g=2:f=140')
            elif L.get('radio'):
                chain += ['highpass=f=350', 'lowpass=f=3000', 'acrusher=bits=11:mix=0.18']
            elif amb in ('room', 'hum'):
                chain.append('aecho=0.85:0.5:22|38:0.11|0.06')
            chain += ['silenceremove=start_periods=1:start_threshold=-45dB', 'areverse',
                      'silenceremove=start_periods=1:start_threshold=-45dB', 'areverse']
            run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-af', ','.join(chain), '-ac', '1', fin])
            os.remove(raw)
            sr, x = wavfile.read(fin); x = x.astype(np.float32) / 32768
            act = x[np.abs(x) > 0.02]
            x = x * (0.16 / (np.sqrt(np.mean(act ** 2)) if len(act) else 0.1))
            pk = np.max(np.abs(x)) if len(x) else 1
            if pk > 0.95: x *= 0.95 / pk
            wavfile.write(fin, sr, (x * 32767).astype(np.int16))
            hop = sr // FPS
            durs[i] = {'dur': len(x) / sr, 'env': [float(np.sqrt(np.mean(x[j:j + hop] ** 2))) for j in range(0, len(x), hop)]}
            i += 1
    json.dump(durs, open(os.path.join(vdir, 'durs.json'), 'w'))
    return vdir


# ------------------------------------------------------------ áudio
def make_audio(S, vdir, seq=None):
    """seq: lista de (linha, quadro_novo) para cortes; None = vídeo inteiro."""
    import synth as Y
    SR = Y.SR
    if seq is None:
        seq = [(ln, ln.f0) for ln in S.lines]
    total = sum(ln.f1 - ln.f0 for ln, _ in seq) / FPS
    N = int(total * SR) + SR
    sfx = np.zeros((N, 2)); amb = np.zeros((N, 2)); voz = np.zeros((N, 2))

    def at(ln, nf0, tt):   # tempo original -> tempo novo
        return nf0 / FPS + (tt - ln.start)
    prev_scene = None
    for k, (ln, nf0) in enumerate(seq):
        t0 = nf0 / FPS
        sc = ln.scene
        if prev_scene is not None and sc is not prev_scene:
            Y.add(sfx, t0 - 0.45, Y.whoosh(0.9), 0.3)
        import bgs
        a = bgs.INFO[sc['bg']][2]
        d = ln.dur + 0.05
        if a == 'hum': Y.add(amb, t0, Y.hum(d), 0.08)
        elif a == 'room': Y.add(amb, t0, Y.filt(Y.noise(d), 'band', (200, 1500)) * Y.env(int(d * SR), 0.05, 0.05), 0.02)
        elif a == 'waves': Y.add(amb, t0, Y.waves(d), 0.3)
        elif a == 'wind': Y.add(amb, t0, Y.wind(d), 0.18)
        elif a == 'city': Y.add(amb, t0, Y.filt(Y.noise(d), 'low', 500) * Y.env(int(d * SR), 0.05, 0.05), 0.06)
        if ln.spk not in ('N', 'END'): Y.add(sfx, t0 + 0.02, Y.tick(), 0.3)
        shows = ln.ex.get('show')
        if shows:
            shows = [shows] if isinstance(shows, dict) else shows
            for sh in shows:
                Y.add(sfx, t0 + 0.15, Y.pop(500, 1100), 0.3)
                if 'list' in sh:
                    n = len(sh['list'])
                    for j in range(n): Y.add(sfx, t0 + 0.2 + j * ln.sdur * 0.85 / n, Y.pop(600, 1300), 0.3)
                if 'title' in sh: Y.add(sfx, t0 + 0.15, Y.boom(1.5) * 0.5, 0.5)
        name = ln.ex.get('sfx')
        if name:
            fx = {'boom': lambda: Y.boom(), 'alarm': lambda: Y.alarm(2), 'chime': lambda: Y.chime(), 'splash': lambda: Y.splash(),
                  'applause': lambda: Y.applause(3.5), 'tape': lambda: Y.tape_rip(), 'clunk': lambda: Y.clunk(),
                  'buzz': lambda: Y.buzz(), 'boing': lambda: Y.boing(), 'thud': lambda: Y.thud(), 'static': lambda: Y.static(1.5),
                  'rustle': lambda: Y.rustle()}.get(name)
            if fx: Y.add(sfx, t0 + float(ln.ex.get('sfx_at', 0.1)), fx(), 0.6 if name == 'boom' else 0.4)
        if ln.ex.get('endcard'):
            Y.add(sfx, t0 + 0.1, Y.boom(1.8) * 0.6, 0.45); Y.add(sfx, t0 + 0.7, Y.pop(500, 1200), 0.35)
        if ln.voice:
            sr_, v = wavfile.read(os.path.join(vdir, f'line_{ln.i:03d}.wav'))
            Y.add(voz, t0 + 0.08, v.astype(np.float64) / 32768, 1.0)
        prev_scene = sc

    def mood_at(t):
        for (ln, nf0) in seq:
            if nf0 / FPS <= t < nf0 / FPS + ln.dur: return ln.scene['mood']
        return 'triumph'
    mus = Y.make_music(mood_at, total, N)
    act = np.abs(voz[:, 0]) + np.abs(voz[:, 1])
    act = Y.signal.sosfiltfilt(Y.signal.butter(1, 3 / (SR / 2), 'low', output='sos'), act)
    duck = 1 - 0.65 * np.clip(act / 0.05, 0, 1)
    g = np.ones(N); e0 = int((total - 2.5) * SR); g[e0:] = np.clip(np.linspace(1, 0, N - e0) * 1.4, 0, 1)
    mix = mus * 0.27 * (g * duck)[:, None] + sfx * 0.45 + amb * 0.4 + voz
    mix = mix[:int(total * SR)]
    mix *= 0.93 / (np.max(np.abs(mix)) + 1e-9)
    return mix, SR


# ------------------------------------------------------------ vídeo
_S = None


def _init(story_path, vdir):
    global _S
    os.environ['CANAL_VDIR'] = vdir
    import video
    _S = video.Story(story_path, vdir)


def _render_chunk(args):
    path, frames, mode = args
    import video
    OW, OH = video.MODES[mode]
    tmp = path + '.tmp.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{OW}x{OH}', '-r', str(FPS),
                          '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '22', '-maxrate', '8M', '-bufsize', '16M',
                          '-pix_fmt', 'yuv420p', '-g', '60', tmp], stdin=subprocess.PIPE)
    for gf, fade in frames:
        p.stdin.write(video.render_frame(_S, gf, mode, fade).tobytes())
    p.stdin.close(); p.wait()
    if p.returncode: raise RuntimeError('ffmpeg falhou em ' + path)
    os.replace(tmp, path)
    return path


def render_video(story_path, vdir, out, mode, frames, name, audio):
    parts = 4
    n = len(frames); step = (n + parts - 1) // parts
    jobs = [(os.path.join(out, f'{name}_p{k}.mp4'), frames[k * step:(k + 1) * step], mode) for k in range(parts) if frames[k * step:(k + 1) * step]]
    with Pool(2, initializer=_init, initargs=(story_path, vdir)) as pool:
        paths = pool.map(_render_chunk, jobs)
    lst = os.path.join(out, f'{name}_list.txt')
    open(lst, 'w').write(''.join(f"file '{os.path.basename(p)}'\n" for p in paths))
    wav = os.path.join(out, f'{name}.wav')
    wavfile.write(wav, audio[1], (audio[0] * 32767).astype(np.int16))
    final = os.path.join(out, f'{name}.mp4')
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-i', wav, '-map', '0:v', '-map', '1:a',
         '-c:v', 'copy', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ar', '48000', '-c:a', 'aac', '-b:a', '192k', '-shortest',
         '-movflags', '+faststart', final])
    for p in paths: os.remove(p)
    os.remove(lst); os.remove(wav)
    return final


def short_seq(S):
    sel = S.d.get('short')
    if not sel:
        # padrão: começo (gancho) + o fim, até ~85 s
        idx = [ln.i for ln in S.lines if ln.spk != 'END']
        sel = []; tot = 0
        for i in idx[:10]:
            if tot + S.lines[i].dur > 55: break
            sel.append(i); tot += S.lines[i].dur
        for i in idx[-3:]:
            if i not in sel: sel.append(i)
    sel = [i for i in sel if i < len(S.lines) - 1] + [len(S.lines) - 1]
    seq = []; frames = []; f = 0
    fade = int(0.22 * FPS)
    for k, i in enumerate(sel):
        ln = S.lines[i]; n = ln.f1 - ln.f0
        seq.append((ln, f)); f += n
        cut_in = k == 0 or sel[k - 1] != i - 1 or S.lines[i - 1].scene is not ln.scene
        cut_out = k == len(sel) - 1 or sel[k + 1] != i + 1 or S.lines[i + 1].scene is not ln.scene
        for j in range(n):
            a = 1.0
            if cut_in: a = min(a, (j + 1) / fade)
            if cut_out: a = min(a, (n - j) / fade)
            frames.append((ln.f0 + j, a))
    return seq, frames


# ------------------------------------------------------------ extras
def srt(S, path):
    def ts(t):
        ms = int(round(t * 1000)); return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    out = []; k = 1
    for ln in S.lines:
        if not ln.text: continue
        out.append(f"{k}\n{ts(ln.start)} --> {ts(ln.start + ln.dur - 0.1)}\n{ln.text}\n"); k += 1
    open(path, 'w').write('\n'.join(out))


def thumbnail(S, story_path, vdir, path):
    import video
    from PIL import Image, ImageDraw, ImageFilter
    from gfx import font, FBL
    # quadro de um close de personagem (ou o primeiro quadro com título)
    cand = [ln for ln in S.lines if ln.spk in S.d['cast']] or S.lines
    ln = cand[0]
    arr = video.render_frame(S, ln.f0 + int(min(ln.dur, 1.2) * FPS), 'h', 1.0)
    im = Image.fromarray(arr).crop((0, video.BAR, 1920, 1080 - video.BAR)).resize((1280, 544))
    th = Image.new('RGB', (1280, 720), (8, 10, 20)); th.paste(im, (0, 88))
    th = th.convert('RGBA')
    txt = S.d.get('thumb_text', S.d.get('title', '')).upper()
    d = ImageDraw.Draw(th)
    f = font(FBL, 92)
    lines = video.wrap(txt, f, 1180)[:2]
    y = 720 - 40 - len(lines) * 100
    shade = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
    ImageDraw.Draw(shade).rectangle([0, y - 30, 1280, 720], fill=(0, 0, 0, 150))
    th.alpha_composite(shade.filter(ImageFilter.GaussianBlur(20)))
    d = ImageDraw.Draw(th)
    for k, s in enumerate(lines):
        d.text((640, y + k * 100 + 45), s, font=f, fill=(255, 214, 70) if k == 0 else (255, 255, 255), anchor='mm', stroke_width=6, stroke_fill=(0, 0, 0))
    th.convert('RGB').save(path, quality=92)


def qa(S, out, files):
    """Checagem automática: duração, som, quadros pretos, tamanho."""
    import video
    res = {'ok': True, 'problemas': [], 'arquivos': {}}
    for name, path, exp in files:
        info = {}
        if not os.path.exists(path):
            res['ok'] = False; res['problemas'].append(f'{name}: arquivo não existe'); continue
        pr = run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration,size:stream=codec_type,width,height', '-of', 'json', path]).stdout
        j = json.loads(pr)
        dur = float(j['format']['duration']); size = int(j['format']['size'])
        info.update(duracao=round(dur, 1), tamanho_mb=round(size / 1e6, 1), streams=[s['codec_type'] for s in j['streams']])
        if abs(dur - exp) > 1.5: res['problemas'].append(f'{name}: duração {dur:.1f}s, esperado {exp:.1f}s')
        if 'audio' not in info['streams']: res['problemas'].append(f'{name}: sem áudio')
        if size > 480e6: res['problemas'].append(f'{name}: arquivo grande demais ({size / 1e6:.0f} MB)')
        lo = run(['ffmpeg', '-hide_banner', '-i', path, '-af', 'ebur128', '-f', 'null', '-'])
        m = re.findall(r'I:\s+(-?[\d.]+) LUFS', lo.stderr.decode(errors='ignore'))
        lufs = float(m[-1]) if m else -99
        info['lufs'] = lufs
        if not (-17 < lufs < -11): res['problemas'].append(f'{name}: volume fora do padrão ({lufs} LUFS)')
        # quadros pretos / congelados
        bd = run(['ffmpeg', '-hide_banner', '-i', path, '-vf', 'blackdetect=d=1.2:pix_th=0.06', '-an', '-f', 'null', '-'])
        blacks = re.findall(r'black_start:([\d.]+) black_end:([\d.]+)', bd.stderr.decode(errors='ignore'))
        info['trechos_pretos'] = blacks
        if blacks: res['problemas'].append(f'{name}: trechos pretos {blacks}')
        res['arquivos'][name] = info
    # vozes: nenhuma fala vazia
    for ln in S.lines:
        if ln.text and (not ln.voice or ln.voice['dur'] < 0.4):
            res['problemas'].append(f'fala {ln.i} sem voz')
    res['ok'] = not res['problemas']
    json.dump(res, open(os.path.join(out, 'qa.json'), 'w'), ensure_ascii=False, indent=1)
    return res


def contact_sheet(path_video, out_img, n=12):
    from PIL import Image
    pr = json.loads(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', path_video]).stdout)
    dur = float(pr['format']['duration'])
    tiles = []
    for k in range(n):
        t = dur * (k + 0.5) / n
        p = out_img + f'.{k}.png'
        run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{t:.2f}', '-i', path_video, '-frames:v', '1', '-vf', 'scale=480:-1', p])
        tiles.append(Image.open(p).convert('RGB')); os.remove(p)
    w, h = tiles[0].size
    cols = 4
    sheet = Image.new('RGB', (w * cols, h * ((n + cols - 1) // cols)))
    for k, im in enumerate(tiles): sheet.paste(im, ((k % cols) * w, (k // cols) * h))
    sheet.save(out_img, quality=85)


def main():
    story_path = os.path.abspath(sys.argv[1]); out = os.path.abspath(sys.argv[2])
    os.makedirs(out, exist_ok=True)
    log('vozes'); vdir = make_voices(story_path, out)
    import video
    S = video.Story(story_path, vdir)
    log('duração prevista', round(S.total_f / FPS, 1), 's')
    log('áudio'); aud = make_audio(S, vdir)
    log('vídeo 16:9')
    frames = [(gf, None) for gf in range(S.total_f)]
    v1 = render_video(story_path, vdir, out, 'h', frames, 'video_16x9', aud)
    log('short 9:16')
    seq, sframes = short_seq(S)
    aud2 = make_audio(S, vdir, seq)
    v2 = render_video(story_path, vdir, out, 'v', sframes, 'short_9x16', aud2)
    log('extras'); srt(S, os.path.join(out, 'legendas.srt'))
    thumbnail(S, story_path, vdir, os.path.join(out, 'thumb.jpg'))
    contact_sheet(v1, os.path.join(out, 'folha_16x9.jpg')); contact_sheet(v2, os.path.join(out, 'folha_9x16.jpg'), 8)
    log('checagem')
    r = qa(S, out, [('video_16x9', v1, S.total_f / FPS), ('short_9x16', v2, len(sframes) / FPS)])
    shutil.rmtree(vdir, ignore_errors=True)
    log('QA', 'OK' if r['ok'] else 'PROBLEMAS: ' + '; '.join(r['problemas']))
    print(json.dumps(r, ensure_ascii=False))
    sys.exit(0 if r['ok'] else 2)


if __name__ == '__main__':
    main()
