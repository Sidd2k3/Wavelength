import axios from "axios";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

const client = axios.create({ baseURL: API_BASE, timeout: 60000 });

export const CATEGORIES = [
  {
    key: "launch",
    label: "Launch",
    description: "Products and websites going live",
    icon: "rocket",
    accent: "teal",
  },
  {
    key: "hiring",
    label: "Hiring",
    description: "Teams looking to bring on a developer",
    icon: "briefcase",
    accent: "amber",
  },
  {
    key: "build_request",
    label: "Build Request",
    description: "People who need something built",
    icon: "hammer",
    accent: "coral",
  },
  {
    key: "progress_update",
    label: "Progress Update",
    description: "Milestones and metrics from active builders",
    icon: "chart",
    accent: "blue",
  },
  {
    key: "industry_news",
    label: "Industry News",
    description: "What's moving in the app & web dev world",
    icon: "globe",
    accent: "violet",
  },
];

export function getCategoryMeta(key) {
  return CATEGORIES.find((c) => c.key === key) || CATEGORIES[0];
}

export async function fetchStats() {
  const res = await client.get("/api/stats");
  return res.data;
}

const NAMED_ENTITIES = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: "\u00a0" };

// Twitter returns HTML-escaped text ("&amp;"); decode it for display.
export function decodeEntities(str) {
  if (!str) return "";
  let out = str;
  for (let i = 0; i < 2; i++) {
    // two passes handle double-escaped text such as "&amp;amp;"
    out = out.replace(/&(#x[0-9a-f]+|#\d+|[a-z]+);/gi, (m, e) => {
      if (e[0] === "#") {
        const code = e[1] === "x" || e[1] === "X" ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10);
        return Number.isFinite(code) ? String.fromCodePoint(code) : m;
      }
      const v = NAMED_ENTITIES[e.toLowerCase()];
      return v !== undefined ? v : m;
    });
  }
  return out;
}

// The same post can be stored under several tweet IDs (reposts, quote
// re-shares). Keep the first occurrence of each author + text pair.
export function dedupeTweets(list) {
  const seen = new Set();
  const out = [];
  for (const t of list) {
    const text = decodeEntities(t.text);
    const key = `${(t.username || "").toLowerCase()}|${text.replace(/\s+/g, " ").trim().toLowerCase()}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({ ...t, text, profile_name: decodeEntities(t.profile_name) });
  }
  return out;
}

export async function fetchTweets({ category, page = 1, limit = 20, sort = "score" } = {}) {
  const params = { page, limit, sort };
  if (category) params.category = category;
  const res = await client.get("/api/tweets", { params });
  const data = res.data;
  return { ...data, tweets: dedupeTweets(data.tweets || []) };
}

export default client;

// --- Auto-retry for cold starts (Render free tier takes ~30-60s to wake) ---
const MAX_RETRIES = 2;

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config;
    if (!config) return Promise.reject(error);

    const status = error.response ? error.response.status : null;
    const worthRetrying = !status || status >= 500 || status === 408 || status === 429;

    config.__retryCount = config.__retryCount || 0;

    if (!worthRetrying || config.__retryCount >= MAX_RETRIES) {
      return Promise.reject(error);
    }

    config.__retryCount += 1;
    await new Promise((r) => setTimeout(r, 2000 * config.__retryCount));
    return client(config);
  }
);
