import React from "react";
import { formatDistanceToNowStrict, format } from "date-fns";
import { ExternalLinkIcon } from "./Icons";

function initials(name) {
  if (!name) return "?";
  const parts = name.trim().split(/\s+/);
  return parts.slice(0, 2).map((p) => p[0]?.toUpperCase()).join("");
}

export default function TweetCard({ tweet, accent }) {
  const postedLabel = (() => {
    if (!tweet.created_at) return "";
    try {
      const d = new Date(tweet.created_at);
      return formatDistanceToNowStrict(d, { addSuffix: true });
    } catch {
      return "";
    }
  })();

  const fullDate = (() => {
    if (!tweet.created_at) return "";
    try {
      return format(new Date(tweet.created_at), "MMM d, yyyy · h:mm a");
    } catch {
      return "";
    }
  })();

  return (
    <article className={`tweet-card tweet-card--${accent}`}>
      <div className="tweet-card-avatar" aria-hidden="true">
        {initials(tweet.profile_name)}
      </div>

      <div className="tweet-card-main">
        <div className="tweet-card-head">
          <span className="tweet-card-name">{tweet.profile_name || "Unknown"}</span>
          <span className="tweet-card-handle">@{tweet.username || "unknown"}</span>
          <span className="tweet-card-dot">·</span>
          <time className="tweet-card-time" title={fullDate}>
            {postedLabel}
          </time>
        </div>

        <p className="tweet-card-text">{tweet.text}</p>

        <div className="tweet-card-foot">
          <span className="tweet-card-score" title="Lead score">
            <span className="score-bar-track">
              <span
                className="score-bar-fill"
                style={{ width: `${Math.min(tweet.lead_score, 100)}%` }}
              />
            </span>
            {tweet.lead_score}/100
          </span>

          {tweet.tweet_url && (
            <a
              href={tweet.tweet_url}
              target="_blank"
              rel="noopener noreferrer"
              className="tweet-card-link"
            >
              View original <ExternalLinkIcon />
            </a>
          )}
        </div>
      </div>
    </article>
  );
}
