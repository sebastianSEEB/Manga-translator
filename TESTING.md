# Verification and deferred acceptance

## Verified in the build environment

- 18 Python tests pass with injected OCR/translation components and a mocked
  HTTP LLM response; no user screenshots or paid API calls are used.
- Python source compiles.
- Chrome extension JavaScript passes Node syntax checks.
- Tests exercise real FastAPI routes and real Pillow rendering: authentication,
  PNG validation, screenshot coordinates, reading order, translation cache and
  invalidation, background-job collection, learning output, image response,
  glossary writes in a temporary test directory, safe CSV/Anki output, limits,
  complete/unique translation IDs, one call per page, and expiring memory cache.

One upstream Starlette warning concerns future httpx test-client compatibility;
it did not fail the tests. No production dependency lock across Mac and Windows
has been established.

Commands from the project root after installing requirements:

```bash
python -m pytest -q
python -m compileall -q backend scripts
node --check extension/background.js
node --check extension/content.js
node --check extension/options.js
node --check extension/popup.js
```

## Browser harness included, not executed successfully here

`tests/browser_smoke.cjs` drives the overlay against a simulated page, with a
mocked Chrome messaging API. It checks screenshot/viewport scaling, modes,
selection and stale-result handling. The build environment lacked Chromium;
the attempted browser download failed. This is explicitly **not** a passing
browser-test claim, nor an installed-extension test.

To run later with Node available:

```bash
npm install --no-save playwright
npx playwright install chromium
node tests/browser_smoke.cjs
```

## Deferred live checks

1. Fresh Python 3.11 install on the target Mac/PC: detector import, model download
   and real manga-ocr inference, including accelerator compatibility.
2. Your chosen LLM: JSON/schema support, natural English, glossary consistency,
   character voice, sound effects and correct ID mapping on real manga.
3. Load the unpacked extension in Chrome: actual activeTab permissions,
   captureVisibleTab, background worker lifecycle, capture on YanMaga canvases,
   full-screen viewer behavior, capture scale at 100/125/150% zoom and Retina.
4. Confirm overlays are absent from a recapture and disappear on a page turn.
   Compare coordinates and translations on different page/panel layouts.
5. Learning: contextual readings, ruby alignment and CSV/Anki import on the
   intended applications. Verify readings before relying on study cards.
6. iPhone: Tailscale Serve hostname, token, raw-PNG Shortcut body, Quick Look,
   waking/sleeping desktop behavior and request timeout on real network latency.
7. Performance: record screenshot size, region count, hardware, model and
   end-to-end cold-page latency. Measure cache hits separately. Under five
   seconds remains a target, not a benchmark result.

## Scope boundaries

The app is user-triggered, visible-area translation. It does not bypass a manga
viewer's access restrictions, scrape chapters or save translated pages. White
text covers are implemented; LaMa inpainting is the optional future v2.
The phone path is a rendered screenshot workflow, not a Safari overlay.

## Cloud preparation

Cloud settings and non-destructive glossary seeding are covered by two additional
Python tests. `node tests/backend_url.cjs` passes for valid HTTPS/local endpoints
and rejects insecure cloud URLs and embedded credentials. Docker was unavailable
in the build workspace; no image build or Railway launch is claimed.
