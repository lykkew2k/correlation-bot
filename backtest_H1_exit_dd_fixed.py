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

# === Generic backtest ===
def backtest(z_threshold=2.0, corr_threshold=0.8, mode="z0", TP=20, SL=30):
    pnl, equity_curve = 0, []
    in_trade, entry_z, entry_spread, entry_time = False, 0, 0, None
    trade_log = []

    for t, row in df.iterrows():
        z, corr, spread = row["zscore"], row["corr"], row["spread"]

        # === Entry ===
        if not in_trade:
            if abs(z) > z_threshold and corr > corr_threshold:
                in_trade, entry_z, entry_spread, entry_time = True, z, spread, t
        else:
            # === Unrealized PnL ===
            move = (spread - entry_spread) * 10000 if entry_z > 0 else (entry_spread - spread) * 10000
            unrealized = move - COST
            equity_curve.append(pnl + unrealized)

            # === Exit logic ===
            exit_trade, profit = False, 0
            if mode == "z0" and abs(z) < 0.1:
                exit_trade, profit = True, unrealized
            elif mode == "partial":
                # 50% ที่ Z=1, อีก 50% ที่ Z=0
                if abs(z) <= 1.0:
                    profit = (abs(entry_z - z) * 10)/2 - COST/2
                    pnl += profit
                if abs(z) < 0.1:
                    exit_trade, profit = True, (abs(entry_z - z) * 10)/2 - COST/2
            elif mode == "tpsl":
                if move >= TP or move <= -SL:
                    exit_trade, profit = True, unrealized

            # === Exit ===
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

    # === Stats from trade log ===
    trades = pd.DataFrame(trade_log)
    if trades.empty:
        stats = {"Trades":0,"Total PnL":0,"Win rate":0,"Avg PnL":0,"Median PnL":0,"Best":0,"Worst":0,
                 "Max DD":0,"Avg Hold":0,"Median Hold":0,"Min Hold":0,"Max Hold":0}
    else:
        winrate = (trades["PnL"] > 0).mean()
        dd = (equity_curve.cummax() - equity_curve).max()
        stats = {
            "Trades": len(trades),
            "Total PnL": trades["PnL"].sum(),
            "Win rate": winrate,
            "Avg PnL": trades["PnL"].mean(),
            "Median PnL": trades["PnL"].median(),
            "Best": trades["PnL"].max(),
            "Worst": trades["PnL"].min(),
            "Max DD": dd,
            "Avg Hold": trades["holding_h"].mean(),
            "Median Hold": trades["holding_h"].median(),
            "Min Hold": trades["holding_h"].min(),
            "Max Hold": trades["holding_h"].max()
        }
    return equity_curve, stats, trades

# === Run 3 exit strategies ===
cases = {
    "Exit Z=0": ("z0", {}),
    "Exit Partial": ("partial", {}),
    "Exit TP/SL": ("tpsl", {"TP":20, "SL":30})
}

plt.figure(figsize=(12,6))
for label, (mode, kwargs) in cases.items():
    eq, stats, trades = backtest(z_threshold=2.0, corr_threshold=0.8, mode=mode, **kwargs)
    plt.plot(eq, label=f"{label} (PnL={stats['Total PnL']:.0f}, DD={stats['Max DD']:.0f})", drawstyle="steps-post")
    print(f"\n=== {label} ===")
    for k,v in stats.items():
        print(f"{k:12}: {v}")

plt.title("Equity Curve Comparison (With DD, COST=1.2 pips)")
plt.ylabel("Cumulative PnL (pips)")
plt.legend(); plt.grid(True)
plt.show()
