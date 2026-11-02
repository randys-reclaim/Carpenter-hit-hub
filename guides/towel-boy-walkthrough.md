# Full walkthrough: "The Towel Boy" (long version, about 40 seconds)

**Real story:** On February 15, 2006, at Greece Athena High School in New York, Jason McElwain, an autistic student, was the basketball team's manager and handed out water and towels. On senior night the coach gave him a jersey and put him in with about 4 minutes left. He missed his first two shots, then made six 3-pointers and finished with 20 points. The crowd stormed the court and carried him off.
Real footage for the ending: search "Jason McElwain 20 points 2006".

**Plan:** about 40 seconds = **5 clips × 8 seconds**, each with 3–4 timed shots (about 18 cuts total), plus `--punch 2`.

---

## Step 1: Character images (make once, reuse in every clip)

**TOWEL BOY:**
> Stylized realistic 3D character, video-game cinematic render. Skinny teenage boy, 17, short light-brown hair, shy kind eyes, slight nervous smile. Wearing a grey hoodie and khaki pants. Standing, full body, facing camera, plain light-grey studio background, soft even lighting, vertical 9:16.

**TOWEL BOY IN UNIFORM** (same boy, for clips 3–5):
> Same character as the reference image: skinny teenage boy, short light-brown hair, shy kind eyes. Now wearing a white basketball jersey with royal-blue trim and the number 52, white shorts with blue stripes, white socks, white sneakers. Standing, full body, plain light-grey background, vertical 9:16.

**COACH:**
> Stylized realistic 3D character, video-game cinematic render. Man in his 50s, thick wavy grey hair, clean shaven, kind but tough face, purple polo shirt, khaki pants, whistle around neck. Standing, full body, facing camera, plain light-grey studio background, soft even lighting, vertical 9:16.

**Set:** high school gym, royal-blue walls and wall padding, packed bleachers, red digital scoreboard. Already written into every prompt below.

---

## Step 2: 5 clips with timed shots
Every prompt starts with the same style line. In Flow, use **Ingredients to Video** with the listed character images.

### Clip 1 (0–8s): Who he is [TOWEL BOY, COACH]
> Stylized realistic 3D animation, video-game cinematic look, vertical 9:16, shallow depth of field, slight handheld shake, no text, no subtitles, no dialogue, ambient gym sound only. High school gym with royal-blue walls and packed bleachers.
> [0–2s] Close-up: the skinny boy in the grey hoodie carries a tall stack of white towels.
> [2–4s] Medium shot: he walks along the bench handing towels to players in white-and-blue uniforms; none of them look at him.
> [4–6s] Close-up: he fills paper cups with water at a cooler, alone.
> [6–8s] Wide shot from behind: he sits at the far end of the bench, watching the game.

### Clip 2 (8–16s): The jersey [TOWEL BOY, COACH]
> [same style line] Same gym, before the game, bright lights.
> [0–2s] Medium shot: the grey-haired coach in the purple polo walks up to the boy holding a folded white jersey.
> [2–4s] Close-up: the jersey unfolds to show the number 52.
> [4–6s] Close-up of the boy's face: shock, then a huge disbelieving smile.
> [6–8s] He hugs the jersey to his chest; the coach pats his shoulder.

### Clip 3 (16–24s): Four minutes left [TOWEL BOY IN UNIFORM, COACH]
> [same style line] Same gym, packed loud crowd.
> [0–2s] Close-up: the red scoreboard clock reads 4:00.
> [2–4s] The coach turns to the bench and points at the boy in jersey 52.
> [4–6s] The boy stands up and jogs onto the court, nervous, the crowd rising.
> [6–8s] Close-up: he catches a pass and looks up at the hoop, taking a deep breath.

### Clip 4 (24–32s): Misses, then the first three [TOWEL BOY IN UNIFORM]
> [same style line] Same gym.
> [0–2s] He shoots; the ball misses the rim completely.
> [2–4s] Close-up: his face drops, embarrassed. The crowd groans.
> [4–6s] He shoots again; the ball bounces off the rim.
> [6–8s] He catches the ball behind the three-point line and shoots; slow-motion close-up as it swishes through the net.

### Clip 5 (32–40s): Twenty points [TOWEL BOY IN UNIFORM, COACH]
> [same style line] Same gym, crowd going wild.
> [0–2s] Another three-pointer swishes; students in the bleachers jump up screaming.
> [2–4s] Another swish; the coach throws both arms in the air.
> [4–6s] The buzzer sounds and the scoreboard flashes; the crowd floods the court.
> [6–8s] Students lift the boy onto their shoulders; he grins with both arms raised, confetti-bright lighting, slow push-in.

---

## Step 3: VO (Jesse) and script.txt
**Paste into ElevenLabs** (Jesse, Stability about 40%):
> For four years… his only job was handing out towels.
> Water. Towels. Then back to the end of the bench.
> But on senior night… the coach handed him something else.
> A jersey. Number fifty-two.
> With four minutes left… he walked onto the court.
> His first shot missed everything.
> His second shot missed too.
> Then he hit a three.
> And another. And another.
> Six three-pointers. Twenty points. In four minutes.
> And the whole gym ran onto the court… to carry him.

**script.txt** (`!` = red, `+` = teal):
```
For four years his only job was handing out !towels.
Water. Towels. Then back to the end of the !bench.
But on senior night the coach handed him something else.
A +jersey. Number fifty-two.
With four minutes left he walked onto the court.
His first shot !missed everything.
His second shot !missed too.
Then he hit a +three.
And +another. And +another.
Six three-pointers. +Twenty +points. In four minutes.
And the whole gym ran onto the court to +carry +him.
```

---

## Step 4: Put it together (Claude does this)
```bash
python3 tools/assemble.py projects/towel-boy --punch 2 --reveal jmac_real.mp4 --reveal-seconds 4
```
Use 4 seconds for the reveal on this one. The real crowd-storming footage is the best part, so let it play.

## Notes for longer stories
- **About 8 seconds of VO per clip.** Count the VO length, divide by 8, and that's how many clips you need.
- **Two images for a character who changes outfits** (hoodie, then uniform), made from the same face.
- **The same set line in every prompt** keeps the gym consistent across clips.
- **If a clip comes out wrong,** regenerate only that clip. Don't redo the whole short.
