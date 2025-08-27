import os
import pandas as pd

# === ตั้งค่า ===
base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir, "data")
outdir = data_dir   # เซฟไฟล์ออกใน data/ เดิม

# หาเฉพาะไฟล์ M1 ต้นฉบับ
files = {}
for fname in os.listdir(data_dir):
    if fname.endswith(".csv") and "_M1_" in fname.upper():
        if "EURUSD" in fname.upper():
            files["EURUSD"] = os.path.join(data_dir, fname)
        elif "GBPUSD" in fname.upper():
            files["GBPUSD"] = os.path.join(data_dir, fname)

print("Found files:", files)

def load_histdata(filepath):
    df = pd.read_csv(
        filepath,
        sep=";",
        header=None,
        names=["datetime", "open", "high", "low", "close", "volume"],
        parse_dates=["datetime"]
    )
    df = df.set_index("datetime")
    return df

def resample_tf(df, rule):
    return df.resample(rule).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum"
    }).dropna()

# === แปลงเป็น H1 และ M15 ===
for symbol, filepath in files.items():
    print(f"\nProcessing {symbol} from {filepath} ...")
    df = load_histdata(filepath)

    for tf_name, rule in [("M15", "15min"), ("H1", "1H")]:
        df_tf = resample_tf(df, rule)

        fname = f"{symbol}_{tf_name}_2024.csv"
        fpath = os.path.join(outdir, fname)
        df_tf.to_csv(fpath)
        print("Saved:", fpath, "Rows:", len(df_tf))
