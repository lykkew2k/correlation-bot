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

COST = 1.2

# === Backtest Partial Exit ===
def backtest_partial(z_threshold=2.0, corr_threshold=0.8):
    pnl, equity_curve = 0, []
    in_trade, entry_z, entry_spread, entry_time = False, 0, 0, None
    trade_log = []

    for t, row in df.iterrows():
        z, corr, spread = row["zscore"], row["corr"], row["spread"]

        if not in_trade:
            if abs(z) > z_threshold and corr > corr_threshold:
                in_trade, entry_z, entry_spread, entry_time = True, z, spread, t
        else:
            move = (spread - entry_spread) * 10000 if entry_z > 0 else (entry_spread - spread) * 10000
            unrealized = move - COST
            equity_curve.append(pnl + unrealized)

            # partial exit logic
            exit_trade, profit = False, 0
            if abs(z) <= 1.0:   # ครึ่งแรก
                pnl += (abs(entry_z - z) * 10)/2 - COST/2
            if abs(z) < 0.1:    # ครึ่งสอง
                exit_trade, profit = True, (abs(entry_z - z) * 10)/2 - COST/2

            if exit_trade:
                pnl += profit
                trade_log.append({
                    "entry": entry_time,
                    "exit": t,
                    "PnL": profit,
                    "holding_h": (t - entry_time).total_seconds()/3600
                })
                in_trade = False

    equity_curve = pd.Series(equity_curve, index=df.index[:len(equity_curve)])
    trades = pd.DataFrame(trade_log)

    dd = (equity_curve.cummax() - equity_curve).max()
    stats = {
        "Trades": len(trades),
        "Total PnL": trades["PnL"].sum(),
        "Win rate": (trades["PnL"] > 0).mean() if len(trades)>0 else 0,
        "Avg PnL": trades["PnL"].mean() if len(trades)>0 else 0,
        "Max DD": dd,
        "Avg Hold": trades["holding_h"].mean() if len(trades)>0 else 0,
    }
    return equity_curve, stats

# === Run compare Corr 0.8 vs 0.9 ===
cases = {"Corr>0.8":0.8, "Corr>0.9":0.9}

plt.figure(figsize=(12,6))
for label, corr_th in cases.items():
    eq, stats = backtest_partial(z_threshold=2.0, corr_threshold=corr_th)
    plt.plot(eq, label=f"{label} (PnL={stats['Total PnL']:.0f}, DD={stats['Max DD']:.0f})", drawstyle="steps-post")
    print(f"\n=== {label} ===")
    for k,v in stats.items():
        print(f"{k:12}: {v}")

plt.title("Partial Exit Comparison (Corr>0.8 vs Corr>0.9, COST=1.2 pips)")
plt.ylabel("Cumulative PnL (pips)")
plt.legend(); plt.grid(True)
plt.show()
