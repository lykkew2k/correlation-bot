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
SPREAD_COST = 1.0 + 1.5   # EURUSD + GBPUSD
COMMISSION  = 0.5 * 2
COST_PER_TRADE = SPREAD_COST + COMMISSION  # ~3.5 pips

TP_LIST = [0.0, 0.5, 0.8]   # <<< ทดลองหลายค่า

# --- Function Backtest ---
def backtest(tp_target):
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
            if abs(z) <= tp_target or abs(z) >= 3:
                eur_exit, gbp_exit = eur_price, gbp_price

                if position["side"] == "long":
                    eur_pnl = (eur_exit - position["eur_entry"]) / 0.0001
                    gbp_pnl = (position["gbp_entry"] - gbp_exit) / 0.0001
                else:  # short
                    eur_pnl = (position["eur_entry"] - eur_exit) / 0.0001
                    gbp_pnl = (gbp_exit - position["gbp_entry"]) / 0.0001

                net_pnl = eur_pnl + gbp_pnl - COST_PER_TRADE

                trades.append({
                    "entry_time": position["entry_time"],
                    "exit_time": t,
                    "side": position["side"],
                    "entry_z": position["entry_z"],
                    "exit_z": z,
                    "eur_pnl": eur_pnl,
                    "gbp_pnl": gbp_pnl,
                    "net_pnl": net_pnl,
                    "result": "TP" if abs(z) <= tp_target else "SL"
                })
                position = None

    results = pd.DataFrame(trades)
    if results.empty:
        return {"TP_target": tp_target, "Total trades": 0}

    results["equity"] = results["net_pnl"].cumsum()

    total_trades = len(results)
    win_rate = (results["net_pnl"] > 0).mean()
    avg_pnl = results["net_pnl"].mean()
    max_dd = (results["equity"].cummax() - results["equity"]).max()
    sharpe = results["net_pnl"].mean() / results["net_pnl"].std() * np.sqrt(252) if results["net_pnl"].std() > 0 else 0
    expectancy = avg_pnl * win_rate - (1-win_rate)*abs(avg_pnl)

    return {
        "TP_target": tp_target,
        "Total trades": total_trades,
        "Win rate": round(win_rate*100,2),
        "Avg PnL": round(avg_pnl,2),
        "Max DD": round(max_dd,2),
        "Sharpe": round(sharpe,2),
        "Expectancy": round(expectancy,2)
    }

# --- Run all TP ---
summary = pd.DataFrame([backtest(tp) for tp in TP_LIST])
print(summary)

# --- Plot equity for compare ---
plt.figure(figsize=(12,6))
for tp in TP_LIST:
    results = backtest(tp)
    # rerun to get equity
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
            if abs(z) <= tp or abs(z) >= 3:
                eur_exit, gbp_exit = eur_price, gbp_price
                if position["side"] == "long":
                    eur_pnl = (eur_exit - position["eur_entry"]) / 0.0001
                    gbp_pnl = (position["gbp_entry"] - gbp_exit) / 0.0001
                else:
                    eur_pnl = (position["eur_entry"] - eur_exit) / 0.0001
                    gbp_pnl = (gbp_exit - position["gbp_entry"]) / 0.0001
                net_pnl = eur_pnl + gbp_pnl - COST_PER_TRADE
                trades.append({"exit_time": t, "net_pnl": net_pnl})
                position = None
    if trades:
        res = pd.DataFrame(trades)
        res["equity"] = res["net_pnl"].cumsum()
        plt.plot(res["exit_time"], res["equity"], label=f"TP={tp}")

plt.title("Equity Curve Comparison (different TP targets)")
plt.legend()
plt.grid(True)
plt.show()
