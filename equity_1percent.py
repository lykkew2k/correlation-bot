import pandas as pd
import matplotlib.pyplot as plt

# โหลด trade log ที่มี PnL (pips) และ in-trade DD (pips)
trades = pd.read_csv("trade_log_partial_noSL.csv")

# พารามิเตอร์
initial_equity = 1000
risk_percent = 0.01
SL = 30  # สมมติ normalize SL=30 pips

# ตัวแปรเก็บค่า
equity = [initial_equity]
dd_equity = [initial_equity]  # equity ที่ถูกลาก
current_equity = initial_equity

for pnl_pips, dd_pips in zip(trades["PnL"], trades["tradeDD"]):
    # ขนาด lot ตาม risk
    risk_usd = current_equity * risk_percent
    lot_size = risk_usd / (SL * 10)   # 1 lot = $10/pip
    
    # PnL จริง (USD)
    pnl_usd = pnl_pips * 10 * lot_size
    current_equity += pnl_usd
    equity.append(current_equity)

    # equity ที่ถูกลาก (USD)
    dd_usd = dd_pips * 10 * lot_size
    dd_equity.append(current_equity + dd_usd)

# DataFrame
result = pd.DataFrame({
    "equity": equity,
    "dd_equity": dd_equity
})

result.to_csv("equity_curve_with_floatingDD_overlay.csv", index=False)
print("✅ บันทึกไฟล์ equity_curve_with_floatingDD_overlay.csv แล้ว")
print("Final equity:", result['equity'].iloc[-1])
print("Max floating drawdown (USD):", (result["dd_equity"] - result["equity"]).min())

# Plot
plt.figure(figsize=(10,6))
plt.plot(result["equity"], label="Equity (USD)", color="blue")
plt.plot(result["dd_equity"], label="Equity incl. Floating DD (USD)", color="red", linestyle="--")

plt.title("Equity Curve with Floating DD (Overlay, 1% Risk per Trade)")
plt.ylabel("USD")
plt.xlabel("Trades")
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
