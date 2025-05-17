import sqlite3
from datetime import datetime

DATABASE_FILE = "komuten_kanri.db" # データベースファイル名

def get_current_timestamp():
    """現在の日時をYYYY-MM-DD HH:MM:SS形式の文字列で返す"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def create_connection(db_file):
    """データベースファイルへの接続を作成する"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        # 外部キー制約を有効にする (SQLiteではデフォルトでOFFの場合があるため)
        conn.execute("PRAGMA foreign_keys = ON")
        print(f"SQLite DB Browser version: {sqlite3.sqlite_version}")
        print(f"Successfully connected to {db_file}")
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
    return conn

def create_table(conn, create_table_sql):
    """テーブルを作成する"""
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        table_name_clause = create_table_sql.split('TABLE IF NOT EXISTS ')[1]
        table_name = table_name_clause.split(' (')[0]
        print(f"Table '{table_name}' created successfully (or already exists).")
    except sqlite3.Error as e:
        print(f"Error creating table: {e}")
        print(f"SQL: {create_table_sql}")


# database_setup.py の内容 (setup_database 関数全体を更新)

# ... (DATABASE_FILE, get_current_timestamp, create_connection, create_table 関数は変更なし) ...

def setup_database():
    """データベースの初期設定（テーブル作成）を行う"""

    sql_create_customers_table = """
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL UNIQUE, 
        contact_person_name TEXT,
        phone_number TEXT,
        email TEXT,
        address TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        notes TEXT
    );
    """

    sql_create_projects_table = """
    CREATE TABLE IF NOT EXISTS projects (
        project_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_code TEXT UNIQUE NOT NULL,
        project_name TEXT NOT NULL,
        customer_id INTEGER,
        parent_project_id INTEGER,
        site_address TEXT,
        reception_date TEXT,
        start_date_scheduled TEXT,
        completion_date_scheduled TEXT,
        actual_completion_date TEXT,
        responsible_staff_name TEXT,
        estimated_amount INTEGER,
        status TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        remarks TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
            ON DELETE SET NULL
            ON UPDATE CASCADE,
        FOREIGN KEY (parent_project_id) REFERENCES projects (project_id)
            ON DELETE RESTRICT
            ON UPDATE CASCADE
    );
    """

    sql_create_employees_table = """
    CREATE TABLE IF NOT EXISTS employees (
        employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_code TEXT UNIQUE,
        full_name TEXT NOT NULL,
        name_kana TEXT,
        ccus_id TEXT UNIQUE,
        date_of_birth TEXT,
        gender TEXT,
        position TEXT,
        address TEXT,
        phone_number TEXT,
        job_title TEXT NOT NULL,
        employment_date TEXT,
        experience_years_trade REAL,
        emergency_contact_name TEXT,
        emergency_contact_phone TEXT,
        emergency_contact_relationship TEXT,
        last_health_check_date TEXT,
        blood_type TEXT,
        social_insurance_status_notes TEXT,
        retirement_allowance_notes TEXT,
        qualifications_notes TEXT,
        paid_leave_days_notes TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        remarks TEXT
    );
    """

    # ### 追加 ### 見積ヘッダー (quotations) テーブルのSQL
    sql_create_quotations_table = """
    CREATE TABLE IF NOT EXISTS quotations (
        quotation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        quotation_staff_id INTEGER,
        quotation_code TEXT UNIQUE NOT NULL,
        quotation_date TEXT NOT NULL,
        customer_name_at_quote TEXT NOT NULL,
        project_name_at_quote TEXT NOT NULL,
        site_address_at_quote TEXT,
        construction_period_notes TEXT,
        total_amount_exclusive_tax INTEGER,
        tax_rate REAL,
        tax_amount INTEGER,
        total_amount_inclusive_tax INTEGER,
        validity_period_notes TEXT,
        payment_terms_notes TEXT,
        status TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        remarks TEXT,
        FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE RESTRICT,
        FOREIGN KEY(quotation_staff_id) REFERENCES employees(employee_id) ON DELETE SET NULL
    );
    """

    # ### 追加 ### 見積明細 (quotation_items) テーブルのSQL
    sql_create_quotation_items_table = """
    CREATE TABLE IF NOT EXISTS quotation_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        quotation_id INTEGER NOT NULL,
        display_order INTEGER,
        name TEXT NOT NULL,
        specification TEXT,
        quantity REAL,
        unit TEXT,
        unit_price INTEGER,
        amount INTEGER,
        remarks TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(quotation_id) REFERENCES quotations(quotation_id) ON DELETE CASCADE
    );
    """

    conn = create_connection(DATABASE_FILE)

    if conn is not None:
        try:
            create_table(conn, sql_create_customers_table)
            create_table(conn, sql_create_projects_table)
            create_table(conn, sql_create_employees_table)
            
            # ### 追加 ### 見積関連テーブルを作成
            create_table(conn, sql_create_quotations_table)
            create_table(conn, sql_create_quotation_items_table)

            conn.commit()
            print("Database setup complete. All tables (customers, projects, employees, quotations, quotation_items) created/checked.")
        except sqlite3.Error as e:
            print(f"An error occurred during database setup: {e}")
        finally:
            conn.close()
            print("Database connection closed.")
    else:
        print("Error! Cannot create the database connection.")

if __name__ == '__main__':
    setup_database()