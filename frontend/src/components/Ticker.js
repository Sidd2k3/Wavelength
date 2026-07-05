import React from "react";
import { formatDistanceToNowStrict } from "date-fns";

export default function Ticker({ tweets }) {
  if (!tweets || tweets.length === 0) return null;

  // Duplicate the list so the CSS marquee can loop seamlessly
  const items = [...tweets, ...tweets];

  return (
    <div className="ticker">
      <span className="ticker-label">
        <span className="ticker-dot" />
        Latest signal
      </span>
      <div className="ticker-track-wrap">
        <div className="ticker-track">
          {items.map((t, i) => (
            <span className="ticker-item" key={i}>
              <strong>@{t.username}</strong>
              <span className="ticker-sep">·</span>
              {t.text.length > 90 ? t.text.slice(0, 90) + "…" : t.text}
              <span className="ticker-sep">·</span>
              <span className="ticker-time">
                {(() => {
                  try {
                    return formatDistanceToNowStrict(new Date(t.created_at), { addSuffix: true });
                  } catch {
                    return "";
                  }
                })()}
              </span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
