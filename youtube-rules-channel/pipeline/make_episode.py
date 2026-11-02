"""One command from finished script to upload-ready videos.

  python make_episode.py ../05-script-smoke-detector.md            # frames, voice, videos
  python make_episode.py ../05-script-smoke-detector.md --upload   # ...then upload to YouTube as private

Steps: frames.py (all images) -> voice.py (ElevenLabs narration, if a key is
set) -> assemble.py (full video + vertical short) -> upload_youtube.py.
"""
import argparse
from pathlib import Path
import frames, voice, assemble

HERE = Path(__file__).parent

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--upload", action="store_true", help="upload the full video to YouTube as private")
    ap.add_argument("--publish-at", help="schedule public release, e.g. 2026-11-10T17:00:00Z")
    a = ap.parse_args()

    ep = frames.build(a.script, HERE.parent / "episodes")
    voiced = voice.run(ep)
    assemble.run(ep)
    print(f"done: {ep}/video-16x9.mp4 and short-9x16.mp4" + ("" if voiced else " (no narration yet: room tone only)"))
    if a.upload:
        import upload_youtube
        upload_youtube.upload(ep, a.script, a.publish_at)

if __name__ == "__main__":
    main()
