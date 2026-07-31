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

export async function fetchTweets({ category, page = 1, limit = 20 } = {}) {
  const params = { page, limit };
  if (category) params.category = category;
  const res = await client.get("/api/tweets", { params });
  return res.data;
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
