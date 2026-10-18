"""
Generate the scene illustrations for one Kand with FLUX.1 [schnell] (Apache-2.0, commercial use allowed).

Run on a free Google Colab GPU (Runtime > Change runtime type > T4 GPU):

    !git clone https://github.com/shubhampost4u/ramcharitmanas-path
    %cd ramcharitmanas-path
    !pip -q install diffusers transformers accelerate sentencepiece protobuf pillow
    !python tools/make_images.py --kand sundar

Images are written to images/<kand>/sXX.webp (1600x704, WebP, under about 200 KB).
Download the folder, check every image for wrong iconography (number of heads, weapons,
clothing, extra fingers), then commit the good ones to the repo.

Options:
    --only s05 s07   regenerate just these scenes
    --seed 7         change the seed to get a different picture
    --steps 4        schnell is tuned for 1 to 4 steps
"""
import argparse
import json
import os

import torch
from diffusers import FluxPipeline
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("--kand", default="sundar")
ap.add_argument("--only", nargs="*", default=None)
ap.add_argument("--seed", type=int, default=108)
ap.add_argument("--steps", type=int, default=4)
ap.add_argument("--width", type=int, default=1600)
ap.add_argument("--height", type=int, default=704)
ap.add_argument("--max_kb", type=int, default=200)
args = ap.parse_args()

with open(f"data/{args.kand}.scenes.json", encoding="utf-8") as f:
    spec = json.load(f)
style = spec.get("style", "")
scenes = [s for s in spec["scenes"] if not args.only or s["id"] in args.only]

pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-schnell", torch_dtype=torch.bfloat16)
pipe.enable_model_cpu_offload()  # fits a 16 GB T4

out_dir = f"images/{args.kand}"
os.makedirs(out_dir, exist_ok=True)


def save_webp(img: Image.Image, path: str, max_kb: int) -> int:
    q = 85
    while True:
        img.save(path, "WEBP", quality=q, method=6)
        kb = os.path.getsize(path) // 1024
        if kb <= max_kb or q <= 40:
            return kb
        q -= 8


for s in scenes:
    prompt = f"{s['prompt']}, {style}"
    gen = torch.Generator("cpu").manual_seed(args.seed)
    img = pipe(prompt, width=args.width, height=args.height, num_inference_steps=args.steps,
               guidance_scale=0.0, max_sequence_length=256, generator=gen).images[0]
    path = os.path.join(out_dir, f"{s['id']}.webp")
    kb = save_webp(img, path, args.max_kb)
    print(f"{s['id']}  {kb} KB  {s['title']}")
