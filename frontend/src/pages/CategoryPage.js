import React, { useEffect, useState, useCallback } from "react";
import { useParams, Link, Navigate } from "react-router-dom";
import TopBar from "../components/TopBar";
import TweetCard from "../components/TweetCard";
import { ArrowLeftIcon, ICONS_BY_KEY_MAP } from "../components/Icons";
import { getCategoryMeta, CATEGORIES, fetchTweets, fetchStats } from "../api";

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
  const [lastScrape, setLastScrape] = useState(null);

  const category = getCategoryMeta(categoryKey);
  const Icon = ICONS_BY_KEY_MAP()[category.icon];

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [tweetsData, statsData] = await Promise.all([
        fetchTweets({ category: categoryKey, page, limit: 15 }),
        fetchStats(),
      ]);
      let list = tweetsData.tweets || [];
      if (sort === "recent") {
        list = [...list].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      }
      setTweets(list);
      setTotal(tweetsData.total);
      setTotalPages(tweetsData.total_pages || 1);
      setLastScrape(statsData.last_scrape);
      setError(null);
    } catch (e) {
      setError("Can't reach the backend. Make sure it's running on localhost:8000.");
    } finally {
      setLoading(false);
    }
  }, [categoryKey, page, sort]);

  useEffect(() => {
    setPage(1);
  }, [categoryKey]);

  useEffect(() => {
    load();
  }, [load]);

  if (!isValid) return <Navigate to="/" replace />;

  return (
    <div className="page">
      <TopBar lastScrape={lastScrape} />

      <main className="cat-main">
        <Link to="/" className="back-link">
          <ArrowLeftIcon />
          All channels
        </Link>

        <div className={`cat-header cat-header--${category.accent}`}>
          <div className="cat-header-icon">
            <Icon />
          </div>
          <div>
            <h1 className="cat-header-title">{category.label}</h1>
            <p className="cat-header-desc">{category.description}</p>
          </div>
          <div className="cat-header-count">
            <span className="cat-header-count-num">{total}</span>
            <span className="cat-header-count-label">signal{total === 1 ? "" : "s"}</span>
          </div>
        </div>

        <div className="cat-toolbar">
          <div className="sort-toggle">
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
        </div>

        {error && (
          <div className="empty-state empty-state--error">
            <p>{error}</p>
          </div>
        )}

        {!error && loading && (
          <div className="tweet-list">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="tweet-card tweet-card--skeleton" />
            ))}
          </div>
        )}

        {!error && !loading && tweets.length === 0 && (
          <div className="empty-state">
            <p className="empty-state-title">No {category.label.toLowerCase()} signals yet</p>
            <p className="empty-state-sub">
              Wavelength scans every 30 minutes — check back shortly, or explore another channel.
            </p>
          </div>
        )}

        {!error && !loading && tweets.length > 0 && (
          <>
            <div className="tweet-list">
              {tweets.map((t) => (
                <TweetCard key={t.id} tweet={t} accent={category.accent} />
              ))}
            </div>

            {totalPages > 1 && (
              <div className="pagination">
                <button
                  className="page-btn"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  ← Prev
                </button>
                <span className="page-info">
                  Page {page} of {totalPages}
                </span>
                <button
                  className="page-btn"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Next →
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
