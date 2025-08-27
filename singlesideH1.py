import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- Load Data (H1 for example) ---
eur = pd.read_csv("data/EURUSD_H1_2024.csv", parse_dates=["datetime"], index_col="datetime")
gbp = pd.read_csv("data/GBPUSD_H1_2024.csv", parse_dates=["datetime"], index_col="datetime")

df = pd.DataFrame({"EURUSD": eur["close"], "GBPUSD": gbp["close"]}).dropna()

# --- Indicators ---
window = 20
df["spread"] = df["EURUSD"] - df["GBPUSD"]
df["zscore"] = (df["spread"] - df["spread"].rolling(window).mean()) / df["spread"].rolling(window).std()
df["corr"] = df["EURUSD"].rolling(window).corr(df["GBPUSD"])

# --- Parameters ---
SL = 20      # stoploss in pips
TP = 40      # takeprofit in pips
COST = 0.6   # broker cost

trades = []
position = None

for t, row in df.iterrows():
    z, corr = row["zscore"], row["corr"]
    eur_price = row["EURUSD"]

    if position is None:
        if corr > 0.8:
            if z > 2:
                position = {"side":"short","entry_price":eur_price,"entry_time":t}
            elif z < -2:
                position = {"side":"long","entry_price":eur_price,"entry_time":t}
    else:
        # Calculate movement in pips
        move = (eur_price - position["entry_price"]) / 0.0001 if position["side"]=="long" else (position["entry_price"] - eur_price) / 0.0001
        
        if move >= TP:   # TP hit
            pnl = move - COST
            trades.append({"entry_time":position["entry_time"],"exit_time":t,"side":position["side"],"pnl":pnl,"result":"TP"})
            position = None
        elif move <= -SL: # SL hit
            pnl = move - COST
            trades.append({"entry_time":position["entry_time"],"exit_time":t,"side":position["side"],"pnl":pnl,"result":"SL"})
            position = None

# --- Results ---
results = pd.DataFrame(trades)
results["equity"] = results["pnl"].cumsum()

print("Total trades:", len(results))
print("Win rate:", (results["pnl"]>0).mean())
print("Avg PnL (pips):", results["pnl"].mean())
print("Max DD (pips):", (results["equity"].cummax()-results["equity"]).max())
print("Expectancy (pips):", results["pnl"].mean())

# --- Plot ---
plt.figure(figsize=(12,6))
plt.plot(results["exit_time"], results["equity"])
plt.title("Equity Curve (Single-side EURUSD, SL=20, TP=40, Corr>0.8, Z>2)")
plt.xlabel("Date")
plt.ylabel("Cumulative PnL (pips)")
plt.grid(True)
plt.show()
