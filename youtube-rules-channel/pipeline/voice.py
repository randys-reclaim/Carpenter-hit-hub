"""Narration: one ElevenLabs clip per caption line.

Needs ELEVENLABS_API_KEY in the environment and a voice_id in channel.json
(or ELEVENLABS_VOICE_ID). To use your own voice instead, record one clip per
caption line as audio/0001.mp3, 0002.mp3... in the episode folder; they are
picked up automatically. With neither, the video uses estimated timings.
"""
import json, os, subprocess, sys, time, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
CH = json.loads((HERE / "channel.json").read_text())

def tts(text, out, key, voice, model):
    body = json.dumps({"text": text, "model_id": model,
                       "voice_settings": {"stability": 0.7, "similarity_boost": 0.75, "style": 0.0}}).encode()
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
                                 data=body, headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                out.write_bytes(r.read())
            return
        except Exception as e:  # rate limits and network blips
            if attempt == 3:
                raise
            print(f"  retry {text[:30]!r}: {e}")
            time.sleep(2 ** (attempt + 1))

def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())

def run(ep_dir):
    key = os.environ.get("ELEVENLABS_API_KEY")
    voice = os.environ.get("ELEVENLABS_VOICE_ID") or CH.get("voice_id")
    ep_dir = Path(ep_dir)
    tl = json.loads((ep_dir / "timeline.json").read_text())
    recorded = all((ep_dir / f'audio/{ln["line"]:04d}.mp3').exists() for ln in tl["lines"])
    if not recorded and (not key or not voice):
        print("voice: no ELEVENLABS_API_KEY / voice_id and no recorded audio/, using estimated timings")
        return False
    (ep_dir / "audio").mkdir(exist_ok=True)
    for ln in tl["lines"]:
        p = ep_dir / f'audio/{ln["line"]:04d}.mp3'
        if not p.exists():
            tts(ln["text"], p, key, voice, CH.get("tts_model", "eleven_multilingual_v2"))
        ln["audio"] = str(p.relative_to(ep_dir))
        ln["audio_dur"] = round(duration(p), 3)
    (ep_dir / "timeline.json").write_text(json.dumps(tl, indent=1))
    print(f"voice: {len(tl['lines'])} lines narrated")
    return True

if __name__ == "__main__":
    run(sys.argv[1])
