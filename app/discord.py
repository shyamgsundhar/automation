import asyncio
import aiohttp

from .config import (
    DISCORD_WEBHOOK_URL,
    MAX_DISCORD_CHARS,
    DISCORD_RETRIES,
    DISCORD_RETRY_DELAY,
    DISCORD_MESSAGE_DELAY,
)


def build_message(article, summary, number):
    message = f"""💻 **TECH NEWS BRIEF**

**{number}. {article["title"]}**

📝 {summary}

🔗 <{article["link"]}>"""

    if len(message) > MAX_DISCORD_CHARS:
        allowed_summary_length = 500

        summary = summary[:allowed_summary_length].rsplit(" ", 1)[0] + "..."

        message = f"""💻 **TECH NEWS BRIEF**

**{number}. {article["title"]}**

📝 {summary}

🔗 <{article["link"]}>"""

    return message


async def send_to_discord(session, message):

    for attempt in range(1, DISCORD_RETRIES + 1):

        try:

            async with session.post(
                DISCORD_WEBHOOK_URL,
                json={
                    "content": message
                },
            ) as response:

                if response.status in (200, 204):

                    print("  ✓ Discord message sent")

                    return True

                body = await response.text()

                print(
                    f"  ✗ Discord failed "
                    f"(attempt {attempt}): "
                    f"{response.status} {body}"
                )

        except Exception as error:

            print(
                f"  ✗ Discord error "
                f"(attempt {attempt}): {error}"
            )

        if attempt < DISCORD_RETRIES:
            await asyncio.sleep(DISCORD_RETRY_DELAY)

    return False


async def send_news_queue(articles):

    successful_articles = []

    async with aiohttp.ClientSession() as session:

        for index, article in enumerate(articles, start=1):

            summary = article.get("summary")

            if not summary:
                print(
                    f"  ⚠ Skipping Discord "
                    f"(no summary): {article['title']}"
                )

                continue

            message = build_message(
                article,
                summary,
                index,
            )

            success = await send_to_discord(
                session,
                message,
            )

            if success:
                successful_articles.append(article)

            await asyncio.sleep(DISCORD_MESSAGE_DELAY)

    return successful_articles