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

COST = 1.2   # pip ต่อรอบ (2 legs)

# === Backtest generic ===
def backtest(z_threshold=2.0, corr_threshold=0.8, mode="z0", TP=20, SL=30):
    pnl, equity_curve = 0, []
    trades, wins = 0, 0
    in_trade, entry_z, entry_spread, entry_time = False, 0, 0, None
    hold_times, trade_pnls = [], []

    for t, row in df.iterrows():
        z, corr, spread = row["zscore"], row["corr"], row["spread"]

        if not in_trade:
            if abs(z) > z_threshold and corr > corr_threshold:
                in_trade, entry_z, entry_spread, entry_time = True, z, spread, t
                trades += 1
        else:
            move = (spread - entry_spread) * 10000 if entry_z > 0 else (entry_spread - spread) * 10000
            unrealized = move - COST
            equity_curve.append(pnl + unrealized)

            exit_trade = False
            if mode == "z0" and abs(z) < 0.1:
                exit_trade = True
            elif mode == "partial":
                # simple partial: half at Z=1, rest at Z=0
                if abs(z) <= 1.0:
                    profit = (abs(entry_z - z) * 10)/2 - COST/2
                    pnl += profit
                if abs(z) < 0.1:
                    exit_trade = True
            elif mode == "tpsl":
                if move >= TP or move <= -SL:
                    exit_trade = True

            if exit_trade:
                profit = unrealized
                pnl += profit
                trade_pnls.append(profit)
                if profit > 0: wins += 1
                hold_times.append((t - entry_time).total_seconds()/3600)
                in_trade = False

    equity_curve = pd.Series(equity_curve, index=df.index[:len(equity_curve)])

    # Stats
    dd = (equity_curve.cummax() - equity_curve).max()
    avg_pnl = np.mean(trade_pnls) if trade_pnls else 0
    med_pnl = np.median(trade_pnls) if trade_pnls else 0
    best = np.max(trade_pnls) if trade_pnls else 0
    worst = np.min(trade_pnls) if trade_pnls else 0
    avg_hold = np.mean(hold_times) if hold_times else 0
    med_hold = np.median(hold_times) if hold_times else 0
    min_hold = np.min(hold_times) if hold_times else 0
    max_hold = np.max(hold_times) if hold_times else 0

    stats = {
        "Trades": trades,
        "Total PnL": pnl,
        "Win rate": wins/trades if trades>0 else 0,
        "Avg PnL": avg_pnl,
        "Median PnL": med_pnl,
        "Best trade": best,
        "Worst trade": worst,
        "Max DD": dd,
        "Avg Hold (h)": avg_hold,
        "Median Hold (h)": med_hold,
        "Min Hold (h)": min_hold,
        "Max Hold (h)": max_hold
    }
    return equity_curve, stats

# === Run 3 exit strategies ===
cases = {
    "Exit Z=0": ("z0", {}),
    "Exit Partial": ("partial", {}),
    "Exit TP/SL": ("tpsl", {"TP":20, "SL":30})
}

plt.figure(figsize=(12,6))
for label, (mode, kwargs) in cases.items():
    eq, stats = backtest(z_threshold=2.0, corr_threshold=0.8, mode=mode, **kwargs)
    plt.plot(eq, label=f"{label} (PnL={stats['Total PnL']:.0f}, DD={stats['Max DD']:.0f})", drawstyle="steps-post")
    print(f"\n=== {label} ===")
    for k,v in stats.items():
        print(f"{k:15}: {v}")

plt.title("Equity Curve Comparison (With Max DD, COST=1.2 pips)")
plt.ylabel("Cumulative PnL (pips)")
plt.legend(); plt.grid(True)
plt.show()
