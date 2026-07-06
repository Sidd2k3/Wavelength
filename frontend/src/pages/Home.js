import React, { useEffect, useState, useCallback } from "react";
import TopBar from "../components/TopBar";
import Ticker from "../components/Ticker";
import CategoryCard from "../components/CategoryCard";
import { CATEGORIES, fetchStats, fetchTweets } from "../api";

export default function Home() {
  const [stats, setStats] = useState(null);
  const [recentTweets, setRecentTweets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try {
      const [statsData, tweetsData] = await Promise.all([
        fetchStats(),
        fetchTweets({ limit: 6 }),
      ]);
      setStats(statsData);
      setRecentTweets(tweetsData.tweets || []);
      setError(null);
    } catch (e) {
      setError("Can't reach the backend. Make sure it's running on localhost:8000.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 60000); // refresh view every minute
    return () => clearInterval(interval);
  }, [load]);

  const totalSignals = stats?.total_relevant_leads ?? 0;
  const breakdown = stats?.category_breakdown ?? {};

  return (
    <div className="page">
      <TopBar lastScrape={stats?.last_scrape} />

      <Ticker tweets={recentTweets} />

      <main className="home-main">
        <section className="hero">
          <h1 className="hero-title">
            The signal, sorted from the noise.
          </h1>
          <p className="hero-sub">
            Wavelength listens across Twitter/X for people building, hiring, and
            shipping — then sorts what matters into five channels below.
            {totalSignals > 0 && (
              <>
                {" "}
                <span className="hero-count">{totalSignals}</span> signals tracked right now.
              </>
            )}
          </p>
        </section>

        {error && (
          <div className="empty-state empty-state--error">
            <p>{error}</p>
          </div>
        )}

        {!error && loading && (
          <div className="cat-grid">
            {CATEGORIES.map((c) => (
              <div key={c.key} className="cat-card cat-card--skeleton" />
            ))}
          </div>
        )}

        {!error && !loading && (
          <div className="cat-grid">
            {CATEGORIES.map((c) => (
              <CategoryCard key={c.key} category={c} count={breakdown[c.key] ?? 0} />
            ))}
          </div>
        )}
      </main>

      <footer className="footer">
        Signals expire automatically after 3 months to keep the board current.
      </footer>
    </div>
  );
}
