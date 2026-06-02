"""
Voiceover generator — asks which method to use each time.

Primary:   Google Colab notebook (free T4 GPU, no local GPU needed)
Secondary: DashScope API         (cloud API, pay-per-character, instant)

Run from: D:\bhrikuty\myvideo\edit\
  python generate_voiceover.py
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

COLAB_NOTEBOOK       = Path(r"D:\bhrikuty\Qwen3-TTS\voiceover_colab.ipynb")
CLONE_COLAB_NOTEBOOK = Path(r"D:\bhrikuty\Qwen3-TTS\voice_clone_colab.ipynb")
DASHSCOPE_SCRIPT     = Path(r"D:\bhrikuty\Qwen3-TTS\voiceover_dashscope.py")
VOICEOVER_DIR = Path(r"D:\bhrikuty\myvideo\edit\voiceover")
FINAL_MP4 = Path(r"D:\bhrikuty\myvideo\edit\final.mp4")
MIXED_MP4 = Path(r"D:\bhrikuty\myvideo\edit\final_with_voice.mp4")


def banner():
    print()
    print("=" * 60)
    print("  Docker DevOps Ep.1 — Voiceover Generator")
    print("=" * 60)
    print()


def ask_method() -> str:
    print("Choose generation method:\n")
    print("  [1] Google Colab  (primary — free T4 GPU, ~10 min)")
    print("      Upload the notebook to colab.research.google.com")
    print("      Download the zip, then come back here to mix.\n")
    print("  [2] DashScope API (secondary — instant, requires API key)")
    print("      Runs locally, generates audio via Alibaba Cloud.\n")
    print("  [3] Mix existing voiceover into final.mp4")
    print("      (use this after downloading from Colab or DashScope)\n")
    print("  [4] Voice Clone Colab (use YOUR voice — upload ref_clean.wav)")
    print("      Whisper transcribes your clip, Qwen3-TTS clones your voice\n")
    while True:
        choice = input("Enter 1, 2, 3, or 4: ").strip()
        if choice in ("1", "2", "3", "4"):
            return choice
        print("  Please enter 1, 2, 3, or 4.")


def colab_instructions():
    print()
    print("── COLAB NOTEBOOK ──────────────────────────────────────")
    print(f"  Notebook: {COLAB_NOTEBOOK}")
    print()
    print("  Steps:")
    print("  1. Go to  https://colab.research.google.com")
    print("  2. File → Upload notebook → select the file above")
    print("  3. Runtime → Change runtime type → T4 GPU → Save")
    print("  4. Runtime → Run all  (or Ctrl+F9)")
    print("  5. Last cell downloads voiceover_docker_ep1.zip")
    print()
    print("  After downloading:")
    print(f"  - Extract the zip")
    print(f"  - Copy voiceover_full.wav  to  {VOICEOVER_DIR}")
    print(f"  - Re-run this script and choose [3] to mix")
    print()
    try:
        os.startfile(str(COLAB_NOTEBOOK.parent))
    except Exception:
        pass
    print(f"  (Opened folder: {COLAB_NOTEBOOK.parent})")


def run_dashscope():
    print()
    print("── DASHSCOPE API ───────────────────────────────────────")
    python = sys.executable
    result = subprocess.run([python, str(DASHSCOPE_SCRIPT)])
    if result.returncode != 0:
        print("DashScope generation failed. Check errors above.")
        return False
    return True


def mix_voiceover():
    """Blend voiceover_full.wav into final.mp4 → final_with_voice.mp4"""
    voice_file = VOICEOVER_DIR / "voiceover_full.wav"
    if not voice_file.exists():
        # try zip extract
        zip_file = next(VOICEOVER_DIR.glob("*.zip"), None)
        if zip_file:
            print(f"  Extracting {zip_file.name} ...")
            shutil.unpack_archive(str(zip_file), str(VOICEOVER_DIR))
        if not voice_file.exists():
            print(f"  ERROR: {voice_file} not found.")
            print(f"  Place voiceover_full.wav in {VOICEOVER_DIR} and try again.")
            return

    if not FINAL_MP4.exists():
        print(f"  ERROR: {FINAL_MP4} not found.")
        return

    print(f"\n  Mixing:")
    print(f"    video : {FINAL_MP4}")
    print(f"    voice : {voice_file}")
    print(f"    output: {MIXED_MP4}")
    print()

    # video audio kept at low level (ambient music), voiceover at full
    cmd = [
        "ffmpeg", "-y",
        "-i", str(FINAL_MP4),
        "-i", str(voice_file),
        "-filter_complex",
            "[0:a]volume=0.15[bg];"          # lower the existing ambient
            "[1:a]volume=1.0[vo];"
            "[bg][vo]amix=inputs=2:duration=first:weights=1 1[outa]",
        "-map", "0:v",
        "-map", "[outa]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(MIXED_MP4),
    ]
    import subprocess as sp
    result = sp.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("ffmpeg error:")
        print(result.stderr[-2000:])
    else:
        size_mb = MIXED_MP4.stat().st_size // (1024 * 1024)
        print(f"  Done: {MIXED_MP4} ({size_mb} MB)")


def main():
    banner()
    VOICEOVER_DIR.mkdir(parents=True, exist_ok=True)

    choice = ask_method()

    if choice == "1":
        colab_instructions()
    elif choice == "2":
        ok = run_dashscope()
        if ok:
            ans = input("\nMix voiceover into final.mp4 now? [y/N]: ").strip().lower()
            if ans == "y":
                mix_voiceover()
    elif choice == "3":
        mix_voiceover()
    elif choice == "4":
        clone_colab_instructions()


def clone_colab_instructions():
    print()
    print("── VOICE CLONE COLAB ───────────────────────────────────")
    print(f"  Notebook: {CLONE_COLAB_NOTEBOOK}")
    print()
    print("  Steps:")
    print("  1. Record yourself (5-10s of natural speech)")
    print("  2. Run:  python clean_voice.py <your_recording>")
    print(f"     Output: {VOICEOVER_DIR / 'ref_clean.wav'}")
    print()
    print("  3. Go to  https://colab.research.google.com")
    print("  4. File → Upload notebook → select voice_clone_colab.ipynb")
    print("  5. Runtime → Change runtime type → T4 GPU → Save")
    print("  6. Run all cells — upload ref_clean.wav when prompted")
    print("  7. Last cell downloads the zip with all scenes in your voice")
    print()
    print("  After downloading:")
    print(f"  - Extract → copy voiceover_full.wav to {VOICEOVER_DIR}")
    print("  - Re-run this script and choose [3] to mix")
    print()
    try:
        os.startfile(str(CLONE_COLAB_NOTEBOOK.parent))
    except Exception:
        pass
    print(f"  (Opened folder: {CLONE_COLAB_NOTEBOOK.parent})")


if __name__ == "__main__":
    main()
