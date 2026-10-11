import React from "react";
import { timeAgo, fullDate } from "./timeago";

export default function SignalRow({ tweet }) {
  const score = Math.min(tweet.lead_score ?? 0, 100);

  return (
    <article className="signal">
      <div className={score >= 80 ? "signal-score signal-score--hot" : "signal-score"}>
        {score}
        <small>score</small>
      </div>
      <div>
        <div className="signal-head">
          <span className="signal-name">{tweet.profile_name || "Unknown"}</span>
          <span className="signal-handle">@{tweet.username || "unknown"}</span>
          <time className="signal-time" title={fullDate(tweet.created_at)}>
            · {timeAgo(tweet.created_at)}
          </time>
        </div>
        <p className="signal-text">{tweet.text}</p>
        {tweet.tweet_url && (
          <a className="signal-link" href={tweet.tweet_url} target="_blank" rel="noopener noreferrer">
            View on X →
          </a>
        )}
      </div>
    </article>
  );
}
