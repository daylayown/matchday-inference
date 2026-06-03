# Deployment — THE INFERENCE

How the live system fits together and how to stand it up. Three web-facing
pieces, only one needs a server.

```
                         ┌─────────────────────────────┐
  reader's browser  ───▶ │  Landing page (static)      │   Cloudflare Pages (free)
                         │  web/index.html             │
                         └──────────────┬──────────────┘
                                        │  POST /signup
                                        ▼
                         ┌─────────────────────────────┐
                         │  Signup endpoint (FastAPI)  │   Fly.io  ($0–5/mo)
                         │  + SQLite on a volume       │
                         └──────────────┬──────────────┘
                                        │  GET /export  (Bearer token)
                                        ▼
                         ┌─────────────────────────────┐
                         │  Daily orchestrator         │   GitHub Actions cron (free)
                         │  generate → Resend email    │
                         └─────────────────────────────┘
```

The orchestrator does **not** run on Fly — it runs on GitHub Actions and pulls
the live subscriber list from the Fly endpoint's `GET /export` at the start of
each run. The Fly volume is the single source of truth for subscribers.

---

## 0. Prerequisites

- A domain (buy at Cloudflare). Bought: `matchdayinference.com`.
- `flyctl` installed: `curl -L https://fly.io/install.sh | sh`
- A Fly.io account: `fly auth signup` (or `fly auth login`)

---

## 1. Deploy the signup endpoint to Fly.io

From the repo root:

```bash
# First time only — creates the app. Decline when it offers to deploy
# immediately (we need the volume + secrets first). It will detect fly.toml.
fly launch --no-deploy --copy-config --name matchday-inference-signup

# Persistent volume for the SQLite file (1 GB is plenty). Match the region
# in fly.toml (primary_region).
fly volumes create inference_data --size 1 --region iad

# Secrets. EXPORT_TOKEN is a shared secret you invent — also goes in GH Actions.
fly secrets set \
  INFERENCE_EXPORT_TOKEN="$(openssl rand -hex 32)" \
  INFERENCE_ALLOWED_ORIGINS="https://matchdayinference.com"

# Deploy.
fly deploy

# Sanity check.
curl https://matchday-inference-signup.fly.dev/health    # → {"status":"ok"}
```

Note the `INFERENCE_EXPORT_TOKEN` value — print it with
`fly ssh console -C 'printenv INFERENCE_EXPORT_TOKEN'` — you'll need it in step 4.

> **Scale-to-zero:** `fly.toml` sets `min_machines_running = 0`, so the machine
> sleeps when idle and cold-starts (~1s) on the next request. Fine for a signup
> form. The volume persists across sleeps.

---

## 2. Point DNS at Fly (Cloudflare dashboard)

In Cloudflare → your domain → DNS, add the records Fly prints from
`fly certs add api.matchdayinference.com`:

```bash
fly certs add api.matchdayinference.com
```

Add the CNAME/A/AAAA it tells you (typically a CNAME `api` → `matchday-inference-signup.fly.dev`).
Set the Cloudflare proxy to **DNS only (grey cloud)** for this record so Fly can
issue its own TLS cert; once `fly certs show api.matchdayinference.com` reports valid,
you can flip the proxy back on if you want Cloudflare in front.

---

## 3. Deploy the landing page to Cloudflare Pages

The landing page is static (`web/index.html`). In Cloudflare → Workers & Pages →
Create → Pages → Direct Upload (or connect the repo if you push it to GitHub):

- Build output directory: `web/`
- No build command needed.
- Add custom domain: `matchdayinference.com` (and `www` if you want).

Then wire the form: edit `web/index.html` near the bottom where the signup JS
currently writes to `localStorage`, and POST to the live endpoint instead:

```js
await fetch("https://api.matchdayinference.com/signup", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email, display_name, teams, players, lens, length, wildcard, location }),
});
```

(See `src/inference/subscribers/api.py` → `SignupRequest` for the exact field shape.)

---

## 4. Wire the daily cron to the live subscriber list

The GitHub Actions workflow (`.github/workflows/daily.yml`) needs to fetch the
subscriber list before generating. Add these **repo secrets**
(Settings → Secrets and variables → Actions):

| Secret | Value |
|---|---|
| `OPENAI_API_KEY` | your OpenAI key |
| `API_FOOTBALL_KEY` | your API-Football key |
| `RESEND_API_KEY` | your Resend key |
| `FROM_EMAIL` | e.g. `matchday@matchdayinference.com` |
| `INFERENCE_EXPORT_TOKEN` | the same token set in Fly (step 1) |
| `INFERENCE_EXPORT_URL` | `https://api.matchdayinference.com/export` |

The workflow step that pulls the list:

```bash
curl -sf -H "Authorization: Bearer $INFERENCE_EXPORT_TOKEN" \
  "$INFERENCE_EXPORT_URL" > data/readers.json
.venv/bin/python scripts/run_day.py "$DATE" --issue "$ISSUE"   # reads data/readers.json
```

> The export step is already in `daily.yml` ("Fetch live subscriber list"). If
> `INFERENCE_EXPORT_URL`/`INFERENCE_EXPORT_TOKEN` aren't set, it falls back to the
> committed sample `data/readers.json` so dress-rehearsal runs still complete.

---

## 5. Verify the sending domain in Resend

In Resend → Domains → Add `matchdayinference.com`. It gives you SPF, DKIM, and DMARC
TXT records. Add them in Cloudflare DNS. Once Resend shows the domain verified,
set `FROM_EMAIL=matchday@matchdayinference.com` (step 4) and emails will send from
your domain instead of being rejected.

Resend free tier: 3,000 emails/month, 100/day. At 50 readers × 35 days = 1,750
sends total — fits, but the **100/day cap** bites if you pass ~100 subscribers.
Upgrade ($20/mo, 50k) before then.

---

## Redeploying

Code change to the endpoint → `fly deploy`. Everything else (cron, landing page)
redeploys on its own platform. The SQLite volume is untouched by `fly deploy`.

## Local testing

```bash
pip install -e '.[web]'
INFERENCE_EXPORT_TOKEN=dev uvicorn inference.subscribers.api:app --reload --port 8000
curl localhost:8000/health
curl -H "Authorization: Bearer dev" localhost:8000/export
```
