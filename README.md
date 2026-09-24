# Manga Translator

**Cloud mode:** no local Python setup needed. Follow [deploy/CLOUD.md](deploy/CLOUD.md) to run OCR/backend on Railway and connect Chrome/iPhone over HTTPS. Hosting and a cloud LLM have separate usage costs. This is a deployment-ready recipe, not a live deployment.

Japanese → English for visible manga pages, with a Chrome Manifest V3 extension,
local OCR, one page-context LLM call, session caching, series glossaries, learning
mode, explicit CSV/Anki exports, and an iPhone screenshot → translated PNG route.

**Implementation complete for stages 1–6; live acceptance testing is deferred.**
This is not a claim of verified YanMaga compatibility, translation quality or
sub-five-second performance. No real manga/model/API/iPhone run was performed
for this delivery. See `TESTING.md` for automated checks and remaining checks.
LaMa inpainting remains the separately optional v2 feature, not part of this build.

## Structure

```text
manga-translator-complete/
├── README.md
├── TESTING.md
├── .env.example
├── .gitignore
├── requirements.txt
├── backend/
│   ├── __init__.py
│   ├── app.py                 # APIs, authentication, bounded background jobs
│   ├── config.py
│   ├── settings.py
│   ├── schemas.py
│   ├── imaging.py
│   ├── engine.py              # Page pipeline and cache keys
│   ├── cache.py               # Bounded, expiring memory only
│   ├── glossary.py            # Explicit persistent series mappings
│   ├── exports.py             # CSV/Anki bytes, no backend files
│   ├── rendering.py           # English PNG for iPhone
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── detector.py
│   │   ├── ocr.py
│   │   ├── reading_order.py
│   │   └── service.py
│   └── translation/
│       ├── __init__.py
│       ├── llm.py
│       ├── models.py
│       └── service.py
├── extension/
│   ├── manifest.json
│   ├── background.js
│   ├── content.js
│   ├── popup.html
│   ├── popup.js
│   ├── options.html
│   ├── options.js
│   └── ui.css
├── glossaries/
│   └── wangan-midnight.json
├── ios/
│   └── SETUP.md
├── scripts/
│   ├── configure.py
│   ├── setup_detector.py
│   └── test_ocr.py
├── tests/
│   ├── test_contract.py
│   ├── test_translation.py
│   └── browser_smoke.cjs
├── models/                   # Downloaded detector weights
└── vendor/                   # Pinned detector source
```

## 1. Install the backend

Install **Python 3.11** and **Git**, extract this folder and open a terminal here.
On Windows use Python from python.org. Do not reuse the stage-1 .venv blindly;
this build adds authentication and new dependencies/configuration.

macOS:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/configure.py
python scripts/setup_detector.py
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/configure.py
python scripts/setup_detector.py
```

If PowerShell blocks activation, use `.\.venv\Scripts\python.exe` in place of
`python`; activation is optional. The configuration script creates `.env` and a
random backend token. Running it again preserves a valid existing token.

The detector setup downloads ONNX weights and pins upstream source to
`440b978563c71b758e31aaa315d100faba1efa2f`. The first backend start also downloads
manga-ocr weights (roughly 400 MB per upstream documentation). Wait for
`Application startup complete`. Model files persist; manga screenshots do not.

Torch and torchvision must be a compatible pair. For NVIDIA acceleration,
install the appropriate pair from https://pytorch.org/get-started/locally/.
The detector uses CPU ONNX for portability. manga-ocr selects its supported
accelerator; set `OCR_FORCE_CPU=true` if necessary. Dependency ranges are not
fully validated cross-platform lockfiles. Python 3.11 is the intended target.

## 2. Configure translation

Edit `.env`. The extension never receives the LLM API key.

**Local LLM (default):** run an OpenAI-compatible server that supports
`/v1/chat/completions` and structured JSON output. Set:

```dotenv
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_MODEL=your-installed-model-name
LLM_API_KEY=
LLM_ALLOW_REMOTE=false
LLM_STRICT_SCHEMA=true
```

The default URL is the common Ollama local port, but this project does not
install or download an LLM for you. Use the exact model name from your server.
For a server supporting JSON mode but not strict JSON schemas, set
`LLM_STRICT_SCHEMA=false`. Outputs are still validated, including exact box IDs.
There are no automatic retries or silent fallbacks that multiply API calls.
Check your local LLM server's own logging settings if you require no retention.

**Cloud API (optional):** use a compatible HTTPS endpoint, set `LLM_MODEL`,
`LLM_API_KEY`, and `LLM_ALLOW_REMOTE=true`. For an OpenAI endpoint, the base URL is
`https://api.openai.com/v1`. Choose an available model that supports the chosen
structured-output mode. API use requires its own credentials/billing.
Only Japanese OCR text plus the series glossary is sent for translation, not
screenshots. Learning requests send the selected Japanese and English text.

`store:false` is sent, but this does **not** prove a provider has zero retention.
If “never shared or retained outside this computer” is strict, keep the LLM local.
Remote-provider policy/configuration remains your responsibility. No cloud
request occurs until you explicitly configure and use it.

## 3. Run

```bash
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --workers 1 --no-access-log
```

Use one worker: models, cache and background jobs belong to that process.
Open http://127.0.0.1:8000/health. Readiness means OCR models loaded;
`translation_configured` only indicates that `LLM_MODEL` is set, not that a
provider has been tested. Restart after changing `.env`.

Optional OCR-only check in another activated terminal:

```bash
python scripts/test_ocr.py "/absolute/path/to/screenshot.png"
```

This prints Japanese JSON to the terminal. It neither creates nor deletes your
input file. Terminal scrollback may retain printed text.

## 4. Load the Chrome extension

1. Open `chrome://extensions` on your Mac/PC.
2. Turn on **Developer mode**.
3. Click **Load unpacked** and select this project's `extension` directory.
4. Open the extension's **Settings**.
5. Copy `BACKEND_TOKEN` from `.env` into **Backend token**. Do not use the LLM key.
6. Keep series ID `wangan-midnight`, then **Save settings → Check connection**.
7. Open a manga page you can view in YanMaga or another ordinary website.
8. Click the extension → **Translate page**, or press **Alt+Shift+T**.

Chrome captures the visible tab after a user gesture using `activeTab`; the
extension does not find image URLs or decode scrambled tiles. It never accesses
pages you cannot already view. There is no automatic site scraping or background
capture. The screenshot includes any website UI currently visible; crop/zoom the
reader appropriately. Content outside the viewport is not translated.

Controls:

- **English / Original / Both** switches the overlay. Both includes Japanese
  and English. **Alt+Shift+O** toggles original/English; Escape shows original.
- Click a translated region for its full text and optional learning details.
- **Translate** captures again; prior overlays are removed from the screenshot.
- **Clear** removes overlay and the tab's selected learning queue.
- **Settings → Clear backend session cache** clears cached OCR/translations,
  lessons and completed jobs. It refuses while a request is running.

Default shortcuts can be changed at `chrome://extensions/shortcuts`.
If loading a new extension version, click **Reload** there and reload manga tabs.

Boxes map original screenshot pixels to the captured viewport width/height,
so regular browser zoom and Retina/high-DPI screens are accounted for. Pinch
zoom must be reset before capture. Scroll, resize, navigation, page clicks,
page-turn keys, detected image/DOM changes, or hiding the tab discard pending
results/overlays. A canvas animation without an input or DOM event cannot be
reliably detected; translate again after an automatic page change.

Text bounds are not full bubble outlines. English uses white covers over those
bounds; no original artwork is inpainted. Small regions shrink to a minimum
font and then scroll; click for full text. Sound effects use smaller bracketed
text. Stylized effects and website UI may be misdetected.

## 5. Glossaries and learning

**Settings → Load series** loads the Wangan Midnight glossary. Add explicit
character mappings to `characters`, for example `"アキオ": "Akio"`, then Save.
Use a new lowercase series ID and new JSON title/terms/characters to create a
series. Glossaries persist as local JSON, and changes invalidate page caches.
Names are never silently inferred and written to disk. Each page receives the
full selected glossary and all detected text in one ordered translation call.

Learning mode shows Japanese, ruby readings when token surfaces align exactly,
word meanings, parts of speech, grammar and English. These are LLM-generated
explanations, not dictionary-certified readings. Names and slang need checking.
When segmentation does not reproduce the source exactly, the UI shows the
whole reading instead of attaching potentially misplaced furigana.

**Save sentence / Save with reading / Save word** adds to a tab-local memory
queue (maximum 500). Press **CSV** or **Anki** to intentionally download it.
This explicit export is the exception to “never save translations.” Reloading
or closing the tab discards the queue. Anki export is UTF-8 tab-separated text
with Japanese, Reading, English and Notes; import it into a matching four-field
note type and map the columns. It is not an `.apkg` deck. HTML is escaped and
CSV formula-like cells are protected.

## 6. iPhone

Follow [`ios/SETUP.md`](ios/SETUP.md): Tailscale Serve privately exposes the
loopback backend to your phone, and an iOS Shortcut sends a screenshot and
shows the translated PNG in Quick Look. No Xcode or Safari extension is needed.
The desktop/server must stay on. The endpoint is implemented; Shortcut setup
must be completed on your own iPhone. No signed installable `.shortcut` is
included, because signing requires the Apple environment.

## API

All endpoints except `/health` require `Authorization: Bearer BACKEND_TOKEN`.

| Method | Route | Input / output |
|---|---|---|
| GET | `/health` | Readiness and whether an LLM model is configured |
| POST | `/ocr` | `{image: base64 PNG}` → dimensions, Japanese regions, timings |
| POST | `/translate` | `{image, series?}` → dimensions, translated regions, timings |
| POST | `/jobs` | Same page input → 202 `{job_id}` |
| GET | `/jobs/{id}` | `running`, `done` + result, or `error` + detail |
| POST | `/learn` | `{jp,en}` → reading, words, grammar |
| POST | `/learn/jobs` | Same learning input → 202 `{job_id}` |
| POST | `/translate/image?series=wangan-midnight` | Raw PNG body → rendered PNG |
| GET | `/glossaries` | Available series IDs and titles |
| GET/PUT | `/glossaries/{id}` | Read/write `{title,terms,characters}` |
| DELETE | `/cache` | Clear backend session data |
| POST | `/export` | `{rows:[{jp,reading,en,notes}],format:"csv" or "anki"}` → download |

`image` accepts raw base64 or `data:image/png;base64,...`. Only PNG input is
accepted. Translation output is an envelope, not a bare array, to preserve
image dimensions, timing and cache status:

```json
{
  "width": 1440,
  "height": 900,
  "coordinate_space": "screenshot_pixels",
  "regions": [
    {"id":"b000","bbox":[980,120,110,190],"jp":"行くぞ","en":"Let's go!","vertical":true,"kind":"dialogue"}
  ],
  "series":"wangan-midnight",
  "cache_hit":false,
  "timing_ms":{"detection":0,"ocr":0,"translation":0,"total":0},
  "warnings":[]
}
```

Above is an illustrative shape; zero timings are placeholders, not measurements.
`bbox` is `[x,y,width,height]` in PNG pixels. IDs are response-local. Reading
order is row-based right-to-left and top-to-bottom; irregular panels and spreads
are approximate. OCR handles vertical crops without rotation. Furigana can be
recognized as part of the input but is not separately returned by manga-ocr.

Requests: maximum 16 MiB including base64, 20 million decoded pixels, 80 regions.
One processing operation runs at a time; overlapping requests receive 429.
The extension uses short background-job requests plus polling to avoid long
service-worker fetches. Completed job results are collected once, bounded to
eight waiting results and expire after five minutes (cleanup every 30 seconds).

## Privacy, cache and performance

No screenshot, OCR result, translation or lesson is written by the backend.
Result/lesson caches are bounded process memory, default 24 pages and 100
lessons for 30 minutes; restart clears them. Set `CACHE_PAGES=0` to disable page
caching. Cache keys include decoded image pixels/dimensions, glossary contents,
model, endpoint and pipeline version. Exact repeated screenshots hit the cache;
changing ads/UI/scroll position can cause a miss.

Settings/token, model files, explicit glossary edits and explicit exports are
persistent by design. Extension storage contains only settings/token; results
remain in the content script's memory. The extension token is restricted to
trusted extension contexts, never passed to the page. The web page can still
observe DOM/layout changes and code running on the same OS is not isolated from
this local application. Memory is not securely erased, and OS swap, browser
crash recovery, screenshots you create yourself or provider logs are outside
the app's non-persistence guarantee.

Local inference telemetry is disabled and upstream manga-ocr text logging is
suppressed. No server access log is enabled by the documented command. HTTP
responses use no-store. Foreign website origins are rejected; extension origins
still need the token. Host allowlisting prevents arbitrary Host headers. Keep
the backend on loopback; use the authenticated Tailscale route for iPhone.

Under five seconds per page is an **unverified target**. CPU OCR across many
regions plus a local/remote LLM may take substantially longer. Measure a cold
page separately from a cache hit. Backend translation timings include decode,
OCR and translation, but exclude Chrome capture, network transfer and overlay
rendering. PNG endpoint timings do not separately expose typesetting time.

## Troubleshooting

- Backend exits immediately: run `scripts/configure.py`, then detector setup;
  confirm the dependencies installed inside the active virtual environment.
- 401: copy the current backend token into extension settings; restart after
  editing `.env`. A token change also requires updating the iPhone Shortcut.
- 429: wait for the current request; simultaneous page/learning requests are
  deliberately rejected rather than queued indefinitely.
- 502/model error: verify the model name, API key and structured-output support.
  Set `LLM_STRICT_SCHEMA=false` only if your endpoint supports JSON mode.
- Remote LLM blocked at startup: use HTTPS and explicit `LLM_ALLOW_REMOTE=true`.
- No/mistaken text: zoom for legibility, use one manga page, check OCR-only output.
- Misaligned/vanishing overlay: keep the page still, reset pinch zoom, wait for
  lazy loading and translate again. Animated canvases require manual recapture.
- iPhone timeout: desktop must be awake; use a smaller screenshot/faster model.
- Unicode Windows terminal: `python -X utf8 scripts/test_ocr.py screenshot.png`.

## Sources and licenses

- Detector: https://github.com/dmMaze/comic-text-detector (GPL-3.0)
- Weights: https://github.com/zyddnys/manga-image-translator/releases/tag/beta-0.2.1
- OCR: https://github.com/kha-white/manga-ocr (Apache-2.0)
- Capture API: https://developer.chrome.com/docs/extensions/reference/api/tabs
- Structured outputs: https://developers.openai.com/api/docs/guides/structured-outputs
- Apple/Tailscale references are linked in `ios/SETUP.md`.

Upstream source, model weights and fonts are not bundled. Their respective
licenses apply if you redistribute a combined installation.
