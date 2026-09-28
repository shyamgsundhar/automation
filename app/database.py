import psycopg

from datetime import datetime, timezone
from .config import DATABASE_URL


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():

    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")

    clean_url = DATABASE_URL.strip()

    return psycopg.connect(clean_url)


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_database():

    create_table_query = """
    CREATE TABLE IF NOT EXISTS sent_articles (
        id BIGSERIAL PRIMARY KEY,
        url TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        source TEXT NOT NULL,
        sent_at TIMESTAMPTZ NOT NULL
    );
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(create_table_query)

    print("✓ Database ready")


# =========================================================
# NORMALIZE URL
# =========================================================

def normalize_url(url: str) -> str:

    if not url:
        return ""

    url = url.strip()

    # Remove query parameters
    url = url.split("?", 1)[0]

    # Remove trailing slash
    url = url.rstrip("/")

    return url


# =========================================================
# GET PREVIOUSLY SENT ARTICLE URLS
# =========================================================

def get_sent_urls(urls):

    if not urls:
        return set()

    normalized_urls = [
        normalize_url(url)
        for url in urls
        if url
    ]

    if not normalized_urls:
        return set()

    query = """
    SELECT url
    FROM sent_articles
    WHERE url = ANY(%s);
    """

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(query, (normalized_urls,))

            rows = cur.fetchall()

    return {
        normalize_url(row[0])
        for row in rows
    }


# =========================================================
# MARK ARTICLE AS SENT
# =========================================================

def mark_article_sent(article):

    url = normalize_url(article.get("link") or article.get("url"))

    title = article.get("title", "Untitled")

    source = article.get("source", "Unknown")

    if not url:
        print("⚠ Cannot save article: missing URL")
        return

    query = """
    INSERT INTO sent_articles (
        url,
        title,
        source,
        sent_at
    )
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (url) DO NOTHING;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                query,
                (
                    url,
                    title,
                    source,
                    datetime.now(timezone.utc),
                ),
            )


# =========================================================
# CHECK IF ARTICLE WAS ALREADY SENT
# =========================================================

def is_article_sent(url):

    normalized_url = normalize_url(url)

    if not normalized_url:
        return False

    query = """
    SELECT 1
    FROM sent_articles
    WHERE url = %s
    LIMIT 1;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(query, (normalized_url,))

            return cur.fetchone() is not None