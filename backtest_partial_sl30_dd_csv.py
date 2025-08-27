import pandas as pd

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

COST = 1.2

def backtest_partial_sl30(z_threshold=2.0, corr_threshold=0.8, SL=30, filename="trade_log_SL30_DD.csv"):
    equity = 0
    in_trade, entry_z, entry_spread, entry_time = False, 0, 0, None
    trade_log = []

    for t, row in df.iterrows():
        z, corr, spread = row["zscore"], row["corr"], row["spread"]

        if not in_trade:
            # Entry
            if abs(z) > z_threshold and corr > corr_threshold:
                in_trade, entry_z, entry_spread, entry_time = True, z, spread, t
                partial_pnl = 0  # reset partial result for this trade
        else:
            # Unrealized PnL (pips)
            move = (spread - entry_spread) * 10000 if entry_z > 0 else (entry_spread - spread) * 10000
            unrealized = move - COST

            exit_trade, trade_pnl = False, 0
            if unrealized <= -SL:   # Stop Loss
                exit_trade, trade_pnl = True, unrealized + partial_pnl
            else:
                if abs(z) <= 1.0 and partial_pnl == 0:  # ทำ partial ครั้งเดียว
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
                    "equity": equity
                })
                in_trade = False

    trades = pd.DataFrame(trade_log)
    trades["cummax"] = trades["equity"].cummax()
    trades["drawdown"] = trades["equity"] - trades["cummax"]

    trades.to_csv(filename, index=False)
    print(f"✅ บันทึกไฟล์เรียบร้อย: {filename}")
    print(f"Total trades: {len(trades)}, Total PnL: {trades['PnL'].sum():.2f}, Max DD: {trades['drawdown'].min():.2f}")

    return trades

# Run
trades = backtest_partial_sl30()
print(trades.head(15))
