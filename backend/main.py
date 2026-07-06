from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from dotenv import load_dotenv
import subprocess
import csv
import os

# Load variables from backend/.env (e.g. RETTIWT_API_KEY) into the process
# environment. Must happen before anything reads os.getenv(...).
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from database import (
    init_db, insert_tweet, get_tweets, get_total_count,
    get_category_counts, log_scrape, get_last_scrape, cleanup_old_tweets
)
from classifier import classify_tweet

BASE_DIR = os.path.dirname(__file__)
FETCHER_DIR = os.path.join(BASE_DIR, "fetcher")
RAW_TWEETS_PATH = os.path.join(FETCHER_DIR, "raw_tweets.csv")

MAX_AGE_DAYS = 90        # ~6 months — tweets older than this are hidden, then cleaned up
FETCH_INTERVAL_MINUTES = 30  # how often the fetcher automatically runs

scheduler = AsyncIOScheduler()


def _classify_and_store(tweets: list[dict]) -> dict:
    """Core logic: classify each raw tweet through the model and store it.
    Shared by both the manual /api/ingest route and the automatic scheduler,
    so behavior is identical whichever path triggers it."""
    found = len(tweets)
    saved = 0
    relevant = 0

    for raw in tweets:
        text = raw.get("text", "")
        if not text:
            continue

        result = classify_tweet(text)
        if result["is_relevant"]:
            relevant += 1

        record = {
            "tweet_id": raw.get("tweet_id"),
            "profile_name": raw.get("profile_name", raw.get("author_name", "")),
            "username": raw.get("username", raw.get("author", "")),
            "text": text,
            "label": result["label"],
            "label_name": result["label_name"],
            "confidence": result["confidence"],
            "lead_score": result["lead_score"],
            "created_at": raw.get("created_at", datetime.now().isoformat()),
        }

        # Store every classified tweet (even irrelevant) so we keep a full
        # audit trail; the /api/tweets endpoint filters irrelevant out.
        if insert_tweet(record):
            saved += 1

    return {"found": found, "new_saved": saved, "relevant": relevant}


def run_scheduled_fetch():
    """Runs the Node.js fetcher as a subprocess, then classifies and stores
    whatever it found. This is what makes the whole pipeline automatic —
    no manual `node fetcher.js` / `ingest_csv.py` steps required."""
    api_key = os.getenv("RETTIWT_API_KEY", "")
    if not api_key:
        print("⚠️  RETTIWT_API_KEY not set — skipping scheduled fetch. "
              "Set it in backend/.env to enable automatic fetching.")
        log_scrape(status="skipped", message="RETTIWT_API_KEY not set")
        return

    env = os.environ.copy()
    env["RETTIWT_API_KEY"] = api_key

    print(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] Running scheduled fetch...")
    try:
        result = subprocess.run(
            ["node", "fetcher.js"],
            cwd=FETCHER_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.stdout:
            print(result.stdout[-1500:])
        if result.returncode != 0:
            print("❌ Fetcher process failed:", result.stderr[-800:])
            log_scrape(status="error", message=f"Fetcher failed: {result.stderr[:300]}")
            return
    except FileNotFoundError:
        print("❌ 'node' command not found. Is Node.js installed and on PATH?")
        log_scrape(status="error", message="node not found on PATH")
        return
    except subprocess.TimeoutExpired:
        print("❌ Fetcher timed out after 10 minutes")
        log_scrape(status="error", message="Fetcher timed out")
        return
    except Exception as e:
        print("❌ Failed to run fetcher:", e)
        log_scrape(status="error", message=str(e))
        return

    if not os.path.exists(RAW_TWEETS_PATH):
        print("⚠️  Fetcher ran but produced no raw_tweets.csv")
        log_scrape(status="error", message="No output file produced")
        return

    tweets = []
    with open(RAW_TWEETS_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tweets.append(row)

    outcome = _classify_and_store(tweets)
    log_scrape(
        status="success",
        tweets_found=outcome["found"],
        tweets_relevant=outcome["relevant"],
        message=f"Auto-fetched {outcome['found']} tweets, "
                f"{outcome['new_saved']} new, {outcome['relevant']} relevant",
    )
    print(f"✅ Scheduled fetch complete: {outcome['found']} found, "
          f"{outcome['new_saved']} new, {outcome['relevant']} relevant")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    cleanup_old_tweets(max_age_days=MAX_AGE_DAYS)

    scheduler.add_job(
        cleanup_old_tweets,
        trigger=IntervalTrigger(hours=24),
        kwargs={"max_age_days": MAX_AGE_DAYS},
        id="cleanup_old_tweets",
        replace_existing=True,
    )

    scheduler.add_job(
        run_scheduled_fetch,
        trigger=IntervalTrigger(minutes=FETCH_INTERVAL_MINUTES),
        id="scheduled_fetch",
        replace_existing=True,
        next_run_time=datetime.now(),  # also run once immediately on startup
    )

    scheduler.start()
    print(f"✅ FastAPI backend ready — auto-fetching every {FETCH_INTERVAL_MINUTES} minutes")
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Twitter Lead Intelligence API",
    description="Classifies tweets about web/app development into business-relevant categories",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "Twitter Lead Intelligence API is running 🚀"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/tweets")
def fetch_tweets(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: str = Query(None, description="Filter by label_name e.g. 'hiring'"),
):
    """Returns only the 5 business-relevant categories.
    Irrelevant tweets (label=0) are never returned here."""
    offset = (page - 1) * limit
    tweets = get_tweets(limit=limit, offset=offset, label_name=category, only_relevant=True)
    total = get_total_count(label_name=category, only_relevant=True)
    return {
        "tweets": tweets,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit if total else 0,
    }


@app.get("/api/stats")
def get_stats():
    total_relevant = get_total_count(only_relevant=True)
    category_counts = get_category_counts()
    last_scrape = get_last_scrape()
    return {
        "total_relevant_leads": total_relevant,
        "category_breakdown": category_counts,
        "last_scrape": last_scrape,
    }


@app.post("/api/classify")
def classify_single(text: str = Query(..., description="Tweet text to classify")):
    """Classify a single piece of text on demand (useful for testing)."""
    return classify_tweet(text)


@app.post("/api/ingest")
def ingest_tweets(tweets: list[dict]):
    """Manually trigger classification + storage of a batch of raw tweets.
    Normally you don't need this — the scheduler does it automatically every
    30 minutes — but it's here for testing or one-off imports."""
    if not tweets:
        raise HTTPException(status_code=400, detail="No tweets provided")

    outcome = _classify_and_store(tweets)
    log_scrape(
        status="success",
        tweets_found=outcome["found"],
        tweets_relevant=outcome["relevant"],
        message=f"Manually ingested {outcome['found']} tweets, "
                f"{outcome['new_saved']} new, {outcome['relevant']} relevant",
    )
    return {**outcome, "message": "Ingestion complete"}


@app.post("/api/fetch/trigger")
def trigger_fetch_now():
    """Manually trigger an immediate fetch instead of waiting for the
    next scheduled run. Useful for demos."""
    scheduler.add_job(run_scheduled_fetch, id="manual_fetch_trigger", replace_existing=True)
    return {"message": "Fetch triggered — check /api/stats shortly for results"}
