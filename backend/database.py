import os
import psycopg2
import psycopg2.extras
from datetime import datetime

# Supabase / Postgres connection string, e.g.
# postgresql://postgres:PASSWORD@db.xxxx.supabase.co:5432/postgres
# Set this in Render as the DATABASE_URL environment variable.
DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Add it as an environment variable "
            "(your Supabase Postgres connection string)."
        )
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tweets (
            id SERIAL PRIMARY KEY,
            tweet_id TEXT UNIQUE,
            profile_name TEXT,
            username TEXT,
            text TEXT,
            label INTEGER,
            label_name TEXT,
            confidence REAL,
            lead_score INTEGER,
            created_at TIMESTAMPTZ,
            scraped_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scrape_logs (
            id SERIAL PRIMARY KEY,
            status TEXT,
            tweets_found INTEGER DEFAULT 0,
            tweets_relevant INTEGER DEFAULT 0,
            message TEXT,
            ran_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Database initialized (Postgres/Supabase)")


def insert_tweet(tweet: dict) -> bool:
    """Insert a classified tweet. Returns True if new, False if duplicate."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO tweets (tweet_id, profile_name, username, text, label,
                                 label_name, confidence, lead_score, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (tweet_id) DO NOTHING
        """, (
            tweet.get("tweet_id"),
            tweet.get("profile_name"),
            tweet.get("username"),
            tweet.get("text"),
            tweet.get("label"),
            tweet.get("label_name"),
            tweet.get("confidence"),
            tweet.get("lead_score"),
            tweet.get("created_at", datetime.now().isoformat()),
        ))
        inserted = cursor.rowcount > 0
        conn.commit()
        return inserted
    finally:
        cursor.close()
        conn.close()


def get_tweets(limit=50, offset=0, label_name=None, only_relevant=True, max_age_days=180):
    """Fetch tweets. By default excludes 'irrelevant' (label=0) so the
    website only ever shows the 5 business-relevant categories.

    max_age_days=180 (~6 months): tweets older than this (based on when
    they were actually posted, i.e. created_at) are excluded from display
    automatically, even though they still exist in the database."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    conditions = []
    params = []

    if only_relevant:
        conditions.append("label != 0")

    if label_name:
        conditions.append("label_name = %s")
        params.append(label_name)

    if max_age_days is not None:
        conditions.append("created_at >= NOW() - INTERVAL '%s days'")
        params.append(max_age_days)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT * FROM tweets
        {where_clause}
        ORDER BY lead_score DESC, scraped_at DESC
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    results = []
    for row in rows:
        tweet = dict(row)
        # Construct the direct link back to the original tweet on X/Twitter.
        # Synthetic training examples never existed on Twitter, so we must
        # not generate a fake/broken link for them.
        is_synthetic = tweet.get("username") == "synthetic_data"
        if tweet.get("username") and tweet.get("tweet_id") and not is_synthetic:
            tweet["tweet_url"] = f"https://x.com/{tweet['username']}/status/{tweet['tweet_id']}"
        else:
            tweet["tweet_url"] = None
        results.append(tweet)
    return results


def get_total_count(label_name=None, only_relevant=True, max_age_days=180):
    conn = get_connection()
    cursor = conn.cursor()

    conditions = []
    params = []

    if only_relevant:
        conditions.append("label != 0")
    if label_name:
        conditions.append("label_name = %s")
        params.append(label_name)
    if max_age_days is not None:
        conditions.append("created_at >= NOW() - INTERVAL '%s days'")
        params.append(max_age_days)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    cursor.execute(f"SELECT COUNT(*) FROM tweets {where_clause}", params)
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count


def get_category_counts(max_age_days=180):
    """Count of tweets per category (excluding irrelevant and stale tweets)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT label_name, COUNT(*) as count
        FROM tweets
        WHERE label != 0 AND created_at >= NOW() - INTERVAL '%s days'
        GROUP BY label_name
        ORDER BY count DESC
    """, (max_age_days,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {row[0]: row[1] for row in rows}


def cleanup_old_tweets(max_age_days=180):
    """Permanently deletes tweets older than max_age_days from the database.
    Meant to be run periodically (e.g. once a day) via the scheduler, so the
    database doesn't grow forever with stale leads nobody will ever see."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM tweets WHERE created_at < NOW() - INTERVAL '%s days'",
        (max_age_days,)
    )
    deleted = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    if deleted:
        print(f"🧹 Cleaned up {deleted} tweets older than {max_age_days} days")
    return deleted


def log_scrape(status, tweets_found=0, tweets_relevant=0, message=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO scrape_logs (status, tweets_found, tweets_relevant, message)
        VALUES (%s, %s, %s, %s)
    """, (status, tweets_found, tweets_relevant, message))
    conn.commit()
    cursor.close()
    conn.close()


def get_last_scrape():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM scrape_logs ORDER BY ran_at DESC LIMIT 1")
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(row) if row else None


if __name__ == "__main__":
    init_db()
