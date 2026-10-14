import pandas as pd

def add_indicators(data):
    data = data.copy()

    # Handle Yahoo Finance MultiIndex columns
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # Ensure Close is numeric
    close = pd.to_numeric(data["Close"], errors="coerce")

    # Moving averages
    data["MA50"] = close.rolling(
        window=50, min_periods=1
    ).mean()

    data["MA200"] = close.rolling(
        window=200, min_periods=1
    ).mean()

    # RSI
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(
        window=14, min_periods=14
    ).mean()

    avg_loss = loss.rolling(
        window=14, min_periods=14
    ).mean()

    rs = avg_gain / avg_loss
    data["RSI"] = 100 - (100 / (1 + rs))

    return data