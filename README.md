# The shadow trader - Bot trader projects
## Project Overview
    [/] 1. create data_handler.py
    [/] 2. create strategy_handler.py
    [/] 3. create main.py
    [/] 4. create config.py and .env
    [/] 5. แก้ไข main.py เพื่อเชื่อมต่อ Exchange
    [/] 6. สร้างระบบ Backtesting

---

## 6. สร้างระบบ Backtesting
สวัสดี, เราจะเริ่มทำ Task 3.1(TODO.md): สร้างระบบ Backtesting

ช่วยสร้างโค้ดสำหรับไฟล์ `backtest.py` เพื่อทดสอบประสิทธิภาพของกลยุทธ์การเทรดของเรากับข้อมูลในอดีต โดยใช้โมดูลที่เรามีอยู่แล้วใน `@codebase`

**โครงสร้างและ Logic ของไฟล์:**

1.  **Import ที่จำเป็น:**
    - `pandas as pd`
    - `config`
    - `data_handler` (สำหรับ `get_historical_data` และ `calculate_indicators`)
    - `strategy` (สำหรับ `check_buy_condition` และ `check_sell_condition`)

2.  **สร้างฟังก์ชัน `run_backtest(start_date_str)`:**
    - รับ `start_date_str` (เช่น "1 year ago UTC", "2022-01-01T00:00:00Z") เพื่อกำหนดจุดเริ่มต้นของข้อมูล
    - **Step 1: Load Historical Data**
        - พิมพ์ข้อความ "Starting Backtest..."
        - ใช้ `ccxt` เพื่อแปลง `start_date_str` เป็น timestamp
        - ดึงข้อมูล OHLCV ทั้งหมดตั้งแต่ `start_date_str` จนถึงปัจจุบันสำหรับ `config.SYMBOL` และ `config.TIMEFRAME` (อาจจะต้องดึงมาทีละ 1000 แท่งแล้วต่อกัน)
        - พิมพ์ข้อความบอกช่วงเวลาและจำนวนข้อมูลที่ได้มา
    - **Step 2: Calculate Indicators**
        - เรียก `calculate_indicators()` เพื่อคำนวณ Indicator ทั้งหมดสำหรับ DataFrame ชุดใหญ่นี้
    - **Step 3: Simulation Loop**
        - กำหนดตัวแปรเริ่มต้น:
            - `in_position = False`
            - `entry_price = 0`
            - `trades = []` (List ว่างสำหรับเก็บผลการเทรด)
            - `initial_balance = 1000.0` (เงินทุนเริ่มต้นจำลอง)
            - `current_balance = initial_balance`
        - วน Loop ผ่าน DataFrame ด้วย `for i in range(len(df)):`
        - **ภายใน Loop:**
            - สร้าง `current_df` ที่เป็นข้อมูลตั้งแต่เริ่มต้นจนถึงแถวที่ `i`
            - **ถ้า `in_position` เป็น `False`:**
                - เรียก `check_buy_condition(current_df)`
                - ถ้าเป็น `True`:
                    - `in_position = True`
                    - `entry_price = current_df['close'].iloc[-1]`
                    - บันทึกเวลาและราคาเข้า
            - **ถ้า `in_position` เป็น `True`:**
                - เรียก `check_sell_condition(current_df, entry_price)`
                - ถ้าเป็น `True`:
                    - `in_position = False`
                    - `exit_price = current_df['close'].iloc[-1]`
                    - คำนวณ P&L ของการเทรดนี้: `pnl_percent = ((exit_price - entry_price) / entry_price)`
                    - อัปเดต `current_balance`
                    - บันทึกการเทรด (entry_price, exit_price, pnl_percent) ลงใน List `trades`
                    - รีเซ็ต `entry_price = 0`
    - **Step 4: Generate Report**
        - หลังจาก Loop จบ, เรียกฟังก์ชัน `generate_report(trades, initial_balance, current_balance)`

3.  **สร้างฟังก์ชัน `generate_report(trades, initial_balance, final_balance)`:**
    - รับ List ของ `trades` และค่า balance
    - **คำนวณสถิติ:**
        - Total Trades
        - Win Rate (จำนวนเทรดที่กำไร / Total Trades)
        - Average Profit per trade
        - Average Loss per trade
        - Max Drawdown (ส่วนนี้อาจจะซับซ้อน อาจจะเริ่มจากการคำนวณง่ายๆ ก่อน)
        - Total P&L Percentage
    - **พิมพ์ Report:** แสดงผลสถิติทั้งหมดออกมาในรูปแบบที่อ่านง่าย

4.  **ส่วน Entry Point ของโปรแกรม:**
    - ใช้ `if __name__ == "__main__":`
    - เรียก `run_backtest(start_date_str="1 year ago UTC")`

ช่วยเขียนโค้ดทั้งหมดสำหรับไฟล์ `backtest.py` ให้สมบูรณ์ตามนี้





