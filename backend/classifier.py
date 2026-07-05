import re
import joblib
import os
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Ensure NLTK data is available
try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords", quiet=True)
try:
    nltk.data.find("corpora/wordnet")
except LookupError:
    nltk.download("wordnet", quiet=True)

BASE_DIR = os.path.dirname(__file__)

# Load trained artifacts (produced by the Jupyter notebook)
model = joblib.load(os.path.join(BASE_DIR, "tweet_classifier_final.pkl"))
label_map = joblib.load(os.path.join(BASE_DIR, "label_map.pkl"))
category_weights = joblib.load(os.path.join(BASE_DIR, "category_weights.pkl"))

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words("english"))
keep_words = {"not", "no", "never", "need", "want", "looking", "building", "built", "hire", "hiring"}
stop_words -= keep_words

# Minimum model confidence (0-1) required to accept a prediction as a real lead.
CONFIDENCE_THRESHOLD = 0.45

# Patterns that indicate crypto/airdrop/spam junk, NOT genuine leads.
SPAM_PATTERNS = [
    r"\$[A-Z]{2,10}\b",
    r"\bpump\b",
    r"[A-Za-z0-9]{30,}",
    r"community just went live",
    r"\bairdrop\b",
    r"\bpresale\b",
    r"\bwhitelist\b",
    r"\bnft\b",
    r"\bmemecoin\b",
    r"\bto the moon\b",
    r"100x|1000x",
    r"\bgiveaway\b",
    r"\bsolana\b|\bbnb\b|\bbsc\b",
]
SPAM_REGEX = re.compile("|".join(SPAM_PATTERNS), re.IGNORECASE)


def is_spam(raw_text: str) -> bool:
    """Rule-based junk filter for crypto/airdrop/spam tweets."""
    if not raw_text:
        return True
    if len(re.findall(r"\$[A-Za-z]{2,10}\b", raw_text)) >= 1 and "pump" in raw_text.lower():
        return True
    return bool(SPAM_REGEX.search(raw_text))


def preprocess(text: str) -> str:
    """Same preprocessing used during training."""
    text = str(text).lower()
    text = re.sub(r"http\S+|www\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"[@#]", "", text)
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    tokens = text.split()
    tokens = [lemmatizer.lemmatize(t) for t in tokens if t not in stop_words and len(t) > 2]
    return " ".join(tokens)


def _irrelevant(reason="irrelevant"):
    return {
        "label": 0,
        "label_name": "irrelevant",
        "confidence": 0.0,
        "lead_score": 0,
        "is_relevant": False,
    }


def classify_tweet(text: str) -> dict:
    """Classify a single tweet and compute its lead score."""
    if is_spam(text):
        return _irrelevant()

    clean = preprocess(text)

    if not clean.strip():
        return _irrelevant()

    proba = model.predict_proba([clean])[0]
    predicted_class = int(model.predict([clean])[0])
    confidence = float(proba[predicted_class])

    if predicted_class != 0 and confidence < CONFIDENCE_THRESHOLD:
        return _irrelevant()

    base_weight = category_weights[predicted_class]
    lead_score = round(base_weight * confidence)

    return {
        "label": predicted_class,
        "label_name": label_map[predicted_class],
        "confidence": round(confidence * 100, 1),
        "lead_score": lead_score,
        "is_relevant": predicted_class != 0,
    }


if __name__ == "__main__":
    tests = [
        "Need someone to build an e-commerce website for my clothing brand urgently",
        "This app is a complete scam stole my money avoid it",
        "Just launched our fintech app on Play Store after 6 months of work",
        "Hiring senior React developer for our startup remote friendly apply now",
        "Get in on $PUMPERS community just went live 8wQydVUD4MuZG5KCgMmSWDBbjeujwA2ak6es2Yxapump",
        "Don't forget to join $CARDS community just went live",
    ]
    for t in tests:
        result = classify_tweet(t)
        status = "✅" if result["is_relevant"] else "❌"
        print(f"{status} [{result['label_name']:16}] Score:{result['lead_score']:3}/100 | {t[:50]}")
