import requests
import json
import pandas as pd

# 🔑 Replace with your Fireworks API key
API_KEY = "fw_3Ze6VZiWKsBQLrAtUnmu4FCc"

# Fireworks endpoint
url = "https://api.fireworks.ai/inference/v1/chat/completions"

# Function to fetch historical price data from CoinGecko
def get_historical_prices(symbol="bitcoin", days=90):
    cg_url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart?vs_currency=usd&days={days}"
    r = requests.get(cg_url).json()
    if "prices" not in r:
        raise ValueError(f"Error fetching {symbol}. Check spelling or try another coin.")
    prices = r["prices"]  # [timestamp, price]
    df = pd.DataFrame(prices, columns=["timestamp", "price"])
    df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("date", inplace=True)
    return df

# Simple moving average backtest
def backtest_ma(df, short=10, long=30):
    df["SMA_short"] = df["price"].rolling(short).mean()
    df["SMA_long"] = df["price"].rolling(long).mean()
    df["signal"] = 0
    df.loc[df["SMA_short"] > df["SMA_long"], "signal"] = 1
    df["returns"] = df["price"].pct_change()
    df["strategy"] = df["signal"].shift(1) * df["returns"]
    return df

# Run backtest + get Dobby’s analysis
def run_backtest(symbol="bitcoin", days=180):
    try:
        df = get_historical_prices(symbol, days)
        df = backtest_ma(df)

        total_return = (df["strategy"] + 1).prod() - 1
        hold_return = (df["returns"] + 1).prod() - 1

        summary = f"""
Backtest results for {symbol.upper()} (last {days} days):
- Strategy Return: {total_return:.2%}
- Buy & Hold Return: {hold_return:.2%}
- Signals generated: {df['signal'].sum()}
        """

        print("📊 Backtest Summary:")
        print(summary)

        # Send results to Dobby
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Dobby, the chaotic crypto oracle. "
                    "Explain backtest results in wild, funny, and chaotic style. "
                    "⚠️ NEVER give financial advice. This is for entertainment only."
                )
            },
            {"role": "user", "content": summary}
        ]

        payload = {
            "model": "accounts/sentientfoundation/models/dobby-unhinged-llama-3-3-70b-new",
            "max_tokens": 400,
            "temperature": 0.9,
            "messages": messages
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            result = response.json()
            reply = result['choices'][0]['message']['content']
            print("\n💎 Dobby’s Chaotic Analysis:\n", reply)
        else:
            print("⚠️ API Error:", response.text)

    except Exception as e:
        print(f"❌ Error: {e}")

# -------------------------
# 🧑‍💻 Interactive Loop
# -------------------------
while True:
    coin = input("\n👉 Enter a crypto coin (e.g., bitcoin, ethereum, solana) or 'quit' to exit: ").lower().strip()
    if coin == "quit":
        print("👋 Exiting... Dobby vanishes into the blockchain abyss.")
        break
    days = input("📅 Enter number of days for backtest (e.g., 90, 180, 365): ").strip()
    if not days.isdigit():
        days = "180"
    run_backtest(coin, int(days))
