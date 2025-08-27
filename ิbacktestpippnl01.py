import pandas as pd
import matplotlib.pyplot as plt

# --- Load data ---
eur = pd.read_csv("data/EURUSD_M15_2024.csv", parse_dates=["datetime"], index_col="datetime")
gbp = pd.read_csv("data/GBPUSD_M15_2024.csv", parse_dates=["datetime"], index_col="datetime")

df = pd.DataFrame({"EURUSD": eur["close"], "GBPUSD": gbp["close"]}).dropna()

# --- Indicators ---
window = 20
df["spread"] = df["EURUSD"] - df["GBPUSD"]
df["zscore"] = (df["spread"] - df["spread"].rolling(window).mean()) / df["spread"].rolling(window).std()
df["corr"] = df["EURUSD"].rolling(window).corr(df["GBPUSD"])

# --- Backtest loop ---
trades = []
position = None

for t, row in df.iterrows():
    z, corr = row["zscore"], row["corr"]
    eur_price, gbp_price = row["EURUSD"], row["GBPUSD"]

    if position is None:
        # Entry
        if corr > 0.8:  # correlation filter
            if z > 2:
                position = {
                    "side": "short", "entry_time": t,
                    "eur_entry": eur_price, "gbp_entry": gbp_price, "entry_z": z
                }
            elif z < -2:
                position = {
                    "side": "long", "entry_time": t,
                    "eur_entry": eur_price, "gbp_entry": gbp_price, "entry_z": z
                }
    else:
        # Exit
        if abs(z) <= 0.5 or abs(z) >= 3:
            eur_exit, gbp_exit = eur_price, gbp_price

            if position["side"] == "long":
                eur_pnl = (eur_exit - position["eur_entry"]) / 0.0001
                gbp_pnl = (position["gbp_entry"] - gbp_exit) / 0.0001
            else:  # short
                eur_pnl = (position["eur_entry"] - eur_exit) / 0.0001
                gbp_pnl = (gbp_exit - position["gbp_entry"]) / 0.0001

            net_pnl = eur_pnl + gbp_pnl

            trades.append({
                "entry_time": position["entry_time"],
                "exit_time": t,
                "side": position["side"],
                "entry_z": position["entry_z"],
                "exit_z": z,
                "eur_pnl": eur_pnl,
                "gbp_pnl": gbp_pnl,
                "net_pnl": net_pnl,
                "result": "TP" if abs(z) <= 0.5 else "SL"
            })

            position = None

# --- Summary ---
results = pd.DataFrame(trades)
print("Win rate:", (results["result"]=="TP").mean())
print("Average PnL (pips):", results["net_pnl"].mean())
print("Total trades:", len(results))

# --- Equity curve ---
results["equity"] = results["net_pnl"].cumsum()
plt.figure(figsize=(12,6))
plt.plot(results["exit_time"], results["equity"])
plt.title("Equity Curve (PnL in pips, 2024)")
plt.xlabel("Date")
plt.ylabel("Cumulative PnL (pips)")
plt.grid(True)
plt.show()
