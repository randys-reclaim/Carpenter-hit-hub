# Full walkthrough: "Olive Pizza Birthday" (one short, start to finish)

Goal: a 20–22 second short from **2 character images and 3 video generations** instead of about 20.

---

## Step 1: Make the character images (once per story, about 5 minutes)
In Flow (image tool, Nano Banana or Imagen) or Higgsfield (Soul), make each character **alone, standing, full body, plain background**. These are your "ingredients."

**WORKER image:**
> Stylized realistic 3D character, video-game cinematic render. Young woman in her 20s, dark brown hair in a low bun, warm brown eyes, green long-sleeve shirt, white apron. Standing, full body, facing camera, neutral expression, plain light-grey studio background, soft even lighting, vertical 9:16.

**BOSS image:**
> Stylized realistic 3D character, video-game cinematic render. Man in his 50s, salt-and-pepper beard, dark hair slicked back into a small bun, white dress shirt, olive-green striped tie, black pants. Standing, full body, facing camera, stern expression, plain light-grey studio background, soft even lighting, vertical 9:16.

**CUSTOMER image:**
> Stylized realistic 3D character, video-game cinematic render. Woman in her 30s, curly blonde hair, blue patterned sweater. Standing, full body, facing camera, tired sad expression, plain light-grey studio background, soft even lighting, vertical 9:16.

Save these. If a face looks off, regenerate now. It's much cheaper than fixing it in every clip.

---

## Step 2: Generate 3 video clips, each with several shots inside
In **Flow, use Ingredients to Video** and add the character images for that clip. In **Higgsfield**, use image-to-video with the main character image. Each prompt asks for **timed shots**, so one 8-second generation gives you 3–4 cuts.

**Style line** (already included below; keep it in every prompt):
`Stylized realistic 3D animation, video-game cinematic look, vertical 9:16, shallow depth of field, slight handheld shake, no text, no subtitles, no dialogue, ambient sound only.`

### Clip 1: Hook (add WORKER and BOSS)
> Stylized realistic 3D animation, video-game cinematic look, vertical 9:16, shallow depth of field, slight handheld shake, no text, no subtitles, no dialogue, ambient sound only. Small pizza shop kitchen, black-and-white checkered floor, stainless steel counters, warm red accent lights.
> [0–2s] Close-up: the young woman in the green shirt and white apron shakes a big container of black olives over a pizza.
> [2–4s] Overhead close-up: the pizza is buried under a mountain of black olives.
> [4–6s] Wide shot: the bearded boss in the white shirt and striped tie storms in from the back of the kitchen, pointing angrily.
> [6–8s] Close-up: the young woman flinches and looks down, nervous.

### Clip 2: Twist (add BOSS)
> Stylized realistic 3D animation, video-game cinematic look, vertical 9:16, shallow depth of field, slight handheld shake, no text, no subtitles, no dialogue, ambient sound only. Same pizza shop kitchen.
> [0–2s] Medium shot: the bearded boss snatches an order ticket off the counter, scowling.
> [2–4s] Over-the-shoulder shot: the ticket in his hand, text blurred and unreadable.
> [4–6s] Slow push-in on his face: anger melts into surprise, then softness.
> [6–8s] He picks up a marker and leans over an open white pizza box lid, smiling gently. Lighting shifts from red to warm gold.

### Clip 3: Payoff (add CUSTOMER)
> Stylized realistic 3D animation, video-game cinematic look, vertical 9:16, shallow depth of field, slight handheld shake, no text, no subtitles, no dialogue, ambient sound only.
> [0–2s] Extreme close-up: a hand draws a simple birthday cake with three candles inside a white pizza box lid.
> [2–5s] Cozy living room: the curly-haired woman in the blue sweater opens the pizza box on a coffee table.
> [5–8s] Close-up: she sees the drawing and the olive pizza, covers her mouth with both hands, eyes watering, then breaks into a big smile. Slow push-in, soft golden light.

**If a clip comes out wrong:** regenerate only that clip. If one shot inside it is bad, cut around it. The punch-in option in Step 4 covers the gap.

---

## Step 3: The VO (Jesse, ElevenLabs)
Paste this into ElevenLabs with Jesse, Stability about 40% and Similarity about 75%:
> She was almost fired… for putting way too many black olives on a pizza.
> Her boss was furious.
> Then he read the order note.
> It was the customer's birthday… and her whole family had forgotten.
> All she asked for was extra olives.
> So he drew her a birthday cake… inside the box.

Save it as `vo.mp3`.

---

## Step 4: Put it together (Claude does this)
Send Claude the 3 clips, `vo.mp3`, and the real clip (receipt or box photo) for the ending. Claude runs:
```bash
python3 tools/assemble.py projects/olive-pizza --punch 2 --reveal real.mp4
```
`script.txt` for this one (the `!` and `+` mark the colored words):
```
She was almost !fired for putting way too many black olives on a pizza.
Her boss was !furious.
Then he read the order note.
It was the customer's +birthday, and her whole family had !forgotten.
All she asked for was extra olives.
So he drew her a +birthday +cake inside the box.
```
`--punch 2` switches between wide, close and medium framing every 2 seconds, so 3 clips with 3–4 shots each look like about 12 cuts, the same pace as Wendy's.

**Result:** `out/final.mp4`, 1080×1920, with captions, the watermark and the Animated-vs-Real ending. Ready to post.

---

## Time comparison
| | Old | New |
|---|---|---|
| Screenshots | about 20 | 0 |
| Video generations | about 20 | 3 (plus 2–3 character images) |
| CapCut editing | 30–60 min | 0 (Claude assembles it) |
