# Import our AI stock research function
from ai_researcher import research_stock


def main():
    # Test the agent using Nvidia
    print("Testing AI Stock Research Agent...")
    print("\nStock: NVDA (Nvidia)\n")

    try:
        # Retrieve news and generate an AI summary
        result = research_stock("NVDA")
        print(result)

    except Exception as error:
        print(f"AI research error: {error}")
        raise


if __name__ == "__main__":
    main()
