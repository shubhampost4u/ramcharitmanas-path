"""
Voice the verses of a Kand with an open-source TTS engine and save them in the app's format.

Engines
  parler   AI4Bharat Indic Parler-TTS (Apache-2.0). Voice and pace set by a text description.
  indicf5  AI4Bharat IndicF5 (MIT). Copies voice AND recitation style from a reference clip.
           Give it a 8-15 s recording of a chaupai recited the way you want (your own voice,
           or someone who has given permission) plus the exact words in that clip.

Easiest: open tools/oss_tts.ipynb in Colab and run the cells in order:
https://colab.research.google.com/github/shubhampost4u/ramcharitmanas-path/blob/main/tools/oss_tts.ipynb

Or run on a free Google Colab GPU (Runtime > Change runtime type > T4 GPU):

    !git clone https://github.com/shubhampost4u/ramcharitmanas-path
    %cd ramcharitmanas-path
    !pip -q install -r tools/oss_tts_requirements.txt
    from huggingface_hub import login; from getpass import getpass; login(token=getpass("HF token: "))      # account must have accepted the model's terms

    # 1) listen to 5 verses first (written to audio-test/<engine>/)
    !python tools/oss_tts.py --engine parler --test
    !python tools/oss_tts.py --engine indicf5 --ref my_chaupai.wav --ref-text "जामवंत के बचन सुहाए। सुनि हनुमंत हृदय अति भाए॥" --test

    # 2) whole Kand, saved as audio/sundar-<engine>/ and data/sundar.audio.<engine>.json
    !python tools/oss_tts.py --engine parler
    #    add --as-default to make it the voice the app plays (writes data/sundar.audio.json)

    # 3) save to GitHub (fine-grained token with Contents: read and write on this repo)
    import os, getpass; os.environ["GITHUB_TOKEN"] = getpass.getpass("GitHub token: ")
    !python tools/oss_tts.py --push-only

Already-voiced verses are skipped, so a run that stops halfway can simply be started again.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

import numpy as np

# Colab ships TensorFlow; older transformers versions then try to load it and fail.
# These models only need PyTorch.
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("USE_TORCH", "1")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

REPO = "shubhampost4u/ramcharitmanas-path"
TEST_IDS = ["sk-p01", "sk-002", "sk-006", "sk-052", "sk-120"]
PARLER_VOICE = ("Rohit speaks slowly and calmly in a deep, warm voice, reciting devotional verse "
                "with gentle rhythm and clear pauses at each comma and full stop. "
                "The recording is very high quality with no background noise.")

ap = argparse.ArgumentParser()
ap.add_argument("--kand", default="sundar")
ap.add_argument("--engine", choices=["parler", "indicf5", "sine"], default="parler")
ap.add_argument("--voice", default=PARLER_VOICE, help="Parler description of voice, pace and tone")
ap.add_argument("--ref", help="IndicF5 reference recording (wav/mp3, 8-15 s)")
ap.add_argument("--ref-text", help="exact words spoken in the reference recording")
ap.add_argument("--test", action="store_true", help="only the 5 test verses, into audio-test/")
ap.add_argument("--ids", nargs="*", help="only these verse ids")
ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--gap-ms", type=int, default=450, help="silence between the lines of a verse")
ap.add_argument("--bitrate", default="64k")
ap.add_argument("--as-default", action="store_true", help="also write data/<kand>.audio.json")
ap.add_argument("--push-only", action="store_true", help="commit and push what is already generated")
args = ap.parse_args()


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def push():
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok:
        sys.exit("Set GITHUB_TOKEN first.")
    run(["git", "config", "user.name", "Ramcharitmanas TTS"])
    run(["git", "config", "user.email", "shubhampost4u@users.noreply.github.com"])
    run(["git", "add", "--"] + [d for d in ("audio", "data") if os.path.exists(d)])
    if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode == 0:
        print("Nothing new to push.")
        return
    run(["git", "commit", "-q", "-m", f"Add open-source TTS audio ({args.engine})"])
    url = f"https://x-access-token:{tok}@github.com/{REPO}.git"
    run(["git", "pull", "-q", "--rebase", url, "main"])
    run(["git", "push", "-q", url, "HEAD:main"])
    print("Pushed to GitHub.")


if args.push_only:
    push()
    sys.exit(0)

# ---------- verses (same rules as the app: patch inserts and overrides) ----------
data = json.load(open(f"data/{args.kand}.json", encoding="utf-8"))
verses = list(data["verses"])
pp = f"data/{args.kand}.patch.json"
if os.path.exists(pp):
    patch = json.load(open(pp, encoding="utf-8"))
    for vid, ch in (patch.get("override") or {}).items():
        for v in verses:
            if v["id"] == vid:
                v.update(ch)
    for ins in patch.get("insert") or []:
        if any(v["id"] == ins["verse"]["id"] for v in verses):
            continue
        i = -1 if not ins.get("after") else next((k for k, v in enumerate(verses) if v["id"] == ins["after"]), None)
        if i is None:
            continue
        verses.insert(i + 1, ins["verse"])


def speakable(line):
    """What the voice should read: no verse numbers, no quote marks, a danda at the end."""
    t = re.sub(r"[॥|]+\s*[०-९0-9]*\s*[॥|]*\s*$", "", line)
    t = re.sub(r"[०-९0-9]+", "", t)
    t = re.sub(r"[“”\"'`]", "", t)
    t = re.sub(r"\s*,\s*", ", ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t if t.endswith("।") else t + "।"


ids = args.ids or (TEST_IDS if args.test else None)
todo = [v for v in verses if (ids is None or v["id"] in ids)]
if args.limit:
    todo = todo[: args.limit]

tag = args.engine
out_dir = f"audio-test/{tag}" if args.test else f"audio/{args.kand}-{tag}"
man_path = f"audio-test/{tag}/manifest.json" if args.test else f"data/{args.kand}.audio.{tag}.json"
os.makedirs(out_dir, exist_ok=True)
manifest = json.load(open(man_path, encoding="utf-8")) if os.path.exists(man_path) else {"verses": {}}
manifest.update({"kand": args.kand, "engine": tag,
                 "voice": args.voice if tag == "parler" else (os.path.basename(args.ref or "") if tag == "indicf5" else "test")})

# ---------- engines ----------
if args.engine == "parler":
    import torch
    from parler_tts import ParlerTTSForConditionalGeneration
    from transformers import AutoTokenizer
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    model = ParlerTTSForConditionalGeneration.from_pretrained("ai4bharat/indic-parler-tts").to(dev)
    tok = AutoTokenizer.from_pretrained("ai4bharat/indic-parler-tts")
    dtok = AutoTokenizer.from_pretrained(model.config.text_encoder._name_or_path)
    SR = model.config.sampling_rate
    desc = dtok(args.voice, return_tensors="pt").to(dev)

    def synth(text, seed):
        torch.manual_seed(seed)
        p = tok(text, return_tensors="pt").to(dev)
        g = model.generate(input_ids=desc.input_ids, attention_mask=desc.attention_mask,
                           prompt_input_ids=p.input_ids, prompt_attention_mask=p.attention_mask)
        return g.cpu().numpy().squeeze().astype(np.float32)

elif args.engine == "indicf5":
    if not (args.ref and args.ref_text):
        sys.exit("IndicF5 needs --ref <recording> and --ref-text \"exact words in it\".")
    from transformers import AutoModel
    model = AutoModel.from_pretrained("ai4bharat/IndicF5", trust_remote_code=True)
    SR = 24000

    def synth(text, seed):
        a = model(text, ref_audio_path=args.ref, ref_text=args.ref_text)
        a = np.asarray(a)
        return (a.astype(np.float32) / 32768.0) if a.dtype == np.int16 else a.astype(np.float32)

else:  # 'sine': pipeline check without a GPU
    SR = 24000

    def synth(text, seed):
        n = int(SR * (0.6 + 0.08 * len(text)))
        return (0.2 * np.sin(2 * np.pi * 220 * np.arange(n) / SR)).astype(np.float32)


def trim(a, thresh=0.01, pad=0.08):
    """Cut leading/trailing silence so line timings are tight."""
    idx = np.where(np.abs(a) > thresh)[0]
    if not len(idx):
        return a
    p = int(pad * SR)
    return a[max(0, idx[0] - p): idx[-1] + p]


def to_mp3(a, path):
    with tempfile.NamedTemporaryFile(suffix=".f32", delete=False) as f:
        f.write(np.clip(a, -1, 1).astype(np.float32).tobytes())
        raw = f.name
    run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", raw,
         "-af", "loudnorm=I=-18:TP=-1.5:LRA=11", "-ar", "24000", "-ac", "1", "-b:a", args.bitrate, path])
    os.unlink(raw)


# ---------- render ----------
done = 0
for n, v in enumerate(todo, 1):
    path = f"{out_dir}/{v['id']}.mp3"
    if v["id"] in manifest["verses"] and os.path.exists(path):
        continue
    lines = [speakable(l) for l in v.get("lines", []) if l.strip()]
    parts, starts, t = [], [], 0
    gap = np.zeros(int(SR * args.gap_ms / 1000), dtype=np.float32)
    for k, line in enumerate(lines):
        a = trim(synth(line, seed=1000 + k))
        starts.append(round(t * 1000 / SR))
        parts.append(a)
        t += len(a)
        if k < len(lines) - 1:
            parts.append(gap)
            t += len(gap)
    to_mp3(np.concatenate(parts), path)
    manifest["verses"][v["id"]] = {"file": path, "timestamps": starts, "duration": round(t * 1000 / SR)}
    done += 1
    if done % 10 == 0 or n == len(todo):
        json.dump(manifest, open(man_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{n}/{len(todo)}  {v['id']}  {len(lines)} lines  {t / SR:.1f}s")

json.dump(manifest, open(man_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if args.as_default and not args.test:
    json.dump(manifest, open(f"data/{args.kand}.audio.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"Done: {done} new verses in {out_dir}; manifest {man_path}")
