# Ramcharitmanas Path

Interactive web app for the path of Shri Ramcharitmanas (Goswami Tulsidas): Devanagari text, transliteration, word meanings, Hindi and English meanings, and Hindi/English voice explanation.

Static site, no build step. Host on GitHub Pages, Cloudflare Pages or Netlify.

## Layout

```
index.html          the app
data/<kand>.json    one file per Kand (sundar, bal, ayodhya, aranya, kishkindha, lanka, uttar)
source/<kand>.txt   base text, one verse per block (input for the n8n workflow)
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
