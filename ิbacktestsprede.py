import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- Load data ---
eur = pd.read_csv("data/EURUSD_M15_2024.csv", parse_dates=["datetime"], index_col="datetime")
gbp = pd.read_csv("data/GBPUSD_M15_2024.csv", parse_dates=["datetime"], index_col="datetime")

df = pd.DataFrame({"EURUSD": eur["close"], "GBPUSD": gbp["close"]}).dropna()

# --- Indicators ---
window = 20
df["spread"] = df["EURUSD"] - df["GBPUSD"]
df["zscore"] = (df["spread"] - df["spread"].rolling(window).mean()) / df["spread"].rolling(window).std()
df["corr"] = df["EURUSD"].rolling(window).corr(df["GBPUSD"])

# --- Parameters ---
SPREAD_COST = 1.0 + 1.5   # EURUSD 1 pip + GBPUSD 1.5 pips
COMMISSION  = 0.5 * 2     # 0.5 pip per pair
COST_PER_TRADE = SPREAD_COST + COMMISSION  # ~3.5 pips

# --- Backtest loop ---
trades = []
position = None

for t, row in df.iterrows():
    z, corr = row["zscore"], row["corr"]
    eur_price, gbp_price = row["EURUSD"], row["GBPUSD"]

    if position is None:
        if corr > 0.8:
            if z > 2:
                position = {"side": "short", "entry_time": t,
                            "eur_entry": eur_price, "gbp_entry": gbp_price, "entry_z": z}
            elif z < -2:
                position = {"side": "long", "entry_time": t,
                            "eur_entry": eur_price, "gbp_entry": gbp_price, "entry_z": z}
    else:
        if abs(z) <= 0.5 or abs(z) >= 3:
            eur_exit, gbp_exit = eur_price, gbp_price

            if position["side"] == "long":
                eur_pnl = (eur_exit - position["eur_entry"]) / 0.0001
                gbp_pnl = (position["gbp_entry"] - gbp_exit) / 0.0001
            else:  # short
                eur_pnl = (position["eur_entry"] - eur_exit) / 0.0001
                gbp_pnl = (gbp_exit - position["gbp_entry"]) / 0.0001

            net_pnl = eur_pnl + gbp_pnl - COST_PER_TRADE  # หักค่าใช้จ่าย

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

# --- Results ---
results = pd.DataFrame(trades)
results["equity"] = results["net_pnl"].cumsum()

# Metrics
total_trades = len(results)
win_rate = (results["net_pnl"] > 0).mean()
avg_pnl = results["net_pnl"].mean()
max_dd = (results["equity"].cummax() - results["equity"]).max()
sharpe = results["net_pnl"].mean() / results["net_pnl"].std() * np.sqrt(252)  # daily approx
expectancy = avg_pnl * win_rate - (1-win_rate)*abs(avg_pnl)

# Print summary
print(f"Total trades: {total_trades}")
print(f"Win rate: {win_rate:.2%}")
print(f"Average PnL (pips): {avg_pnl:.2f}")
print(f"Max Drawdown (pips): {max_dd:.2f}")
print(f"Sharpe Ratio: {sharpe:.2f}")
print(f"Expectancy (pips per trade): {expectancy:.2f}")

# --- Equity curve ---
plt.figure(figsize=(12,6))
plt.plot(results["exit_time"], results["equity"])
plt.title("Equity Curve after Costs (PnL in pips, 2024)")
plt.xlabel("Date")
plt.ylabel("Cumulative PnL (pips)")
plt.grid(True)
plt.show()
