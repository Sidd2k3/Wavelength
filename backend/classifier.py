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


def preprocess(text: str) -> str:
    """Same preprocessing used during training — must stay identical
    or predictions will be inconsistent with the notebook's evaluation."""
    text = str(text).lower()
    text = re.sub(r"http\S+|www\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"[@#]", "", text)
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    tokens = text.split()
    tokens = [lemmatizer.lemmatize(t) for t in tokens if t not in stop_words and len(t) > 2]
    return " ".join(tokens)


def classify_tweet(text: str) -> dict:
    """Classify a single tweet and compute its lead score.

    Returns:
        label (int): 0-5 category id
        label_name (str): category name
        confidence (float): model's confidence in the predicted class (0-100)
        lead_score (int): business-value score (0-100), always 0 for irrelevant
        is_relevant (bool): False if label == 0 (irrelevant), used to filter
                             what actually gets shown on the website
    """
    clean = preprocess(text)

    if not clean.strip():
        # Empty after cleaning (e.g. was just a URL) -> treat as irrelevant
        return {
            "label": 0,
            "label_name": "irrelevant",
            "confidence": 0.0,
            "lead_score": 0,
            "is_relevant": False,
        }

    proba = model.predict_proba([clean])[0]
    predicted_class = int(model.predict([clean])[0])
    confidence = float(proba[predicted_class])

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
    # Quick sanity check when running this file directly
    tests = [
        "Need someone to build an e-commerce website for my clothing brand urgently",
        "This app is a complete scam stole my money avoid it",
        "Just launched our fintech app on Play Store after 6 months of work",
        "Hiring senior React developer for our startup remote friendly apply now",
    ]
    for t in tests:
        result = classify_tweet(t)
        status = "✅" if result["is_relevant"] else "❌"
        print(f"{status} [{result['label_name']:16}] Score:{result['lead_score']:3}/100 | {t[:50]}")
