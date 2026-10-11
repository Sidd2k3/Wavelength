"""One-off cleanup for existing rows.

1. Decodes HTML entities in stored text (&amp; -> &).
2. Deletes re-posts: rows with the same author + text as an earlier row,
   keeping the oldest row (lowest id).

Run from backend/ with the same .env the backend uses:
    set -a && source .env && set +a && python3 dedupe_supabase.py
"""
import html
import os
import psycopg2

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

cur.execute("SELECT id, text, profile_name FROM tweets WHERE text LIKE '%&%;%' OR profile_name LIKE '%&%;%'")
fixed = 0
for row_id, text, name in cur.fetchall():
    new_text = html.unescape(html.unescape(text or ""))
    new_name = html.unescape(html.unescape(name or ""))
    if new_text != text or new_name != name:
        cur.execute("UPDATE tweets SET text = %s, profile_name = %s WHERE id = %s", (new_text, new_name, row_id))
        fixed += 1
conn.commit()
print(f"Decoded HTML entities in {fixed} rows")

cur.execute("""
    DELETE FROM tweets t
    USING tweets k
    WHERE LOWER(t.username) = LOWER(k.username)
      AND t.text = k.text
      AND t.id > k.id
""")
print(f"Deleted {cur.rowcount} duplicate rows")
conn.commit()

cur.execute("SELECT COUNT(*) FROM tweets WHERE label != 0")
print(f"Relevant signals now: {cur.fetchone()[0]}")
conn.close()
