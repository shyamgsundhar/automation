import psycopg

from datetime import datetime, timezone

from .config import DATABASE_URL


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not configured"
        )

    clean_url = DATABASE_URL.strip()

    return psycopg.connect(clean_url)


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
