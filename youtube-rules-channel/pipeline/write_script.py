"""Draft a new episode script with Claude, in the exact format the pipeline reads.

Usage:
  python write_script.py "If Your Smoke Detector Ever Beeps 13 Times... DO NOT CHANGE THE BATTERY" --notice 005

Needs ANTHROPIC_API_KEY (or an `ant auth login` profile). The two finished
scripts in the folder above are sent as style examples, and the scene catalog
below tells Claude which frame templates exist, so every cue comes back tagged.
Always read and edit the draft before producing it.
"""
import argparse, json, re, sys
from pathlib import Path
import anthropic

HERE = Path(__file__).parent
ROOT = HERE.parent
CH = json.loads((HERE / "channel.json").read_text())

CATALOG = """Scene templates (use these in <!-- shot: ... --> lines; params are key=value, quote values with spaces):
rule n=1..7 text="Short rule name" [glitch=1]      rule title card
title l1=WORD l2="WORDS"                            big two-line command card
icons items=a,b,c [label=...]                       1-3 icons from: playx porchlight wave boot hose steer kettle carseat steps speech bell thermo cupholder home
houses n=7 lit=7                                    row of houses, one lit
doorcam fig=none|stepout|walkaway|turn|wave|stand|walkin|porchwave door=1 moth=1 headlights=1 shimmer=1 footprints=1 porchlight=1 ts="03:12:04 AM" notif="Title|Subtitle"
bedroom person=sleep|awake|lump|climb device=phone|clock clock=6:12 glow=1 x=1 kettle=1 notif="Title|Subtitle"
phone screen=notif|clip|replay|delete|storage|toggle|battery|shared|shared2|remove|clips|feed time=6:01 pct=41 notif="Title|Subtitle"
split mode=walk|figs|days|life [fade=0.2]
pin city=Name extra=couch|doorway|parka|boxes|calendar [big=18]   map pin anecdote
peephole [prints=1] | footprints | doorknob | face | gray count=0:60 ts=...
keypad lit=0419 | kitchen kettle=1 coffee=1 dashglow=1 | mascot [text=...] [sub=...] | endscreen
dash light=on|off|flicker|pulse frost=1 | route bends=1..3 | loop | thermo from=50° to=20° squash=1
car frost=1 sunrise=1 dash=1 figure=kick|kneel happy=1 | tires face=whine|sulk|happy cap=green glow=1 squash=1
tire mode=glow|breath|water|rust|chuck | jamb psi=35 | calendar top=DAYS big=30 light=1 | states
airmachine timer=4:00 price=$2.00 drop=1 off=1 tire=0 | compressor | highway sign=AIR slosh=1 light=1
sign l1=NITROGEN l2=FILLED | wheel tilt=14 hands=1 station=1 light=1
If nothing fits, pick the closest template; a human can add new ones to art.py."""

SYSTEM = f"""You write scripts for "{CH['name']}", a YouTube channel of calm, deadpan "rules" horror: second-person survival notices about ordinary household things behaving slightly wrong. Narrator sign-off: "{CH['signoff']}"

Match the two example scripts exactly in structure and markdown format:
- Header block, "## Upload package" (title, A/B titles, thumbnail, description with chapters, tags, pinned comment), "## Full script", "## Why this topic should perform", "## Production notes".
- Full script: COLD OPEN, RULE 1..RULE 7 (Rule 7 is the twist where the viewer turns out to be part of the anomaly), SIGN-OFF. Each section header ends with its time range, like "### RULE 3: DON'T CHECK THE PORCH (2:15–3:10)".
- Every cue is a "**[VISUAL]** ..." line, followed by one or more "<!-- shot: template params -->" lines (one per narration line if the picture should change line by line), then narration lines.
- Narration lines are 3-10 words, one caption each, with " /" for a half-second pause and " //" for a one-second pause.
- About 820-870 words of narration in total so the video runs about 8 minutes.
- Each rule opens with a true, checkable fact, bends it, ends with a "that's why" payoff explaining a real everyday annoyance, and has one short anecdote ("A woman in <city>...") or one dry joke.
- No gore, no jump scares, no profanity in the first minute. Don't use another channel's names, catchphrases, or "File" numbering.

{CATALOG}

Output only the markdown script, starting with '# Script: "<title>"' and then the line <!-- episode: notice=NNN slug=short-slug -->."""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("title")
    ap.add_argument("--notice", required=True, help="episode number, e.g. 005")
    ap.add_argument("--notes", default="", help="your own lines or ideas to build around")
    a = ap.parse_args()

    examples = "\n\n".join(f"<example_script>\n{p.read_text()}\n</example_script>"
                           for p in sorted(ROOT.glob("0*-script-*.md")))
    ask = f"Write notice {a.notice}: \"{a.title}\"."
    if a.notes:
        ask += f"\n\nKeep these lines or ideas from me, word for word where possible:\n{a.notes}"

    client = anthropic.Anthropic()
    with client.beta.messages.stream(
        model="claude-opus-5-5",
        max_tokens=64000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=SYSTEM,
        messages=[{"role": "user", "content": [
            {"type": "text", "text": examples, "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": ask},
        ]}],
    ) as stream:
        msg = stream.get_final_message()

    if msg.stop_reason == "refusal":
        sys.exit("Claude declined this topic. Try rephrasing the title.")
    text = "".join(b.text for b in msg.content if b.type == "text").strip()
    if msg.stop_reason == "max_tokens":
        print("warning: draft was cut off at max_tokens", file=sys.stderr)
    slug = re.search(r"slug=([\w-]+)", text)
    out = ROOT / f"{a.notice}-script-{slug.group(1) if slug else 'draft'}.md"
    out.write_text(text + "\n")
    print(f"wrote {out.name}  (model: {msg.model}, {msg.usage.output_tokens} output tokens)")

if __name__ == "__main__":
    main()
