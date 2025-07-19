import psycopg2
import os
from datetime import date

# --- 1. 資料庫連線設定 ---
# 建議使用環境變數來管理敏感資料，但此處為求簡單，直接寫在程式碼中
# 若要使用環境變數，請取消註解 os.getenv 的部分
DB_USER = "postgres"  # os.getenv("DB_USER", "postgres")
DB_PASSWORD = "Zaq@1234" # os.getenv("DB_PASSWORD", "your_password")
DB_HOST = "localhost" # os.getenv("DB_HOST", "localhost")
DB_PORT = "5432"      # os.getenv("DB_PORT", "5432")
DB_NAME = "body_data" # os.getenv("DB_NAME", "body_data")

# --- 2. 核心功能：新增身體數據紀錄 ---
def log_body_data(weight: float, skeletal_muscle_mass: float, body_fat: float, log_date: date, note: str = None):
    """
    將一筆身體數據紀錄新增至 PostgreSQL 資料庫。

    Args:
        weight (float): 體重 (公斤)
        skeletal_muscle_mass (float): 骨骼肌重 (公斤)
        body_fat (float): 體脂肪重 (公斤)
        log_date (date): 記錄日期
        note (str, optional): 備註. Defaults to None.

    Returns:
        bool: 成功回傳 True, 失敗回傳 False.
    """
    conn = None
    try:
        # 建立資料庫連線
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        # 建立 cursor 物件
        with conn.cursor() as cur:
            # SQL INSERT 指令，使用 %s 避免 SQL Injection 攻擊
            # id 和 created_at 由資料庫自動生成，不需手動插入
            sql_query = """
                INSERT INTO body_records (weight, skeletal_muscle_mass, body_fat, log_date, note)
                VALUES (%s, %s, %s, %s, %s);
            """
            # 準備要插入的資料
            data_to_insert = (weight, skeletal_muscle_mass, body_fat, log_date, note)

            # 執行 SQL 指令
            cur.execute(sql_query, data_to_insert)

            # 提交交易
            conn.commit()
            print("數據新增成功！")
            return True

    except psycopg2.Error as e:
        # 如果發生錯誤，印出錯誤訊息
        print(f"資料庫操作失敗: {e}")
        # 如果連線存在，則回滾交易
        if conn:
            conn.rollback()
        return False

    finally:
        # 無論成功或失敗，最後都關閉連線
        if conn:
            conn.close()
            # print("資料庫連線已關閉。")


# --- 3. 程式執行進入點與範例 ---
if __name__ == "__main__":
    print("--- 開始執行身體數據紀錄程式 ---")

    # 範例 1: 記錄今天的數據
    today = date.today()
    log_body_data(
        weight=75.5,
        skeletal_muscle_mass=35.2,
        body_fat=15.8,
        log_date=today,
        note="今天運動後測量"
    )

    print("\n" + "="*30 + "\n")

    # 範例 2: 補登昨天的數據，沒有備註
    # from datetime import timedelta
    # yesterday = date.today() - timedelta(days=1)
    # log_body_data(
    #     weight=75.8,
    #     skeletal_muscle_mass=35.0,
    #     body_fat=16.1,
    #     log_date=yesterday
    # )

    print("--- 程式執行完畢 ---")