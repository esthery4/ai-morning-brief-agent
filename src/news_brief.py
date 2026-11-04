# Retrieve and summarize personalized news
import os
import time
from datetime import datetime, timezone
from urllib.parse import quote

import feedparser
from langchain_google_genai import ChatGoogleGenerativeAI


# News topics for the morning briefing
NEWS_CATEGORIES = {
    "General News": "major US and world news",
    "Technology": "artificial intelligence technology news",
    "K-pop": "K-pop music groups comeback entertainment",
    "Music": "music industry Grammy Awards new releases",
    "Entertainment": "celebrity pop culture Met Gala entertainment"
}


def fetch_headlines(query, limit=4):
    """Retrieve recent headlines from Google News."""

    search_query = quote(f"{query} when:2d")

    url = (
        "https://news.google.com/rss/search"
        f"?q={search_query}&hl=en-US&gl=US&ceid=US:en"
    )

    feed = feedparser.parse(url)

    headlines = []

    for entry in feed.entries[:limit]:
        headlines.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.get("published", "Unknown")
        })

    return headlines


def summarize_news(category, headlines):
    """Ask Gemini to summarize recent headlines."""

    if not headlines:
        return "No recent headlines available."

    # Format the headlines for Gemini
    news_text = "\n".join(
        f"- {item['title']}\n"
        f"  Published: {item['published']}\n"
        f"  Source: {item['link']}"
        for item in headlines
    )

    model = ChatGoogleGenerativeAI(
        model=os.environ["GEMINI_MODEL"],
        temperature=0
    )

    prompt = f"""
    You are preparing a personalized morning news briefing.

    Current UTC date: {datetime.now(timezone.utc).date()}
    Category: {category}

    Headlines:
    {news_text}

    Write a short, easy-to-read summary.

    Requirements:
    - Highlight the most important developments.
    - Use only the supplied headlines as evidence.
    - Do not invent facts or events.
    - Do not treat predictions as confirmed events.
    - Clearly distinguish speculation from facts.
    - Include links to relevant articles.
    - Avoid repeating similar stories.
    - Keep the summary under 130 words.
    """

    # Retry temporary Gemini server errors
    for attempt in range(3):
        try:
            response = model.invoke(prompt)
            return response.text

        except Exception as error:
            message = str(error)

            if "503" not in message and "UNAVAILABLE" not in message:
                raise

            if attempt == 2:
                raise

            wait_time = 5 * (2 ** attempt)

            print(
                f"Gemini unavailable. "
                f"Retrying in {wait_time}s..."
            )

            time.sleep(wait_time)


def main():
    """Generate personalized news summaries."""

    print("=" * 45)
    print("PERSONALIZED NEWS BRIEFING")
    print("=" * 45)

    for category, query in NEWS_CATEGORIES.items():
        print(f"\n--- {category.upper()} ---")

        try:
            # Retrieve recent headlines
            headlines = fetch_headlines(query)

            # Summarize with Gemini
            summary = summarize_news(category, headlines)

            print(summary)

        except Exception as error:
            # Keep the briefing running if one topic fails
            print(f"News summary unavailable: {error}")

    print("\nPersonalized news briefing completed!")


if __name__ == "__main__":
    main()
