# Connect the stock scanner to Gemini
from market_analyzer import scan_market
from ai_researcher import research_stock


def main():
    print("=" * 45)
    print("AI STOCK INVESTIGATION")
    print("=" * 45)

    # Scan the market for unusual stocks
    market = scan_market()

    print(
        f"Successfully scanned: "
        f"{market['scanned']}/{market['expected']}"
    )

    # Select the top three anomalies
    top_stocks = market["anomalies"][:3]

    if not top_stocks:
        print("No unusual stock movements detected.")
        return

    # Investigate each stock
    for stock in top_stocks:
        ticker = stock["ticker"]

        print(f"\n{'=' * 45}")
        print(f"INVESTIGATING: {ticker}")
        print(f"{'=' * 45}")

        # Display the market statistics
        print(f"Date: {stock['date']}")
        print(f"Daily change: {stock['daily_change']:+.2f}%")
        print(f"Weekly change: {stock['weekly_change']:+.2f}%")
        print(f"Monthly change: {stock['monthly_change']:+.2f}%")
        print(f"Z-score: {stock['z_score']:.2f}")
        print(f"Volume ratio: {stock['volume_ratio']:.2f}x")

        # Ask Gemini to investigate the stock
        try:
            analysis = research_stock(
                ticker,
                market_data=stock
            )

            print("\nAI RESEARCH SUMMARY")
            print(analysis)

        except Exception as error:
            # Continue if one stock's AI research fails
            print(
                f"AI research unavailable for "
                f"{ticker}: {error}"
            )

    print("\nAI stock investigation completed!")


if __name__ == "__main__":
    main()
