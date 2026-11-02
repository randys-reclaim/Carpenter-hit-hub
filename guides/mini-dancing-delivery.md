# Mini short: "The Dancing Delivery Driver" (about 16s, 2 clips)

**Real video (16s, no sound):** A little girl in a floral dress dances at her front gate. A delivery driver in an orange hi-vis vest, carrying paper bags, stops on the pavement and dances right back with her, laughing and waving.

**Mini format:** no twist, just a hook and a payoff. 2 clips, short VO, then the real clip side by side for 3–4 seconds.

**Kid warning:** Flow may refuse the little girl, like it refused J-Mac. Try in this order:
1. Flow with the prompts below (the cartoon style sometimes passes)
2. Higgsfield with the same prompts
3. If both refuse: make her a **grandma** in a floral dress. A grandma dancing with the delivery driver works just as well.

---

## Characters
**DRIVER**
```
Stylized 3D animated character, super layered, hyperrealistic but almost cartoonish. Matte skin. Arms slightly long, legs thin. Hair and eyebrows sculpted as solid pieces. Clothing built from cartoonish solid panels in bright neon colors. Super bright saturated colors; blacks are glossy and layered for depth. Friendly Black man in his 40s, short beard, big warm smile, glossy black cap, glossy black jacket and pants, neon orange hi-vis vest with "HOLLY" printed on the back, carrying brown paper delivery bags. Neutral expression, standing, full body, facing camera, plain grey studio background, soft even lighting, vertical 9:16.
```
**LITTLE GIRL** (Grandma version: replace the first line with "Cheerful grandmother in her 70s, short curly white hair")
```
Stylized 3D animated character, super layered, hyperrealistic but almost cartoonish, cartoon proportions. Matte skin. Hair sculpted as solid pieces. Clothing built from cartoonish solid panels in bright neon colors. Super bright saturated colors. Cheerful little girl, light-brown hair in a small ponytail with a neon blue clip, neon pink floral sundress, white sandals. Neutral expression, standing, full body, facing camera, plain grey studio background, soft even lighting, vertical 9:16.
```

## Clip 1 (0–8s): Hook [DRIVER, LITTLE GIRL]
```
Stylized 3D animated video, super layered, hyperrealistic but almost cartoonish, matte skin, slightly long arms and thin legs, solid sculpted hair and eyebrows, cartoonish paneled clothing in bright neon colors, super bright saturated colors, glossy layered blacks for depth, expressive faces, vertical 9:16, shallow depth of field, slight handheld shake, no subtitles, no captions, no dialogue, ambient street sound only. The only readable text in the scene is "HOLLY" where described. Sunny suburban street, front garden with a red brick path and a glossy black iron gate, a white delivery van parked behind with "HOLLY" on its side. [0-2s] Wide shot: the delivery driver in the neon orange vest walks up the pavement carrying paper bags. [2-4s] Shot from behind the little girl at the gate: she spots him and starts wiggling and dancing. [4-6s] Close-up: the driver stops, surprised, then breaks into a huge grin. [6-8s] He sets one bag down and starts dancing back, bouncing his shoulders.
```

## Clip 2 (8–16s): Payoff [DRIVER, LITTLE GIRL]
```
[same style line as Clip 1] Same sunny street, black iron gate, white "HOLLY" van behind. [0-2s] Over-the-shoulder shot from behind the girl: she waves her arms and spins. [2-4s] The driver copies her, waving his arms and spinning with his paper bags. [4-6s] Close-up: the little girl laughing with pure joy. [6-8s] Wide shot: both dancing together on either side of the gate, the driver throws his arms up and laughs, warm golden sunlight, slow push-in.
```

## VO (Jesse, about 12s)
```
She danced at the gate… every time a stranger walked by. Most people kept walking. But the delivery driver stopped… put his bags down… and danced right back. Sometimes the best part of the day… takes thirty seconds.
```
The video only shows one moment, so the VO doesn't claim more than that. "Every time a stranger walked by" is a soft framing. Drop that line if you want to stick strictly to what the video shows.

**script.txt**
```
She danced at the gate every time a stranger walked by.
Most people kept !walking.
But the delivery driver +stopped, put his bags down, and danced right +back.
Sometimes the best part of the day takes +thirty +seconds.
```

## Put it together
```bash
python3 tools/assemble.py projects/dancing-driver --punch 2 --reveal real.mp4 --reveal-seconds 4
```
The real video has no sound, so the reveal runs silent under the end of the VO, which is fine.
