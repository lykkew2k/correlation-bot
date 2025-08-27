import pandas as pd
import matplotlib.pyplot as plt

# === Load Data (H1) ===
eur = pd.read_csv("data/EURUSD_H1_2024.csv", parse_dates=["datetime"], index_col="datetime")
gbp = pd.read_csv("data/GBPUSD_H1_2024.csv", parse_dates=["datetime"], index_col="datetime")

df = pd.DataFrame({
    "EURUSD": eur["close"],
    "GBPUSD": gbp["close"]
}).dropna()

# คำนวณ spread, zscore, correlation
window = 50
df["spread"] = df["EURUSD"] - df["GBPUSD"]
df["zscore"] = (df["spread"] - df["spread"].rolling(window).mean()) / df["spread"].rolling(window).std()
df["corr"] = df["EURUSD"].rolling(window).corr(df["GBPUSD"])
df = df.dropna()

COST = 1.2  # pip ต่อรอบ (2 ขา)

# === Backtest (exit-only version) ===
def backtest(z_threshold, corr_threshold):
    pnl = 0
    equity, times = [], []
    trades, wins = 0, 0
    hold_times = []
    in_trade, entry_z, entry_time = False, 0, None

    for t, row in df.iterrows():
        z, corr = row["zscore"], row["corr"]

        # Entry
        if not in_trade:
            if abs(z) > z_threshold and corr > corr_threshold:
                in_trade = True
                entry_z = z
                entry_time = t
                trades += 1
        else:
            # Exit เมื่อ zscore กลับศูนย์
            if (entry_z > 0 and z <= 0) or (entry_z < 0 and z >= 0):
                profit = abs(entry_z - z) * 10 - COST
                pnl += profit
                if profit > 0: wins += 1
                hold_times.append((t - entry_time).total_seconds()/3600)

                equity.append(pnl)
                times.append(t)
                in_trade = False

    equity = pd.Series(equity, index=times)
    winrate = wins / trades if trades > 0 else 0
    avg_hold = sum(hold_times)/len(hold_times) if hold_times else 0
    return equity, trades, pnl, winrate, avg_hold

# === Run 4 Cases ===
cases = [
    ("Z>2, Corr>0.8", 2.0, 0.8),
    ("Z>2.5, Corr>0.8", 2.5, 0.8),
    ("Z>2, Corr>0.9", 2.0, 0.9),
    ("Z>2.5, Corr>0.9", 2.5, 0.9),
]

results = []
plt.figure(figsize=(12,6))
for label, zval, corrval in cases:
    equity, trades, pnl, winrate, avg_hold = backtest(zval, corrval)
    plt.plot(equity, label=label, drawstyle="steps-post")
    results.append([label, trades, pnl, winrate, avg_hold])

plt.title("Equity Curve Comparison (H1 Hedge, COST=1.2 pips)")
plt.xlabel("Date"); plt.ylabel("Cumulative PnL (pips)")
plt.legend(); plt.grid(True)
plt.show()

# === Show Summary ===
res_df = pd.DataFrame(results, columns=["Case", "Trades", "Total PnL", "Win rate", "Avg Holding (h)"])
print(res_df)
