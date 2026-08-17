# Wavelength

Real-time lead intelligence for web development agencies. Wavelength continuously ingests public tweets, classifies them into buying-intent categories with a trained model, discards the noise, and surfaces the remainder as a ranked lead feed.

**Live:** [wavelength-one-rho.vercel.app](https://wavelength-one-rho.vercel.app)

---

## The problem

Agencies looking for inbound work have no good way to catch the moment a prospect signals intent. Somebody tweets "just raised our seed, need to rebuild the marketing site" and it's buried under a million unrelated posts within the hour. Manual search doesn't scale and generic scrapers return mostly garbage.

Wavelength runs the search continuously, applies a classifier trained on hand-labelled data to separate signal from noise, and keeps a rolling 90-day window of qualified leads.

---

## How it works

```
Twitter  ──►  Node fetcher      ──►  FastAPI backend  ──►  Supabase        ──►  React frontend
              (Rettiwt-API,          (classify, filter,     (PostgreSQL,          (ranked feed,
               residential IP)        dedupe, persist)       90-day window)        dual sort)
                    ▲
                    │
              macOS LaunchAgent
              APScheduler, every 30 min
```

Every 30 minutes the scheduler triggers a fetch cycle:

1. **Fetch** — the Node fetcher queries Twitter using a weighted rotation of keyword slots, in `latest` mode over a 7-day window.
2. **Pre-filter** — an English-only filter and a spam heuristic drop obvious junk before the model ever sees it.
3. **Classify** — TF-IDF vectorisation feeding a logistic regression classifier assigns one of six labels. Predictions below a 0.45 confidence threshold are treated as unusable.
4. **Persist** — qualified leads land in Supabase. Anything older than 90 days is aged out.
5. **Serve** — the React frontend reads from the API and renders the feed with two sort modes.

### Classification

Six classes, roughly 73% accuracy on held-out data:

| Class | What it captures |
|---|---|
| `build_request` | Explicit ask for someone to build or rebuild something |
| `hiring` | Actively hiring for dev or design work |
| `launch` | Shipped or launching a product |
| `progress_update` | Building in public, mid-project |
| `industry_news` | Relevant context, not a lead |
| `irrelevant` | Everything else — discarded |

The `irrelevant` class does real work here. Most of what a keyword search returns is off-target, and giving the model an explicit bucket for it beats trying to threshold it away after the fact.

Training data is 1,012 hand-labelled tweets — 767 scraped, 245 synthetic to balance the thinner classes. The labelling rule was deliberately blunt: unclear or rambling goes to `irrelevant`, clear and direct gets categorised. Consistency mattered more than nuance, since an inconsistently labelled set will cap model quality no matter what you do downstream.

Keyword slots are weighted rather than uniform — `build_request` ×4, `hiring` ×3, everything else ×1 — because the high-value categories are also the rarest, and an even rotation wastes most of the fetch budget on classes that don't convert.

---

## Why the fetcher runs on a Mac

This is the least obvious part of the architecture, so: Twitter blocks datacenter IP ranges aggressively. Running the fetcher on Render, Railway, or any other cloud host gets it throttled or blocked outright within a cycle or two.

The fetcher therefore runs locally on a residential connection, managed by a macOS LaunchAgent so it survives reboots and restarts on failure. The FastAPI backend, which has no such constraint, stays on Render.

It's an honest trade-off, not a clever one: it buys reliable ingestion at the cost of a single point of failure that isn't in the cloud. A residential proxy pool would be the cloud-native fix, and it's the obvious first change if this ever needed to run unattended.

---

## Stack

| Layer | Technology | Host |
|---|---|---|
| Fetcher | Node.js, Rettiwt-API, ES modules | Local (macOS LaunchAgent) |
| Backend | Python, FastAPI, APScheduler, Docker | Render |
| ML | scikit-learn (TF-IDF + logistic regression) | In-process with the backend |
| Database | PostgreSQL | Supabase (Singapore, transaction pooler) |
| Frontend | React | Vercel |

---

## Repository layout

```
backend/               FastAPI service, classifier, scheduler, fetcher
complete_ml_notebook/  Training and evaluation notebooks
frontend/              React client
```

---

## Running it locally

**Requirements:** Python 3.9+, Node.js 18+, a Supabase project, Twitter credentials for Rettiwt-API.

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Serves on `http://localhost:8000`.

### Fetcher

```bash
cd backend
npm install
node fetcher.js
```

### Frontend

```bash
cd frontend
npm install
npm start
```

Serves on `http://localhost:3000`.

### Configuration

Set these in `backend/.env` and `frontend/.env` respectively. Never commit either file.

**Backend**

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Supabase Postgres connection string (transaction pooler) |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase API key |
| `TWITTER_AUTH_TOKEN` | Rettiwt-API session credential |

**Frontend**

| Variable | Purpose |
|---|---|
| `REACT_APP_API_URL` | Base URL of the backend |

> On Vercel, do not mark `REACT_APP_API_URL` as Sensitive. Sensitive variables are withheld at build time, and since Create React App inlines env vars during the build, the value silently resolves to an empty string with no error anywhere in the logs.

---

## Known limitations

- **73% accuracy** is workable for triage but not for automation. The failure mode is usually a `progress_update` misread as a `build_request`, which is the tolerable direction to be wrong in.
- **Single point of ingestion.** If the Mac is asleep or offline, no leads arrive. Nothing queues.
- **Cold starts.** The backend sleeps on Render's free tier; the frontend compensates with longer timeouts and auto-retry, but the first request after idle is slow.
- **English only.** Non-English tweets are dropped before classification.

## Roadmap

- Connection pooling fix on the Supabase client
- Classifier quality pass — more training data, transformer embeddings over TF-IDF
- Contact capture on the frontend
- RAG layer for querying the lead corpus in natural language

---

Built by [Siddharth Kumar Meher](https://github.com/Sidd2k3).
