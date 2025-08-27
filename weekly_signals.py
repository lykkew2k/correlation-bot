import pandas as pd
import matplotlib.pyplot as plt

# === โหลดไฟล์ H1 และ M15 ===
eur_h1 = pd.read_csv("data/EURUSD_H1_2024.csv", parse_dates=["datetime"], index_col="datetime")
gbp_h1 = pd.read_csv("data/GBPUSD_H1_2024.csv", parse_dates=["datetime"], index_col="datetime")

eur_m15 = pd.read_csv("data/EURUSD_M15_2024.csv", parse_dates=["datetime"], index_col="datetime")
gbp_m15 = pd.read_csv("data/GBPUSD_M15_2024.csv", parse_dates=["datetime"], index_col="datetime")

# === เลือกช่วงเวลาที่ต้องการ (1 ก.พ. ถึง 7 ก.พ. 2024) ===
start, end = "2024-02-01", "2024-02-07"
eur_h1, gbp_h1 = eur_h1.loc[start:end], gbp_h1.loc[start:end]
eur_m15, gbp_m15 = eur_m15.loc[start:end], gbp_m15.loc[start:end]

# === รวมข้อมูล ===
df_h1 = pd.DataFrame({"EURUSD": eur_h1["close"], "GBPUSD": gbp_h1["close"]}).dropna()
df_m15 = pd.DataFrame({"EURUSD": eur_m15["close"], "GBPUSD": gbp_m15["close"]}).dropna()

# === ฟังก์ชันสร้าง indicator ===
def make_indicators(df, window):
    df["corr"] = df["EURUSD"].rolling(window).corr(df["GBPUSD"])
    df["spread"] = df["EURUSD"] - df["GBPUSD"]
    df["zscore"] = (df["spread"] - df["spread"].rolling(window).mean()) / df["spread"].rolling(window).std()
    return df

df_h1 = make_indicators(df_h1, window=50)
df_m15 = make_indicators(df_m15, window=20)

# === ฟังก์ชัน plot signals ===
def plot_with_signals(ax, df, title):
    ax.plot(df.index, df["zscore"], color="red", label="Z-score")
    ax.axhline(2, color="gray", linestyle="--")
    ax.axhline(-2, color="gray", linestyle="--")
    ax.axhline(0, color="black", linestyle=":")
    
    # Entry signals
    entry_long = df[df["zscore"] < -2]   # ซื้อ EURUSD / ขาย GBPUSD
    entry_short = df[df["zscore"] > 2]   # ขาย EURUSD / ซื้อ GBPUSD
    exit_signal = df[(df["zscore"].abs() < 0.5)]  # ปิดโพสิชัน
    
    for t in entry_long.index:
        ax.axvline(t, color="blue", linestyle=":", alpha=0.5)
    for t in entry_short.index:
        ax.axvline(t, color="orange", linestyle=":", alpha=0.5)
    for t in exit_signal.index:
        ax.axvline(t, color="green", linestyle=":", alpha=0.3)
    
    ax.set_title(title)
    ax.legend()

# === Plot ===
fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex=False)

# --- H1 ---
axes[0,0].plot(df_h1.index, df_h1["EURUSD"], label="EURUSD")
axes[0,0].plot(df_h1.index, df_h1["GBPUSD"], label="GBPUSD")
axes[0,0].set_title("H1 Prices"); axes[0,0].legend()

axes[0,1].plot(df_h1.index, df_h1["corr"], color="purple")
axes[0,1].axhline(0.8, color="gray", linestyle="--")
axes[0,1].set_title("H1 Correlation")

plot_with_signals(axes[0,2], df_h1, "H1 Spread Z-score with Signals")

# --- M15 ---
axes[1,0].plot(df_m15.index, df_m15["EURUSD"], label="EURUSD")
axes[1,0].plot(df_m15.index, df_m15["GBPUSD"], label="GBPUSD")
axes[1,0].set_title("M15 Prices"); axes[1,0].legend()

axes[1,1].plot(df_m15.index, df_m15["corr"], color="purple")
axes[1,1].axhline(0.8, color="gray", linestyle="--")
axes[1,1].set_title("M15 Correlation")

plot_with_signals(axes[1,2], df_m15, "M15 Spread Z-score with Signals")

plt.tight_layout()
plt.show()
