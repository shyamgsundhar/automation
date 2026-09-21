import re
from html import unescape
from datetime import datetime, timezone, timedelta

from email.utils import parsedate_to_datetime

from .config import MAX_NEWS_AGE_HOURS


TOPIC_KEYWORDS = {

    "ai": [
        "artificial intelligence",
        "generative ai",
        "machine learning",
        "large language model",
        "llm",
        "ai model",
        "ai agent",
        "chatbot",
        "computer vision",
    ],

    "cybersecurity": [
        "cybersecurity",
        "cyber security",
        "malware",
        "ransomware",
        "data breach",
        "vulnerability",
        "zero-day",
        "exploit",
        "hackers",
    ],

    "software": [
        "software",
        "programming",
        "developer",
        "github",
        "api",
        "database",
        "open source",
        "linux",
        "python",
        "java",
        "javascript",
        "typescript",
    ],

    "cloud": [
        "cloud",
        "aws",
        "azure",
        "google cloud",
        "kubernetes",
        "docker",
        "datacenter",
        "data center",
    ],

    "hardware": [
        "chip",
        "chips",
        "semiconductor",
        "processor",
        "gpu",
        "cpu",
        "memory",
        "datacenter",
        "robotics",
    ],

    "big_tech": [
        "google",
        "microsoft",
        "apple",
        "amazon",
        "meta",
        "nvidia",
        "openai",
        "anthropic",
    ],

    "startups": [
        "startup",
        "funding",
        "venture capital",
        "acquisition",
        "ipo",
        "merger",
    ],

    "internet": [
        "internet",
        "browser",
        "web",
        "5g",
        "6g",
        "social media",
    ],
}


HIGH_PRIORITY = [
    "data breach",
    "zero-day",
    "ransomware",
    "critical vulnerability",
    "major vulnerability",
    "artificial intelligence",
    "ai model",
    "ai agent",
    "semiconductor",
    "chip",
    "acquisition",
    "funding",
    "ipo",
    "launch",
    "announces",
    "announced",
    "unveils",
    "released",
]


def clean_text(text):

    text = unescape(
        text or ""
    )

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def normalize_title(title):

    return re.sub(
        r"[^a-z0-9 ]",
        "",
        title.lower()
    ).strip()


def normalize_url(url):

    return url.split("?")[0].rstrip("/")


def deduplicate_articles(articles):

    seen_titles = set()

    seen_urls = set()

    result = []

    for article in articles:

        title_key = normalize_title(
            article["title"]
        )

        url_key = normalize_url(
            article["link"]
        )

        if (
            title_key in seen_titles
            or url_key in seen_urls
        ):
            continue

        seen_titles.add(
            title_key
        )

        seen_urls.add(
            url_key
        )

        result.append(
            article
        )

    return result


def parse_date(value):

    if not value:
        return None

    try:

        return parsedate_to_datetime(
            value
        ).astimezone(
            timezone.utc
        )

    except Exception:
        return None


def is_fresh(article):

    published = parse_date(
        article.get(
            "published",
            ""
        )
    )

    if published is None:

        # If feed doesn't expose a date,
        # keep it rather than accidentally
        # dropping good news.
        return True

    cutoff = (
        datetime.now(
            timezone.utc
        )
        - timedelta(
            hours=MAX_NEWS_AGE_HOURS
        )
    )

    return published >= cutoff


def filter_fresh(articles):

    return [
        article
        for article in articles
        if is_fresh(article)
    ]


def classify_topic(article):

    text = (
        article["title"]
        + " "
        + article.get(
            "description",
            ""
        )
    ).lower()

    scores = {}

    for topic, keywords in (
        TOPIC_KEYWORDS.items()
    ):

        score = 0

        for keyword in keywords:

            if keyword in text:

                score += 1

        scores[topic] = score

    if not any(
        scores.values()
    ):

        return "general"

    return max(
        scores,
        key=scores.get
    )


def is_tech_news(article):

    return (
        classify_topic(article)
        != "general"
        or any(
            keyword in (
                article["title"]
                + " "
                + article.get(
                    "description",
                    ""
                )
            ).lower()
            for keywords
            in TOPIC_KEYWORDS.values()
            for keyword in keywords
        )
    )


def filter_tech_news(articles):

    result = []

    for article in articles:

        if is_tech_news(article):

            article["topic"] = (
                classify_topic(
                    article
                )
            )

            result.append(
                article
            )

    return result


def calculate_score(article):

    text = (
        article["title"]
        + " "
        + article.get(
            "description",
            ""
        )
    ).lower()

    topic_score = 0

    for keywords in (
        TOPIC_KEYWORDS.values()
    ):

        for keyword in keywords:

            if keyword in text:

                topic_score += 1

    importance = 0

    for keyword in HIGH_PRIORITY:

        if keyword in text:

            importance += 3

    source_quality = (
        article.get(
            "source_quality",
            5
        )
    )

    return (
        topic_score
        + importance
        + source_quality
    )


def rank_articles(articles):

    for article in articles:

        article["score"] = (
            calculate_score(
                article
            )
        )

    return sorted(
        articles,
        key=lambda x: x["score"],
        reverse=True
    )


def select_diverse_articles(
    articles,
    limit=5
):

    selected = []

    used_topics = set()

    used_urls = set()

    # First pass:
    # Try to cover different topics.
    for article in articles:

        if len(selected) >= limit:
            break

        topic = article.get(
            "topic",
            "general"
        )

        url = normalize_url(
            article["link"]
        )

        if url in used_urls:
            continue

        if topic in used_topics:
            continue

        selected.append(
            article
        )

        used_topics.add(
            topic
        )

        used_urls.add(
            url
        )

    # Second pass:
    # Fill remaining slots by score.
    for article in articles:

        if len(selected) >= limit:
            break

        url = normalize_url(
            article["link"]
        )

        if url in used_urls:
            continue

        selected.append(
            article
        )

        used_urls.add(
            url
        )

    return selected