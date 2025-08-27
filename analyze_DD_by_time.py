import pandas as pd
import matplotlib.pyplot as plt

# โหลด trade log (ต้องมีคอลัมน์ entry, exit, tradeDD)
trades = pd.read_csv("trade_log_partial_noSL.csv", parse_dates=["entry","exit"])

# แปลงเวลา UTC -> Asia/Bangkok
trades["entry_thai"] = trades["entry"].dt.tz_localize("UTC").dt.tz_convert("Asia/Bangkok")
trades["exit_thai"]  = trades["exit"].dt.tz_localize("UTC").dt.tz_convert("Asia/Bangkok")

# เพิ่มคอลัมน์วัน/ชั่วโมงไทย
trades["hour_thai"] = trades["entry_thai"].dt.hour
trades["day_thai"]  = trades["entry_thai"].dt.day_name()

# === วิเคราะห์ DD ===
dd_by_hour = trades.groupby("hour_thai")["tradeDD"].agg(["mean","min","max","count"])
dd_by_day  = trades.groupby("day_thai")["tradeDD"].agg(["mean","min","max","count"])

# === Export CSV ===
dd_by_hour.to_csv("dd_by_hour.csv")
dd_by_day.to_csv("dd_by_day.csv")

print("✅ บันทึก dd_by_hour.csv และ dd_by_day.csv แล้ว")

# === Plot ===
plt.figure(figsize=(12,4))
plt.bar(dd_by_hour.index, dd_by_hour["mean"], color="red", alpha=0.7)
plt.title("Average In-trade DD by Hour (Thai Time)")
plt.xlabel("Hour of Day (Thai Time)")
plt.ylabel("Average DD (pips)")
plt.grid(True, alpha=0.3)
plt.show()

plt.figure(figsize=(8,4))
dd_by_day.loc[["Monday","Tuesday","Wednesday","Thursday","Friday"]]["mean"].plot(kind="bar", color="blue", alpha=0.7)
plt.title("Average In-trade DD by Day (Thai Time)")
plt.ylabel("Average DD (pips)")
plt.grid(True, alpha=0.3)
plt.show()
