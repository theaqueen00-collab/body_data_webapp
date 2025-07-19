import psycopg2
import psycopg2.extras
import os
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv # 載入 python-dotenv 函式庫

# 在程式最一開始就執行，它會去讀取 .env 檔案，並把裡面的變數載入到環境中
load_dotenv()

# --- 1. 初始化 Flask 應用程式 ---
app = Flask(__name__)
# 從環境變數讀取密鑰。如果在本地 .env 中沒設定，或在 Render 上沒設定，就會使用一個預設值
app.secret_key = os.getenv('SECRET_KEY', 'a_default_fallback_secret_key')


# --- 2. 【最終版】資料庫連線邏輯 ---
def get_db_connection():
    """
    建立資料庫連線。
    自動判斷是在雲端(使用 DATABASE_URL)還是在本地(使用 .env 裡的變數)。
    """
    try:
        # os.getenv('DATABASE_URL') 會先嘗試讀取 Render 提供的雲端資料庫網址
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            # 如果在雲端，直接使用 DATABASE_URL 連線
            return psycopg2.connect(database_url)
        else:
            # 如果在本地 (找不到 DATABASE_URL)，就讀取 .env 裡的變數來連線
            return psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT")
            )
    except psycopg2.OperationalError as e:
        print(f"資料庫連線失敗: {e}")
        # 在 Web App 中，將錯誤顯示在頁面上會比讓程式崩潰更好
        flash(f"資料庫連線錯誤，請聯繫管理員: {e}", "danger")
        return None


# --- 3. 核心功能函式區 (維持不變，因為它們都呼叫 get_db_connection) ---
def log_body_data(name: str, weight: float, skeletal_muscle_mass: float, body_fat: float, log_date: date, note: str = None):
    conn = get_db_connection()
    if not conn: return False, "無法建立資料庫連線"
    try:
        with conn.cursor() as cur:
            sql_query = "INSERT INTO body_records (name, weight, skeletal_muscle_mass, body_fat, log_date, note) VALUES (%s, %s, %s, %s, %s, %s);"
            data_to_insert = (name, weight, skeletal_muscle_mass, body_fat, log_date, note)
            cur.execute(sql_query, data_to_insert)
            conn.commit()
            return True, None
    except psycopg2.Error as e:
        if conn: conn.rollback()
        return False, str(e)
    finally:
        if conn: conn.close()

def get_report_data():
    conn = get_db_connection()
    if not conn: return {}
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT name, skeletal_muscle_mass, body_fat, log_date FROM body_records ORDER BY name, log_date ASC")
            records = cur.fetchall()
    except psycopg2.Error as e:
        print(f"查詢報告資料時發生錯誤: {e}")
        return {}
    finally:
        if conn: conn.close()

    if not records: return {}
    # (計算邏輯不變，此處省略)
    progress_data = {}
    for record in records:
        name = record['name']
        if name not in progress_data:
            progress_data[name] = {'first': record, 'last': record}
        else:
            progress_data[name]['last'] = record
    report_results = {}
    for name, data in progress_data.items():
        first_record, last_record = data['first'], data['last']
        if first_record['log_date'] == last_record['log_date']:
            report_results[name] = {'has_progress': False, 'first_date': first_record['log_date']}
            continue
        first_fat = first_record['body_fat']
        last_fat = last_record['body_fat']
        first_muscle = first_record['skeletal_muscle_mass']
        last_muscle = last_record['skeletal_muscle_mass']
        fat_loss_percentage = ((first_fat - last_fat) / first_fat * 100) if first_fat > 0 else 0
        muscle_gain_percentage = ((last_muscle - first_muscle) / first_muscle * 100) if first_muscle > 0 else 0
        report_results[name] = {
            'has_progress': True, 'first_date': first_record['log_date'], 'last_date': last_record['log_date'],
            'fat_loss_percentage': fat_loss_percentage, 'muscle_gain_percentage': muscle_gain_percentage
        }
    return report_results

# --- 4. 網頁路由區 (Routes) (維持不變) ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            name = request.form['name']
            weight = float(request.form['weight'])
            skeletal_muscle_mass = float(request.form['skeletal_muscle_mass'])
            body_fat = float(request.form['body_fat'])
            log_date_str = request.form['log_date']
            note = request.form.get('note')
            success, error_message = log_body_data(name, weight, skeletal_muscle_mass, body_fat, log_date_str, note)
            if success:
                flash(f'使用者 {name} 的數據已成功儲存！', 'success')
            else:
                flash(f'儲存失敗：{error_message}', 'danger')
        except ValueError:
            flash('輸入的數字格式不正確，請重新輸入。', 'danger')
        except Exception as e:
            flash(f'發生未知錯誤：{e}', 'danger')
        return redirect(url_for('index'))
    return render_template('index.html')

@app.route('/report')
def report():
    final_report = get_report_data()
    return render_template('report.html', report_data=final_report)

# --- 5. 啟動伺服器 ---
if __name__ == '__main__':
    app.run(debug=True)