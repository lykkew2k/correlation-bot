import pandas as pd
import matplotlib.pyplot as plt

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

COST = 1.2   # cost ต่อรอบ (2 legs)

def backtest_partial_noSL(z_threshold=2.0, corr_threshold=0.8, filename="trade_log_partial_noSL.csv"):
    equity = 0
    in_trade, entry_z, entry_spread, entry_time = False, 0, 0, None
    trade_log = []

    for t, row in df.iterrows():
        z, corr, spread = row["zscore"], row["corr"], row["spread"]

        if not in_trade:
            # Entry
            if abs(z) > z_threshold and corr > corr_threshold:
                in_trade, entry_z, entry_spread, entry_time = True, z, spread, t
                partial_pnl = 0
                worst_unreal = 0
        else:
            # Unrealized
            move = (spread - entry_spread) * 10000 if entry_z > 0 else (entry_spread - spread) * 10000
            unrealized = move - COST
            worst_unreal = min(worst_unreal, unrealized)

            exit_trade, trade_pnl = False, 0
            if abs(z) <= 1.0 and partial_pnl == 0:
                partial_pnl = (abs(entry_z - z) * 10)/2 - COST/2
            if abs(z) < 0.1:
                exit_trade, trade_pnl = True, partial_pnl + ((abs(entry_z - z) * 10)/2 - COST/2)

            if exit_trade:
                equity += trade_pnl
                trade_log.append({
                    "entry": entry_time,
                    "exit": t,
                    "PnL": trade_pnl,
                    "holding_h": (t - entry_time).total_seconds()/3600,
                    "equity": equity,
                    "tradeDD": worst_unreal
                })
                in_trade = False

    trades = pd.DataFrame(trade_log)

    # Save CSV
    trades.to_csv(filename, index=False)
    print(f"✅ บันทึกไฟล์: {filename}")

    # Summary
    print(f"Total trades : {len(trades)}")
    print(f"Total PnL    : {trades['PnL'].sum():.2f} pips")
    print(f"Win rate     : {(trades['PnL']>0).mean()*100:.2f}%")
    print(f"Avg PnL/trade: {trades['PnL'].mean():.2f} pips")
    print(f"Best trade   : {trades['PnL'].max():.2f} pips")
    print(f"Worst trade  : {trades['PnL'].min():.2f} pips")
    print(f"Max In-trade DD: {trades['tradeDD'].min():.2f} pips")
    print(f"Avg Hold     : {trades['holding_h'].mean():.1f} h")
    print(f"Max Hold     : {trades['holding_h'].max():.1f} h")

    # === Plot ===
    fig, ax = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    # Equity curve
    ax[0].plot(trades["exit"], trades["equity"], label="Equity")
    ax[0].set_title("Equity Curve (Partial Exit, No SL)")
    ax[0].legend()
    # In-trade DD
    ax[1].bar(trades["exit"], trades["tradeDD"], color="red", alpha=0.6, label="Trade DD")
    ax[1].set_title("In-trade Drawdown per Trade")
    ax[1].legend()

    plt.tight_layout()
    plt.show()

    return trades

# Run
trades = backtest_partial_noSL()
