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

# === Exit strategy A: ออกเมื่อ Z กลับเข้าใกล้ศูนย์ ===
def backtest_exit_z0(z_threshold=2.0, corr_threshold=0.8):
    pnl, equity, times = 0, [], []
    trades, wins = 0, 0
    in_trade, entry_z = False, 0

    for t, row in df.iterrows():
        z, corr = row["zscore"], row["corr"]

        if not in_trade:
            if abs(z) > z_threshold and corr > corr_threshold:
                in_trade, entry_z = True, z
                trades += 1
        else:
            if abs(z) < 0.1:  # exit
                profit = abs(entry_z - z) * 10 - COST
                pnl += profit
                if profit > 0: wins += 1
                equity.append(pnl); times.append(t)
                in_trade = False

    return pd.Series(equity, index=times), pnl, trades, wins

# === Exit strategy B: Partial exit (ครึ่งหนึ่งที่ Z=1, อีกครึ่งเมื่อ Z=0) ===
def backtest_exit_partial(z_threshold=2.0, corr_threshold=0.8):
    pnl, equity, times = 0, [], []
    trades, wins = 0, 0
    in_trade, entry_z, half_closed = False, 0, False

    for t, row in df.iterrows():
        z, corr = row["zscore"], row["corr"]

        if not in_trade:
            if abs(z) > z_threshold and corr > corr_threshold:
                in_trade, entry_z, half_closed = True, z, False
                trades += 1
        else:
            if not half_closed and abs(z) <= 1.0:
                profit = abs(entry_z - z) * 10/2 - COST/2
                pnl += profit
                half_closed = True
            elif abs(z) < 0.1:
                profit = abs(entry_z - z) * 10/2 - COST/2
                pnl += profit
                if profit > 0: wins += 1
                equity.append(pnl); times.append(t)
                in_trade = False

    return pd.Series(equity, index=times), pnl, trades, wins

# === Exit strategy C: Fixed TP/SL (TP=20, SL=30 pip) ===
def backtest_exit_fixed(z_threshold=2.0, corr_threshold=0.8, TP=20, SL=30):
    pnl, equity, times = 0, [], []
    trades, wins = 0, 0
    in_trade, entry_spread, entry_z = False, 0, 0

    for t, row in df.iterrows():
        z, corr, spread = row["zscore"], row["corr"], row["spread"]

        if not in_trade:
            if abs(z) > z_threshold and corr > corr_threshold:
                in_trade, entry_spread, entry_z = True, spread, z
                trades += 1
        else:
            move = (spread - entry_spread) * 10000 if entry_z > 0 else (entry_spread - spread) * 10000
            if move >= TP or move <= -SL:
                profit = move - COST
                pnl += profit
                if profit > 0: wins += 1
                equity.append(pnl); times.append(t)
                in_trade = False

    return pd.Series(equity, index=times), pnl, trades, wins

# === Run and Compare ===
cases = {
    "Exit Z=0": backtest_exit_z0,
    "Exit Partial": backtest_exit_partial,
    "Exit TP/SL": backtest_exit_fixed
}

plt.figure(figsize=(12,6))
for label, func in cases.items():
    equity, pnl, trades, wins = func()
    plt.plot(equity, label=f"{label} (PnL={pnl:.0f}, Trades={trades}, Win={wins/trades:.1%})", drawstyle="steps-post")

plt.title("Equity Curve Comparison (Different Exit Strategies, COST=1.2 pips)")
plt.xlabel("Date"); plt.ylabel("Cumulative PnL (pips)")
plt.legend(); plt.grid(True)
plt.show()
