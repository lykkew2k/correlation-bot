import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# === Load H1 Data ===
eur = pd.read_csv("data/EURUSD_H1_2024.csv", parse_dates=["datetime"], index_col="datetime")
gbp = pd.read_csv("data/GBPUSD_H1_2024.csv", parse_dates=["datetime"], index_col="datetime")

df = pd.DataFrame({
    "EURUSD": eur["close"],
    "GBPUSD": gbp["close"]
}).dropna()

# Calculate spread, zscore, corr
window = 50
df["spread"] = df["EURUSD"] - df["GBPUSD"]
df["zscore"] = (df["spread"] - df["spread"].rolling(window).mean()) / df["spread"].rolling(window).std()
df["corr"] = df["EURUSD"].rolling(window).corr(df["GBPUSD"])
df = df.dropna()

COST = 1.2  # pip per trade (2 legs)

def backtest(z_threshold, corr_threshold):
    equity = []
    in_trade = False
    entry_z = 0
    pnl = 0
    holding_times = []
    entry_time = None
    trades = 0
    
    for t, row in df.iterrows():
        z, corr = row["zscore"], row["corr"]

        if not in_trade:
            if abs(z) > z_threshold and corr > corr_threshold:
                in_trade = True
                entry_z = z
                entry_time = t
                trades += 1
        else:
            if (entry_z > 0 and z <= 0) or (entry_z < 0 and z >= 0):
                pnl += abs(entry_z - z) * 10 - COST
                in_trade = False
                holding_times.append((t - entry_time).total_seconds()/3600)
        equity.append(pnl)

    return np.array(equity), pnl, holding_times, trades

# Run 4 cases
cases = [
    ("Z>2, Corr>0.8", 2.0, 0.8),
    ("Z>2.5, Corr>0.8", 2.5, 0.8),
    ("Z>2, Corr>0.9", 2.0, 0.9),
    ("Z>2.5, Corr>0.9", 2.5, 0.9),
]

results = []
plt.figure(figsize=(12,6))
for label, zval, corrval in cases:
    eq, pnl, hold, trades = backtest(zval, corrval)
    plt.plot(df.index[-len(eq):], eq, label=label)
    win_rate = 1.0 if trades>0 else 0
    avg_hold = np.mean(hold) if hold else 0
    results.append([label, trades, pnl, win_rate, avg_hold])

plt.title("Equity Curve Comparison (H1 Hedge, COST=1.2 pips)")
plt.xlabel("Date"); plt.ylabel("Cumulative PnL (pips)")
plt.legend(); plt.grid()
plt.show()

# Summary
res_df = pd.DataFrame(results, columns=["Case", "Trades", "Total PnL", "Win rate", "Avg Holding (h)"])
print(res_df)
