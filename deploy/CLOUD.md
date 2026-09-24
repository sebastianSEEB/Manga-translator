# Run processing in the cloud (Railway)

The cloud service runs detection, Japanese OCR, caching and image rendering.
A configured cloud LLM API performs translation and learning explanations.
Chrome only captures and overlays the visible page; Python is not required on
your PC. The iPhone Shortcut calls the same HTTPS service with no Tailscale.

This repository is prepared for deployment, not proof of a live deployment.
The Docker image and real OCR/LLM flow must be verified on the host. Docker was
not available in the build workspace. Five-second response time is unverified.

## Hosting choice and cost

Railway can build a Dockerfile directly from this GitHub repository and provide
an HTTPS domain. Its Hobby plan has a $5 monthly minimum including $5 usage;
usage above that is additional. At the time this guide was prepared, RAM costs
$10 per GB-month and CPU $20 per vCPU-month, metered by usage. A continuously
resident 2 GB model process alone would therefore use about $20/month of RAM,
before CPU, storage, network or LLM charges. That is an illustrative calculation,
not a measured footprint or a quote for this app. Set a spending limit and inspect
actual metrics after startup. Do not assume this runs for $5/month or for free.

Start with access to at least 4 GB RAM for loading/testing, then right-size after
measuring. This is a starting allowance, not a verified requirement. The CPU
image is selected for simple hosting; a GPU host may be needed for your latency
target. One replica and one worker are required: background jobs/cache are local
to that process. Do not enable horizontal replicas with the current design.

## Deploy from GitHub

1. Sign in at https://railway.com and connect your GitHub account/repository.
2. Create a project/service from `sebastianSEEB/Manga-translator`, branch `main`.
   Railway detects the root `Dockerfile`. Do not add a different Start Command.
3. Add the service variables below before deploying. A first auto-deploy without
   the token will fail intentionally; configure variables and redeploy.
4. Set deployment healthcheck path `/health`, timeout 300 seconds (raise if actual
   model startup needs it). Keep one replica. Set resource/spending limits.
5. Add a volume mounted at `/data` and set `GLOSSARY_DIR=/data/glossaries` if you
   want edits made in the extension to survive a redeploy. Only explicit glossary
   mappings are written there, not pages, translations or lessons. Without a
   volume, use repository glossary files as the durable source of truth.
6. Deploy. The first image build downloads Python packages, detector source and
   model weights. This can take several minutes. The models are baked into the
   image so runtime does not redownload them.
7. Under service Settings → Networking, **Generate Domain**. Railway supplies
   `RAILWAY_PUBLIC_DOMAIN`; restart/redeploy once it is present. If a custom host
   is used, add its exact hostname to `EXTRA_ALLOWED_HOSTS` as well.
8. Open `https://YOUR-HOST/health`. It should return `status: ready` and
   `translation_configured: true`. This checks model loading and configuration,
   not whether your LLM key/model actually works. Test one page to establish that.

## Service variables

| Variable | Value |
|---|---|
| `BACKEND_TOKEN` | A random secret of at least 32 characters, generated with your password manager; store privately |
| `LLM_BASE_URL` | Your provider's OpenAI-compatible HTTPS base URL ending in `/v1` |
| `LLM_MODEL` | Exact model name supported by your provider |
| `LLM_API_KEY` | Your provider API key, entered as a private service variable |
| `LLM_ALLOW_REMOTE` | `true` |
| `LLM_STRICT_SCHEMA` | `true`; use `false` only for a provider requiring JSON mode |
| `GLOSSARY_DIR` | `/data/glossaries` when a volume is mounted at `/data` |
| `CACHE_PAGES` | `24` by default, or `0` to disable page cache |
| `CACHE_TTL_SECONDS` | `1800` by default |
| `EXTRA_ALLOWED_HOSTS` | Optional custom hostname(s), comma-separated, no scheme/path |

Railway provides `PORT` automatically. The container listens on `0.0.0.0:$PORT`.
It adds Railway's healthcheck hostname and public service hostname to the host
allowlist. It does not use a wildcard host allowance. No secrets go into GitHub,
the Dockerfile, image build arguments or browser JavaScript source.

Do not use the default localhost LLM URL in cloud mode: there is no LLM server
inside this CPU container. A separate cloud LLM API is required for this recipe.
Using a cloud-hosted open model instead is possible through the same compatible
HTTPS endpoint, but hosting that additional model is not included here.

## Connect Chrome

Download the latest repository ZIP or pull the changes. At `chrome://extensions`,
reload the unpacked extension (or load its `extension/` folder), then reload manga
tabs. Open extension Settings:

1. **Backend URL:** `https://YOUR-HOST` (no trailing path).
2. **Backend token:** the `BACKEND_TOKEN` service variable, not the LLM key.
3. Save settings and grant Chrome access to that selected HTTPS origin.
4. Check connection, then translate a page.

The extension requests optional access for the chosen server only. It refuses
HTTP cloud URLs, URLs containing credentials/paths/queries, and HTTP redirects
while sending screenshots and bearer tokens. Local mode still accepts
`http://127.0.0.1:8000`.

## Connect iPhone

Follow the action sequence in `ios/SETUP.md`, but **skip Tailscale entirely**.
Use `https://YOUR-HOST/translate/image?series=wangan-midnight` as the URL and
the cloud service's backend token. The Shortcut sends raw PNG and displays the
returned PNG in Quick Look. Your PC can be turned off.

## Privacy and restarts

Screenshots now leave your device and are processed on the hosting provider's
infrastructure. Recognized text is also sent to your selected LLM provider.
The application keeps results in RAM only and sends `store:false` to the LLM,
but it cannot guarantee the hosting/LLM providers' retention or infrastructure
logging policies. Cloud processing changes the original all-local privacy
boundary. Explicit glossary files and requested learning exports persist.

A redeploy/restart loses all in-memory jobs/cache. If a request gets interrupted,
recapture it after the service becomes ready. Completed results expire and do
not survive deployment. Avoid redeploying while reading. With a volume, a short
interruption during deployment is expected. Sleeping services also incur cold
start delays; the extension may need a retry once startup completes.

## Verification status

Python regression tests and backend-URL validation can run without real models.
The full Docker build, cloud startup, Chrome capture and iPhone request are not
claimed tested. After deployment, check for dependency import errors, model
load failures, out-of-memory events, HTTP 401/429/502, and end-to-end latency.
A running healthcheck alone is not a complete acceptance test.

Official references:
- https://docs.railway.com/builds/dockerfiles
- https://docs.railway.com/services
- https://docs.railway.com/deployments/healthchecks
- https://docs.railway.com/networking/domains/working-with-domains
- https://docs.railway.com/pricing
