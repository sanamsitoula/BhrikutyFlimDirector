#!/usr/bin/env python3
"""
FFmpeg Deep Diagnostic — Tests every operation used in the pipeline
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class FFmpegDebugger:
    def __init__(self):
        self.errors = []
        self.tests_passed = 0
        self.tests_failed = 0

    def log(self, msg, level="INFO"):
        prefix = {"INFO": "ℹ️ ", "PASS": "✅ ", "FAIL": "❌ ", "WARN": "⚠️ "}[level]
        print(f"{prefix}{msg}")

    def run_cmd(self, cmd, desc, timeout=30):
        self.log(f"Testing: {desc}")
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            if result.returncode == 0:
                self.tests_passed += 1
                self.log(f"{desc}: PASS", "PASS")
                return True, result.stdout
            else:
                self.tests_failed += 1
                self.log(f"{desc}: FAIL", "FAIL")
                self.log(f"  stderr: {result.stderr[:500]}", "FAIL")
                self.errors.append({
                    "test": desc,
                    "stderr": result.stderr[:1000],
                    "cmd": " ".join(str(c) for c in cmd)
                })
                return False, result.stderr
        except subprocess.TimeoutExpired:
            self.tests_failed += 1
            self.log(f"{desc}: TIMEOUT", "FAIL")
            self.errors.append({"test": desc, "error": "Timeout"})
            return False, "timeout"
        except Exception as e:
            self.tests_failed += 1
            self.log(f"{desc}: EXCEPTION - {e}", "FAIL")
            self.errors.append({"test": desc, "error": str(e)})
            return False, str(e)

    def test_suite(self):
        print("\n" + "=" * 60)
        print("  FFMPEG DEEP DIAGNOSTIC SUITE")
        print("=" * 60 + "\n")

        temp_dir = Path(tempfile.mkdtemp(prefix="ffmpeg_debug_"))
        self.log(f"Workspace: {temp_dir}")

        # 1: Version
        self.run_cmd(["ffmpeg", "-version"], "FFmpeg binary accessible")

        # 2: Generate test pattern
        test_mp4 = temp_dir / "test_gen.mp4"
        self.run_cmd([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", "testsrc=duration=3:size=1920x1080:rate=30",
            "-pix_fmt", "yuv420p", "-c:v", "libx264", str(test_mp4)
        ], "Generate 1080p test video")

        # 3: Extract frame
        if test_mp4.exists():
            frame_png = temp_dir / "frame_1.png"
            self.run_cmd([
                "ffmpeg", "-y", "-i", str(test_mp4),
                "-ss", "00:00:01", "-vframes", "1", str(frame_png)
            ], "Extract frame to PNG")

        # 4: Cut/trim (platform cutter simulation)
        if test_mp4.exists():
            cut_mp4 = temp_dir / "cut_1s.mp4"
            self.run_cmd([
                "ffmpeg", "-y", "-i", str(test_mp4),
                "-ss", "00:00:00", "-t", "1",
                "-c:v", "libx264", "-c:a", "aac", str(cut_mp4)
            ], "Cut 1-second clip (platform cutter)")

        # 5: Concatenate
        if test_mp4.exists():
            concat_list = temp_dir / "concat.txt"
            concat_list.write_text(f"file '{test_mp4}'\nfile '{test_mp4}'\n")
            concat_out = temp_dir / "concat.mp4"
            self.run_cmd([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", str(concat_list), "-c", "copy", str(concat_out)
            ], "Concatenate videos")

        # 6: Scale to vertical (TikTok/Instagram)
        if test_mp4.exists():
            vertical_mp4 = temp_dir / "vertical_1080x1920.mp4"
            self.run_cmd([
                "ffmpeg", "-y", "-i", str(test_mp4),
                "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,"
                       "pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
                "-c:v", "libx264", str(vertical_mp4)
            ], "Scale to 9:16 vertical (TikTok/Instagram)")

        # 7: Burn subtitles
        if test_mp4.exists():
            srt_file = temp_dir / "test.srt"
            srt_file.write_text(
                "1\n00:00:00,000 --> 00:00:02,000\nTest Subtitle Line\n"
            )
            sub_mp4 = temp_dir / "with_subs.mp4"
            self.run_cmd([
                "ffmpeg", "-y", "-i", str(test_mp4),
                "-vf", f"subtitles={srt_file}",
                "-c:v", "libx264", str(sub_mp4)
            ], "Burn subtitles into video")

        # 8: Audio extraction
        if test_mp4.exists():
            audio_wav = temp_dir / "audio.wav"
            self.run_cmd([
                "ffmpeg", "-y", "-i", str(test_mp4),
                "-vn", "-acodec", "pcm_s16le",
                "-ar", "44100", "-ac", "2", str(audio_wav)
            ], "Extract audio to WAV")

        # 9: Merge video + audio
        audio_wav = temp_dir / "audio.wav"
        if test_mp4.exists() and audio_wav.exists():
            final_mp4 = temp_dir / "final_with_audio.mp4"
            self.run_cmd([
                "ffmpeg", "-y", "-i", str(test_mp4), "-i", str(audio_wav),
                "-c:v", "copy", "-c:a", "aac", "-shortest", str(final_mp4)
            ], "Merge video + audio track")

        # 10: MoviePy integration
        self.log("\n--- MoviePy Integration Test ---")
        try:
            from moviepy.editor import VideoFileClip
            if test_mp4.exists():
                clip = VideoFileClip(str(test_mp4))
                self.log(f"MoviePy loaded video: {clip.size} @ {clip.fps}fps", "PASS")
                self.log(f"Duration: {clip.duration}s", "PASS")
                clip.close()
                self.tests_passed += 1
        except ImportError:
            self.log("MoviePy not installed", "WARN")
        except Exception as e:
            self.tests_failed += 1
            self.log(f"MoviePy failed: {e}", "FAIL")
            self.errors.append({"test": "moviepy_load", "error": str(e)})

        shutil.rmtree(temp_dir, ignore_errors=True)

        print("\n" + "=" * 60)
        print("  SUMMARY")
        print("=" * 60)
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_failed}")

        if self.errors:
            print("\nDetailed Errors:")
            for err in self.errors:
                print(f"  [{err['test']}] {err.get('error', err.get('stderr', 'Unknown'))[:200]}")

        return self.tests_failed == 0


if __name__ == "__main__":
    debugger = FFmpegDebugger()
    success = debugger.test_suite()
    sys.exit(0 if success else 1)
