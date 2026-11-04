import os
import re
import html
import smtplib
import subprocess
import sys
import time

from datetime import datetime, timezone
from email.message import EmailMessage
from urllib.parse import quote
from zoneinfo import ZoneInfo

import feedparser
import requests

from market_analyzer import scan_market


# News topics
NEWS_TOPICS = {
    "Finance & Politics": "US financial markets economy politics",
    "Technology & AI": "artificial intelligence technology",
    "K-pop & Entertainment": "K-pop music entertainment celebrity"
}


def get_daily_weather():
    """Get Rochester weather in Fahrenheit and Celsius."""

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": 43.1566,
        "longitude": -77.6088,
        "current": "temperature_2m,apparent_temperature",
        "daily": "temperature_2m_max,temperature_2m_min",
        "temperature_unit": "fahrenheit",
        "timezone": "America/New_York",
        "forecast_days": 1
    }

    response = requests.get(
        url,
        params=params,
        timeout=15
    )
    response.raise_for_status()

    data = response.json()
    current = data["current"]
    daily = data["daily"]

    def format_temp(fahrenheit):
        celsius = (fahrenheit - 32) * 5 / 9
        return f"{fahrenheit:.0f}°F / {celsius:.0f}°C"

    return {
        "temperature": format_temp(
            current["temperature_2m"]
        ),
        "feels_like": format_temp(
            current["apparent_temperature"]
        ),
        "high": format_temp(
            daily["temperature_2m_max"][0]
        ),
        "low": format_temp(
            daily["temperature_2m_min"][0]
        )
    }


def get_headlines(query, limit=3):
    """Retrieve recent headlines from Google News."""

    search = quote(f"{query} when:2d")

    url = (
        "https://news.google.com/rss/search"
        f"?q={search}&hl=en-US&gl=US&ceid=US:en"
    )

    feed = feedparser.parse(url)
    articles = []

    for entry in feed.entries:
        published = entry.get("published_parsed")

        if not published:
            continue

        # Convert publication date to UTC
        published_time = datetime.fromtimestamp(
            time.mktime(published),
            tz=timezone.utc
        )

        age = (
            datetime.now(timezone.utc) - published_time
        ).total_seconds()

        # Only include articles from the last 48 hours
        if age < 0 or age > 172800:
            continue

        articles.append({
            "title": entry.title,
            "link": entry.link
        })

        if len(articles) >= limit:
            break

    return articles


def get_market_overview():
    """Get the latest market performance."""

    result = subprocess.run(
        [sys.executable, "main.py"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        capture_output=True,
        text=True,
        timeout=180,
        check=False
    )

    if result.returncode != 0:
        print("Market overview failed.")
        return {}

    output = result.stdout

    def find(pattern):
        match = re.search(pattern, output)
        return match.group(1) if match else "Unavailable"

    return {
        "sp500": find(r"S&P 500:\s*([^\n]+)"),
        "nasdaq": find(r"Nasdaq:\s*([^\n]+)"),
        "dow": find(r"Dow Jones:\s*([^\n]+)")
    }


def get_market_highlights(stocks):
    """Summarize unusual stocks without Gemini."""

    if not stocks:
        return "No unusual stock movements identified."

    highlights = []

    for stock in stocks[:3]:
        ticker = stock["ticker"]
        change = stock["daily_change"]
        volume = stock["volume_ratio"]

        direction = "rose" if change >= 0 else "fell"

        highlights.append(
            f"{ticker} {direction} {abs(change):.2f}%, "
            f"with trading volume {volume:.2f}x "
            f"its recent average."
        )

    return "\n".join(
        f"• {highlight}" for highlight in highlights
    )


def generate_ai_summary(stocks, news):
    """Generate one concise Gemini summary."""

    from langchain_google_genai import ChatGoogleGenerativeAI

    stock_lines = "\n".join(
        f"{s['ticker']}: {s['daily_change']:+.2f}%, "
        f"Z-score {s['z_score']}, "
        f"volume {s['volume_ratio']}x"
        for s in stocks
    )

    news_lines = "\n".join(
        f"{category}: {item['title']}"
        for category, items in news.items()
        for item in items
    )

    prompt = f"""
    Prepare a concise morning briefing.

    STOCK DATA:
    {stock_lines}

    NEWS HEADLINES:
    {news_lines}

    Return plain text with these headings:

    MARKET DRIVERS
    Summarize important financial or political developments
    in 2 short sentences.

    STOCK WATCH
    Explain possible reasons for unusual stock movements
    in 2 short sentences.

    WHAT TO WATCH
    Identify one upcoming development and explain how it
    could affect everyday consumers.

    REQUIREMENTS:
    - Maximum 110 words.
    - Use only the supplied data and headlines.
    - Do not invent events or financial statistics.
    - Do not claim a headline caused a price movement
      unless evidence establishes the connection.
    - Clearly distinguish facts from speculation.
    - If evidence is insufficient, say so.
    - Do not repeat the news headlines.
    - Do not include URLs.
    """

    try:
        model = ChatGoogleGenerativeAI(
            model=os.environ.get(
                "GEMINI_MODEL", "gemini-3.8-flash"
            ),
            temperature=0,
            max_retries=0
        )

        response = model.invoke(prompt)
        return str(response.text).strip()

    except Exception as error:
        message = str(error)

        if "429" in message or "RESOURCE_EXHAUSTED" in message:
            print("Gemini quota reached. Using fallback.")
        elif "503" in message or "UNAVAILABLE" in message:
            print("Gemini temporarily unavailable.")
        else:
            print("Gemini failed:", type(error).__name__)

        return (
            "MARKET DRIVERS\n"
            "AI analysis is unavailable today. "
            "See the latest headlines below.\n\n"
            "STOCK WATCH\n"
            "Unusual price movements were detected. "
            "Their causes have not been verified.\n\n"
            "WHAT TO WATCH\n"
            "Monitor upcoming economic and company announcements."
        )


def build_email(weather, markets, stocks, news, ai_summary):
    """Build a compact HTML morning briefing."""

    today = datetime.now(
        ZoneInfo("America/New_York")
    ).strftime("%A, %B %d, %Y")

    def safe(value):
        return html.escape(str(value))

    def panel(title, content):
        return f"""
        <div style="
            background:#ffffff;
            border:1px solid #e5e7eb;
            border-radius:10px;
            padding:18px;
            margin-bottom:14px;
        ">
            <h2 style="
                font-size:16px;
                margin:0 0 12px;
                color:#17283e;
            ">{safe(title)}</h2>
            {content}
        </div>
        """

    # WEATHER
    weather_panel = panel(
        "Weather | Rochester, NY",
        f"""
        <p style="font-size:23px;margin:0 0 5px;">
            <b>{safe(weather.get('temperature', 'N/A'))}</b>
        </p>

        <p style="color:#64748b;margin:0 0 14px;">
            Feels like {safe(weather.get('feels_like', 'N/A'))}
        </p>

        <table style="width:100%;">
            <tr>
                <td>
                    <b>Today's High</b><br>
                    {safe(weather.get('high', 'N/A'))}
                </td>
                <td>
                    <b>Today's Low</b><br>
                    {safe(weather.get('low', 'N/A'))}
                </td>
            </tr>
        </table>
        """
    )

    # FINANCIAL MARKETS
    markets_panel = panel(
        "Financial Markets",
        f"""
        <p><b>S&P 500:</b> {safe(markets.get('sp500', 'N/A'))}</p>
        <p><b>Nasdaq:</b> {safe(markets.get('nasdaq', 'N/A'))}</p>
        <p><b>Dow Jones:</b> {safe(markets.get('dow', 'N/A'))}</p>
        <p style="font-size:12px;color:#64748b;">
            Latest available market performance.
        </p>
        """
    )

    # STOCK HIGHLIGHTS
    stock_rows = ""

    for stock in stocks:
        change = stock["daily_change"]
        color = "#16803c" if change >= 0 else "#c2413b"

        stock_rows += f"""
        <tr>
            <td style="padding:8px 0;">
                <b>{safe(stock['ticker'])}</b>
            </td>
            <td style="
                text-align:right;
                color:{color};
                padding:8px 0;
            ">
                {change:+.2f}%
            </td>
        </tr>
        """

    stocks_panel = panel(
        "Unusual Stock Activity",
        f"""
        <table style="width:100%;border-collapse:collapse;">
            {stock_rows}
        </table>

        <div style="
            white-space:pre-wrap;
            font-size:13px;
            color:#64748b;
            margin-top:10px;
        ">{safe(get_market_highlights(stocks))}</div>
        """
        if stock_rows else "<p>No unusual stocks identified.</p>"
    )

    # AI MARKET ANALYSIS
    ai_panel = panel(
        "Why It Matters & What to Watch",
        f"""
        <div style="
            white-space:pre-wrap;
            line-height:1.6;
            font-size:14px;
        ">{safe(ai_summary)}</div>
        """
    )

    # NEWS
    news_panels = ""

    for category, articles in news.items():
        rows = ""

        for article in articles:
            title = safe(article["title"])
            link = safe(article["link"])

            rows += f"""
            <p style="margin:0 0 12px;">
                <a href="{link}" style="
                    color:#2563eb;
                    text-decoration:none;
                ">{title}</a>
            </p>
            """

        news_panels += panel(
            category,
            rows or "<p>No recent headlines available.</p>"
        )

    # COMPLETE EMAIL
    return f"""
    <html>
    <body style="
        background:#f3f4f6;
        font-family:Arial,sans-serif;
        color:#334155;
        padding:18px;
        margin:0;
        line-height:1.5;
    ">
        <div style="max-width:620px;margin:auto;">

            <div style="
                background:#17283e;
                padding:24px;
                border-radius:10px;
                margin-bottom:16px;
                color:white;
            ">
                <h1 style="margin:0;font-size:25px;">
                    Your Morning Brief
                </h1>
                <p style="margin:8px 0 0;color:#cbd5e1;">
                    {safe(today)} · 2-minute read
                </p>
            </div>

            {weather_panel}
            {markets_panel}
            {stocks_panel}
            {ai_panel}
            {news_panels}

            <p style="
                font-size:11px;
                text-align:center;
                color:#64748b;
            ">
                Generated by your AI Morning Brief Agent.
                Financial information is not investment advice.
                AI summaries may contain errors.
            </p>

        </div>
    </body>
    </html>
    """


def send_email(html_body):
    """Send the briefing through Gmail."""

    sender = os.environ["GMAIL_ADDRESS"]
    password = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ.get("BRIEF_RECIPIENT", sender)

    today = datetime.now(
        ZoneInfo("America/New_York")
    ).strftime("%b %d, %Y")

    message = EmailMessage()

    message["Subject"] = f"Morning Brief | {today}"
    message["From"] = sender
    message["To"] = recipient

    message.set_content(
        "Your Morning Brief is available in HTML format."
    )
    message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL(
        "smtp.gmail.com", 465, timeout=30
    ) as server:
        server.login(sender, password)
        server.send_message(message)

    print("Morning Brief email sent successfully!")


def main():
    print("Generating your morning briefing...")

    # 1. WEATHER
    try:
        weather = get_daily_weather()
    except Exception as error:
        print("Weather unavailable:", type(error).__name__)
        weather = {}

    # 2. FINANCIAL MARKETS
    try:
        markets = get_market_overview()
    except Exception as error:
        print("Markets unavailable:", type(error).__name__)
        markets = {}

    # 3. STOCK ANOMALIES
    try:
        scan = scan_market()
        stocks = scan["anomalies"][:3]

        print(f"Successfully scanned {scan['scanned']} stocks.")

    except Exception as error:
        print("Stock scan failed:", type(error).__name__)
        stocks = []

    # 4. NEWS
    news = {}

    for category, query in NEWS_TOPICS.items():
        try:
            news[category] = get_headlines(
                query,
                limit=3
            )
        except Exception as error:
            print(f"News fetch failed: {category}")
            news[category] = []

    # 5. GEMINI SUMMARY
    ai_summary = generate_ai_summary(stocks, news)

    # 6. BUILD EMAIL
    email_html = build_email(
        weather,
        markets,
        stocks,
        news,
        ai_summary
    )

    # 7. SEND EMAIL
    send_email(email_html)


if __name__ == "__main__":
    main()
