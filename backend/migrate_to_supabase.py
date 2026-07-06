import sys, sqlite3, os
try:
    import psycopg2
except ImportError:
    print("Run: pip3 install psycopg2-binary"); sys.exit(1)

SQLITE_PATH = os.path.join(os.path.dirname(__file__), "leads.db")

def main(pg_url):
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    scur = sqlite_conn.cursor()
    pg_conn = psycopg2.connect(pg_url)
    pcur = pg_conn.cursor()
    pcur.execute("""CREATE TABLE IF NOT EXISTS tweets (id SERIAL PRIMARY KEY, tweet_id TEXT UNIQUE, profile_name TEXT, username TEXT, text TEXT, label INTEGER, label_name TEXT, confidence REAL, lead_score INTEGER, created_at TIMESTAMPTZ, scraped_at TIMESTAMPTZ DEFAULT NOW())""")
    pcur.execute("""CREATE TABLE IF NOT EXISTS scrape_logs (id SERIAL PRIMARY KEY, status TEXT, tweets_found INTEGER DEFAULT 0, tweets_relevant INTEGER DEFAULT 0, message TEXT, ran_at TIMESTAMPTZ DEFAULT NOW())""")
    pg_conn.commit()
    scur.execute("SELECT * FROM tweets")
    rows = scur.fetchall()
    print(f"Found {len(rows)} tweets. Copying to Supabase...")
    copied = 0
    for row in rows:
        r = dict(row)
        try:
            pcur.execute("""INSERT INTO tweets (tweet_id, profile_name, username, text, label, label_name, confidence, lead_score, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (tweet_id) DO NOTHING""", (r.get("tweet_id"), r.get("profile_name"), r.get("username"), r.get("text"), r.get("label"), r.get("label_name"), r.get("confidence"), r.get("lead_score"), r.get("created_at")))
            if pcur.rowcount > 0: copied += 1
        except Exception as e:
            print(f"  skipped: {e}")
    pg_conn.commit()
    print(f"✅ Copied {copied} new tweets into Supabase ({len(rows)-copied} already there).")
    sqlite_conn.close(); pg_conn.close()
    print("Done.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python3 migrate_to_supabase.py "SUPABASE_URL"'); sys.exit(1)
    main(sys.argv[1])
