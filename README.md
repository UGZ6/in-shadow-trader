# The shadow trader - Bot trader projects
## Project Overview
    [/] create data_handler.py
    [ ] create strategy_handler.py

เยี่ยมมาก! ตอนนี้เรามี `data_handler.py` ที่สมบูรณ์แล้ว

ต่อไป ช่วยสร้างโค้ดสำหรับไฟล์ `strategy.py` ให้สมบูรณ์ โดยอ้างอิงจากโค้ดใน `@codebase` โดยเฉพาะฟังก์ชันจาก `data_handler.py`

1.  **Import ที่จำเป็น:**
    *   `import pandas as pd`
    *   `from data_handler import calculate_indicators` (สมมติว่าเราจะใช้ฟังก์ชันนี้)

2.  **สร้างฟังก์ชัน `find_recent_swing_high_low(df, lookback_period=100)`:**
    *   **Goal:** เพื่อหาจุด Swing High และ Swing Low สำหรับคำนวณ Fibonacci.
    *   **Logic:** รับ DataFrame เข้ามา, มองย้อนหลังไป `lookback_period` แท่งเทียน, หาค่าราคาสูงสุด (`high`) และค่าราคาต่ำสุด (`low`) ในช่วงเวลานั้น.
    *   **Returns:** คืนค่า `(swing_high, swing_low)`.

3.  **สร้างฟังก์ชัน `check_buy_condition(df)`:**
    *   **Goal:** ตรวจสอบเงื่อนไขการเข้าซื้อจากข้อมูลล่าสุด.
    *   **Logic:**
        *   ดึงข้อมูลแถวล่าสุด (last_row) จาก DataFrame.
        *   เรียกใช้ `find_recent_swing_high_low` เพื่อหาแนว Fibo.
        *   คำนวณแนวรับ Fibonacci 0.5 และ 0.618.
        *   **ใช้ Logic ที่เราเคยออกแบบไว้:**
            *   EMA_12 > EMA_26 AND EMA_26 > EMA_50
            *   AND MACD_12_26_9 > MACDh_12_26_9 (เส้น MACD > เส้น Signal)
            *   AND RSI_14 < 68 (ให้มีพื้นที่วิ่งขึ้น)
            *   AND ADX_14 > 25
            *   AND ราคา `close` ปัจจุบันอยู่ระหว่างแนวรับ Fibo 0.5 และ 0.618
    *   **Returns:** `True` ถ้าเงื่อนไขครบ, `False` ถ้าไม่.

4.  **สร้างฟังก์ชัน `check_sell_condition(df, entry_price)`:**
    *   **Goal:** ตรวจสอบเงื่อนไขการขาย.
    *   **Logic:**
        *   ดึงข้อมูลแถวล่าสุด (last_row).
        *   **ใช้ Logic การขาย:**
            *   EMA_12 < EMA_26
            *   OR MACD_12_26_9 < MACDh_12_26_9
            *   OR ราคา `close` <= `entry_price` * 0.97 (Stop Loss 3%)
    *   **Returns:** `True` ถ้าเงื่อนไขข้อใดข้อหนึ่งจริง, `False` ถ้าไม่.

ช่วยเขียนโค้ดทั้งหมดสำหรับไฟล์ `strategy.py` พร้อม Docstrings และ Comments ตามกฎใน `.claude.md` ด้วย
