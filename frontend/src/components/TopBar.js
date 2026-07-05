import React from "react";
import { Link } from "react-router-dom";
import { formatDistanceToNowStrict } from "date-fns";

export default function TopBar({ lastScrape }) {
  const lastRunLabel = (() => {
    if (!lastScrape?.ran_at) return "awaiting first scan";
    try {
      return formatDistanceToNowStrict(new Date(lastScrape.ran_at), { addSuffix: true });
    } catch {
      return lastScrape.ran_at;
    }
  })();

  return (
    <header className="topbar">
      <Link to="/" className="brand">
        <span className="brand-mark" aria-hidden="true">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M4 15a8 8 0 0 1 16 0" stroke="var(--teal)" strokeWidth="1.6" strokeLinecap="round" />
            <path d="M7.5 15a4.5 4.5 0 0 1 9 0" stroke="var(--amber)" strokeWidth="1.6" strokeLinecap="round" />
            <circle cx="12" cy="15" r="1.6" fill="var(--text-primary)" />
          </svg>
        </span>
        Wavelength
      </Link>

      <div className="status-pill">
        <span className="status-dot" />
        Listening
        <span className="status-sep">·</span>
        <span className="status-mono">last scan {lastRunLabel}</span>
      </div>
    </header>
  );
}
