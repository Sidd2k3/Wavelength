import os
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
USE_PG = DATABASE_URL.startswith("postgres")

if USE_PG:
    import psycopg2
    import psycopg2.extras
    def get_connection():
        return psycopg2.connect(DATABASE_URL)
    PH = "%s"
else:
    import sqlite3
    DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "leads.db"))
    def get_connection():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    PH = "?"

def _dict_cursor(conn):
    if USE_PG:
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return conn.cursor()

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    if USE_PG:
        cur.execute("""CREATE TABLE IF NOT EXISTS tweets (
            id SERIAL PRIMARY KEY, tweet_id TEXT UNIQUE, profile_name TEXT,
            username TEXT, text TEXT, label INTEGER, label_name TEXT,
            confidence REAL, lead_score INTEGER, created_at TEXT,
            scraped_at TIMESTAMP DEFAULT NOW())""")
        cur.execute("""CREATE TABLE IF NOT EXISTS scrape_logs (
            id SERIAL PRIMARY KEY, status TEXT, tweets_found INTEGER DEFAULT 0,
            tweets_relevant INTEGER DEFAULT 0, message TEXT,
            ran_at TIMESTAMP DEFAULT NOW())""")
    else:
        cur.execute("""CREATE TABLE IF NOT EXISTS tweets (
            id INTEGER PRIMARY KEY AUTOINCREMENT, tweet_id TEXT UNIQUE, profile_name TEXT,
            username TEXT, text TEXT, label INTEGER, label_name TEXT,
            confidence REAL, lead_score INTEGER, created_at TEXT,
            scraped_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS scrape_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, status TEXT, tweets_found INTEGER DEFAULT 0,
            tweets_relevant INTEGER DEFAULT 0, message TEXT,
            ran_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit(); conn.close()
    print(f"Database initialized ({'Supabase/Postgres' if USE_PG else 'local SQLite'})")

def insert_tweet(tweet):
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute(f"""INSERT INTO tweets (tweet_id, profile_name, username, text, label,
            label_name, confidence, lead_score, created_at)
            VALUES ({PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH})""" +
            (" ON CONFLICT (tweet_id) DO NOTHING" if USE_PG else ""),
            (tweet.get("tweet_id"), tweet.get("profile_name"), tweet.get("username"),
             tweet.get("text"), tweet.get("label"), tweet.get("label_name"),
             tweet.get("confidence"), tweet.get("lead_score"),
             tweet.get("created_at", datetime.now().isoformat())))
        new = cur.rowcount > 0
        conn.commit(); return new
    except Exception:
        conn.rollback(); return False
    finally:
        conn.close()

def _age_cond(col="created_at"):
    if USE_PG:
        return f"{col} >= (NOW() - (%s || ' days')::interval)::text", None
    return f"{col} >= datetime('now', ?)", None

def get_tweets(limit=50, offset=0, label_name=None, only_relevant=True, max_age_days=90):
    conn = get_connection(); cur = _dict_cursor(conn)
    conds, params = [], []
    if only_relevant: conds.append("label != 0")
    if label_name:
        conds.append(f"label_name = {PH}"); params.append(label_name)
    if max_age_days is not None:
        if USE_PG:
            conds.append("created_at::timestamptz >= (NOW() - (%s || ' days')::interval)"); params.append(str(max_age_days))
        else:
            conds.append("created_at >= datetime('now', ?)"); params.append(f"-{max_age_days} days")
    where = f"WHERE {' AND '.join(conds)}" if conds else ""
    cur.execute(f"SELECT * FROM tweets {where} ORDER BY lead_score DESC, scraped_at DESC LIMIT {PH} OFFSET {PH}",
                params + [limit, offset])
    rows = cur.fetchall(); conn.close()
    results = []
    for row in rows:
        tweet = dict(row)
        is_syn = tweet.get("username") == "synthetic_data"
        if tweet.get("username") and tweet.get("tweet_id") and not is_syn:
            tweet["tweet_url"] = f"https://x.com/{tweet['username']}/status/{tweet['tweet_id']}"
        else:
            tweet["tweet_url"] = None
        results.append(tweet)
    return results

def get_total_count(label_name=None, only_relevant=True, max_age_days=90):
    conn = get_connection(); cur = conn.cursor()
    conds, params = [], []
    if only_relevant: conds.append("label != 0")
    if label_name:
        conds.append(f"label_name = {PH}"); params.append(label_name)
    if max_age_days is not None:
        if USE_PG:
            conds.append("created_at::timestamptz >= (NOW() - (%s || ' days')::interval)"); params.append(str(max_age_days))
        else:
            conds.append("created_at >= datetime('now', ?)"); params.append(f"-{max_age_days} days")
    where = f"WHERE {' AND '.join(conds)}" if conds else ""
    cur.execute(f"SELECT COUNT(*) FROM tweets {where}", params)
    count = cur.fetchone()[0]; conn.close(); return count

def get_category_counts(max_age_days=90):
    conn = get_connection(); cur = conn.cursor()
    if USE_PG:
        cur.execute("""SELECT label_name, COUNT(*) as count FROM tweets
            WHERE label != 0 AND created_at::timestamptz >= (NOW() - (%s || ' days')::interval)
            GROUP BY label_name ORDER BY count DESC""", (str(max_age_days),))
    else:
        cur.execute("""SELECT label_name, COUNT(*) as count FROM tweets
            WHERE label != 0 AND created_at >= datetime('now', ?)
            GROUP BY label_name ORDER BY count DESC""", (f"-{max_age_days} days",))
    rows = cur.fetchall(); conn.close()
    return {r[0]: r[1] for r in rows}

def cleanup_old_tweets(max_age_days=90):
    conn = get_connection(); cur = conn.cursor()
    if USE_PG:
        cur.execute("DELETE FROM tweets WHERE created_at::timestamptz < (NOW() - (%s || ' days')::interval)", (str(max_age_days),))
    else:
        cur.execute("DELETE FROM tweets WHERE created_at < datetime('now', ?)", (f"-{max_age_days} days",))
    deleted = cur.rowcount; conn.commit(); conn.close()
    if deleted: print(f"Cleaned up {deleted} tweets older than {max_age_days} days")
    return deleted

def log_scrape(status, tweets_found=0, tweets_relevant=0, message=""):
    conn = get_connection(); cur = conn.cursor()
    cur.execute(f"INSERT INTO scrape_logs (status, tweets_found, tweets_relevant, message) VALUES ({PH},{PH},{PH},{PH})",
                (status, tweets_found, tweets_relevant, message))
    conn.commit(); conn.close()

def get_last_scrape():
    conn = get_connection(); cur = _dict_cursor(conn)
    cur.execute("SELECT * FROM scrape_logs ORDER BY ran_at DESC LIMIT 1")
    row = cur.fetchone(); conn.close()
    return dict(row) if row else None

if __name__ == "__main__":
    init_db()
