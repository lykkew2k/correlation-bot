import pandas as pd
import matplotlib.pyplot as plt

# --- Load Data (H1) ---
eur = pd.read_csv("data/EURUSD_H1_2024.csv", parse_dates=["datetime"], index_col="datetime")
gbp = pd.read_csv("data/GBPUSD_H1_2024.csv", parse_dates=["datetime"], index_col="datetime")

df = pd.DataFrame({"EURUSD": eur["close"], "GBPUSD": gbp["close"]}).dropna()

# --- Indicators ---
window = 20
df["spread"] = df["EURUSD"] - df["GBPUSD"]
df["zscore"] = (df["spread"] - df["spread"].rolling(window).mean()) / df["spread"].rolling(window).std()
df["corr"] = df["EURUSD"].rolling(window).corr(df["GBPUSD"])

# --- Parameters ---
COST = 1.2  # broker cost in pips (2 legs: EURUSD + GBPUSD)
Z_ENTRY = 2.0
Z_TP1   = 0.5
Z_TP2   = 0.0
Z_SL    = 3.0

trades = []
position = None

for t, row in df.iterrows():
    z, corr = row["zscore"], row["corr"]

    if position is None:
        if corr > 0.8:
            if z > Z_ENTRY:
                position = {"entry_time": t, "entry_z": z, "side": "short"}
            elif z < -Z_ENTRY:
                position = {"entry_time": t, "entry_z": z, "side": "long"}
    else:
        # Exit conditions
        exit_flag = None
        if position["side"] == "short":
            if z <= Z_TP1: exit_flag = "TP1"
            if z <= Z_TP2: exit_flag = "TP2"
            if z >= Z_SL:  exit_flag = "SL"
        elif position["side"] == "long":
            if z >= -Z_TP1: exit_flag = "TP1"
            if z >= -Z_TP2: exit_flag = "TP2"
            if z <= -Z_SL:  exit_flag = "SL"

        if exit_flag:
            pnl = (abs(position["entry_z"]) - abs(z)) * 10 - COST
            trades.append({
                "entry_time": position["entry_time"],
                "exit_time": t,
                "side": position["side"],
                "pnl": pnl,
                "exit_reason": exit_flag
            })
            position = None

# --- Results ---
results = pd.DataFrame(trades)
results["equity"] = results["pnl"].cumsum()

# Holding time
results["holding_time"] = results["exit_time"] - results["entry_time"]
results["holding_hours"] = results["holding_time"].dt.total_seconds() / 3600

print("Total trades:", len(results))
print("Win rate:", (results["pnl"] > 0).mean())
print("Avg PnL (pips):", results["pnl"].mean())
print("Max DD (pips):", (results["equity"].cummax() - results["equity"]).max())
print("Average holding (hours):", results["holding_hours"].mean())
print("Median holding (hours):", results["holding_hours"].median())
print("Shortest trade (hours):", results["holding_hours"].min())
print("Longest trade (hours):", results["holding_hours"].max())

# --- Plot Equity ---
plt.figure(figsize=(12,5))
plt.plot(results["exit_time"], results["equity"])
plt.title("Equity Curve (H1 Hedge, COST=1.2 pips)")
plt.xlabel("Date")
plt.ylabel("Cumulative PnL (pips)")
plt.grid(True)
plt.show()

# --- Plot Holding time distribution ---
plt.figure(figsize=(10,5))
plt.hist(results["holding_hours"], bins=30, color="skyblue", edgecolor="black")
plt.title("Distribution of Holding Time (H1 Hedge, COST=1.2 pips)")
plt.xlabel("Holding time (hours)")
plt.ylabel("Number of trades")
plt.show()
