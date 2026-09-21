import asyncio

from .feeds import fetch_all_feeds

from .filter import (
    clean_text,
    deduplicate_articles,
    filter_fresh,
    filter_tech_news,
    rank_articles,
    select_diverse_articles,
)

from .article import fetch_article_contents

from .summarizer import summarize_article

from .discord import send_news_queue

from .database import (
    init_database,
    get_sent_urls,
    mark_article_sent,
)

from .config import (
    MAX_ARTICLES_TO_SUMMARIZE,
    MAX_CANDIDATES,
)


async def main():

    print("=" * 60)
    print("TECH NEWS BOT STARTED")
    print("=" * 60)

    # ==================================================
    # 1. DATABASE
    # ==================================================

    print("\n[1] Initializing database...")

    try:
        init_database()

        print("✓ Database ready")

    except Exception as error:

        print(
            f"✗ Database initialization failed: "
            f"{error}"
        )

        return

    # ==================================================
    # 2. FETCH RSS
    # ==================================================

    print("\n[2] Fetching RSS feeds...")

    try:

        articles = await fetch_all_feeds()

    except Exception as error:

        print(
            f"✗ RSS fetching failed: {error}"
        )

        return

    print(
        f"✓ Total fetched: {len(articles)}"
    )

    if not articles:

        print("No articles found.")

        return

    # ==================================================
    # 3. CLEAN TEXT
    # ==================================================

    for article in articles:

        article["title"] = clean_text(
            article.get("title", "")
        )

        article["description"] = clean_text(
            article.get("description", "")
        )

    # ==================================================
    # 4. DEDUPLICATE
    # ==================================================

    articles = deduplicate_articles(
        articles
    )

    print(
        f"✓ After dedup: {len(articles)}"
    )

    if not articles:

        print("No articles after dedup.")

        return

    # ==================================================
    # 5. FRESHNESS FILTER
    # ==================================================

    articles = filter_fresh(
        articles
    )

    print(
        f"✓ Fresh articles: {len(articles)}"
    )

    if not articles:

        print("No fresh articles.")

        return

    # ==================================================
    # 6. CHECK SENT ARTICLES
    # ==================================================

    print(
        "\n[3] Checking previously sent articles..."
    )

    try:

        urls = [
            article["link"]
            for article in articles
            if article.get("link")
        ]

        sent_urls = get_sent_urls(
            urls
        )

        print(
            f"✓ Already sent: "
            f"{len(sent_urls)}"
        )

        unsent_articles = []

        for article in articles:

            normalized_url = (
                article["link"]
                .split("?")[0]
                .rstrip("/")
            )

            if normalized_url not in sent_urls:

                unsent_articles.append(
                    article
                )

        articles = unsent_articles

        print(
            f"✓ Unsent articles: "
            f"{len(articles)}"
        )

    except Exception as error:

        print(
            f"✗ Database check failed: "
            f"{error}"
        )

        return

    if not articles:

        print(
            "\n✓ No new articles to send."
        )

        return

    # ==================================================
    # 7. TECH NEWS FILTER
    # ==================================================

    articles = filter_tech_news(
        articles
    )

    print(
        f"✓ Tech articles: {len(articles)}"
    )

    if not articles:

        print(
            "No relevant tech articles."
        )

        return

    # ==================================================
    # 8. RANK ARTICLES
    # ==================================================

    articles = rank_articles(
        articles
    )

    # ==================================================
    # 9. TOP CANDIDATES
    # ==================================================

    candidates = articles[
        :MAX_CANDIDATES
    ]

    print(
        f"✓ Candidates selected: "
        f"{len(candidates)}"
    )

    # ==================================================
    # 10. DIVERSITY SELECTION
    # ==================================================

    selected = select_diverse_articles(
        candidates,
        MAX_ARTICLES_TO_SUMMARIZE,
    )

    if not selected:

        print(
            "No articles selected."
        )

        return

    print("\nTop stories:")

    for index, article in enumerate(
        selected,
        start=1,
    ):

        print(
            f"{index}. "
            f"{article['source']} - "
            f"{article['title']}"
        )

    # ==================================================
    # 11. FETCH ORIGINAL ARTICLE CONTENT
    # ==================================================

    print(
        "\n[4] Fetching article content..."
    )

    try:

        selected = await fetch_article_contents(
            selected
        )

    except Exception as error:

        print(
            f"✗ Article fetching failed: "
            f"{error}"
        )

        return

    # ==================================================
    # 12. GROQ SUMMARIZATION
    # ==================================================

    print(
        "\n[5] Generating summaries..."
    )

    valid_articles = []

    for article in selected:

        print(
            f"\nSummarizing: "
            f"{article['title']}"
        )

        try:

            summary = summarize_article(
                article
            )

        except Exception as error:

            print(
                f"  ✗ Summarization error: "
                f"{error}"
            )

            summary = None

        if summary:

            article["summary"] = summary

            valid_articles.append(
                article
            )

        else:

            print(
                "  ⚠ Skipping article "
                "(summary generation failed)"
            )

    print(
        f"\n✓ Valid summaries: "
        f"{len(valid_articles)}"
    )

    if not valid_articles:

        print(
            "No valid summaries generated."
        )

        return

    # ==================================================
    # 13. SEND TO DISCORD
    # ==================================================

    print(
        "\n[6] Sending to Discord..."
    )

    try:

        sent_articles = await send_news_queue(
            valid_articles
        )

    except Exception as error:

        print(
            f"✗ Discord queue failed: "
            f"{error}"
        )

        return

    print(
        f"✓ Successfully sent: "
        f"{len(sent_articles)}"
    )

    # ==================================================
    # 14. SAVE SUCCESSFULLY SENT ARTICLES
    # ==================================================

    print(
        "\n[7] Saving sent articles..."
    )

    saved_count = 0

    for article in sent_articles:

        try:

            mark_article_sent(
                article
            )

            saved_count += 1

            print(
                f"✓ Saved: "
                f"{article['title']}"
            )

        except Exception as error:

            print(
                f"✗ Failed to save "
                f"{article['title']}: "
                f"{error}"
            )

    # ==================================================
    # 15. COMPLETE
    # ==================================================

    print("\n" + "=" * 60)
    print("TECH NEWS BOT COMPLETED")
    print("=" * 60)

    print(
        f"Articles sent : "
        f"{len(sent_articles)}"
    )

    print(
        f"Articles saved: "
        f"{saved_count}"
    )

    print("=" * 60)


if __name__ == "__main__":

    asyncio.run(main())