"""
Host intro card — 12s · 1920×1080 · 24fps
Pipes raw RGB frames directly to ffmpeg stdin (no temp PNGs).
"""

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import numpy as np

# ── paths ──────────────────────────────────────────────────────────────────
SLOT_DIR  = Path(__file__).parent
SRC_PHOTO = Path(r"D:\bhrikuty\myvideo\p1.jpg")
OUT_VIDEO = SLOT_DIR / "render.mp4"

W, H   = 1920, 1080
FPS    = 24
TOTAL  = 12          # seconds
N      = TOTAL * FPS # 288 frames

# ── colors ─────────────────────────────────────────────────────────────────
BG          = (15, 17, 23)          # #0f1117
BLUE        = (59, 130, 246)        # #3b82f6
GRAY_DOT    = (71, 85, 105)         # #475569
WHITE_TEXT  = (248, 250, 252)       # #f8fafc
GRAY_TEXT   = (148, 163, 184)       # #94a3b8
MIC_DARK    = (20, 40, 80)
MIC_GRILLE  = (40, 70, 140)

# ── fonts ───────────────────────────────────────────────────────────────────
def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()

font_label  = load_font(20, bold=True)
font_title  = load_font(58, bold=True)
font_sub    = load_font(28, bold=False)

# ── easing ──────────────────────────────────────────────────────────────────
def ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3

# ── pre-build static layers ─────────────────────────────────────────────────

# 1. background with dot grid (left half only)
def make_base() -> Image.Image:
    img = Image.new("RGBA", (W, H), (*BG, 255))
    draw = ImageDraw.Draw(img)
    # dot grid: every 48px, 2px dots, 20% opacity → alpha=51
    for x in range(0, 960, 48):
        for y in range(0, H, 48):
            draw.ellipse([x-1, y-1, x+1, y+1], fill=(*GRAY_DOT, 51))
    return img

BASE = make_base()

# 2. photo composite (right side 960–1920, left-edge fade over 180px)
def make_photo_layer() -> Image.Image:
    photo = Image.open(SRC_PHOTO).convert("RGBA")
    # scale photo to fill the right-side panel (960×1080)
    ph_w, ph_h = photo.size
    scale = max(960 / ph_w, H / ph_h)
    new_w, new_h = int(ph_w * scale), int(ph_h * scale)
    photo = photo.resize((new_w, new_h), Image.LANCZOS)
    # center-crop to 960×1080
    left = (new_w - 960) // 2
    top  = (new_h - H) // 2
    photo = photo.crop((left, top, left + 960, top + H))

    # build gradient mask: leftmost 180px fade 0→255, rest 255
    mask = Image.new("L", (960, H), 255)
    for x in range(180):
        alpha = int(255 * (x / 180))
        for y in range(H):
            mask.putpixel((x, y), alpha)

    photo.putalpha(mask)

    # paste onto a full-canvas transparent layer at x=960
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.paste(photo, (960, 0), photo)
    return layer

PHOTO_LAYER = make_photo_layer()

# ── per-frame composer ───────────────────────────────────────────────────────

def draw_mic(draw: ImageDraw.Draw, alpha: float):
    """Draw microphone graphic with overall alpha blending."""
    a = int(255 * alpha)

    def ba(color):
        return (*color, a)

    # capsule body
    draw.ellipse([147, 515, 203, 585], fill=ba(BLUE))
    # inner dark oval
    draw.ellipse([157, 525, 193, 578], fill=ba(MIC_DARK))
    # grille dots 3×3
    xs = [163, 175, 187]
    ys = [535, 549, 563]
    for gx in xs:
        for gy in ys:
            draw.ellipse([gx-3, gy-3, gx+3, gy+3], fill=ba(MIC_GRILLE))
    # handle
    draw.rectangle([163, 585, 187, 650], fill=ba(GRAY_DOT))
    # base
    draw.rectangle([157, 650, 193, 658], fill=ba(GRAY_DOT))
    # stand
    draw.rectangle([173, 658, 177, 685], fill=ba(GRAY_DOT))


def render_frame(frame_idx: int) -> bytes:
    t = frame_idx / FPS   # current time in seconds

    # start from base (dot-grid BG) — copy so we don't mutate
    canvas = BASE.copy()

    # composite photo layer
    canvas = Image.alpha_composite(canvas, PHOTO_LAYER)

    # ── overlay layer for all animated elements ──────────────────────────
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)

    # bottom blue bar — always visible, 4px
    draw.rectangle([0, H-4, W, H], fill=(*BLUE, 255))

    # blue vertical accent line: x=916–920, 360px tall, centered, appears at t=0.5s
    if t >= 0.5:
        line_prog  = ease_out_cubic((t - 0.5) / 0.4)   # 0.4s fade-in
        line_alpha = int(255 * line_prog)
        cy = H // 2
        draw.rectangle([916, cy - 180, 920, cy + 180], fill=(*BLUE, line_alpha))

    # ── text elements ────────────────────────────────────────────────────

    # "DEVOPS SERIES  ·  EP. 1" — fade in at t=1.2s
    if t >= 1.2:
        prog  = ease_out_cubic((t - 1.2) / 0.5)
        alpha = int(255 * prog)
        draw.text((80, 335), "DEVOPS SERIES  ·  EP. 1",
                  font=font_label, fill=(*BLUE, alpha))

    # "What is Docker?" — slide in from x=50→80 at t=2.2s
    if t >= 2.2:
        prog  = ease_out_cubic((t - 2.2) / 0.5)
        alpha = int(255 * prog)
        x_pos = int(50 + 30 * prog)   # 50 → 80
        draw.text((x_pos, 385), "What is Docker?",
                  font=font_title, fill=(*WHITE_TEXT, alpha))

    # "Install on Windows" — fade in at t=3.5s
    if t >= 3.5:
        prog  = ease_out_cubic((t - 3.5) / 0.5)
        alpha = int(255 * prog)
        draw.text((80, 465), "Install on Windows",
                  font=font_sub, fill=(*GRAY_TEXT, alpha))

    # microphone graphic — appears at t=5.0s
    if t >= 5.0:
        prog = ease_out_cubic((t - 5.0) / 0.5)
        draw_mic(draw, prog)

    # composite overlay onto canvas
    canvas = Image.alpha_composite(canvas, overlay)

    # convert to RGB for raw pipe
    rgb = canvas.convert("RGB")
    return rgb.tobytes()


# ── ffmpeg pipe ──────────────────────────────────────────────────────────────

def main():
    print(f"Rendering {N} frames -> {OUT_VIDEO}")

    proc = subprocess.Popen(
        [
            "ffmpeg", "-y",
            "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{W}x{H}",
            "-pix_fmt", "rgb24",
            "-r", str(FPS),
            "-i", "-",
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-t", str(TOTAL),
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            str(OUT_VIDEO),
        ],
        stdin=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    for i in range(N):
        if i % 24 == 0:
            print(f"  frame {i}/{N}  ({i//24}s)", flush=True)
        proc.stdin.write(render_frame(i))

    proc.stdin.close()
    proc.wait()

    if proc.returncode == 0:
        size_mb = OUT_VIDEO.stat().st_size / 1_048_576
        print(f"\nDone. {OUT_VIDEO}  ({size_mb:.2f} MB)")
    else:
        print(f"\nffmpeg exited with code {proc.returncode}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
