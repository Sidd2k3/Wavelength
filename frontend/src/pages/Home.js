import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import Masthead from "../components/Masthead";
import Footer from "../components/Footer";
import { timeAgo } from "../components/timeago";
import { CATEGORIES, getCategoryMeta, fetchStats, fetchTweets } from "../api";

export default function Home() {
  const [stats, setStats] = useState(null);
  const [latest, setLatest] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try {
      const [statsData, tweetsData] = await Promise.all([
        fetchStats(),
        fetchTweets({ limit: 12, sort: "recent" }),
      ]);
      setStats(statsData);
      setLatest((tweetsData.tweets || []).slice(0, 6));
      setError(null);
    } catch (e) {
      setError("Couldn't load signals right now. The server may be waking up — refresh in a moment.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 60000);
    return () => clearInterval(interval);
  }, [load]);

  const total = stats?.total_relevant_leads ?? 0;
  const breakdown = stats?.category_breakdown ?? {};
  const channels = [...CATEGORIES]
    .map((c) => ({ ...c, count: breakdown[c.key] ?? 0 }))
    .sort((a, b) => b.count - a.count);
  const max = Math.max(1, ...channels.map((c) => c.count));

  return (
    <div className="page">
      <Masthead lastScrape={stats?.last_scrape} total={total} />

      <section className="lede">
        <div>
          <h1 className="lede-title">Who is building, hiring and shipping right now.</h1>
          <p className="lede-sub">
            Wavelength reads Twitter/X every 30 minutes, filters out the noise with a trained
            classifier, and files each business signal into one of five channels, ranked by lead score.
          </p>
        </div>
        <div className="lede-total">
          <span className="lede-total-num">{loading ? "—" : total.toLocaleString("en-IN")}</span>
          <span className="lede-total-label">signals tracked</span>
        </div>
      </section>

      {error && (
        <div className="notice">
          <p>{error}</p>
        </div>
      )}

      {!error && (
        <div className="home-cols">
          <section>
            <h2 className="section-label">
              <span>Channels</span>
              <span>by volume</span>
            </h2>
            {loading
              ? CATEGORIES.map((c) => <div key={c.key} className="channel channel--skeleton" />)
              : channels.map((c, i) => (
                  <Link key={c.key} to={`/${c.key}`} className="channel">
                    <span className="channel-rank">{String(i + 1).padStart(2, "0")}</span>
                    <span className="channel-name">{c.label}</span>
                    <span className="channel-count">{c.count.toLocaleString("en-IN")}</span>
                    <span className="channel-desc">{c.description}</span>
                    <span className="channel-share">
                      {total ? Math.round((c.count / total) * 100) : 0}%
                    </span>
                    <span className="channel-bar" aria-hidden="true">
                      <span style={{ width: `${(c.count / max) * 100}%` }} />
                    </span>
                  </Link>
                ))}
          </section>

          <section>
            <h2 className="section-label">
              <span>Latest on the wire</span>
              <span>newest first</span>
            </h2>
            {latest.map((t) => (
              <div key={t.id} className="wire-item">
                <div className="wire-meta">
                  <span className="wire-tag">{getCategoryMeta(t.label_name).label}</span>
                  <span>@{t.username}</span>
                  <span>· {timeAgo(t.created_at)}</span>
                </div>
                <p className="wire-text">
                  {t.text.length > 160 ? t.text.slice(0, 160).trimEnd() + "…" : t.text}
                </p>
              </div>
            ))}
          </section>
        </div>
      )}

      <Footer />
    </div>
  );
}
