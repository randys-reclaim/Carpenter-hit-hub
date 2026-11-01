# Mini short: "Flowers From a Stranger" (about 24s, 3 clips + 1 note image)

**Real video (38s):** Three young men sit on a park bench. A stranger in a black hoodie walks up, crouches, and hands one of them a bouquet of pink flowers with a handwritten card, then walks off. The guy reads the card: "I hope you heal from all the things you don't talk about ♥". He breaks down crying, and his friend puts an arm around him.

All the people are adults, so Flow should allow it.

## Characters
**STRANGER**
```
Stylized 3D animated character, super layered, hyperrealistic but almost cartoonish. Matte skin. Arms slightly long, legs thin. Hair and eyebrows sculpted as solid pieces. Clothing built from cartoonish solid panels in bright neon colors. Super bright saturated colors; blacks are glossy and layered for depth. Young Black man in his 20s, short hair, calm kind face, glossy black hoodie with a small neon green "HOLLY" logo on the chest, glossy black joggers, white sneakers with neon blue accents. Neutral expression, standing, full body, facing camera, plain grey studio background, soft even lighting, vertical 9:16.
```
**GUY**
```
Stylized 3D animated character, super layered, hyperrealistic but almost cartoonish. Matte skin. Arms slightly long, legs thin. Hair and eyebrows sculpted as solid pieces. Clothing built from cartoonish solid panels in bright neon colors. Super bright saturated colors; blacks are glossy and layered for depth. Young man in his early 20s, big curly brown hair, bright white t-shirt with a neon red logo, glossy black pants, chunky white-and-grey sneakers. Neutral expression, standing, full body, facing camera, plain grey studio background, soft even lighting, vertical 9:16.
```
**FRIEND**
```
Stylized 3D animated character, super layered, hyperrealistic but almost cartoonish. Matte skin. Arms slightly long, legs thin. Hair and eyebrows sculpted as solid pieces. Clothing built from cartoonish solid panels in bright neon colors. Super bright saturated colors; blacks are glossy and layered for depth. Young man in his early 20s, dark wavy hair, round glasses, neon sky-blue button-up shirt, white pants. Neutral expression, standing, full body, facing camera, plain grey studio background, soft even lighting, vertical 9:16.
```

## Clip style line (start of each clip)
```
Stylized 3D animated video, super layered, hyperrealistic but almost cartoonish, matte skin, slightly long arms and thin legs, solid sculpted hair and eyebrows, cartoonish paneled clothing in bright neon colors, super bright saturated colors, glossy layered blacks for depth, expressive faces, vertical 9:16, shallow depth of field, slight handheld shake, no subtitles, no captions, no dialogue, ambient park sound only. The only readable text in the scene is "HOLLY" where described.
```

## Clip 1 (0–8s): Hook [STRANGER, GUY, FRIEND]
```
[CLIP STYLE LINE] Sunny city park, bright green grass, glossy dark-green park benches, tall trees. [0-2s] Wide shot: the young man with curly hair and his friend in glasses sit laughing on a park bench. [2-4s] Wide shot: the stranger in the black hoodie walks straight toward them holding something behind his back. [4-6s] Close-up: the curly-haired guy stops laughing and looks up, confused and wary. [6-8s] The stranger crouches down in front of him and holds out a big bouquet of neon pink flowers.
```

## Clip 2 (8–16s): The gift [STRANGER, GUY, FRIEND]
```
[CLIP STYLE LINE] Same sunny park bench. [0-2s] Close-up: the curly-haired guy slowly takes the neon pink bouquet; a small white card is tucked inside. [2-4s] The stranger gives a small kind nod, stands up, and walks away without a word. [4-6s] The guy and his friend look at each other, puzzled. [6-8s] Close-up: the guy pulls the small white card out of the flowers and opens it.
```

## Note image (still image, Flow image tool; images handle text much better than video)
```
Close-up of a small cream-colored card held in a hand, handwritten in black marker in neat casual handwriting: "I hope you heal from all the things you don't talk about" with a small hand-drawn heart underneath. Pink flower petals blurred in the background, soft natural light, stylized 3D render, vertical 9:16.
```
If the words come out wrong, regenerate. Save it as `02b_note.png` so it lands between clips 2 and 3. The editing tool holds it for 2.5 seconds with a slow zoom.

## Clip 3 (16–24s): Payoff [GUY, FRIEND]
```
[CLIP STYLE LINE] Same sunny park bench. [0-2s] Close-up: the curly-haired guy reads the card, his face slowly crumbling. [2-4s] He covers his face with his hand and starts crying, shoulders shaking. [4-6s] His friend in glasses puts an arm around him and pulls him close. [6-8s] Wide shot: the two friends on the bench, the guy still holding the neon pink flowers, warm golden light, slow push-in.
```

## VO (Jesse, about 20s)
```
A complete stranger walked up to him in the park… and handed him flowers. No reason. No words. He just walked away. Then he found the note inside. "I hope you heal… from all the things you don't talk about." Sometimes a stranger sees what nobody else does.
```

## script.txt
```
A complete !stranger walked up to him in the park and handed him +flowers.
No reason. No words. He just walked away.
Then he found the +note inside.
I hope you +heal from all the things you don't talk about.
Sometimes a stranger sees what nobody else does.
```

## Put it together
```bash
python3 tools/assemble.py projects/park-flowers --punch 2 --reveal real.mp4 --reveal-seconds 4
```
Clips folder: `01.mp4`, `02.mp4`, `02b_note.png`, `03.mp4`.
