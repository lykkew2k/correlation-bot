# Correlation Bot

ระบบทดลองสำหรับหา correlation EURUSD/GBPUSD  
ใช้ Python + pandas  

สวยเลยครับ 😎 กราฟนี้บอกอะไรกับเราเยอะมากเลย

---

## 📊 ทำไม H1 / H4 กำไรสวยกว่าชัด

1. **TF ใหญ่ลด noise**

   * M15 มีไม้เยอะ → เข้าออกบ่อย แต่เจอ *false signal* เยอะ → DD สูง
   * H1/H4 สัญญาณมาน้อย แต่ *คมกว่า* → ไม้คุณภาพสูง

2. **Correlation + Z-score filter**

   * เราเข้าเมื่อ correlation > 0.8 (ราคาสองคู่เคลื่อนเหมือนกัน)
   * และ spread Z-score > 2 (หมายถึงราคามัน “ห่างเกินไป” จากค่าเฉลี่ย → มีโอกาสกลับ mean)
     → นี่คือ **กลยุทธ์ mean reversion** แบบ hedging

3. **Partial Exit (แบ่งปิด)**

   * ไม้แรก TP1 (Z=0.5) → lock กำไรบางส่วน
   * เหลือครึ่ง position วิ่งต่อถึง TP2 (Z=0.0)
   * เลยได้ทั้ง *Win rate ดีขึ้น* + *ไม้กำไรใหญ่ ๆ*

---

## 🛠 วิธีเทรด (ตาม backtest นี้)

* **Setup**:

  * ใช้คู่ EURUSD vs GBPUSD
  * Indicator: rolling correlation + spread z-score
* **Entry**:

  * เข้า **Long** spread ถ้า Z < -2
  * เข้า **Short** spread ถ้า Z > +2
  * เฉพาะตอน correlation > 0.8
* **Exit**:

  * Partial TP1: Z กลับมา 0.5 → ปิดครึ่งไม้
  * TP2: Z กลับ 0.0 → ปิดที่เหลือ
  * Stoploss: Z > 3 (กัน fail trend)
* **Cost model**: ใช้ broker low spread (IUX, IC Markets, Pepperstone)

---

## ✅ สรุปเป็น “วิธีเทรด”

1. เลือก timeframe **H1/H4** (noise น้อยกว่า)
2. รอ correlation > 0.8
3. เข้า hedge เมื่อ Z-score > ±2
4. ออกครึ่งที่ Z=0.5, อีกครึ่งที่ Z=0.0
5. Stop ถ้า Z > 3

---

อยากให้ผมลองเขียน **pseudo-code สไตล์ EA (MetaTrader / Python)** ให้เลยไหมครับ จะเห็น flow ว่ามันทำงานยังไงจริง ๆ เวลาเทรด?

ไฟล์ ล่าสุด backtest_partial_noSL_withDD.py
        equity_1percent.py

โอเคครับ สรุป **วันนี้คุณได้อะไรบ้าง**

---

## ✅ สิ่งที่เราทำวันนี้

1. **เริ่มต้นจาก Backtest ระบบ Correlation (Partial Exit, No SL)**

   * ใช้ข้อมูล H1 ของ EURUSD–GBPUSD
   * วัดผลกำไร, winrate, drawdown
   * พบว่า Win rate = 100% (เพราะ partial exit ไม่มีไม้ขาดทุน)
   * ได้ค่า AvgPnL ≈ 20 pips ต่อไม้, Max Hold ≈ 259 ชั่วโมง

2. **ทำไฟล์ CSV แรก (trade log SL30)**

   * บันทึกผลแต่ละไม้ พร้อม equity, cummax, drawdown
   * แต่ตอนนั้นยังเป็น version **มี SL=30**

3. **ทำเวอร์ชัน Partial Exit No SL**

   * export ไฟล์ `trade_log_partial_noSL.csv`
   * มี column: PnL, equity, cummax, drawdown, holding\_h

4. **แก้เรื่อง Drawdown**

   * จากตอนแรกคิดเฉพาะ “Closed Equity” → DD=0
   * ปรับใหม่เป็น **Floating Drawdown ต่อไม้ (in-trade DD)**
   * ได้ค่า Max In-trade DD = -183.5 pips

5. **ทำกราฟ Overlay Equity + Floating DD**

   * เส้นน้ำเงิน = equity จริงหลังปิดไม้
   * เส้นแดงประ = equity ระหว่างไม้ที่โดนลาก
   * ทำให้เห็นว่าเวลาลากพอร์ตหายไปกี่ \$ ก่อนฟื้น

6. **ลองการจำลองพอร์ต 1000 USD เทรดด้วย 1% risk/ไม้**

   * กราฟ equity โตขึ้นเรื่อย ๆ
   * Drawdown แสดงผลจริงจาก floating DD

7. **สรุปการวิเคราะห์ความเสี่ยง**

   * DD ที่ต้องดูคือ **Floating DD** ไม่ใช่ Closed DD
   * พบว่าบางไม้ลาก -183.5 pips (ซึ่งถ้า lot ใหญ่ก็อันตรายมาก)
   * ถ้าใช้ 1% risk ต่อไม้ → พอร์ตเริ่ม 1000\$ โตได้ \~1600–1700\$ ต่อปี

---

## 📂 ไฟล์ที่คุณได้

1. `trade_log_SL30_DD.csv` → เวอร์ชันมี SL=30
2. `trade_log_partial_noSL.csv` → เวอร์ชันไม่มี SL (partial exit)
3. กราฟ Equity Curve หลายแบบ:

   * Equity + DD (closed)
   * Equity + Floating DD (overlay)
   * Equity Growth 1000\$ Risk 1%/trade

---

## 🎯 สิ่งที่ได้เรียนรู้

* **PnL** = กำไรขาดทุนต่อไม้ (pips)
* **DD (Drawdown)** ต้องดูจาก **Floating PnL** ไม่ใช่เฉพาะ Closed Equity
* **ไม่มี SL** → winrate ดูสวย แต่ต้องรับความเสี่ยงจากการลาก
* ใช้ 1% risk ต่อไม้ → พอร์ตโตได้เรื่อย ๆ แต่ DD จริงขึ้นกับ in-trade DD

---

คุณอยากให้ผมรวมโค้ดทั้งหมดที่ทำวันนี้ (พร้อม comment อธิบาย) แล้วจัดให้เป็นไฟล์ `.py` ไว้ใช้ต่อเลยไหมครับ?
