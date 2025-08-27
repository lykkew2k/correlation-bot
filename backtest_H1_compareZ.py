import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# === โหลดไฟล์ H1 ===
eur = pd.read_csv("data/EURUSD_H1_2024.csv", parse_dates=["datetime"], index_col="datetime")
gbp = pd.read_csv("data/GBPUSD_H1_2024.csv", parse_dates=["datetime"], index_col="datetime")

df = pd.DataFrame({
    "EURUSD": eur["close"],
    "GBPUSD": gbp["close"]
}).dropna()

# คำนวณ spread และ zscore
window = 50
df["spread"] = df["EURUSD"] - df["GBPUSD"]
df["zscore"] = (df["spread"] - df["spread"].rolling(window).mean()) / df["spread"].rolling(window).std()
df = df.dropna()

COST = 1.2  # pip ต่อ 1 รอบ (2 ขา)

def backtest(z_threshold):
    equity = []
    in_trade = False
    entry_z = 0
    pnl = 0
    holding_times = []
    entry_time = None
    
    for t, row in df.iterrows():
        z = row["zscore"]

        if not in_trade:
            if abs(z) > z_threshold:
                in_trade = True
                entry_z = z
                entry_time = t
        else:
            if (entry_z > 0 and z <= 0) or (entry_z < 0 and z >= 0):
                pnl += abs(entry_z - z) * 10 - COST
                in_trade = False
                holding_times.append((t - entry_time).total_seconds()/3600)
        equity.append(pnl)

    return np.array(equity), pnl, holding_times

# Run 2 case
eq2, pnl2, hold2 = backtest(2.0)
eq25, pnl25, hold25 = backtest(2.5)

# Plot
plt.figure(figsize=(12,6))
plt.plot(df.index[-len(eq2):], eq2, label="Z>2")
plt.plot(df.index[-len(eq25):], eq25, label="Z>2.5")
plt.title("Equity Curve Comparison (H1 Hedge, COST=1.2 pips)")
plt.xlabel("Date"); plt.ylabel("Cumulative PnL (pips)")
plt.legend(); plt.grid()
plt.show()

# Summary
def summary(name, equity, pnl, hold):
    trades = len(hold)
    win_rate = np.mean([h>0 for h in hold]) if trades>0 else 0
    avg_hold = np.mean(hold) if trades>0 else 0
    return {
        "Case": name,
        "Trades": trades,
        "Total PnL": pnl,
        "Win rate": round(win_rate,2),
        "Avg Holding (h)": round(avg_hold,1)
    }

results = [
    summary("Z>2", eq2, pnl2, hold2),
    summary("Z>2.5", eq25, pnl25, hold25)
]

print(pd.DataFrame(results))
