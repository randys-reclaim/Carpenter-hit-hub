# Heartwarming Holly: short-video pipeline

3D "true story" shorts in about 20 seconds: a hook where someone looks like the villain, a twist that shows the kind reason, a payoff, then the real footage side by side.

## The faster workflow

| Step | Old way | New way |
|---|---|---|
| 1. Get the reference | Download Wendy's short | Same (ssstik). Send it to Claude |
| 2. Transcript | Type it up | Claude reads the burned-in captions from `sheet.jpg` |
| 3. Rewrite | By hand | Claude writes your new VO script and the scene prompts |
| 4. Scene images | Screenshot her video at 1s, 8s, 16s... | **Skip.** Make one character sheet per story, then generate each clip from a prompt and that reference (see below) |
| 5. Clips | Make about 8s from each screenshot | Same tool (Flow or Higgsfield), but using the prompts plus the character reference |
| 6. Edit | Cut in CapCut | `tools/assemble.py` builds the finished video: clips, VO, captions, watermark and the real-footage reveal |

### Why skip the screenshots
Starting from her frames copies her shots exactly, which is more likely to get flagged as a copy, and the characters change from clip to clip. Instead:
1. Generate **one character image per character** (in Flow, using Nano Banana / Imagen, or in Higgsfield) from the character description in the prompt file.
2. In Flow, use **Ingredients to Video** with those character images and the scene prompt. In Higgsfield, use image-to-video with the character image as the start frame.
3. Generate each 8s clip. The characters stay the same, and the shots are your own.

See `guides/pizza-walkthrough.md` for one short done start to finish.

## Tools

### Break down a reference video
```bash
tools/breakdown.sh wendy_video.mp4 work/towel-boy        # 8s clips (default)
tools/breakdown.sh wendy_video.mp4 work/towel-boy 5      # 5s clips
```
Outputs `clip_starts/` (one frame per clip), `every_second/`, `sheet.jpg` (for reading captions), `audio.m4a`.

### Assemble a finished short
Folder layout:
```
projects/towel-boy/
  clips/01.mp4 02.mp4 03.mp4    # your generated clips, in order (a .png/.jpg is held 2.5s, e.g. a note close-up)
  vo.mp3                        # your voiceover
  script.txt                    # VO text; !word = red keyword, +word = teal keyword
```
Run:
```bash
python3 tools/assemble.py projects/towel-boy --reveal real_footage.mp4
```
Output in `projects/towel-boy/out/`:
- `final.mp4`: 1080x1920 at 30fps, ready to post
- `captions.srt`: for CapCut, if you'd rather finish there

Options: `--punch 2` (fake a cut every 2s inside each clip), `--reveal-seconds 3`, `--watermark "HEARTWARMING HOLLY"`, `--clip-volume 0.15` (clip sound under the VO; set 0 to mute).

Caption timing is estimated from the script. It's close, but check it once.

Needs `ffmpeg` (with libass) and Python 3.
