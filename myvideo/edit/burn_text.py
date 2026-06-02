"""
Burn step labels and hook text onto base.mp4 using ffmpeg drawtext.
No libass dependency — works reliably on Windows.
"""
import subprocess
from pathlib import Path

BASE  = Path(r"D:\bhrikuty\myvideo\edit\base.mp4")
MUSIC = Path(r"D:\bhrikuty\myvideo\edit\music\ambient.mp3")
OUT   = Path(r"D:\bhrikuty\myvideo\edit\final.mp4")

FONT_BOLD = r"C\:\\Windows\\Fonts\\arialbd.ttf"
FONT_REG  = r"C\:\\Windows\\Fonts\\arial.ttf"

# (start_s, end_s, text, size, is_bold, color_hex)
# color_hex: RRGGBB
ENTRIES = [
    # Hook section (12–28s)
    (12.5,  18.0,  "IT WORKS ON MY MACHINE!",                               40, True,  "FFFFFF"),
    (18.5,  24.5,  "The 4 most dangerous words in software",                28, False, "B8A394"),
    (24.8,  27.8,  "Docker solves this.",                                   32, True,  "3B82F6"),
    # Infographic (28–62s)
    (29.5,  39.0,  "WALL OF CONFUSION  -  Dev vs Ops",                     26, True,  "F59E0B"),
    (39.5,  51.0,  "DEVOPS = Dev + Ops  |  One team, one environment",     26, True,  "3B82F6"),
    (51.5,  62.0,  "DOCKER  -  Step-by-step install on Windows",           26, True,  "34D399"),
    # Installation steps (62–149s)
    (62.5,  74.0,  "STEP 1  -  Enable WSL2 + Virtual Machine Platform",    26, True,  "FFFFFF"),
    (74.5,  87.0,  "STEP 2  -  wsl --set-default-version 2",               26, True,  "FFFFFF"),
    (87.5, 102.0,  "STEP 3  -  docker.com  ->  Download Docker Desktop",   26, True,  "FFFFFF"),
    (102.5,117.0,  "STEP 4  -  Run installer  ->  Use WSL 2 option",       26, True,  "FFFFFF"),
    (117.5,134.0,  "STEP 5  -  docker --version  [OK]",                    26, True,  "6EE7B7"),
    (134.5,149.0,  "STEP 6  -  docker run hello-world  ->  Hello from Docker!", 26, True, "6EE7B7"),
]

def esc(s):
    """Escape text for ffmpeg drawtext on Windows."""
    return (s.replace("\\", "\\\\")
             .replace("'", "\\'")
             .replace(":", "\\:")
             .replace("[", "\\[")
             .replace("]", "\\]"))

def hex_to_ffmpeg(h):
    """Convert RRGGBB hex to ffmpeg color string 0xRRGGBB@alpha."""
    return f"0x{h}@1.0"

def make_drawtext(e, vid_w=1920):
    start, end, text, size, bold, color = e
    font = FONT_BOLD if bold else FONT_REG
    col  = hex_to_ffmpeg(color)
    txt  = esc(text)
    return (
        f"drawtext=fontfile='{font}'"
        f":text='{txt}'"
        f":fontsize={size}"
        f":fontcolor={col}"
        f":x=(w-text_w)/2"
        f":y=18"
        f":box=1"
        f":boxcolor=0x000000@0.55"
        f":boxborderw=12"
        f":enable='between(t\\,{start}\\,{end})'"
    )

filters = ",".join(make_drawtext(e) for e in ENTRIES)

cmd = [
    "ffmpeg", "-y",
    "-i", str(BASE),
    "-i", str(MUSIC),
    "-filter_complex",
        f"[0:v]{filters}[outv];"
        f"[0:a][1:a]amix=inputs=2:duration=first:weights=1 0.3[outa]",
    "-map", "[outv]",
    "-map", "[outa]",
    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k",
    "-movflags", "+faststart",
    str(OUT),
]

print("Running ffmpeg drawtext render...")
print(f"  {len(ENTRIES)} text overlays")
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print("STDERR:", result.stderr[-2000:])
    raise RuntimeError("ffmpeg failed")
print(f"Done: {OUT} ({OUT.stat().st_size // 1024} KB)")
