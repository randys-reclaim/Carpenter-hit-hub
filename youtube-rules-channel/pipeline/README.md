# Episode Pipeline

Turns a script into upload-ready videos with almost no manual work.

```
topic idea ──► write_script.py ──► script .md (you edit it)
                                        │
                                        ▼
                                  make_episode.py
              ┌────────────────┬────────┴───────┬─────────────────┐
              ▼                ▼                ▼                 ▼
          frames.py         voice.py       assemble.py     upload_youtube.py
       every image for    ElevenLabs     8-min 16:9 video   private / scheduled
       16:9 + vertical    narration      + 60-s vertical    upload with title,
                          per caption    short              description, tags
```

## Run an episode

```bash
cd youtube-rules-channel/pipeline
pip install -r requirements.txt

# 1. Draft a script (needs ANTHROPIC_API_KEY). Read and edit it before step 2.
python write_script.py "If Your Dog Ever Barks At An Empty Chair... PULL IT OUT" --notice 005

# 2. Make everything: frames, narration, full video, vertical short
export ELEVENLABS_API_KEY=...        # optional; without it you get timed room tone
export ELEVENLABS_VOICE_ID=...       # or set voice_id in channel.json
python make_episode.py ../005-script-dog-empty-chair.md

# 3. Upload the full video as private (one-time Google setup: see upload_youtube.py)
python make_episode.py ../005-script-dog-empty-chair.md --upload --publish-at 2026-11-17T17:00:00Z
```

Output lands in `../episodes/<notice>-<slug>/`:

| File | What it is |
|---|---|
| `frames/clean/*.png` | one image per shot, no caption, for editing by hand in CapCut |
| `frames/16x9/*.png`, `frames/9x16/*.png` | one image per caption line (rebuilt on demand, not kept in git) |
| `video-16x9.mp4` | the full episode, 1080p, slow push-in on each scene |
| `short-9x16.mp4` | cold open + Rule 1 under 60 s, for Shorts, TikTok and Reels |
| `timeline.json` | every caption with its timing |
| `thumbnail.png` | put your thumbnail here before uploading |

## How a script drives the pictures

Every `**[VISUAL]**` line in a script is followed by one or more shot lines:

```markdown
**[VISUAL]** Doorbell cam: the figure stops at the end of the driveway and turns toward the lens.
<!-- shot: doorcam fig=turn ts="03:14:02 AM" -->
```

The shot names a template in `art.py` (33 scenes: doorbell cam, bedroom, phone screens, rule cards, map pins, cars, tires, and more). With several shot lines, each narration line gets the next picture. `python episode.py <script>` lists any cue missing a shot line. New topics usually need one or two new templates in `art.py`.

## Narration choices

- **ElevenLabs (automatic):** set the key and a voice ID. Pick one calm, flat voice and keep it for every episode.
- **Your own voice:** read `../voiceover/<episode>-voiceover.txt` top to bottom in one take, pausing about a second between lines. Then `python split_recording.py ../episodes/<episode> recording.m4a` cuts it into one clip per line, and `python assemble.py ../episodes/<episode>` builds the narrated videos.
- **No voice:** the videos still build, timed from word counts, which is handy for checking the edit.

## Automating further

- **Weekly drafts:** run `write_script.py` on a schedule (cron, or a scheduled task) with the next title from the idea list. A draft lands in the repo for you to review.
- **TikTok and Instagram:** their posting APIs need an approved business app. Until then, schedule `short-9x16.mp4` with a scheduler such as Meta Business Suite (Instagram) or TikTok's own scheduler.
- **Sound effects:** add a notification ding, doorbell or air-hiss track in CapCut, or extend `assemble.py`'s `soundtrack()`.
