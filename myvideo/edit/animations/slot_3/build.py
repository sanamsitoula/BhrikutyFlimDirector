"""
Outro card — 20s · 1920×1080 · 24fps
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
TOTAL  = 20          # seconds
N      = TOTAL * FPS # 480 frames

# ── colors ─────────────────────────────────────────────────────────────────
BG          = (15, 17, 23)          # #0f1117
BLUE        = (59, 130, 246)        # #3b82f6
GRAY_DOT    = (71, 85, 105)         # #475569
WHITE_TEXT  = (248, 250, 252)       # #f8fafc
GRAY_TEXT   = (148, 163, 184)       # #94a3b8
DIM_GRAY    = (100, 116, 139)       # #64748b
RED_SUB     = (220, 38, 38)         # YouTube-red subscribe button
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

font_big_bold  = load_font(42, bold=True)   # "Thanks for watching!"
font_sub_gray  = load_font(26, bold=False)  # "Subscribe & hit the Bell"
font_sub_btn   = load_font(20, bold=True)   # "SUBSCRIBE" button text
font_ep        = load_font(22, bold=False)  # Ep. 2 line
font_comment   = load_font(18, bold=False)  # "Leave a comment below!"

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

# 2. photo composite (right side 960–1920, left-edge gradient fade over 180px)
def make_photo_layer() -> Image.Image:
    photo = Image.open(SRC_PHOTO).convert("RGBA")
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

# ── microphone graphic ───────────────────────────────────────────────────────

def draw_mic(draw: ImageDraw.Draw, alpha: float):
    """Draw microphone graphic — same style as intro, offset to x=175, y=610."""
    a = int(255 * alpha)

    def ba(color):
        return (*color, a)

    # The intro mic is drawn with capsule top at y~515, center x~175.
    # Brief says "same coordinates and style" at x=175, y=610.
    # We offset the whole graphic down by (610 - 515) = 95px.
    dy = 95

    # capsule body
    draw.ellipse([147, 515+dy, 203, 585+dy], fill=ba(BLUE))
    # inner dark oval
    draw.ellipse([157, 525+dy, 193, 578+dy], fill=ba(MIC_DARK))
    # grille dots 3×3
    xs = [163, 175, 187]
    ys = [535+dy, 549+dy, 563+dy]
    for gx in xs:
        for gy in ys:
            draw.ellipse([gx-3, gy-3, gx+3, gy+3], fill=ba(MIC_GRILLE))
    # handle
    draw.rectangle([163, 585+dy, 187, 650+dy], fill=ba(GRAY_DOT))
    # base
    draw.rectangle([157, 650+dy, 193, 658+dy], fill=ba(GRAY_DOT))
    # stand
    draw.rectangle([173, 658+dy, 177, 685+dy], fill=ba(GRAY_DOT))


# ── per-frame composer ───────────────────────────────────────────────────────

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

    # blue vertical accent line: x=916–920, centered vertically, always visible
    cy = H // 2
    draw.rectangle([916, cy - 180, 920, cy + 180], fill=(*BLUE, 255))

    # ── text elements with ease_out_cubic fades ──────────────────────────

    # t=0.8s: "Thanks for watching!" — x=80, y=300, Arial Bold 42px, white
    if t >= 0.8:
        prog  = ease_out_cubic((t - 0.8) / 0.5)
        alpha = int(255 * prog)
        draw.text((80, 300), "Thanks for watching!",
                  font=font_big_bold, fill=(*WHITE_TEXT, alpha))

    # t=1.8s: "Subscribe & hit the Bell" — x=80, y=370, Arial 26px, gray
    if t >= 1.8:
        prog  = ease_out_cubic((t - 1.8) / 0.5)
        alpha = int(255 * prog)
        draw.text((80, 370), "Subscribe & hit the Bell",
                  font=font_sub_gray, fill=(*GRAY_TEXT, alpha))

    # t=2.8s: Red SUBSCRIBE button rect (80,420,320,460) + white centered text
    if t >= 2.8:
        prog  = ease_out_cubic((t - 2.8) / 0.5)
        alpha = int(255 * prog)
        # Red rectangle background
        draw.rectangle([80, 420, 320, 460], fill=(*RED_SUB, alpha))
        # White "SUBSCRIBE" text centered in box
        btn_text = "SUBSCRIBE"
        bbox = draw.textbbox((0, 0), btn_text, font=font_sub_btn)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = 80 + (240 - tw) // 2
        ty = 420 + (40 - th) // 2
        draw.text((tx, ty), btn_text, font=font_sub_btn, fill=(*WHITE_TEXT, alpha))

    # t=4.0s: "Ep. 2: Docker Images & Dockerfile" — x=80, y=480, Arial 22px, blue
    if t >= 4.0:
        prog  = ease_out_cubic((t - 4.0) / 0.5)
        alpha = int(255 * prog)
        draw.text((80, 480), "Ep. 2: Docker Images & Dockerfile",
                  font=font_ep, fill=(*BLUE, alpha))

    # t=5.5s: "Leave a comment below!" — x=80, y=520, Arial 18px, dim gray
    if t >= 5.5:
        prog  = ease_out_cubic((t - 5.5) / 0.5)
        alpha = int(255 * prog)
        draw.text((80, 520), "Leave a comment below!",
                  font=font_comment, fill=(*DIM_GRAY, alpha))

    # t=7.0s: microphone graphic at x=175, y=610
    if t >= 7.0:
        prog = ease_out_cubic((t - 7.0) / 0.5)
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
