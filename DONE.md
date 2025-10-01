# Projects Workflows

## 1. create data_handler.py
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

---

## 2. create strategy_handler.py
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

---

## 3. create main.py
สุดยอดมาก! ตอนนี้เรามี `data_handler.py` และ `strategy.py` ที่สมบูรณ์แล้วใน `@codebase`

ขั้นตอนสุดท้าย ให้ช่วยสร้างโค้ดสำหรับไฟล์ `main.py` เพื่อเป็นจุดศูนย์กลางในการรันบอททั้งหมด

1.  **Import ที่จำเป็น:**
    *   `time` (สำหรับหน่วงเวลาใน Loop)
    *   `pandas as pd`
    *   `from data_handler import get_historical_data, calculate_indicators`
    *   `from strategy import check_buy_condition, check_sell_condition`
    *   (อาจจะต้อง import `config` ด้วย ถ้าเราสร้างไฟล์ config)

2.  **กำหนดค่าเริ่มต้น (Initial Settings):**
    *   `symbol = 'BTC/USDT'`
    *   `timeframe = '1h'`
    *   `in_position = False` (ตัวแปรสำหรับจัดการสถานะ เริ่มต้นที่ยังไม่มีของ)
    *   `entry_price = 0` (ตัวแปรสำหรับเก็บราคาที่เข้าซื้อ)

3.  **สร้างฟังก์ชัน `run_bot()`:**
    *   นี่คือฟังก์ชันหลักที่จะเป็น Loop การทำงานของบอท
    *   ให้มีการพิมพ์ข้อความเริ่มต้น เช่น "Trading Bot is running..."
    *   สร้าง Loop `while True:` เพื่อให้บอททำงานตลอดเวลา
    *   **ภายใน Loop:**
        *   **Step 1: Fetch Data:**
            *   ใช้ `try...except` เพื่อดักจับข้อผิดพลาดในการเชื่อมต่อ API
            *   เรียก `get_historical_data()` เพื่อดึงข้อมูลล่าสุด (เช่น 200 แท่งเทียน)
            *   เรียก `calculate_indicators()` เพื่อเพิ่ม Indicator ลงใน DataFrame
            *   พิมพ์ข้อความบอกสถานะ เช่น "Fetching new data..."
        *   **Step 2: Check Conditions (Decision Making):**
            *   **ถ้า `in_position` เป็น `False` (กำลังรอซื้อ):**
                *   เรียก `check_buy_condition(df)`
                *   ถ้าคืนค่าเป็น `True`:
                    *   พิมพ์ข้อความ "BUY SIGNAL DETECTED! EXECUTING BUY ORDER."
                    *   อัปเดต `in_position = True`
                    *   บันทึกราคาเข้าซื้อ `entry_price = df['close'].iloc[-1]`
            *   **ถ้า `in_position` เป็น `True` (กำลังถือของอยู่):**
                *   เรียก `check_sell_condition(df, entry_price)`
                *   ถ้าคืนค่าเป็น `True`:
                    *   พิมพ์ข้อความ "SELL SIGNAL DETECTED! EXECUTING SELL ORDER."
                    *   อัปเดต `in_position = False`
                    *   รีเซ็ต `entry_price = 0`
            *   **ถ้าไม่มีสัญญาณ:**
                *   พิมพ์ข้อความ "No signal. Holding position." หรือ "No signal. Waiting for entry."
        *   **Step 3: Wait:**
            *   ใช้ `time.sleep(3600)` เพื่อให้บอทหยุดรอ 1 ชั่วโมง (สำหรับ timeframe '1h') ก่อนจะเริ่ม Loop รอบใหม่

4.  **ส่วน Entry Point ของโปรแกรม:**
    *   ใช้ `if __name__ == "__main__":`
    *   เรียกใช้ฟังก์ชัน `run_bot()`

ช่วยเขียนโค้ดทั้งหมดสำหรับไฟล์ `main.py` ให้สมบูรณ์ตามนี้ และอย่าลืมใส่ Comments อธิบายในแต่ละขั้นตอนด้วย

---

## 4. create config.py and .env
ยอดเยี่ยมมาก! เราจะทำให้โปรเจกต์ปลอดภัยโดยใช้ไฟล์ `.env`

ช่วยสร้างโค้ดสำหรับไฟล์ `config.py` ใหม่ทั้งหมด โดยมี Logic ดังนี้:

1.  **Import ไลบรารีที่จำเป็น:**
    - `os`
    - `load_dotenv` จาก `dotenv`

2.  **โหลดตัวแปรจากไฟล์ .env:**
    - เรียกใช้ฟังก์ชัน `load_dotenv()` ทันทีหลังจาก import เพื่อให้ Python รู้จักตัวแปรในไฟล์ `.env`

3.  **อ่าน API Keys จาก Environment Variables (ส่วนข้อมูลลับ):**
    - `BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')`
    - `BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')`
    - เพิ่มการตรวจสอบว่า Key มีอยู่จริงหรือไม่ ถ้าไม่มีให้โปรแกรมหยุดทำงานและแจ้งเตือนผู้ใช้

4.  **กำหนด Trading Parameters:**
    - `SYMBOL = 'BTC/USDT'`
    - `TIMEFRAME = '1h'`
    - `TRADE_QUANTITY_USD = 15.0`
    - `STOP_LOSS_PERCENT = 0.03`

5.  **กำหนด Strategy Parameters:**
    - `EMA_SHORT, EMA_MEDIUM, EMA_LONG = 12, 26, 50`
    - `RSI_PERIOD = 14`
    - `RSI_OVERBOUGHT = 70`
    - `ADX_PERIOD = 14`
    - `ADX_TREND_THRESHOLD = 25`
    - `FIBO_LOOKBACK_PERIOD = 100`

6.  **กำหนด Bot Operation Parameters:**
    - `LOOP_INTERVAL_SECONDS = 3600`

ช่วยเขียนโค้ดทั้งหมดให้สมบูรณ์ พร้อมคอมเมนต์อธิบายการทำงาน โดยเฉพาะส่วนที่อ่านค่าจาก `.env`

---

## 5. แก้ไข main.py เพื่อเชื่อมต่อ Exchange
เยี่ยมมาก! ตอนนี้โปรเจกต์ของเรามีโครงสร้างที่สมบูรณ์แล้ว

ต่อไป เราจะทำ Task 2.4: Implement Real Exchange Connection

ช่วยแก้ไขไฟล์ `main.py` โดยเพิ่มโค้ดสำหรับสร้างการเชื่อมต่อที่ยืนยันตัวตนแล้วกับ Binance:

1.  **Import เพิ่มเติม:**
    *   `import ccxt`

2.  **ในฟังก์ชัน `run_bot()` หรือก่อนหน้านั้น:**
    *   **สร้าง Exchange Instance:**
        *   ก่อนที่จะเริ่ม `while True:` loop, ให้เพิ่มโค้ดสำหรับสร้าง `exchange` object จาก `ccxt`.
        *   ใช้ `try...except` เพื่อดักจับข้อผิดพลาดหาก API Keys ใน `config.py` ไม่มีค่าหรือผิดพลาด
        *   โค้ดควรมีลักษณะดังนี้:
            ```python
            exchange = ccxt.binance({
                'apiKey': config.BINANCE_API_KEY,
                'secret': config.BINANCE_API_SECRET,
                'options': {
                    'defaultType': 'spot',
                },
            })
            ```
    *   **ตรวจสอบการเชื่อมต่อ:**
        *   (Optional but recommended) ลองเรียกใช้ `exchange.fetch_balance()` ภายใน `try...except` เพื่อทดสอบว่า API Keys ใช้งานได้จริงหรือไม่ ถ้าล้มเหลวให้พิมพ์ข้อความ Error และจบการทำงานของโปรแกรม

3.  **ส่ง `exchange` object ไปใช้งาน:**
    *   เราอาจจะต้องส่ง `exchange` object นี้เข้าไปในฟังก์ชันที่ต้องทำการซื้อขายในอนาคต แต่สำหรับตอนนี้แค่สร้างมันขึ้นมาให้สำเร็จก่อน

ช่วยเพิ่มโค้ดส่วนนี้เข้าไปใน `main.py` อย่างเหมาะสม พร้อม comment อธิบายการทำงาน

---