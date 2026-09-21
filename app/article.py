import asyncio
import re

import aiohttp
from bs4 import BeautifulSoup

from .config import (
    REQUEST_TIMEOUT,
    MAX_ARTICLE_CHARS,
)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36"
    )
}


def clean_article_text(text):
    """Clean extracted article text."""

    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)

    return text.strip()


async def fetch_article_content(
    session,
    article,
):
    """Fetch and extract the main article content."""

    url = article.get("link")

    if not url:
        return article

    try:

        async with session.get(
            url,
            headers=HEADERS,
            timeout=aiohttp.ClientTimeout(
                total=REQUEST_TIMEOUT
            ),
            allow_redirects=True,
        ) as response:

            if response.status != 200:
                print(
                    f"  ⚠ Article fetch failed "
                    f"{response.status}: {url}"
                )

                # RSS description fallback
                article["content"] = article.get(
                    "description",
                    "",
                )

                return article

            html = await response.text(
                errors="ignore"
            )

    except Exception as error:

        print(
            f"  ⚠ Article fetch error: {error}"
        )

        article["content"] = article.get(
            "description",
            "",
        )

        return article

    try:

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        # Remove unnecessary elements
        for element in soup(
            [
                "script",
                "style",
                "nav",
                "footer",
                "header",
                "aside",
                "form",
                "noscript",
                "svg",
                "iframe",
            ]
        ):
            element.decompose()

        # Remove common advertisement elements
        for element in soup.select(
            """
            .advertisement,
            .ad,
            .ads,
            .sidebar,
            .social-share,
            .newsletter,
            .cookie-banner
            """
        ):
            element.decompose()

        paragraphs = []

        for paragraph in soup.find_all("p"):

            text = clean_article_text(
                paragraph.get_text(
                    " ",
                    strip=True,
                )
            )

            if len(text) >= 40:
                paragraphs.append(text)

        content = "\n".join(paragraphs)

        # If webpage extraction is poor,
        # use RSS description.
        if len(content) < 300:

            content = clean_article_text(
                article.get(
                    "description",
                    "",
                )
            )

        # Limit content sent to Groq
        content = content[:MAX_ARTICLE_CHARS]

        article["content"] = content

        return article

    except Exception as error:

        print(
            f"  ⚠ Content extraction error: "
            f"{error}"
        )

        article["content"] = article.get(
            "description",
            "",
        )

        return article


async def fetch_article_contents(articles):
    """
    Fetch multiple article pages concurrently.
    """

    if not articles:
        return []

    timeout = aiohttp.ClientTimeout(
        total=REQUEST_TIMEOUT
    )

    connector = aiohttp.TCPConnector(
        limit=10
    )

    async with aiohttp.ClientSession(
        timeout=timeout,
        connector=connector,
        headers=HEADERS,
    ) as session:

        tasks = [
            fetch_article_content(
                session,
                article,
            )
            for article in articles
        ]

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

    valid_articles = []

    for article, result in zip(
        articles,
        results,
    ):

        if isinstance(result, Exception):

            print(
                f"  ⚠ Failed: "
                f"{article.get('title', '')}"
            )

            article["content"] = article.get(
                "description",
                "",
            )

            valid_articles.append(article)

        else:
            valid_articles.append(result)

    return valid_articles