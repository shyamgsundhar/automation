import asyncio
import aiohttp
import feedparser

from .config import REQUEST_TIMEOUT


RSS_FEEDS = [

    # ========================================================
    # MAJOR TECH
    # ========================================================

    {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "quality": 10,
        "category": "general",
    },

    {
        "name": "The Verge",
        "url": "https://www.theverge.com/rss/index.xml",
        "quality": 9,
        "category": "general",
    },

    {
        "name": "Ars Technica",
        "url": "https://feeds.arstechnica.com/arstechnica/index",
        "quality": 10,
        "category": "technical",
    },

    {
        "name": "WIRED",
        "url": "https://www.wired.com/feed/rss",
        "quality": 10,
        "category": "general",
    },

    {
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com/feed/",
        "quality": 10,
        "category": "research",
    },

    # ========================================================
    # ENTERPRISE / ENGINEERING
    # ========================================================

    {
        "name": "The Register",
        "url": "https://www.theregister.com/?lab_viewport=rss",
        "quality": 9,
        "category": "enterprise",
    },

    {
        "name": "Engadget",
        "url": "https://www.engadget.com/rss.xml",
        "quality": 8,
        "category": "consumer",
    },

    {
        "name": "Hacker News",
        "url": "https://hnrss.org/frontpage",
        "quality": 8,
        "category": "developer",
    },

    {
        "name": "IEEE Spectrum",
        "url": "https://spectrum.ieee.org/feed",
        "quality": 10,
        "category": "engineering",
    },

    # ========================================================
    # CYBERSECURITY
    # ========================================================

    {
        "name": "BleepingComputer",
        "url": "https://www.bleepingcomputer.com/feed/",
        "quality": 9,
        "category": "security",
    },

    {
        "name": "The Hacker News",
        "url": "https://thehackernews.com/feeds/posts/default?alt=rss",
        "quality": 8,
        "category": "security",
    },

    # ========================================================
    # DEVELOPMENT
    # ========================================================

    {
        "name": "HackerNoon",
        "url": "https://hackernoon.com/feed",
        "quality": 7,
        "category": "developer",
    },

    {
        "name": "Smashing Magazine",
        "url": "https://www.smashingmagazine.com/feed/",
        "quality": 7,
        "category": "developer",
    },

    {
        "name": "Lobsters",
        "url": "https://lobste.rs/rss",
        "quality": 7,
        "category": "developer",
    },

    # ========================================================
    # HARDWARE
    # ========================================================

    {
        "name": "Tom's Hardware",
        "url": "https://www.tomshardware.com/feeds/all",
        "quality": 8,
        "category": "hardware",
    },

    {
        "name": "TechRadar",
        "url": "https://www.techradar.com/rss",
        "quality": 7,
        "category": "consumer",
    },

    # ========================================================
    # APPLE / MOBILE
    # ========================================================

    {
        "name": "9to5Mac",
        "url": "https://9to5mac.com/feed/",
        "quality": 7,
        "category": "consumer",
    },

    {
        "name": "Android Authority",
        "url": "https://www.androidauthority.com/feed/",
        "quality": 7,
        "category": "consumer",
    },

    # ========================================================
    # AI / OPEN SOURCE
    # ========================================================

    {
        "name": "Hugging Face",
        "url": "https://huggingface.co/blog/feed.xml",
        "quality": 9,
        "category": "ai",
    },
]


async def fetch_feed(session, feed):

    try:

        print(
            f"Fetching: {feed['name']}"
        )

        async with session.get(
            feed["url"],
            timeout=aiohttp.ClientTimeout(
                total=REQUEST_TIMEOUT
            ),
            headers={
                "User-Agent":
                    "TechNewsAggregator/2.0"
            },
        ) as response:

            if response.status != 200:

                raise Exception(
                    f"HTTP {response.status}"
                )

            content = await response.text()

        parsed = feedparser.parse(
            content
        )

        if not parsed.entries:

            print(
                f"⚠ {feed['name']}: "
                f"0 articles"
            )

            return []

        articles = []

        for entry in parsed.entries:

            title = (
                entry.get("title", "")
                .strip()
            )

            link = (
                entry.get("link", "")
                .strip()
            )

            if not title or not link:
                continue

            description = (
                entry.get("summary", "")
                or entry.get("description", "")
                or ""
            ).strip()

            published = (
                entry.get("published", "")
                or entry.get("updated", "")
                or ""
            )

            articles.append({

                "title": title,

                "link": link,

                "description": description,

                "published": published,

                "source": feed["name"],

                "source_quality":
                    feed["quality"],

                "category":
                    feed["category"],
            })

        print(
            f"✓ {feed['name']}: "
            f"{len(articles)} articles"
        )

        return articles

    except Exception as error:

        print(
            f"✗ {feed['name']} failed: "
            f"{error}"
        )

        return []


async def fetch_all_feeds():

    connector = aiohttp.TCPConnector(
        limit=20
    )

    async with aiohttp.ClientSession(
        connector=connector
    ) as session:

        tasks = [
            fetch_feed(
                session,
                feed
            )
            for feed in RSS_FEEDS
        ]

        results = await asyncio.gather(
            *tasks
        )

    articles = []

    for result in results:

        articles.extend(result)

    return articles