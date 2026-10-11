import React from "react";
import { Link } from "react-router-dom";
import { format } from "date-fns";
import { timeAgo } from "./timeago";

export default function Masthead({ lastScrape, total }) {
  const scanned = lastScrape?.ran_at ? timeAgo(lastScrape.ran_at) : "awaiting first scan";

  return (
    <header className="masthead">
      <div className="masthead-top">
        <span>{format(new Date(), "EEEE, d MMMM yyyy")}</span>
        <span>Lead intelligence for web &amp; app studios</span>
      </div>
      <Link to="/" className="masthead-brand">Wavelength</Link>
      <div className="masthead-strip">
        <span className="live">
          <span className="live-dot" aria-hidden="true" />
          Listening to Twitter/X · last scan <span className="mono">{scanned}</span>
        </span>
        {total > 0 && (
          <span>
            <span className="mono">{total.toLocaleString("en-IN")}</span> signals on file
          </span>
        )}
      </div>
    </header>
  );
}
