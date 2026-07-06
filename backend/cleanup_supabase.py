import sys, psycopg2, psycopg2.extras
from classifier import classify_tweet

def main(pg_url):
    conn = psycopg2.connect(pg_url)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT id, text FROM tweets")
    rows = cur.fetchall()
    print(f"Re-checking {len(rows)} tweets with the new classifier...")
    delcur = conn.cursor()
    deleted = 0
    for r in rows:
        result = classify_tweet(r["text"] or "")
        if not result["is_relevant"]:
            delcur.execute("DELETE FROM tweets WHERE id = %s", (r["id"],))
            deleted += 1
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM tweets")
    remaining = cur.fetchone()["count"]
    print(f"🧹 Deleted {deleted} spam/irrelevant tweets.")
    print(f"✅ {remaining} clean leads remain in Supabase.")
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python3 cleanup_supabase.py "SUPABASE_URL"'); sys.exit(1)
    main(sys.argv[1])
