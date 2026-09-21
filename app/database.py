import psycopg

from datetime import datetime, timezone

from .config import DATABASE_URL


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")

    return psycopg.connect(DATABASE_URL)


def init_database():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sent_articles (
                    id BIGSERIAL PRIMARY KEY,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    source TEXT NOT NULL,
                    sent_at TIMESTAMPTZ NOT NULL
                )
            """)

        connection.commit()

    finally:
        connection.close()


def normalize_url(url):
    """
    Normalize article URL so tracking works
    even when query parameters are different.
    """

    if not url:
        return ""

    return url.split("?")[0].rstrip("/")


def get_sent_urls(urls):
    """
    Check all article URLs in ONE database query.

    Returns:
        set of URLs that were already sent.
    """

    if not urls:
        return set()

    normalized_urls = {
        normalize_url(url)
        for url in urls
        if url
    }

    if not normalized_urls:
        return set()

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                SELECT url
                FROM sent_articles
                WHERE url = ANY(%s)
                """,
                (list(normalized_urls),),
            )

            rows = cursor.fetchall()

            return {
                row[0]
                for row in rows
            }

    finally:
        connection.close()


def mark_article_sent(article):
    """
    Mark an article as sent after
    successful Discord delivery.
    """

    normalized_url = normalize_url(
        article["link"]
    )

    if not normalized_url:
        return

    connection = get_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO sent_articles
                (
                    url,
                    title,
                    source,
                    sent_at
                )
                VALUES (%s, %s, %s, %s)

                ON CONFLICT (url)
                DO NOTHING
                """,
                (
                    normalized_url,
                    article["title"],
                    article["source"],
                    datetime.now(timezone.utc),
                ),
            )

        connection.commit()

    finally:
        connection.close()