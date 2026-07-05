"""
Reads raw_tweets.csv (produced by the Node.js fetcher) and sends it to the
FastAPI backend's /api/ingest endpoint for classification + storage.

Usage:
    python3 ingest_csv.py ../raw_tweets.csv
"""
import sys
import csv
import requests

API_URL = "http://localhost:8000/api/ingest"


def main(csv_path: str):
    tweets = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tweets.append({
                "tweet_id": row.get("tweet_id"),
                "profile_name": row.get("author_name", row.get("profile_name", "")),
                "username": row.get("author", row.get("username", "")),
                "text": row.get("text", ""),
                "created_at": row.get("created_at", ""),
            })

    print(f"Read {len(tweets)} tweets from {csv_path}")
    print("Sending to backend for classification...")

    response = requests.post(API_URL, json=tweets)

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Done!")
        print(f"   Found     : {result['found']}")
        print(f"   New saved : {result['new_saved']}")
        print(f"   Relevant  : {result['relevant']}")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 ingest_csv.py <path_to_raw_tweets.csv>")
        sys.exit(1)
    main(sys.argv[1])
