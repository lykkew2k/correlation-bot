import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def load_data(tf="H1"):
    if tf == "H1":
        eur = pd.read_csv("data/EURUSD_H1_2024.csv", parse_dates=["datetime"], index_col="datetime")
        gbp = pd.read_csv("data/GBPUSD_H1_2024.csv", parse_dates=["datetime"], index_col="datetime")
    elif tf == "H4":
        eur = pd.read_csv("data/EURUSD_H1_2024.csv", parse_dates=["datetime"], index_col="datetime")
        gbp = pd.read_csv("data/GBPUSD_H1_2024.csv", parse_dates=["datetime"], index_col="datetime")
        eur = eur.resample("4H").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
        gbp = gbp.resample("4H").agg({"open":"first","high":"max","low":"min","close":"last"}).dropna()
    else:
        raise ValueError("Unsupported TF")
    return eur, gbp

def backtest(eur, gbp, label=""):
    df = pd.DataFrame({"EURUSD": eur["close"], "GBPUSD": gbp["close"]}).dropna()

    # Indicators
    window = 20
    df["spread"] = df["EURUSD"] - df["GBPUSD"]
    df["zscore"] = (df["spread"] - df["spread"].rolling(window).mean()) / df["spread"].rolling(window).std()
    df["corr"] = df["EURUSD"].rolling(window).corr(df["GBPUSD"])

    # Params
    COST = 0.6
    TP1, TP2, SL = 0.5, 0.0, 3.0

    trades = []
    position, partial = None, False

    for t, row in df.iterrows():
        z, corr = row["zscore"], row["corr"]
        eur_price, gbp_price = row["EURUSD"], row["GBPUSD"]

        if position is None:
            if corr > 0.8:
                if z > 2:
                    position = {"side":"short","entry_time":t,"eur_entry":eur_price,"gbp_entry":gbp_price}
                    partial = False
                elif z < -2:
                    position = {"side":"long","entry_time":t,"eur_entry":eur_price,"gbp_entry":gbp_price}
                    partial = False
        else:
            # SL
            if abs(z) >= SL:
                pnl = (eur_price - position["eur_entry"])/0.0001 + (position["gbp_entry"]-gbp_price)/0.0001 if position["side"]=="long" else (position["eur_entry"]-eur_price)/0.0001 + (gbp_price-position["gbp_entry"])/0.0001
                pnl -= COST
                trades.append({"exit_time":t,"net_pnl":pnl,"result":"SL"})
                position=None

            # TP1
            elif not partial and abs(z)<=TP1:
                pnl = ((eur_price - position["eur_entry"])/0.0001 + (position["gbp_entry"]-gbp_price)/0.0001)/2 if position["side"]=="long" else ((position["eur_entry"]-eur_price)/0.0001 + (gbp_price-position["gbp_entry"])/0.0001)/2
                pnl -= COST/2
                trades.append({"exit_time":t,"net_pnl":pnl,"result":"TP1"})
                partial=True

            # TP2
            elif partial and abs(z)<=TP2:
                pnl = ((eur_price - position["eur_entry"])/0.0001 + (position["gbp_entry"]-gbp_price)/0.0001)/2 if position["side"]=="long" else ((position["eur_entry"]-eur_price)/0.0001 + (gbp_price-position["gbp_entry"])/0.0001)/2
                pnl -= COST/2
                trades.append({"exit_time":t,"net_pnl":pnl,"result":"TP2"})
                position=None

    results = pd.DataFrame(trades)
    if results.empty:
        print(f"{label}: No trades")
        return None

    results["equity"] = results["net_pnl"].cumsum()
    print(f"=== {label} ===")
    print("Total trades:", len(results))
    print("Win rate:", (results["net_pnl"]>0).mean())
    print("Avg PnL:", results["net_pnl"].mean())
    print("Max DD:", (results["equity"].cummax()-results["equity"]).max())

    plt.plot(results["exit_time"], results["equity"], label=label)
    return results

# --- Run both H1 & H4 ---
plt.figure(figsize=(12,6))
eur, gbp = load_data("H1"); backtest(eur, gbp, "H1")
eur, gbp = load_data("H4"); backtest(eur, gbp, "H4")
plt.legend(); plt.title("Equity Curve H1 vs H4 (Partial Exit)"); plt.grid(True)
plt.show()
