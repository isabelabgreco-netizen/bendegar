"""
build_reel.py - monta o reel "Vermelho que dura não é sorte" (Lady Gaga / Copacabana).

Coloque os arquivos de entrada em ./media com estes nomes:
  media/processo.mp4   o vídeo do besouro sendo feito (ago 2024)
  media/show.mp4       o palco da Lady Gaga
  media/fogos.mp4      fogos e multidão do show
  media/praia.jpg      o besouro cicatrizado na praia (mai 2025)
  media/voz.m4a        a sua voz lendo o roteiro
e rode:  python3 build_reel.py
Sai em ./out/reel.mp4. Precisa de ffmpeg com libass e de Pillow.
voz_palavras.json tem o tempo de cada palavra da voz (transcrito com faster-whisper);
se gravar de novo, transcreva de novo antes de rodar.
Apague ./out/build para renderizar as cenas do zero.
O sistema tipográfico está descrito em ../sistema-visual.md.
"""
import json, subprocess, os
from PIL import Image, ImageDraw

D = os.path.dirname(os.path.abspath(__file__))
M = D + "/media/"
V1 = M + "processo.mp4"   # process + fresh beetle (Aug 2024)
V2 = M + "show.mp4"       # Gaga stage
V3 = M + "fogos.mp4"      # fireworks / crowd
PH = M + "praia.jpg"      # healed, Copacabana beach (May 2025)
VOZ = M + "voz.m4a"
B = D + "/out/build"; os.makedirs(B, exist_ok=True)
FONTS = D + "/fonts"
SHIFT = 0.8; FPS = 30

def run(c): subprocess.run(c, check=True)
NORM = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p"

def clip(out, src, ss, dur, speed=1.0, extra=""):
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-t", str(dur * speed + 0.2), "-i", src, "-an",
         "-vf", f"setpts=PTS/{speed},{NORM}{extra}", "-t", str(dur), "-r", "30", "-c:v", "libx264", "-crf", "17", out])

def photo(out, dur, z0, z1, cx, cy):
    n = int(round(dur * FPS))
    vf = (f"scale=2160:3840,zoompan=z='{z0}+({z1}-{z0})*on/{n}'"
          f":x='max(0,min(iw-iw/zoom,{cx}*iw-iw/zoom/2))':y='max(0,min(ih-ih/zoom,{cy}*ih-ih/zoom/2))'"
          f":d={n}:s=1080x1920:fps=30,format=yuv420p")
    run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", PH, "-vf", vf, "-frames:v", str(n), "-c:v", "libx264", "-crf", "17", out])

def split(out, dur):
    # left: fresh (Aug 2024) from V1; right: healed (May 2025) from the photo, beetle at similar size
    n = int(round(dur * FPS))
    fc = (f"[0:v]setpts=PTS/0.8,scale=1080:1995,crop=540:1920:270:30,setsar=1,fps=30[l];"
          f"[1:v]scale=1450:2576,crop=540:1920:252:600,setsar=1,fps=30,"
          f"zoompan=z='1.0+0.06*on/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=540x1920:fps=30[r];"
          f"[l][r]hstack=inputs=2,drawbox=x=538:y=0:w=4:h=1920:color=0xF2EDE6@1:t=fill,format=yuv420p[v]")
    run(["ffmpeg", "-v", "error", "-y", "-ss", "20.6", "-t", str(dur * 0.8 + 0.3), "-i", V1, "-loop", "1", "-i", PH,
         "-filter_complex", fc, "-map", "[v]", "-frames:v", str(n), "-c:v", "libx264", "-crf", "17", out])

# ---------- shot list, timed to the voice (voice time minus SHIFT) ----------
shots = [
    (4.30,  lambda o, d: clip(o, V2, 17.6, d)),                         # hook: Gaga stage
    (6.06,  lambda o, d: clip(o, V1, 20.0, d)),                         # Aug 2024: fresh
    (9.00,  lambda o, d: photo(o, d, 1.25, 1.40, 0.40, 0.58)),         # May 2025: beach
    (10.66, lambda o, d: clip(o, V3, 0.0, d)),                          # 9 meses: fireworks
    (11.30, lambda o, d: photo(o, d, 2.6, 2.9, 0.20, 0.80)),           # SOL: bright sand
    (11.98, lambda o, d: photo(o, d, 1.7, 1.9, 0.20, 0.38)),           # PRAIA: towel, sand
    (12.54, lambda o, d: clip(o, V3, 5.2, d)),                          # MULTIDÃO
    (14.25, lambda o, d: split(o, d)),                                  # fresh vs healed
    (16.30, lambda o, d: clip(o, V1, 12.0, d)),                         # não é sorte: needle in red
    (17.80, lambda o, d: clip(o, V1, 14.0, d)),                         # 01 aplicação
    (19.96, lambda o, d: clip(o, V1, 17.6, d)),
    (23.20, lambda o, d: clip(o, V1, 21.6, d, speed=0.75)),            # 02 cicatrização: fresh
    (24.40, lambda o, d: photo(o, d, 2.3, 2.45, 0.36, 0.64)),          #    -> healed
    (27.14, lambda o, d: photo(o, d, 1.45, 1.30, 0.40, 0.62)),         # 03 cuidado: sun
    (29.00, lambda o, d: clip(o, V2, 23.0, d)),                         # quer um vermelho que dure?
    (30.60, lambda o, d: clip(o, V1, 23.7, d)),                         # logo + link na bio
]
files = []; t = 0
REUSE = os.path.exists(B + '/video.mp4')
for i, (end, mk) in enumerate(shots):
    if REUSE: t = end; continue
    f = f"{B}/s{i:02d}.mp4"; mk(f, round(end - t, 3)); files.append(f); t = end
TOTAL = t
if not REUSE: open(B + "/list.txt", "w").write("".join(f"file '{f}'\n" for f in files))
REUSE or run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", B + "/list.txt", "-c", "copy", B + "/video.mp4"])

# ---------- legibility gradients (top + bottom) ----------
g = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); px = ImageDraw.Draw(g)
for y in range(1920):
    a = 0
    if y < 560: a = int(150 * (1 - y / 560) ** 1.6)
    if y > 1240: a = max(a, int(185 * ((y - 1240) / 680) ** 1.4))
    px.line([(0, y), (1080, y)], fill=(8, 6, 6, a))
g.save(B + "/grad.png")

# ---------- typography v4 (ASS) ----------
# System, after Lupton / Tim Brown / Neumeier:
#  - ONE anchor family for the voice: Instrument Serif (upright = statement, italic = emotion).
#    Its narrow, high-contrast, pointed forms rhyme with the blackletter Bendegar logo. Anton is gone.
#  - ONE utility family: Archivo Narrow, caps, tracked open, for labels, dates and spoken captions.
#  - Large display tracked TIGHT, small caps tracked OPEN.
#  - Red is reserved for the tattoo: type uses it only for one accent per frame (a period, a dot, a rule, the 9).
#  - Fixed grid: margin 90 · label zone y 200-330 · headline zone centred y 860-1060 · caption zone y 1500.
#  - Motion: change by opacity and a 4% scale settle (180 ms), never by flying in.
RED = "&H1E26D7&"; OFF = "&HE6EDF2&"
def ts(s):
    s = max(0, s); return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"
ev = []
def add(a, b, txt, layer=3): ev.append(f"Dialogue: {layer},{ts(a)},{ts(b)},Base,,0,0,0,,{txt}")
IN = "\\fscx104\\fscy104\\t(0,180,\\fscx100\\fscy100)\\fad(180,140)"
SH = "\\bord0\\shad0\\blur0"
def serif(size, it=False, sp=None):
    sp = -round(size / 70) if sp is None else sp
    return f"\\fnInstrument Serif\\i{1 if it else 0}\\b0\\fs{size}\\fsp{sp}\\c{OFF}{SH}"
def label(size, sp=10): return f"\\fnArchivo Narrow\\i0\\b1\\fs{size}\\fsp{sp}\\c{OFF}{SH}"
def fit(size, txt, k=0.40): return int(min(size, 940 / (k * max(1, len(txt)))))
DOT = "m 11 0 b 17 0 22 5 22 11 b 22 17 17 22 11 22 b 5 22 0 17 0 11 b 0 5 5 0 11 0"
def rule(a, b, x, y, w=120): add(a, b, f"{{\\an7\\pos({x},{y})\\p1\\c{RED}{SH}\\fad(180,140)}}m 0 0 l {w} 0 {w} 6 0 6{{\\p0}}")
def band(a, b, y0, y1, alpha="&H30&"):   # framing device: a black field behind type over busy images
    add(a, b, f"{{\\an7\\pos(0,{y0})\\p1\\c&H080606&\\alpha{alpha}{SH}\\fad(120,120)}}m 0 0 l 1080 0 1080 {y1 - y0} 0 {y1 - y0}{{\\p0}}", layer=2)
def head(a, b, txt, y, size, it=False, accent=""):
    acc = f"{{\\c{RED}}}{accent}" if accent else ""
    add(a, b, f"{{\\an5\\pos(540,{y}){serif(size, it)}{IN}}}{txt}{acc}")

# 1 · hook: the sentence builds line by line, centred; only "Lady Gaga" is big
head(0.22, 4.30, "essa tattoozona vermelha", 690, 92, it=True)
add(1.88, 4.30, f"{{\\an5\\pos(540,800){label(44, 14)}{IN}}}FOI PRO SHOW DA")
head(2.50, 4.30, "Lady Gaga", 960, fit(250, "Lady Gaga", 0.38))
head(3.10, 4.30, "em Copacabana", 1110, 92, it=True, accent=".")

# 2-3 · timestamps, top-left on the grid
def stamp(a, b, big, small):
    add(a, b, f"{{\\an7\\pos(90,214)\\p1\\c{RED}{SH}\\fad(150,120)}}{DOT}{{\\p0}}")
    add(a, b, f"{{\\an7\\pos(128,196){label(58, 10)}\\fad(150,120)}}{big}")
    add(a, b, f"{{\\an7\\pos(128,270){label(36, 10)}\\alpha&H50&\\fad(150,120)}}{small}")
stamp(4.30, 6.06, "AGO 2024", "SAINDO DO ESTÚDIO · BH")
stamp(6.06, 9.00, "MAI 2025", "COPACABANA · RJ")

# 4 · nine months: big heavy numeral (Anton, as in the earlier cut), counting 1 to 9 slowly enough to read
STEP = 0.13
for k in range(1, 10):
    a = 9.02 + (k - 1) * STEP; b = a + STEP if k < 9 else 10.66
    col = RED if k == 9 else OFF
    pop = "\\fscx108\\fscy108\\t(0,90,\\fscx100\\fscy100)"
    add(a, b, f"{{\\an5\\pos(540,860)\\fnAnton\\i0\\b0\\fs900\\fsp0\\c{col}{SH}\\shad4\\4c&H000000&\\4a&H70&{pop}}}{k}")
add(10.10, 10.66, f"{{\\an5\\pos(540,1330){label(64, 28)}\\fad(120,100)}}MESES")
head(10.22, 10.66, "depois", 1430, 96, it=True)

# 5 · sol / praia / multidão: one word per cut, lowercase serif, red period
for a, b, w in [(10.66, 11.30, "sol"), (11.30, 11.98, "praia"), (11.98, 12.54, "multidão")]:
    add(a, b, f"{{\\an5\\pos(540,920){serif(fit(300, w + '.', 0.42))}\\fscx104\\fscy104\\t(0,140,\\fscx100\\fscy100)}}{w}{{\\c{RED}}}.")

# 6 · the climax: fresh vs healed, headline on a black band so the divider never cuts the type
band(12.54, 14.25, 0, 640, alpha="&H18&")
head(12.54, 14.25, "e o vermelho", 330, 104, it=True)
head(12.95, 14.25, "tá aí", 500, 190, accent=".")
for x, big, small in [(270, "AGO 2024", "fresh"), (810, "MAI 2025", "9 meses depois")]:
    add(12.54, 14.25, f"{{\\an5\\pos({x},1540){label(44, 10)}\\fad(150,120)}}{big}")
    add(12.54, 14.25, f"{{\\an5\\pos({x},1600){serif(54, True)}\\fad(150,120)}}{small}")

# 7 · the thesis
head(14.30, 16.30, "vermelho que dura", 800, 104, it=True)
head(15.10, 16.30, "não é sorte", 960, fit(190, "não é sorte.", 0.40), accent=".")

# 8-10 · chapters, top-left, same grid every time
def chapter(a, b, n, word, note=None):
    add(a, b, f"{{\\an7\\pos(90,196){label(40, 12)}\\fad(180,140)}}{n} {{\\alpha&H70&}}/ 03")
    add(a, b, f"{{\\an7\\pos(86,240){serif(fit(170, word, 0.36))}\\fad(180,140)}}{word}")
    rule(a, b, 92, 452)
chapter(16.30, 19.96, "01", "Aplicação")
chapter(19.96, 24.40, "02", "Cicatrização")
add(23.20, 24.40, f"{{\\an7\\pos(92,482){serif(64, True)}\\fad(180,140)}}cicatrizada, 9 meses depois")
chapter(24.40, 27.14, "03", "Cuidado")
head(25.70, 27.14, "protetor solar,", 1120, 110, it=True)
head(26.50, 27.14, "sempre", 1260, 170, accent=".")

# 11-12 · close: the question, then the 12-word brand line (Neumeier's focus test)
head(27.14, 29.00, "quer um vermelho", 800, 104, it=True)
head(28.10, 29.00, "que dure?", 960, 190)
add(29.05, 30.60, f"{{\\an2\\pos(540,1500){label(56, 18)}\\fad(180,220)}}LINK NA BIO")
add(29.05, 30.60, f"{{\\an2\\pos(540,1590){serif(64, True)}\\fad(180,220)}}redwork autoral que cicatriza bem · BH")
# ---------- captions v4: spoken words, karaoke by OPACITY (not red), utility face ----------
w = json.load(open(D + "/voz_palavras.json"))
fix = {"tatuzona": "tattoozona"}
words = [[a - SHIFT, b - SHIFT, fix.get(x, x)] for a, b, x in w if x != "The"]
CAP_WINDOWS = [(4.30, 9.00), (16.30, 24.40)]
def in_win(t0): return any(a <= t0 < b for a, b in CAP_WINDOWS)
sel = [wd for wd in words if in_win(wd[0])]
groups = []; cur = []
for wd in sel:
    if cur and (len(cur) == 4 or wd[0] - cur[-1][1] > 0.35): groups.append(cur); cur = []
    cur.append(wd)
    if wd[2][-1] in ".,?": groups.append(cur); cur = []
if cur: groups.append(cur)
for gi, gp in enumerate(groups):
    nxt = groups[gi + 1][0][0] if gi + 1 < len(groups) else gp[-1][1] + 0.4
    win_end = min(b for a, b in CAP_WINDOWS if a <= gp[0][0] < b)
    gend = min(nxt, gp[-1][1] + 0.5, win_end)
    for k, (a, b, _) in enumerate(gp):
        e = gp[k + 1][0] if k + 1 < len(gp) else gend
        txt = " ".join((f"{{\\alpha&H00&}}{x.upper()}{{\\alpha&H5A&}}" if j == k else x.upper())
                       for j, (_, _, x) in enumerate(gp))
        add(a, e, f"{{\\an2\\pos(540,1500){label(60, 6)}\\alpha&H5A&\\shad2\\4c&H000000&\\4a&H80&}}{txt}", layer=4)
ass = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Base,Archivo Narrow,60,&H00E6EDF2,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(ev) + "\n"
open(B + "/type.ass", "w").write(ass)

# ---------- final ----------
run(["ffmpeg", "-v", "error", "-y", "-i", B + "/video.mp4", "-i", B + "/grad.png", "-ss", str(SHIFT), "-i", VOZ,
     "-filter_complex",
     f"[0:v][1:v]overlay=0:0,ass={B}/type.ass:fontsdir={FONTS},format=yuv420p[v];"
     f"[2:a]loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=out:st={TOTAL - 0.4}:d=0.4[a]",
     "-map", "[v]", "-map", "[a]", "-t", str(TOTAL), "-c:v", "libx264", "-crf", "18", "-preset", "slow",
     "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", D + "/out/reel.mp4"])
print("ok", TOTAL)
