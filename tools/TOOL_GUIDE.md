# Bhrikuty Tool Guide
## Install commands, code samples, and expected output for every pipeline tool

Use this guide to test each tool before choosing which one to use for your final render.

---

## TTS / VOICEOVER TOOLS

---

### Kokoro-TTS
**Type:** Open Source (Apache 2.0) | **Cost:** Free | **GPU:** No (CPU works)  
**Quality:** ⭐⭐⭐⭐ 8.8/10 | **#1 on TTS Arena leaderboard (Jan 2026)**

**Install:**
```bash
pip install kokoro soundfile numpy
```

**Generate voiceover for Phase 4:**
```bash
python tools/tts/kokoro_voiceover.py --phase 4 --voice af_heart --speed 1.0
```

**Direct Python usage:**
```python
from kokoro import KPipeline
import soundfile as sf
import numpy as np

pipeline = KPipeline(lang_code="en-us")

text = "In 2023, a single phishing email drained 4.4 million dollars from one crypto wallet."
audio_chunks = []
for _, _, audio in pipeline(text, voice="af_heart", speed=1.0):
    audio_chunks.append(audio)

combined = np.concatenate(audio_chunks)
sf.write("test_kokoro.wav", combined, samplerate=24000)
# → test_kokoro.wav: 24kHz WAV, ~4 seconds
```

**Available voices:**
| Voice | Description |
|-------|-------------|
| `af_heart` | American Female — warm, clear (recommended for education) |
| `af_bella` | American Female — expressive |
| `am_adam`  | American Male — authoritative |
| `am_michael` | American Male — calm |
| `bf_emma` | British Female — professional |
| `bm_george` | British Male — formal |

**Expected output for 12-min video:**
- File: `phase_4/voiceover/phase_04_kokoro.wav`
- Duration: ~11–13 min
- Sample rate: 24kHz mono WAV
- Speed: ~36x real-time on GPU, ~3x on CPU
- Character: Clean, natural US accent. Consistent pacing. Good for technical educational content. No voice cloning.

**Pros:** Free forever, CPU-capable, commercial safe, fastest open model  
**Cons:** No voice cloning, fixed voices, slightly less expressive than Chatterbox

---

### Chatterbox TTS
**Type:** Open Source (MIT) | **Cost:** Free | **GPU:** Yes (8GB+ VRAM)  
**Quality:** ⭐⭐⭐⭐⭐ 9.0/10 | **Beats ElevenLabs in 63.75% of blind tests**

**Install:**
```bash
pip install chatterbox-tts torch torchaudio
# Requires CUDA — verify: python -c "import torch; print(torch.cuda.is_available())"
```

**Generate voiceover for Phase 4 (with voice cloning):**
```bash
# With voice reference clip (5–10 second WAV of your voice)
python tools/tts/chatterbox_voiceover.py --phase 4 --reference my_voice.wav

# Without reference (default voice)
python tools/tts/chatterbox_voiceover.py --phase 4
```

**Direct Python usage:**
```python
import torch
import torchaudio
from chatterbox.tts import ChatterboxTTS

model = ChatterboxTTS.from_pretrained(device="cuda")

wav = model.generate(
    text="In 2023, a single phishing email drained 4.4 million dollars.",
    audio_prompt_path="my_voice.wav",  # optional — remove for default voice
    exaggeration=0.5,   # 0.25=subtle, 0.5=natural, 0.75=expressive
    cfg_weight=0.5,     # 0=creative, 1=faithful to reference
)
torchaudio.save("test_chatterbox.wav", wav, model.sr)
# → 23kHz WAV, sounds like the reference clip voice
```

**Expected output for 12-min video:**
- File: `phase_4/voiceover/phase_04_chatterbox.wav`
- Duration: ~11–13 min
- Sample rate: 22–24kHz WAV
- Speed: ~5–8x real-time on RTX 3090
- Character: Indistinguishable from human narration when given a good reference clip. Natural emphasis on technical terms. Subtle Perth watermark embedded (inaudible).

**Pros:** Best open-source quality, voice cloning, MIT commercial license  
**Cons:** Requires 8GB+ VRAM GPU, 2GB model download

---

### ElevenLabs
**Type:** Paid | **Cost:** Free (10k chars/mo) → Starter $5/mo → Creator $22/mo  
**Quality:** ⭐⭐⭐⭐⭐ 9.5/10 | **Industry standard**

**Install:**
```bash
pip install elevenlabs
export ELEVENLABS_API_KEY=your_key_here
```

**Generate voiceover for Phase 4:**
```bash
python tools/tts/elevenlabs_voiceover.py --phase 4 --voice_id YOUR_VOICE_ID --model turbo
```

**List your available voices:**
```bash
python tools/tts/elevenlabs_voiceover.py --phase 4 --list_voices
```

**Direct Python usage:**
```python
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

client = ElevenLabs(api_key="your_key")

audio = client.text_to_speech.convert(
    text="In 2023, a single phishing email drained 4.4 million dollars.",
    voice_id="pNInz6obpgDQGcFmaJgB",  # Adam — clear, authoritative
    model_id="eleven_turbo_v2_5",
    voice_settings=VoiceSettings(stability=0.65, similarity_boost=0.80),
    output_format="mp3_44100_128",
)
with open("test_elevenlabs.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)
# → 44.1kHz MP3, near-human quality
```

**Cost for Phase 4 (~9000 characters):**
| Plan | Cost |
|------|------|
| Free tier | $0 (10k chars/mo total) |
| Starter $5/mo | Covered (30k chars/mo) |
| Creator $22/mo | Covered + voice cloning |

**Expected output for 12-min video:**
- File: `phase_4/voiceover/phase_04_elevenlabs.mp3`
- Duration: ~11–13 min
- Sample rate: 44.1kHz stereo MP3 (128kbps)
- Character: Near-human prosody. Correct stress on technical terms (decentralization, seed phrase). Natural pause variation. No robotic artifacts.

**Pros:** Best quality, 32+ languages, fastest (75ms Flash model), voice cloning  
**Cons:** Cost scales with volume, cloud dependency, data leaves your machine

---

### F5-TTS
**Type:** Open Source (MIT) | **Cost:** Free | **GPU:** Yes (required)  
**Quality:** ⭐⭐⭐⭐ 8.2/10

**Install:**
```bash
pip install f5-tts
```

**Usage:**
```bash
f5-tts_infer-cli \
  --model F5TTS_v1_Base \
  --ref_audio "reference.wav" \
  --ref_text "Reference text spoken in the audio" \
  --gen_text "In 2023, a single phishing email drained 4.4 million dollars." \
  --output_file test_f5.wav
```

**Expected output:** 16kHz WAV. Good EN/ZH bilingual support. 7x real-time on GPU. Use if Chatterbox has VRAM issues.

---

### Qwen3-TTS / DashScope (Current Default)
**Type:** Freemium | **Cost:** Pay-per-use (API) or free local weights  
**Quality:** ⭐⭐⭐⭐ 8.7/10

**Install:**
```bash
pip install dashscope
export DASHSCOPE_API_KEY=your_key
```

**Usage (existing pipeline):**
```bash
python myvideo/edit/generate_voiceover.py --script phase_4/script.md
```

**Expected output:** Streaming MP3. Best for Chinese/Japanese content. Keep as fallback.

---

## VIDEO RENDERING / MOTION GRAPHICS TOOLS

---

### FFmpeg (Current Base — Keep)
**Type:** Free (GPL/LGPL) | **Cost:** $0 | **Approach:** Pipeline CLI

**Install:** Already present. Verify: `ffmpeg -version`

**Render infographic card overlay on video:**
```bash
ffmpeg -i input.mp4 -i card_01.png \
  -filter_complex "[0:v][1:v]overlay=x=40:y=40:enable='between(t,2,8)'" \
  -c:v libx264 -crf 20 output.mp4
```

**Add text overlay with brand colors:**
```bash
ffmpeg -i input.mp4 \
  -vf "drawtext=text='Chain Clarity | Phase 4':fontcolor=#00D4AA:fontsize=48:x=40:y=40" \
  -c:v libx264 -crf 20 output.mp4
```

**Crop 16:9 to 9:16 for TikTok:**
```bash
ffmpeg -i input.mp4 \
  -vf "crop=608:1080:656:0,scale=1080:1920" \
  -c:v libx264 -crf 20 output_vertical.mp4
```

**Expected output:** Pixel-perfect compositing. No spring animations. Use as transcoding backbone.

---

### MoviePy
**Type:** Free (MIT) | **Cost:** $0 | **Approach:** Python pipeline

**Install:**
```bash
pip install moviepy
# Requires ffmpeg installed
```

**Composite script + audio + card animation:**
```python
from moviepy import VideoFileClip, ImageClip, AudioFileClip, CompositeVideoClip, TextClip

# Load base video
video = VideoFileClip("base.mp4")

# Add voiceover
audio = AudioFileClip("phase_4/voiceover/phase_04_kokoro.wav")
video = video.with_audio(audio)

# Overlay infographic card at 2s for 6 seconds
card = ImageClip("phase_4/infographic_assets/card_01.png") \
    .resized(width=400) \
    .with_position(("right", "bottom")) \
    .with_start(2).with_end(8) \
    .with_duration(6)

# Composite
final = CompositeVideoClip([video, card])
final.write_videofile("output.mp4", codec="libx264", fps=24)
```

**Expected output:** 1080p MP4 with layered compositing. Easier than raw FFmpeg for complex multi-layer compositions. Good Python-native upgrade path from PIL.

---

### Remotion (In repo — `remotion/`)
**Type:** Freemium | **Cost:** Free for individuals | **Approach:** Code-as-video (React)

**Install:**
```bash
cd remotion && npm install
```

**Preview cards in browser:**
```bash
cd remotion && npx remotion studio
# Open http://localhost:3000
```

**Render Phase 4 cards:**
```bash
node remotion/scripts/render_all_cards.js --phase 4
# → _output/phase_04/instagram/card_01.mp4
# → _output/phase_04/instagram/card_01.png
```

**Custom composition — render full video:**
```typescript
// In remotion/src/compositions/FullVideo.tsx
import { Composition } from 'remotion'
import { BRAND } from '../BrandColors'

export const FullVideoRoot = () => (
  <Composition
    id="FullVideo"
    component={FullVideoComposition}
    durationInFrames={12 * 60 * 30}  // 12 min @ 30fps
    fps={30}
    width={1920}
    height={1080}
    defaultProps={{ phase: 4 }}
  />
)
```

**Expected output:** React-component-driven animated video. Spring physics, SVG animations, synchronized audio. Professional motion graphics quality. The best upgrade for visual quality.

---

### Motion Canvas
**Type:** Free (MIT) | **Cost:** $0

**Install:**
```bash
npm create motion-canvas@latest blockchain-animation
cd blockchain-animation && npm install && npm start
```

**Animate a blockchain diagram:**
```typescript
import { makeScene2D, Circle, Line, Text } from '@motion-canvas/2d'
import { createRef, waitFor, all } from '@motion-canvas/core'

export default makeScene2D(function* (view) {
  const node1 = createRef<Circle>()
  view.add(<Circle ref={node1} size={80} fill="#00D4AA" x={-200} opacity={0} />)

  yield* node1().opacity(1, 1)  // Fade in
  yield* node1().position.x(0, 0.5)  // Move center
  // ... build full chain animation
})
```

**Expected output:** 3Blue1Brown-quality mathematical animation. Export as PNG sequence → FFmpeg encode. Use for 2–3 signature animations per video, not full assembly.

---

## TRANSCRIPTION / SUBTITLES

---

### WhisperX (Best Open Source)
**Type:** Free (BSD-4) | **Cost:** $0 | **GPU:** Recommended

**Install:**
```bash
pip install whisperx
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**Transcribe Phase 4 video:**
```bash
whisperx _output/phase_04/youtube/final_1080p.mp4 \
  --model large-v3-turbo \
  --language en \
  --word_timestamps True \
  --output_dir phase_4/ \
  --output_format srt

# → phase_4/final_1080p.srt (word-level timestamps)
# → phase_4/final_1080p.json (full data with speaker labels)
```

**Python usage:**
```python
import whisperx
import gc

device = "cuda"
model = whisperx.load_model("large-v3-turbo", device, compute_type="float16")

audio = whisperx.load_audio("final_1080p.mp4")
result = model.transcribe(audio, batch_size=16)

# Word-level timestamps
model_a, metadata = whisperx.load_align_model(language_code="en", device=device)
result = whisperx.align(result["segments"], model_a, metadata, audio, device)

# Save SRT
with open("subtitles_auto.srt", "w") as f:
    for i, seg in enumerate(result["segments"]):
        f.write(f"{i+1}\n{format_ts(seg['start'])} --> {format_ts(seg['end'])}\n{seg['text'].strip()}\n\n")
```

**Expected output for 12-min blockchain video:**
- SRT file with 180–220 subtitle entries
- Word-level timestamps accurate to ±20ms
- Technical terms (DeFi, UTXO, zkEVM) transcribed correctly
- Processing time: ~1–2 min on GPU, ~5–8 min on CPU

---

### faster-whisper (CPU-Friendly)
**Type:** Free (MIT) | **Cost:** $0 | **GPU:** Optional

**Install:**
```bash
pip install faster-whisper
```

**Usage:**
```python
from faster_whisper import WhisperModel

model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
segments, info = model.transcribe("final_1080p.mp4", word_timestamps=True)

with open("subtitles.srt", "w") as f:
    for i, seg in enumerate(segments):
        f.write(f"{i+1}\n{seg.start:.3f} --> {seg.end:.3f}\n{seg.text.strip()}\n\n")
```

**Expected output:** Same accuracy as WhisperX. No diarization. CPU viable with INT8 quantization.

---

### AssemblyAI (Best Paid — Auto YouTube Chapters)
**Type:** Paid | **Cost:** ~$0.03 per 12-min video | **Unique feature:** Auto chapters

**Install:**
```bash
pip install assemblyai
export ASSEMBLYAI_API_KEY=your_key
```

**Usage:**
```python
import assemblyai as aai

transcriber = aai.Transcriber()
transcript = transcriber.transcribe(
    "https://storage.example.com/phase_4.mp4",
    config=aai.TranscriptionConfig(
        auto_chapters=True,      # YouTube chapter timestamps!
        speaker_labels=True,
        word_boost=["DeFi", "blockchain", "seed phrase", "UTXO"],
    )
)

# SRT output
with open("subtitles.srt", "w") as f:
    f.write(transcript.export_subtitles_srt(chars_per_caption=50))

# Chapter markers for YouTube description
for chapter in transcript.chapters:
    print(f"{chapter.start // 1000 // 60}:{chapter.start // 1000 % 60:02d} {chapter.gist}")
```

**Expected output:** SRT + JSON + auto chapter markers. Unique feature: chapters like "Introduction to Blockchain", "How Mining Works" auto-detected — paste directly into YouTube description.

---

## IMAGE / THUMBNAIL GENERATION

---

### FLUX.1 via BFL API (Best Quality — No Local GPU)
**Type:** Paid | **Cost:** ~$0.055/image (pro), ~$0.003/image (schnell)

**Install:**
```bash
pip install requests
export BFL_API_KEY=your_key
```

**Generate blockchain thumbnail:**
```python
import requests, time, os

def generate_flux_image(prompt: str, width=1280, height=720) -> bytes:
    resp = requests.post(
        "https://api.bfl.ai/v1/flux-pro-1.1",
        headers={"X-Key": os.environ["BFL_API_KEY"]},
        json={"prompt": prompt, "width": width, "height": height, "steps": 28}
    )
    task_id = resp.json()["id"]

    while True:
        result = requests.get(
            f"https://api.bfl.ai/v1/get_result?id={task_id}",
            headers={"X-Key": os.environ["BFL_API_KEY"]}
        ).json()
        if result["status"] == "Ready":
            return requests.get(result["result"]["sample"]).content
        time.sleep(1)

prompt = (
    "YouTube thumbnail, dramatic split scene: left side gold Bitcoin coins "
    "with cinematic lighting, right side abstract blockchain network nodes glowing "
    "teal, bold white text 'BLOCKCHAIN SECURITY 2024' top center, "
    "dark navy background #0A0E1A, photorealistic, 4K"
)
image_bytes = generate_flux_image(prompt)
with open("thumbnail_phase4.jpg", "wb") as f:
    f.write(image_bytes)
```

**Expected output:** 1280×720 JPEG. Photorealistic blockchain visualization with readable bold text. Sharp text (FLUX far outperforms SD for text rendering). Generated in ~15–30 seconds.

---

### Ideogram v2 (Best Text-in-Image)
**Type:** Paid | **Cost:** ~$0.08/image

**Best for:** Thumbnails where the text IS the thumbnail (e.g., "HOW CRYPTO GETS STOLEN" in giant bold letters).

```python
import requests, os

response = requests.post(
    "https://api.ideogram.ai/generate",
    headers={"Api-Key": os.environ["IDEOGRAM_API_KEY"]},
    json={
        "image_request": {
            "prompt": "YouTube thumbnail: bold text 'HOW CRYPTO GETS STOLEN' in white on dark navy #0A0E1A background, dramatic red security breach visual, teal accent #00D4AA glow effects, professional educational channel style",
            "aspect_ratio": "ASPECT_16_9",
            "model": "V_2",
            "magic_prompt_option": "AUTO",
        }
    }
)
url = response.json()["data"][0]["url"]
```

**Expected output:** 1280×720 JPEG with best-in-class text rendering. Text is always readable and properly positioned.

---

## INTEGRATION — SWAPPING TOOLS IN PIPELINE.PY

Each pipeline stage accepts an `--engine` flag:

```bash
# TTS engine
python pipeline.py --phase 4 --tts kokoro      # free, CPU
python pipeline.py --phase 4 --tts chatterbox  # free, GPU
python pipeline.py --phase 4 --tts elevenlabs  # paid

# Transcription engine
python pipeline.py --phase 4 --transcribe whisperx    # free, GPU
python pipeline.py --phase 4 --transcribe faster      # free, CPU
python pipeline.py --phase 4 --transcribe assemblyai  # paid, auto-chapters

# Image generation
python pipeline.py --phase 4 --images flux    # best quality
python pipeline.py --phase 4 --images html    # current (zero cost)
```

All engines produce the same output format — switching requires only a CLI flag change, no code modification.

---

## QUICK DECISION MATRIX

| I have... | Use for TTS | Use for Subtitles | Use for Images |
|-----------|-------------|-------------------|----------------|
| No GPU, no budget | Kokoro-TTS | faster-whisper | HTML cards |
| GPU (8GB+), no budget | Chatterbox TTS | WhisperX | FLUX.1 local |
| $20/mo budget | ElevenLabs Starter | AssemblyAI | Ideogram |
| Best quality needed | ElevenLabs Creator | Gladia Solaria | FLUX.1 pro |
| Multilingual content | Qwen3-TTS | Gladia (100 langs) | FLUX.1 pro |
