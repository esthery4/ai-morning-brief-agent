# Tools for retrieving financial news
import os
import time
from urllib.parse import quote

import feedparser

# Tools for Gemini AI and LangGraph
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict


# Information shared between agent steps
class ResearchState(TypedDict):
    ticker: str
    headlines: list
    analysis: str
    market_data: dict


def fetch_news(state: ResearchState):
    """Retrieve financial news for a stock."""

    ticker = state["ticker"]

    # Search Google News for company developments
    query = quote(f"{ticker} stock earnings company")

    url = (
        "https://news.google.com/rss/search"
        f"?q={query}&hl=en-US&gl=US&ceid=US:en"
    )

    feed = feedparser.parse(url)

    # Keep up to five headlines
    headlines = [
        {
            "title": entry.title,
            "link": entry.link
        }
        for entry in feed.entries[:5]
    ]

    return {"headlines": headlines}


def analyze_news(state: ResearchState):
    """Use Gemini to investigate unusual stock activity."""

    # Connect to Gemini
    model = ChatGoogleGenerativeAI(
        model=os.environ["GEMINI_MODEL"],
        temperature=0
    )

    if not state["headlines"]:
        return {
            "analysis": "No recent financial news found."
        }

    # Format news headlines
    news_text = "\n".join(
        f"- {item['title']}\n  {item['link']}"
        for item in state["headlines"]
    )

    # Get stock statistics from the anomaly detector
    market_data = state.get("market_data") or {}

    statistics = (
        f"Data date: {market_data.get('date', 'N/A')}\n"
        f"Daily change: {market_data.get('daily_change', 'N/A')}%\n"
        f"Weekly change: {market_data.get('weekly_change', 'N/A')}%\n"
        f"Monthly change: {market_data.get('monthly_change', 'N/A')}%\n"
        f"Z-score: {market_data.get('z_score', 'N/A')}\n"
        f"Volume ratio: {market_data.get('volume_ratio', 'N/A')}x"
    )

    # Instructions for Gemini
    prompt = f"""
    You are a financial news research assistant.

    Stock ticker: {state['ticker']}

    Market statistics:
    {statistics}

    Recent headlines:
    {news_text}

    Write a short financial briefing covering:

    1. Company name and industry.
    2. Important recent developments.
    3. Possible reasons for unusual stock activity.
    4. Relevant industry trends.

    Requirements:
    - Use only the supplied statistics and headlines.
    - Do not invent financial events or statistics.
    - Do not assume news caused a price movement.
    - Clearly distinguish facts from possible explanations.
    - If information is insufficient, say so.
    - Include supporting news links.
    - Keep the briefing under 180 words.
    """

    # Retry if Gemini is temporarily unavailable
    for attempt in range(3):
        try:
            response = model.invoke(prompt)

            # Return readable AI-generated text
            return {"analysis": response.text}

        except Exception as error:
            message = str(error)

            # Retry only temporary server errors
            if "503" not in message and "UNAVAILABLE" not in message:
                raise

            # Stop after the final attempt
            if attempt == 2:
                raise

            # Wait longer between attempts
            wait_time = 5 * (2 ** attempt)

            print(
                f"Gemini unavailable. "
                f"Retrying in {wait_time}s..."
            )

            time.sleep(wait_time)


def build_research_agent():
    """Create the LangGraph research workflow."""

    graph = StateGraph(ResearchState)

    # Step 1: Retrieve financial headlines
    graph.add_node("fetch_news", fetch_news)

    # Step 2: Analyze headlines using Gemini
    graph.add_node("analyze_news", analyze_news)

    # Connect the agent steps
    graph.add_edge(START, "fetch_news")
    graph.add_edge("fetch_news", "analyze_news")
    graph.add_edge("analyze_news", END)

    return graph.compile()


def research_stock(ticker, market_data=None):
    """Run AI research for a selected stock."""

    agent = build_research_agent()

    result = agent.invoke({
        "ticker": ticker,
        "headlines": [],
        "analysis": "",
        "market_data": market_data or {}
    })

    return result["analysis"]
