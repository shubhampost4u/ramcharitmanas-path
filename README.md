# Ramcharitmanas Path

Interactive web app for the path of Shri Ramcharitmanas (Goswami Tulsidas): Devanagari text, transliteration, word meanings, Hindi and English meanings, and Hindi/English voice explanation.

Static site, no build step. Host on GitHub Pages, Cloudflare Pages or Netlify.

## Layout

```
index.html          the app
data/<kand>.json          verses and meanings, one file per Kand (written by the n8n workflow)
data/<kand>.scenes.json   scenes: which doha group each illustration starts at, plus its image prompt
source/<kand>.json        original lines with the public-domain commentary, gaps and duplicates found
images/             scene illustrations (FLUX.1 schnell), WebP under 200 KB
audio/              recitation and explanation mp3 files
```

## Verse record (`data/<kand>.json → verses[]`)

| field | meaning |
|---|---|
| `id` | `sk-001` style id |
| `scene` | scene id from `scenes[]` |
| `type`, `n` | चौपाई / दोहा / सोरठा / छंद / श्लोक and its number |
| `lines[]` | Devanagari lines |
| `tr[]` | transliteration per line |
| `words[]` | `[word, Hindi gloss, English gloss]` |
| `hi`, `en` | meaning |
| `ctx_hi`, `ctx_en` | context (भाव) |
| `status` | `draft` → `reviewed` → `approved` |
| `audio` | optional `{verse, exp_hi, exp_en}` file paths |
| `timestamps` | optional ms where each line starts in `audio.verse` |

Meanings are AI-assisted drafts (Gemini via n8n) and must be reviewed by a scholar before `status` is set to `approved`. The original text is public domain; no copyrighted translation is used.

## Workflow

The n8n workflow **Ramcharitmanas: translate and save to GitHub** reads a Kand from the PD-1996 edition on Hindi Wikisource, drafts meanings with Gemini (using the edition's own public-domain commentary as reference) and commits `data/<kand>.json` and `source/<kand>.json`. Change the Kand, page range and `testLimit` in its Settings node.

Gaps: a few scan pages have no proofread text on Wikisource. They are listed in `source/<kand>.json → gaps` with the verses on either side; those verses must be added by hand.

## Review mode

Open the app with `#review` at the end of the URL. Each verse then shows its id, status, a link to its Wikisource scan page and any text correction Gemini suggested (`suggested_lines`). Corrections are never applied automatically.

## Images

`data/sundar.scenes.json` holds one prompt per scene plus a shared style. Generate with FLUX.1 [schnell] (Apache-2.0, commercial use allowed), 16:7 or 1600×700, convert to WebP under 200 KB, and save as `images/sundar/sXX.webp`. Until a file exists the app shows the prompt in its place.

## Offline

`manifest.webmanifest` and `sw.js` make the app installable and usable offline once hosted on HTTPS (GitHub Pages). Bump `VERSION` in `sw.js` after changing the app so phones pick up the new version.
