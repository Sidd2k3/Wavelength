import { Rettiwt } from 'rettiwt-api';
import { writeFileSync } from 'fs';

// API key is passed in by the Python backend as an environment variable —
// never hardcoded here, so it's safe to keep this file in version control.
const API_KEY = process.env.RETTIWT_API_KEY;

if (!API_KEY) {
    console.error('❌ RETTIWT_API_KEY environment variable not set');
    process.exit(1);
}

const rettiwt = new Rettiwt({ apiKey: API_KEY, maxRetries: 5 });

// Keyword pools grouped by category. Every run picks a fresh mix — weighted
// so build_request and hiring (the highest-value lead categories) appear
// most often, while launch/progress_update/industry_news still get covered
// regularly so nothing is permanently neglected.
const KEYWORD_POOLS = {
    build_request: [
        'need developer', 'build website', 'need website', 'build an app',
        'need an app', 'website developer', 'need someone to build',
        'looking for someone to build', 'build mobile app', 'create website',
    ],
    hiring: [
        'hire developer', 'hiring developer', 'looking for developer',
        'web developer', 'react developer', 'flutter developer',
        'frontend developer', 'backend developer', 'fullstack developer',
        'need a developer',
    ],
    launch: [
        'built app', 'launched website', 'launched app', 'just launched',
        'app store launch', 'just shipped', 'went live', 'product launch',
    ],
    progress_update: [
        'users on our app', 'users on our platform', 'building in public',
        'reached milestone', 'shipped update', 'app update', 'new feature',
    ],
    industry_news: [
        'app store update', 'new framework', 'tech startup',
        'developer tools', 'web development trend', 'saas product',
    ],
};

// How many keywords to pull from each pool per run. Build_request and
// hiring get the most slots since they're the highest-value leads.
const SLOTS = {
    build_request: 4,
    hiring: 3,
    launch: 1,
    progress_update: 1,
    industry_news: 1,
};

function pickRandom(pool, count) {
    const shuffled = [...pool].sort(() => Math.random() - 0.5);
    return shuffled.slice(0, count);
}

function buildKeywordMix() {
    let mix = [];
    for (const [category, count] of Object.entries(SLOTS)) {
        mix = mix.concat(pickRandom(KEYWORD_POOLS[category], count));
    }
    return mix;
}

const KEYWORDS = buildKeywordMix();
console.log(`📋 This run's keyword mix: ${KEYWORDS.join(', ')}`);

async function fetchTweets() {
    const allTweets = [];
    const seenIds = new Set();

    for (const keyword of KEYWORDS) {
        try {
            console.log(`🔍 Searching: "${keyword}"`);
            const result = await rettiwt.tweet.search({ includePhrase: keyword, language: "en", startDate: new Date(Date.now() - 7*24*60*60*1000) }, 20);

            if (result?.list?.length) {
                for (const tweet of result.list) {
                    if (!seenIds.has(tweet.id)) {
                        seenIds.add(tweet.id);
                        allTweets.push({
                            tweet_id: tweet.id,
                            text: (tweet.fullText || '').replace(/"/g, "'").replace(/\n/g, ' '),
                            author: tweet.tweetBy?.userName || '',
                            author_name: tweet.tweetBy?.fullName || '',
                            created_at: tweet.createdAt || '',
                        });
                    }
                }
                console.log(`   ✅ Got ${result.list.length} tweets`);
            } else {
                console.log(`   ⚠️ No results`);
            }

            await new Promise((r) => setTimeout(r, 8000));
        } catch (err) {
            console.log(`   ❌ ${keyword}: ${err.message}`);
        }
    }

    const header = 'tweet_id,text,author,author_name,created_at';
    const rows = allTweets.map(
        (t) => `${t.tweet_id},"${t.text}",${t.author},"${t.author_name}",${t.created_at}`
    );

    writeFileSync('raw_tweets.csv', [header, ...rows].join('\n'));
    console.log(`\n✅ Done! Saved ${allTweets.length} tweets to raw_tweets.csv`);
}

fetchTweets();
