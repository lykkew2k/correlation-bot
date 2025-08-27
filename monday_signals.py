import pandas as pd
import matplotlib.pyplot as plt

# --- โหลดไฟล์ H1 & M15 ---
eur_h1 = pd.read_csv("data/EURUSD_H1_2024.csv", parse_dates=["datetime"], index_col="datetime")
gbp_h1 = pd.read_csv("data/GBPUSD_H1_2024.csv", parse_dates=["datetime"], index_col="datetime")
eur_m15 = pd.read_csv("data/EURUSD_M15_2024.csv", parse_dates=["datetime"], index_col="datetime")
gbp_m15 = pd.read_csv("data/GBPUSD_M15_2024.csv", parse_dates=["datetime"], index_col="datetime")

# --- ตั้งค่าช่วง warm-up (1 อาทิตย์ก่อนหน้า) ---
warmup_start, target_day = "2024-01-29", "2024-02-05"
eur_h1, gbp_h1 = eur_h1.loc[warmup_start:target_day], gbp_h1.loc[warmup_start:target_day]
eur_m15, gbp_m15 = eur_m15.loc[warmup_start:target_day], gbp_m15.loc[warmup_start:target_day]

# --- รวมข้อมูล ---
df_h1  = pd.DataFrame({"EURUSD": eur_h1["close"], "GBPUSD": gbp_h1["close"]}).dropna()
df_m15 = pd.DataFrame({"EURUSD": eur_m15["close"], "GBPUSD": gbp_m15["close"]}).dropna()

# --- สร้าง indicator ---
def make_indicators(df, window):
    df["corr"] = df["EURUSD"].rolling(window).corr(df["GBPUSD"])
    df["spread"] = df["EURUSD"] - df["GBPUSD"]
    df["zscore"] = (df["spread"] - df["spread"].rolling(window).mean()) / df["spread"].rolling(window).std()
    return df

df_h1  = make_indicators(df_h1,  window=50)
df_m15 = make_indicators(df_m15, window=20)

# --- ตัดมาเฉพาะวันจันทร์ ---
df_h1_day  = df_h1.loc["2024-02-05"]
df_m15_day = df_m15.loc["2024-02-05"]

# --- ฟังก์ชัน plot signals ---
def plot_with_signals(ax, df, title):
    ax.plot(df.index, df["zscore"], color="red", label="Z-score")
    ax.axhline(2, color="gray", linestyle="--")
    ax.axhline(-2, color="gray", linestyle="--")
    ax.axhline(0, color="black", linestyle=":")
    
    entry_long  = df[df["zscore"] < -2]    # ซื้อ EURUSD / ขาย GBPUSD
    entry_short = df[df["zscore"] > 2]     # ขาย EURUSD / ซื้อ GBPUSD
    exit_signal = df[(df["zscore"].abs() < 0.5)]  # ปิดโพสิชัน
    
    for t in entry_long.index:
        ax.axvline(t, color="blue", linestyle=":", alpha=0.6)
    for t in entry_short.index:
        ax.axvline(t, color="orange", linestyle=":", alpha=0.6)
    for t in exit_signal.index:
        ax.axvline(t, color="green", linestyle=":", alpha=0.3)
    
    ax.set_title(title)
    ax.legend()

# --- Plot ---
fig, axes = plt.subplots(2, 2, figsize=(14, 8))

# H1
axes[0,0].plot(df_h1_day.index, df_h1_day["EURUSD"], label="EURUSD")
axes[0,0].plot(df_h1_day.index, df_h1_day["GBPUSD"], label="GBPUSD")
axes[0,0].legend(); axes[0,0].set_title("H1 Prices (Feb 5)")

plot_with_signals(axes[0,1], df_h1_day, "H1 Z-score with Signals (Feb 5)")

# M15
axes[1,0].plot(df_m15_day.index, df_m15_day["EURUSD"], label="EURUSD")
axes[1,0].plot(df_m15_day.index, df_m15_day["GBPUSD"], label="GBPUSD")
axes[1,0].legend(); axes[1,0].set_title("M15 Prices (Feb 5)")

plot_with_signals(axes[1,1], df_m15_day, "M15 Z-score with Signals (Feb 5)")

plt.tight_layout()
plt.show()
