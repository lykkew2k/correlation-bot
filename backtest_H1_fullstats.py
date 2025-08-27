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

# Indicators
window = 50
df["spread"] = df["EURUSD"] - df["GBPUSD"]
df["zscore"] = (df["spread"] - df["spread"].rolling(window).mean()) / df["spread"].rolling(window).std()
df["corr"] = df["EURUSD"].rolling(window).corr(df["GBPUSD"])
df = df.dropna()

COST = 1.2  # pip ต่อรอบ (2 legs)

def backtest(z_threshold, corr_threshold):
    pnl, equity, times = 0, [], []
    trades, wins = 0, 0
    hold_times, trade_pnls = [], []
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
            # Exit เมื่อ abs(z) < 0.1
            if abs(z) < 0.1:
                profit = abs(entry_z - z) * 10 - COST
                pnl += profit
                trade_pnls.append(profit)
                if profit > 0: wins += 1
                hold_times.append((t - entry_time).total_seconds()/3600)

                equity.append(pnl)
                times.append(t)
                in_trade = False

    equity = pd.Series(equity, index=times)
    winrate = wins / trades if trades > 0 else 0

    # สถิติ PnL
    avg_pnl = np.mean(trade_pnls) if trade_pnls else 0
    med_pnl = np.median(trade_pnls) if trade_pnls else 0
    best = np.max(trade_pnls) if trade_pnls else 0
    worst = np.min(trade_pnls) if trade_pnls else 0

    # สถิติ Holding time
    avg_hold = np.mean(hold_times) if hold_times else 0
    med_hold = np.median(hold_times) if hold_times else 0
    min_hold = np.min(hold_times) if hold_times else 0
    max_hold = np.max(hold_times) if hold_times else 0

    # Max Drawdown
    dd = (equity.cummax() - equity).max() if not equity.empty else 0

    stats = {
        "Trades": trades,
        "Total PnL": pnl,
        "Win rate": winrate,
        "Avg PnL": avg_pnl,
        "Median PnL": med_pnl,
        "Best trade": best,
        "Worst trade": worst,
        "Max DD": dd,
        "Avg Holding (h)": avg_hold,
        "Median Holding (h)": med_hold,
        "Min Holding (h)": min_hold,
        "Max Holding (h)": max_hold
    }
    return equity, stats

# === Run Example Case ===
equity, stats = backtest(2.0, 0.8)   # Z>2, Corr>0.8
print(pd.Series(stats))

# Plot Equity
plt.figure(figsize=(12,6))
plt.plot(equity, drawstyle="steps-post")
plt.title("Equity Curve (Z>2, Corr>0.8, COST=1.2 pips)")
plt.ylabel("Cumulative PnL (pips)")
plt.grid(True)
plt.show()
