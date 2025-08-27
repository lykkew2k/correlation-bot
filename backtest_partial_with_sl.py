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

# === Partial Exit Backtest with optional SL ===
def backtest_partial(z_threshold=2.0, corr_threshold=0.8, SL=None):
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

            exit_trade, profit = False, 0
            # SL check
            if SL is not None and unrealized <= -SL:
                exit_trade, profit = True, unrealized
            else:
                # Partial exit logic
                if abs(z) <= 1.0:
                    pnl += (abs(entry_z - z) * 10)/2 - COST/2
                if abs(z) < 0.1:
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

# === Compare: No SL vs SL=30 ===
cases = {"Partial Exit (no SL)": None, "Partial Exit (SL=30)": 30}

plt.figure(figsize=(12,6))
for label, sl in cases.items():
    eq, stats = backtest_partial(z_threshold=2.0, corr_threshold=0.8, SL=sl)
    plt.plot(eq, label=f"{label} (PnL={stats['Total PnL']:.0f}, DD={stats['Max DD']:.0f}, Win={stats['Win rate']:.2f})", drawstyle="steps-post")
    print(f"\n=== {label} ===")
    for k,v in stats.items():
        print(f"{k:12}: {v}")

plt.title("Partial Exit With vs Without SL (COST=1.2 pips)")
plt.ylabel("Cumulative PnL (pips)")
plt.legend(); plt.grid(True)
plt.show()
