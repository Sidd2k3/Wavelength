import React, { useEffect, useState, useCallback } from "react";
import { useParams, Link, Navigate } from "react-router-dom";
import Masthead from "../components/Masthead";
import Footer from "../components/Footer";
import SignalRow from "../components/SignalRow";
import { getCategoryMeta, CATEGORIES, fetchTweets, fetchStats } from "../api";

const PAGE_SIZE = 15;

export default function CategoryPage() {
  const { categoryKey } = useParams();
  const isValid = CATEGORIES.some((c) => c.key === categoryKey);

  const [tweets, setTweets] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [sort, setSort] = useState("score"); // "score" | "recent"
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);

  const category = getCategoryMeta(categoryKey);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [tweetsData, statsData] = await Promise.all([
        fetchTweets({ category: categoryKey, page, limit: PAGE_SIZE, sort }),
        fetchStats(),
      ]);
      let list = tweetsData.tweets || [];
      if (sort === "recent") {
        list = [...list].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      }
      setTweets(list);
      setTotal(tweetsData.total);
      setTotalPages(tweetsData.total_pages || 1);
      setStats(statsData);
      setError(null);
    } catch (e) {
      setError("Couldn't load signals right now. The server may be waking up — refresh in a moment.");
    } finally {
      setLoading(false);
    }
  }, [categoryKey, page, sort]);

  useEffect(() => {
    setPage(1);
  }, [categoryKey, sort]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [page]);

  if (!isValid) return <Navigate to="/" replace />;

  return (
    <div className="page">
      <Masthead lastScrape={stats?.last_scrape} total={stats?.total_relevant_leads ?? 0} />

      <Link to="/" className="crumb">← All channels</Link>

      <header className="cat-head">
        <div>
          <p className="cat-kicker">Channel</p>
          <h1 className="cat-title">{category.label}</h1>
          <p className="cat-desc">{category.description}</p>
        </div>
        <div className="cat-count">
          <span className="cat-count-num">{total.toLocaleString("en-IN")}</span>
          <span className="cat-count-label">signal{total === 1 ? "" : "s"}</span>
        </div>
      </header>

      <div className="toolbar">
        <span>Sort</span>
        <button
          className={sort === "score" ? "sort-btn sort-btn--active" : "sort-btn"}
          onClick={() => setSort("score")}
        >
          Highest score
        </button>
        <button
          className={sort === "recent" ? "sort-btn sort-btn--active" : "sort-btn"}
          onClick={() => setSort("recent")}
        >
          Most recent
        </button>
      </div>

      {error && (
        <div className="notice">
          <p>{error}</p>
        </div>
      )}

      {!error && loading && [...Array(4)].map((_, i) => <div key={i} className="signal--skeleton" />)}

      {!error && !loading && tweets.length === 0 && (
        <div className="notice">
          <p className="notice-title">No {category.label.toLowerCase()} signals yet</p>
          <p>Wavelength scans every 30 minutes — check back shortly, or open another channel.</p>
        </div>
      )}

      {!error && !loading && tweets.length > 0 && (
        <>
          {tweets.map((t) => (
            <SignalRow key={t.id} tweet={t} />
          ))}

          {totalPages > 1 && (
            <nav className="pagination">
              <button
                className="page-btn"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                ← Previous
              </button>
              <span className="page-info">
                page {page} / {totalPages}
              </span>
              <button
                className="page-btn"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                Next →
              </button>
            </nav>
          )}
        </>
      )}

      <Footer />
    </div>
  );
}
