import sqlite3
from datetime import datetime
DATABASE_FILE = "komuten_kanri.db" # データベースファイル名
def get_current_timestamp():
    """現在の日時をYYYY-MM-DD HH:MM:SS形式の文字列で返す"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def create_connection(db_file=DATABASE_FILE):
    """データベースファイルへの接続を作成し、外部キーを有効にする"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.execute("PRAGMA foreign_keys = ON") # 外部キー制約を有効にする
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
    return conn
# --- 顧客 (Customers) テーブル操作 ---
def add_customer(customer_name, contact_person_name, phone_number, email, address, notes):
    """新しい顧客をデータベースに追加する"""
    conn = create_connection()
    if not conn:
        return None

    sql = ''' INSERT INTO customers(customer_name, contact_person_name, phone_number, email, address, created_at, updated_at, notes)
              VALUES(?,?,?,?,?,?,?,?) '''
    
    current_time = get_current_timestamp()
    try:
        cur = conn.cursor()
        cur.execute(sql, (customer_name, contact_person_name, phone_number, email, address, current_time, current_time, notes))
        conn.commit()
        print(f"Customer '{customer_name}' added successfully with ID: {cur.lastrowid}")
        return cur.lastrowid 
    except sqlite3.IntegrityError as e:
        error_message_lower = str(e).lower() # エラーメッセージを小文字に変換
        # ### 変更点 ### 比較文字列も小文字にし、判定を修正
        if "unique constraint failed: customers.customer_name" in error_message_lower:
            print(f"Error adding customer: Customer name '{customer_name}' already exists.")
            return "DUPLICATE_NAME" 
        else:
            print(f"Error adding customer (IntegrityError): {e}")
            return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error adding customer: {e}")
        return "OTHER_DB_ERROR" 
    finally:
        if conn:
            conn.close()
def get_all_customers():
    """全ての顧客情報をデータベースから取得する"""
    conn = create_connection()
    if not conn:
        return []

    try:
        cur = conn.cursor()
        cur.execute("SELECT customer_id, customer_name, contact_person_name, phone_number, email, address, notes, created_at, updated_at FROM customers ORDER BY customer_name")
        rows = cur.fetchall()
        # fetchall() はタプルのリストを返すので、カラム名と値を対応付けた辞書のリストに変換すると扱いやすい（オプション）
        # customers = []
        # for row in rows:
        #     customers.append(dict(zip([column[0] for column in cur.description], row)))
        # return customers
        return rows # Treeviewで直接使う場合はタプルのリストのままでも良い
    except sqlite3.Error as e:
        print(f"Error fetching customers: {e}")
        return []
    finally:
        if conn:
            conn.close()
def get_customer_by_id(customer_id):
    """指定されたIDの顧客情報を取得する"""
    conn = create_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM customers WHERE customer_id=?", (customer_id,))
        row = cur.fetchone()
        return row # タプルで返す
    except sqlite3.Error as e:
        print(f"Error fetching customer by ID: {e}")
        return None
    finally:
        if conn:
            conn.close()
def update_customer(customer_id, customer_name, contact_person_name, phone_number, email, address, notes):
    """顧客情報を更新する"""
    conn = create_connection()
    if not conn:
        return "CONNECTION_ERROR" 

    sql = ''' UPDATE customers
              SET customer_name = ?,
                  contact_person_name = ?,
                  phone_number = ?,
                  email = ?,
                  address = ?,
                  updated_at = ?,
                  notes = ?
              WHERE customer_id = ? '''
    
    current_time = get_current_timestamp()
    try:
        cur = conn.cursor()
        cur.execute(sql, (customer_name, contact_person_name, phone_number, email, address, current_time, notes, customer_id))
        conn.commit()
        if cur.rowcount == 0: 
            print(f"Error updating customer: Customer ID {customer_id} not found.")
            return "NOT_FOUND" # 更新対象が見つからなかった
        print(f"Customer ID {customer_id} updated successfully.")
        return True # 成功
    except sqlite3.IntegrityError as e:
        error_message_lower = str(e).lower()
        if "unique constraint failed: customers.customer_name" in error_message_lower:
            print(f"Error updating customer: Customer name '{customer_name}' already exists for another customer.")
            return "DUPLICATE_NAME" # 顧客名重複 (他の顧客と)
        else:
            print(f"Error updating customer (IntegrityError): {e}")
            return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error updating customer ID {customer_id}: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn:
            conn.close()
# database_operations.py の delete_customer 関数
def delete_customer(customer_id):
    """顧客情報を削除する"""
    conn = create_connection()
    if not conn:
        return "CONNECTION_ERROR" # 接続エラー

    # 案件テーブル(projects)では customer_id に ON DELETE SET NULL を設定しているため、
    # 顧客を削除すると関連する案件の customer_id は NULL になります。
    # そのため、通常は IntegrityError を心配する必要は少ないですが、
    # 念のため rowcount で削除された行数を確認します。

    sql = 'DELETE FROM customers WHERE customer_id=?'
    try:
        cur = conn.cursor()
        cur.execute(sql, (customer_id,))
        conn.commit()
        if cur.rowcount == 0: # 削除された行が0の場合、指定されたIDの顧客が存在しなかった
            print(f"Error deleting customer: Customer ID {customer_id} not found.")
            return "NOT_FOUND" 
        print(f"Customer ID {customer_id} deleted successfully.")
        return True # 成功
    except sqlite3.Error as e:
        # 他の予期せぬSQLiteエラーが発生した場合
        print(f"Error deleting customer ID {customer_id}: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn:
            conn.close()
# --- (将来的にここへ案件テーブルなどの操作関数も追加していく) ---
# --- 案件 (Projects) テーブル操作 ---
def add_project(project_code, project_name, customer_id, parent_project_id, 
                site_address, reception_date, start_date_scheduled, 
                completion_date_scheduled, actual_completion_date, 
                responsible_staff_name, estimated_amount, status, remarks):
    """新しい案件をデータベースに追加する"""
    conn = create_connection()
    if not conn:
        return "CONNECTION_ERROR"

    sql = ''' INSERT INTO projects(project_code, project_name, customer_id, parent_project_id,
                                 site_address, reception_date, start_date_scheduled,
                                 completion_date_scheduled, actual_completion_date,
                                 responsible_staff_name, estimated_amount, status, 
                                 created_at, updated_at, remarks)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ''' # 15個のプレースホルダ
    
    current_time = get_current_timestamp()
    try:
        cur = conn.cursor()
        cur.execute(sql, (project_code, project_name, customer_id, parent_project_id,
                         site_address, reception_date, start_date_scheduled,
                         completion_date_scheduled, actual_completion_date,
                         responsible_staff_name, estimated_amount, status,
                         current_time, current_time, remarks))
        conn.commit()
        print(f"Project '{project_name}' (Code: {project_code}) added successfully with ID: {cur.lastrowid}")
        return cur.lastrowid # 追加された案件のIDを返す
    except sqlite3.IntegrityError as e:
        error_message_lower = str(e).lower()
        if "unique constraint failed: projects.project_code" in error_message_lower:
            print(f"Error adding project: Project code '{project_code}' already exists.")
            return "DUPLICATE_CODE"
        elif "not null constraint failed" in error_message_lower: # ### この elif を追加・確認 ###
             print(f"Error adding project: A required field (like project_code or project_name) was not provided. Details: {e}")
             return "NOT_NULL_VIOLATION"
        elif "foreign key constraint failed" in error_message_lower: # ### この elif を追加・確認 ###
            print(f"Error adding project: Foreign key constraint failed. Check customer_id or parent_project_id. Details: {e}")
            return "FK_CONSTRAINT_FAILED"
        else:
            print(f"Error adding project (IntegrityError): {e}") # その他のIntegrityError
            return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error adding project: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn:
            conn.close()
# database_operations.py に追記 (add_project 関数の後など)
# database_operations.py に追記
# --- 社員 (Employees) テーブル操作 ---
# database_operations.py に追記
# --- 社員 (Employees) テーブル操作 ---
def add_employee(employee_code, full_name, name_kana, ccus_id, date_of_birth, gender,
                 position, address, phone_number, job_title, employment_date,
                 experience_years_trade, emergency_contact_name, emergency_contact_phone,
                 emergency_contact_relationship, last_health_check_date, blood_type,
                 social_insurance_status_notes, retirement_allowance_notes,
                 qualifications_notes, paid_leave_days_notes, is_active, remarks):
    """新しい社員をデータベースに追加する"""
    conn = create_connection()
    if not conn:
        return "CONNECTION_ERROR"

    sql = ''' INSERT INTO employees(employee_code, full_name, name_kana, ccus_id, 
                                 date_of_birth, gender, position, address, phone_number, 
                                 job_title, employment_date, experience_years_trade, 
                                 emergency_contact_name, emergency_contact_phone, 
                                 emergency_contact_relationship, last_health_check_date, 
                                 blood_type, social_insurance_status_notes, 
                                 retirement_allowance_notes, qualifications_notes, 
                                 paid_leave_days_notes, is_active, remarks,
                                 created_at, updated_at)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ''' # 25個のプレースホルダ
    
    current_time = get_current_timestamp()
    # is_active は整数 (0 or 1) であることを確認
    is_active_int = 1 if is_active else 0

    try:
        cur = conn.cursor()
        cur.execute(sql, (employee_code, full_name, name_kana, ccus_id, 
                         date_of_birth, gender, position, address, phone_number, 
                         job_title, employment_date, experience_years_trade, 
                         emergency_contact_name, emergency_contact_phone, 
                         emergency_contact_relationship, last_health_check_date, 
                         blood_type, social_insurance_status_notes, 
                         retirement_allowance_notes, qualifications_notes, 
                         paid_leave_days_notes, is_active_int, remarks, # is_active を整数に
                         current_time, current_time))
        conn.commit()
        print(f"Employee '{full_name}' (Code: {employee_code or 'N/A'}) added successfully with ID: {cur.lastrowid}")
        return cur.lastrowid # 追加された社員のIDを返す
    except sqlite3.IntegrityError as e:
        error_message_lower = str(e).lower()
        if "unique constraint failed: employees.employee_code" in error_message_lower and employee_code: # employee_codeがNoneでない場合のみチェック
            print(f"Error adding employee: Employee code '{employee_code}' already exists.")
            return "DUPLICATE_EMP_CODE"
        elif "unique constraint failed: employees.ccus_id" in error_message_lower and ccus_id: # ccus_idがNoneでない場合のみチェック
            print(f"Error adding employee: CCUS ID '{ccus_id}' already exists.")
            return "DUPLICATE_CCUS_ID"
        elif "not null constraint failed" in error_message_lower:
             # 具体的にどのNOT NULL制約かはエラーメッセージeで確認可能
             print(f"Error adding employee: A required field was not provided. Details: {e}")
             return "NOT_NULL_VIOLATION"
        else:
            print(f"Error adding employee (IntegrityError): {e}")
            return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error adding employee: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn:
            conn.close()
# database_operations.py に追記 (add_employee 関数の後など)
def get_all_employees():
    """全ての社員情報をデータベースから取得する"""
    conn = create_connection()
    if not conn:
        return [] # 接続エラー時は空のリストを返す

    try:
        cur = conn.cursor()
        # 取得するカラムを全て指定し、社員コード順でソート (employee_code が NULL の可能性も考慮)
        # ORDER BY COALESCE(employee_code, '') は NULL の場合に空文字列としてソートするため、NULLが最後にくるなどを防ぐ
        sql = """
            SELECT 
                employee_id, employee_code, full_name, name_kana, ccus_id, 
                date_of_birth, gender, position, address, phone_number, 
                job_title, employment_date, experience_years_trade, 
                emergency_contact_name, emergency_contact_phone, 
                emergency_contact_relationship, last_health_check_date, 
                blood_type, social_insurance_status_notes, 
                retirement_allowance_notes, qualifications_notes, 
                paid_leave_days_notes, is_active, remarks,
                created_at, updated_at
            FROM employees
            ORDER BY COALESCE(employee_code, full_name) 
        """
        # もし社員コードが必須で常に存在するなら ORDER BY employee_code でOK
        # または ORDER BY full_name などでも良い
        cur.execute(sql)
        rows = cur.fetchall()
        return rows # タプルのリストとして返す
    except sqlite3.Error as e:
        print(f"Error fetching employees: {e}")
        return []
    finally:
        if conn:
            conn.close()
# database_operations.py に追記 (get_all_employees 関数の後など)
def get_employee_by_id(employee_id):
    """指定されたIDの社員情報をデータベースから取得する"""
    conn = create_connection()
    if not conn:
        return None # 接続エラー時は None を返す

    try:
        cur = conn.cursor()
        # 全てのカラムを取得
        sql = """
            SELECT 
                employee_id, employee_code, full_name, name_kana, ccus_id, 
                date_of_birth, gender, position, address, phone_number, 
                job_title, employment_date, experience_years_trade, 
                emergency_contact_name, emergency_contact_phone, 
                emergency_contact_relationship, last_health_check_date, 
                blood_type, social_insurance_status_notes, 
                retirement_allowance_notes, qualifications_notes, 
                paid_leave_days_notes, is_active, remarks,
                created_at, updated_at
            FROM employees
            WHERE employee_id = ?
        """
        cur.execute(sql, (employee_id,))
        row = cur.fetchone() # 1件のデータを取得
        return row # タプルとして返す (存在しない場合はNone)
    except sqlite3.Error as e:
        print(f"Error fetching employee by ID ({employee_id}): {e}")
        return None
    finally:
        if conn:
            conn.close()
# database_operations.py に追記 (get_employee_by_id 関数の後など)
def update_employee(employee_id, employee_code, full_name, name_kana, ccus_id, 
                    date_of_birth, gender, position, address, phone_number, 
                    job_title, employment_date, experience_years_trade, 
                    emergency_contact_name, emergency_contact_phone, 
                    emergency_contact_relationship, last_health_check_date, 
                    blood_type, social_insurance_status_notes, 
                    retirement_allowance_notes, qualifications_notes, 
                    paid_leave_days_notes, is_active, remarks):
    """指定されたIDの社員情報を更新する"""
    conn = create_connection()
    if not conn:
        return "CONNECTION_ERROR"

    sql = ''' UPDATE employees
              SET employee_code = ?, full_name = ?, name_kana = ?, ccus_id = ?, 
                  date_of_birth = ?, gender = ?, position = ?, address = ?, 
                  phone_number = ?, job_title = ?, employment_date = ?, 
                  experience_years_trade = ?, emergency_contact_name = ?, 
                  emergency_contact_phone = ?, emergency_contact_relationship = ?, 
                  last_health_check_date = ?, blood_type = ?, 
                  social_insurance_status_notes = ?, retirement_allowance_notes = ?, 
                  qualifications_notes = ?, paid_leave_days_notes = ?, 
                  is_active = ?, remarks = ?, updated_at = ?
              WHERE employee_id = ? '''
    
    current_time = get_current_timestamp()
    is_active_int = 1 if is_active else 0

    try:
        cur = conn.cursor()
        cur.execute(sql, (employee_code, full_name, name_kana, ccus_id, 
                         date_of_birth, gender, position, address, phone_number, 
                         job_title, employment_date, experience_years_trade, 
                         emergency_contact_name, emergency_contact_phone, 
                         emergency_contact_relationship, last_health_check_date, 
                         blood_type, social_insurance_status_notes, 
                         retirement_allowance_notes, qualifications_notes, 
                         paid_leave_days_notes, is_active_int, remarks, 
                         current_time, employee_id))
        conn.commit()
        if cur.rowcount == 0:
            print(f"Error updating employee: Employee ID {employee_id} not found.")
            return "NOT_FOUND" # 更新対象が見つからなかった
        print(f"Employee ID {employee_id} ('{full_name}') updated successfully.")
        return True # 成功
    except sqlite3.IntegrityError as e:
        error_message_lower = str(e).lower()
        if "unique constraint failed: employees.employee_code" in error_message_lower and employee_code:
            print(f"Error updating employee: Employee code '{employee_code}' already exists for another employee.")
            return "DUPLICATE_EMP_CODE"
        elif "unique constraint failed: employees.ccus_id" in error_message_lower and ccus_id:
            print(f"Error updating employee: CCUS ID '{ccus_id}' already exists for another employee.")
            return "DUPLICATE_CCUS_ID"
        elif "not null constraint failed" in error_message_lower:
             print(f"Error updating employee: A required field was not provided. Details: {e}")
             return "NOT_NULL_VIOLATION"
        else:
            print(f"Error updating employee (IntegrityError): {e}")
            return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error updating employee ID {employee_id}: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn:
            conn.close()
# database_operations.py に追記 (update_employee 関数の後など)
def delete_employee(employee_id):
    """指定されたIDの社員情報を削除する"""
    conn = create_connection()
    if not conn:
        return "CONNECTION_ERROR"

    # 将来的に、社員が案件の担当者になっている場合などの整合性を考慮するなら、
    # ここで関連チェックを入れることもできますが、まずは単純な削除処理とします。
    # projects テーブルの responsible_staff_name は現在ただのTEXT型なので、
    # 社員を削除しても直接的なDBエラーにはなりにくいです。

    sql = 'DELETE FROM employees WHERE employee_id = ?'
    try:
        cur = conn.cursor()
        cur.execute(sql, (employee_id,))
        conn.commit()
        if cur.rowcount == 0: # 削除された行が0の場合
            print(f"Error deleting employee: Employee ID {employee_id} not found.")
            return "NOT_FOUND"
        print(f"Employee ID {employee_id} deleted successfully.")
        return True # 成功
    except sqlite3.Error as e: # 他の予期せぬSQLiteエラー
        print(f"Error deleting employee ID {employee_id}: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn:
            conn.close()

def get_all_projects():
    """全ての案件情報をデータベースから取得する"""
    conn = create_connection()
    if not conn:
        return [] # 接続エラー時は空のリストを返す

    try:
        cur = conn.cursor()
        # 取得するカラムを明確に指定し、案件コード順でソート
        # customer_name も JOIN して取得すると一覧表示で便利ですが、まずは projects テーブルの情報のみ取得します
        sql = """
            SELECT 
                p.project_id, p.project_code, p.project_name, 
                p.customer_id, c.customer_name, -- 顧客IDと顧客名
                p.parent_project_id, pp.project_code as parent_project_code, -- 親案件IDと親案件コード
                p.site_address, p.reception_date, p.start_date_scheduled, 
                p.completion_date_scheduled, p.actual_completion_date, 
                p.responsible_staff_name, p.estimated_amount, p.status, 
                p.remarks, p.created_at, p.updated_at
            FROM projects p
            LEFT JOIN customers c ON p.customer_id = c.customer_id
            LEFT JOIN projects pp ON p.parent_project_id = pp.project_id
            ORDER BY p.project_code
        """
        cur.execute(sql)
        rows = cur.fetchall()
        # カラム名も一緒に返すとGUIで扱いやすい場合があるため、辞書のリストに変換する選択肢も提示
        # projects = []
        # columns = [desc[0] for desc in cur.description]
        # for row in rows:
        #     projects.append(dict(zip(columns, row)))
        # return projects
        return rows # まずはタプルのリストとして返す
    except sqlite3.Error as e:
        print(f"Error fetching projects: {e}")
        return []
    finally:
        if conn:
            conn.close()
# database_operations.py に追記 (get_all_projects 関数の後など)
def get_project_by_id(project_id):
    """指定されたIDの案件情報をデータベースから取得する"""
    conn = create_connection()
    if not conn:
        return None # 接続エラー時は None を返す

    try:
        cur = conn.cursor()
        # get_all_projects と同様のカラムを取得
        sql = """
            SELECT 
                p.project_id, p.project_code, p.project_name, 
                p.customer_id, c.customer_name, 
                p.parent_project_id, pp.project_code as parent_project_code, 
                p.site_address, p.reception_date, p.start_date_scheduled, 
                p.completion_date_scheduled, p.actual_completion_date, 
                p.responsible_staff_name, p.estimated_amount, p.status, 
                p.remarks, p.created_at, p.updated_at
            FROM projects p
            LEFT JOIN customers c ON p.customer_id = c.customer_id
            LEFT JOIN projects pp ON p.parent_project_id = pp.project_id
            WHERE p.project_id = ?
        """
        cur.execute(sql, (project_id,))
        row = cur.fetchone() # 1件のデータを取得
        
        # カラム名も一緒に返すとGUIで扱いやすい場合があるため、辞書に変換する選択肢も提示
        # if row:
        #     columns = [desc[0] for desc in cur.description]
        #     return dict(zip(columns, row))
        # return None
        return row # まずはタプルとして返す
    except sqlite3.Error as e:
        print(f"Error fetching project by ID ({project_id}): {e}")
        return None
    finally:
        if conn:
            conn.close()
# database_operations.py に追記 (get_project_by_id 関数の後など)
def update_project(project_id, project_code, project_name, customer_id, parent_project_id,
                   site_address, reception_date, start_date_scheduled,
                   completion_date_scheduled, actual_completion_date,
                   responsible_staff_name, estimated_amount, status, remarks):
    """指定されたIDの案件情報を更新する"""
    conn = create_connection()
    if not conn:
        return "CONNECTION_ERROR"

    sql = ''' UPDATE projects
              SET project_code = ?,
                  project_name = ?,
                  customer_id = ?,
                  parent_project_id = ?,
                  site_address = ?,
                  reception_date = ?,
                  start_date_scheduled = ?,
                  completion_date_scheduled = ?,
                  actual_completion_date = ?,
                  responsible_staff_name = ?,
                  estimated_amount = ?,
                  status = ?,
                  remarks = ?,
                  updated_at = ?
              WHERE project_id = ? '''
    
    current_time = get_current_timestamp()
    try:
        cur = conn.cursor()
        cur.execute(sql, (project_code, project_name, customer_id, parent_project_id,
                         site_address, reception_date, start_date_scheduled,
                         completion_date_scheduled, actual_completion_date,
                         responsible_staff_name, estimated_amount, status, remarks,
                         current_time, project_id))
        conn.commit()
        if cur.rowcount == 0:
            print(f"Error updating project: Project ID {project_id} not found.")
            return "NOT_FOUND" # 更新対象が見つからなかった
        print(f"Project ID {project_id} updated successfully.")
        return True # 成功
    except sqlite3.IntegrityError as e:
        error_message_lower = str(e).lower()
        if "unique constraint failed: projects.project_code" in error_message_lower:
            print(f"Error updating project: Project code '{project_code}' already exists for another project.")
            return "DUPLICATE_CODE"
        elif "not null constraint failed" in error_message_lower:
             print(f"Error updating project: A required field was not provided. Details: {e}")
             return "NOT_NULL_VIOLATION"
        elif "foreign key constraint failed" in error_message_lower:
            print(f"Error updating project: Foreign key constraint failed (e.g., customer_id or parent_project_id does not exist). Details: {e}")
            return "FK_CONSTRAINT_FAILED"
        else:
            print(f"Error updating project (IntegrityError): {e}")
            return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error updating project ID {project_id}: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn:
            conn.close()
# database_operations.py に追記 (update_project 関数の後など)
def delete_project(project_id):
    """指定されたIDの案件情報を削除する"""
    conn = create_connection()
    if not conn:
        return "CONNECTION_ERROR"

    # projects テーブルの parent_project_id には ON DELETE RESTRICT が設定されています。
    # もし削除しようとしている案件が、他の案件の親案件として参照されている場合、
    # この削除処理は sqlite3.IntegrityError を発生させます。
    # これをキャッチしてユーザーに伝えることも可能です。

    sql = 'DELETE FROM projects WHERE project_id = ?'
    try:
        cur = conn.cursor()
        cur.execute(sql, (project_id,))
        conn.commit()
        if cur.rowcount == 0: # 削除された行が0の場合
            print(f"Error deleting project: Project ID {project_id} not found.")
            return "NOT_FOUND"
        print(f"Project ID {project_id} deleted successfully.")
        return True # 成功
    except sqlite3.IntegrityError as e:
        error_message_lower = str(e).lower()
        if "foreign key constraint failed" in error_message_lower or \
           "constraint failed" in error_message_lower: # RESTRICT による削除失敗も含む
            print(f"Error deleting project ID {project_id}: Integrity constraint violated. This project might be referenced by other data (e.g., as a parent project). Details: {e}")
            return "FK_CONSTRAINT_FAILED" # 外部キー制約違反（子案件が存在するなど）
        else:
            print(f"Error deleting project ID {project_id} (IntegrityError): {e}")
            return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error deleting project ID {project_id}: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn:
            conn.close()
# database_operations.py に追記
# --- 見積ヘッダー (Quotations) テーブル操作 ---
def add_quotation(project_id, quotation_staff_id, quotation_code, quotation_date, 
                  customer_name_at_quote, project_name_at_quote, site_address_at_quote,
                  construction_period_notes, total_amount_exclusive_tax, tax_rate, 
                  tax_amount, total_amount_inclusive_tax, validity_period_notes, 
                  payment_terms_notes, status, remarks):
    """新しい見積ヘッダーをデータベースに追加する"""
    conn = create_connection()
    if not conn:
        return "CONNECTION_ERROR"

    sql = """
        INSERT INTO quotations (
            project_id, quotation_staff_id, quotation_code, quotation_date, 
            customer_name_at_quote, project_name_at_quote, site_address_at_quote,
            construction_period_notes, total_amount_exclusive_tax, tax_rate, 
            tax_amount, total_amount_inclusive_tax, validity_period_notes, 
            payment_terms_notes, status, remarks, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """ # 18個のプレースホルダ
    
    current_time = get_current_timestamp()
    try:
        cur = conn.cursor()
        cur.execute(sql, (
            project_id, quotation_staff_id, quotation_code, quotation_date, 
            customer_name_at_quote, project_name_at_quote, site_address_at_quote,
            construction_period_notes, total_amount_exclusive_tax, tax_rate, 
            tax_amount, total_amount_inclusive_tax, validity_period_notes, 
            payment_terms_notes, status, remarks, current_time, current_time
        ))
        conn.commit()
        new_id = cur.lastrowid
        print(f"Quotation (Code: {quotation_code}) added successfully with ID: {new_id}")
        return new_id
    except sqlite3.IntegrityError as e:
        error_message_lower = str(e).lower()
        if "unique constraint failed: quotations.quotation_code" in error_message_lower:
            print(f"Error adding quotation: Quotation code '{quotation_code}' already exists.")
            return "DUPLICATE_QUOTATION_CODE"
        elif "not null constraint failed" in error_message_lower:
             print(f"Error adding quotation: A required field was not provided. Details: {e}")
             return "NOT_NULL_VIOLATION"
        elif "foreign key constraint failed" in error_message_lower:
            print(f"Error adding quotation: Foreign key constraint failed (e.g., project_id or quotation_staff_id). Details: {e}")
            return "FK_CONSTRAINT_FAILED"
        else:
            print(f"Error adding quotation (IntegrityError): {e}")
            return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error adding quotation: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn:
            conn.close()
# database_operations.py に追記 (add_quotation 関数の後など)
# database_operations.py の add_quotation_item 関数を修正
def add_quotation_item(quotation_id, name, specification, 
                       quantity, unit, unit_price, amount, remarks): # display_order を引数から削除
    """新しい見積明細をデータベースに追加する (表示順は自動採番)"""
    conn = create_connection()
    if not conn:
        return "CONNECTION_ERROR"

    try:
        cur = conn.cursor()

        # --- 表示順 (display_order) の自動採番ロジック ---
        cur.execute("SELECT MAX(display_order) FROM quotation_items WHERE quotation_id = ?", (quotation_id,))
        max_order = cur.fetchone()[0]
        current_display_order = (max_order if max_order is not None else 0) + 10 # 10刻みで採番 (または +1 でも可)
        # --- ここまで ---

        sql = """
            INSERT INTO quotation_items (
                quotation_id, display_order, name, specification, quantity, 
                unit, unit_price, amount, remarks, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
        """ 
        
        current_time = get_current_timestamp()
        cur.execute(sql, (
            quotation_id, current_display_order, name, specification, quantity, # current_display_order を使用
            unit, unit_price, amount, remarks, current_time, current_time
        ))
        conn.commit()
        new_item_id = cur.lastrowid
        print(f"Quotation item '{name}' for quotation_id {quotation_id} added successfully with item_id: {new_item_id}, display_order: {current_display_order}")
        return new_item_id
    except sqlite3.IntegrityError as e:
        # ... (エラー処理は変更なし) ...
        error_message_lower = str(e).lower()
        if "not null constraint failed" in error_message_lower:
             print(f"Error adding quotation item: A required field (like name or quotation_id) was not provided. Details: {e}")
             return "NOT_NULL_VIOLATION"
        elif "foreign key constraint failed" in error_message_lower: 
            print(f"Error adding quotation item: Foreign key constraint failed (quotation_id {quotation_id} does not exist). Details: {e}")
            return "FK_CONSTRAINT_FAILED"
        else:
            print(f"Error adding quotation item (IntegrityError): {e}")
            return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error adding quotation item: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn:
            conn.close()

def get_items_for_quotation(quotation_id):
    """指定された見積IDに紐づく全ての明細情報を取得する"""
    conn = create_connection()
    if not conn:
        return [] # 接続エラー時は空のリストを返す

    try:
        cur = conn.cursor()
        # 表示順 (display_order) でソートし、NULLの場合は最後に表示されるようにする
        # COALESCE(display_order, CAST('Infinity' AS REAL)) はSQLiteでNULLを最後にソートする一般的な方法の一つ
        # または、単純に ORDER BY display_order でNULLが先頭に来る(SQLiteのデフォルト)のを許容しても良い。
        sql = """
            SELECT 
                item_id, quotation_id, display_order, name, specification, 
                quantity, unit, unit_price, amount, remarks, 
                created_at, updated_at
            FROM quotation_items
            WHERE quotation_id = ?
            ORDER BY COALESCE(display_order, 999999), item_id 
        """
        # display_order が NULL の場合に大きな値として扱い、実質最後にソートされるようにする。
        # display_order が同じ場合は item_id でソート。
        cur.execute(sql, (quotation_id,))
        rows = cur.fetchall()
        return rows # タプルのリストとして返す
    except sqlite3.Error as e:
        print(f"Error fetching items for quotation ID ({quotation_id}): {e}")
        return []
    finally:
        if conn:
            conn.close()
# (この後、get_all_quotations, get_quotation_by_id, update_quotation, delete_quotation 関数や、
#  quotation_items テーブル用の関数も追加していきます)
# database_operations.py に追加 (例: get_items_for_quotation 関数の後など)

def get_quotation_item_by_id(item_id):
    """指定されたitem_idの明細データを取得し、辞書として返す"""
    conn = create_connection()
    if not conn:
        return None # 接続エラー時は None を返す

    # quotation_items テーブルの全てのカラムを取得する想定
    # display_order も含みます
    query = """
        SELECT 
            item_id, quotation_id, display_order, name, specification, 
            quantity, unit, unit_price, amount, remarks, 
            created_at, updated_at 
        FROM quotation_items 
        WHERE item_id = ?;
    """
    try:
        cur = conn.cursor()
        cur.execute(query, (item_id,))
        item_data_tuple = cur.fetchone() # 1件のデータをタプルとして取得
        
        if item_data_tuple:
            # カラム名（実際のテーブル定義に合わせてください）
            columns = [
                "item_id", "quotation_id", "display_order", "name", 
                "specification", "quantity", "unit", "unit_price", 
                "amount", "remarks", "created_at", "updated_at"
            ]
            item_data_dict = dict(zip(columns, item_data_tuple))
            return item_data_dict # 辞書として返す
        else:
            print(f"No quotation item found with item_id: {item_id}")
            return None # データが見つからない場合はNone
            
    except sqlite3.Error as e:
        print(f"Error getting quotation item by id {item_id}: {e}")
        return None # エラー時はNoneを返す
    finally:
        if conn:
            conn.close()

def get_all_quotations():
    """全ての見積ヘッダー情報をデータベースから取得する"""
    conn = create_connection()
    if not conn:
        return []

    try:
        cur = conn.cursor()
        sql = """
            SELECT 
                q.quotation_id, q.quotation_code, q.quotation_date,
                q.project_id, p.project_code AS original_project_code, p.project_name AS original_project_name,
                q.quotation_staff_id, e.full_name AS staff_name,
                q.customer_name_at_quote, q.project_name_at_quote,
                q.total_amount_inclusive_tax, q.status, q.validity_period_notes,
                q.updated_at
            FROM quotations q
            LEFT JOIN projects p ON q.project_id = p.project_id
            LEFT JOIN employees e ON q.quotation_staff_id = e.employee_id
            ORDER BY q.quotation_date DESC, q.quotation_code DESC
        """
        # 見積日、見積番号の降順でソート
        cur.execute(sql)
        rows = cur.fetchall()
        return rows
    except sqlite3.Error as e:
        print(f"Error fetching all quotations: {e}")
        return []
    finally:
        if conn:
            conn.close()
# database_operations.py に追記

def get_quotation_by_id(quotation_id):
    """指定されたIDの見積ヘッダー情報を取得する (明細は含まない)"""
    conn = create_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()
        sql = """
            SELECT 
                q.quotation_id, q.project_id, p.project_code AS original_project_code,
                q.quotation_staff_id, e.full_name AS staff_name,
                q.quotation_code, q.quotation_date, 
                q.customer_name_at_quote, q.project_name_at_quote, 
                q.site_address_at_quote, q.construction_period_notes, 
                q.total_amount_exclusive_tax, q.tax_rate, q.tax_amount, 
                q.total_amount_inclusive_tax, q.validity_period_notes, 
                q.payment_terms_notes, q.status, q.remarks,
                q.created_at, q.updated_at
            FROM quotations q
            LEFT JOIN projects p ON q.project_id = p.project_id
            LEFT JOIN employees e ON q.quotation_staff_id = e.employee_id
            WHERE q.quotation_id = ?
        """
        cur.execute(sql, (quotation_id,))
        row = cur.fetchone()
        return row 
    except sqlite3.Error as e:
        print(f"Error fetching quotation by ID ({quotation_id}): {e}")
        return None
    finally:
        if conn:
            conn.close()
# database_operations.py に追記 (get_quotation_by_id 関数の後など)

def update_quotation(quotation_id, project_id, quotation_staff_id, quotation_code, quotation_date,
                     customer_name_at_quote, project_name_at_quote, site_address_at_quote,
                     construction_period_notes, total_amount_exclusive_tax, tax_rate,
                     tax_amount, total_amount_inclusive_tax, validity_period_notes,
                     payment_terms_notes, status, remarks):
    """指定されたIDの見積ヘッダー情報を更新する"""
    conn = create_connection()
    if not conn:
        return "CONNECTION_ERROR"

    sql = """
        UPDATE quotations SET
            project_id = ?, quotation_staff_id = ?, quotation_code = ?, quotation_date = ?, 
            customer_name_at_quote = ?, project_name_at_quote = ?, site_address_at_quote = ?,
            construction_period_notes = ?, total_amount_exclusive_tax = ?, tax_rate = ?, 
            tax_amount = ?, total_amount_inclusive_tax = ?, validity_period_notes = ?, 
            payment_terms_notes = ?, status = ?, remarks = ?, updated_at = ?
        WHERE quotation_id = ?
    """ # 17個の更新フィールド + 1個のWHERE条件 = 18個のプレースホルダ
    
    current_time = get_current_timestamp()
    try:
        cur = conn.cursor()
        cur.execute(sql, (
            project_id, quotation_staff_id, quotation_code, quotation_date, 
            customer_name_at_quote, project_name_at_quote, site_address_at_quote,
            construction_period_notes, total_amount_exclusive_tax, tax_rate, 
            tax_amount, total_amount_inclusive_tax, validity_period_notes, 
            payment_terms_notes, status, remarks, current_time, 
            quotation_id # WHERE句のquotation_id
        ))
        conn.commit()
        if cur.rowcount == 0:
            print(f"Error updating quotation: Quotation ID {quotation_id} not found.")
            return "NOT_FOUND"
        print(f"Quotation ID {quotation_id} (Code: {quotation_code}) updated successfully.")
        return True
    except sqlite3.IntegrityError as e:
        error_message_lower = str(e).lower()
        if "unique constraint failed: quotations.quotation_code" in error_message_lower:
            print(f"Error updating quotation: Quotation code '{quotation_code}' already exists for another quotation.")
            return "DUPLICATE_QUOTATION_CODE"
        elif "not null constraint failed" in error_message_lower:
             print(f"Error updating quotation: A required field was not provided. Details: {e}")
             return "NOT_NULL_VIOLATION"
        elif "foreign key constraint failed" in error_message_lower:
            print(f"Error updating quotation: Foreign key constraint failed (e.g., project_id or quotation_staff_id is invalid). Details: {e}")
            return "FK_CONSTRAINT_FAILED"
        else:
            print(f"Error updating quotation (IntegrityError): {e}")
            return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error updating quotation ID {quotation_id}: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn:
            conn.close()
# database_operations.py に追記 (update_quotation 関数の後など)
# database_operations.py に追記 (update_quotation_item 関数の後など)

def delete_quotation_item(item_id):
    """指定されたIDの見積明細情報を削除する"""
    conn = create_connection()
    if not conn:
        return "CONNECTION_ERROR"

    sql = 'DELETE FROM quotation_items WHERE item_id = ?'
    try:
        cur = conn.cursor()
        cur.execute(sql, (item_id,))
        conn.commit()
        if cur.rowcount == 0: # 削除された行が0の場合
            print(f"Error deleting quotation item: Item ID {item_id} not found.")
            return "NOT_FOUND"
        print(f"Quotation item ID {item_id} deleted successfully.")
        return True # 成功
    except sqlite3.Error as e: # 他の予期せぬSQLiteエラー
        print(f"Error deleting quotation item ID {item_id}: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn:
            conn.close()
def delete_quotation(quotation_id):
    """指定されたIDの見積ヘッダー情報（とそれに関連する明細）を削除する"""
    conn = create_connection()
    if not conn:
        return "CONNECTION_ERROR"

    # projects テーブルへの quotation.project_id の外部キーは ON DELETE RESTRICT なので、
    # 見積もりを削除してもプロジェクトは影響を受けません。
    # quotation_items テーブルへの quotation_items.quotation_id の外部キーは ON DELETE CASCADE なので、
    # quotations レコードを削除すると、関連する quotation_items レコードも自動的に削除されます。

    sql = 'DELETE FROM quotations WHERE quotation_id = ?'
    try:
        cur = conn.cursor()
        cur.execute(sql, (quotation_id,))
        conn.commit()
        if cur.rowcount == 0: # 削除された行が0の場合
            print(f"Error deleting quotation: Quotation ID {quotation_id} not found.")
            return "NOT_FOUND"
        print(f"Quotation ID {quotation_id} and its items deleted successfully.")
        return True # 成功
    except sqlite3.IntegrityError as e:
        # 通常、quotationsの削除でIntegrityErrorが出るのは、
        # 他のテーブルからこのquotationが参照されていて、それがRESTRICTされている場合などですが、
        # 現在のスキーマでは考えにくいです。
        print(f"Error deleting quotation ID {quotation_id} (IntegrityError): {e}")
        return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error deleting quotation ID {quotation_id}: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn:
            conn.close()
# database_operations.py に追記

def update_quotation_item(item_id, display_order, name, specification, 
                          quantity, unit, unit_price, amount, remarks):
    """指定されたIDの見積明細情報を更新する"""
    conn = create_connection()
    if not conn:
        return "CONNECTION_ERROR"

    # quotation_id は通常、明細の更新時には変更しません。
    # もし変更する場合は、引数に追加し、SQL文も修正する必要があります。
    sql = """
        UPDATE quotation_items SET
            display_order = ?, name = ?, specification = ?, quantity = ?, 
            unit = ?, unit_price = ?, amount = ?, remarks = ?, updated_at = ?
        WHERE item_id = ? 
    """ # 9個の更新フィールド + 1個のWHERE条件 = 10個のプレースホルダ
    
    current_time = get_current_timestamp()
    try:
        cur = conn.cursor()
        cur.execute(sql, (
            display_order, name, specification, quantity, 
            unit, unit_price, amount, remarks, current_time,
            item_id # WHERE句のitem_id
        ))
        conn.commit()
        if cur.rowcount == 0:
            print(f"Error updating quotation item: Item ID {item_id} not found.")
            return "NOT_FOUND"
        print(f"Quotation item ID {item_id} ('{name}') updated successfully.")
        return True
    except sqlite3.IntegrityError as e:
        error_message_lower = str(e).lower()
        if "not null constraint failed" in error_message_lower:
             print(f"Error updating quotation item: A required field (like name) was not provided. Details: {e}")
             return "NOT_NULL_VIOLATION"
        # 他のIntegrityError (例えば、もしquotation_idを更新対象にしていてFK違反が起きた場合など)
        else:
            print(f"Error updating quotation item (IntegrityError): {e}")
            return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error updating quotation item ID {item_id}: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn:
            conn.close()







if __name__ == '__main__':
    # このファイルが直接実行されたときのテストコード
    print("Running database operations tests...")

    # データベースファイルとテーブルがまだない場合は、先に database_setup.py を実行してください。
    # from database_setup import setup_database
    # print("Running initial database setup...")
    # setup_database() # 初回のみ、またはDB構造変更時

    # 新しい顧客を追加
    new_customer_id = add_customer(
        customer_name="株式会社テスト商事",
        contact_person_name="試験 太郎",
        phone_number="03-1234-5678",
        email="test@example.com",
        address="東京都試験区試験1-2-3",
        notes="初回テスト顧客"
    )
    if new_customer_id:
        add_customer(
            customer_name="有限会社サンプル建設",
            contact_person_name="見本 次郎",
            phone_number="06-9876-5432",
            email="sample@example.co.jp",
            address="大阪府見本市見本町4-5-6",
            notes="サンプルデータ"
        )

    # 全ての顧客を取得して表示
    print("\nAll customers:")
    customers = get_all_customers()
    if customers:
        for customer_tuple in customers:
            print(customer_tuple) # タプルのまま表示
    else:
        print("No customers found or error fetching.")

    # 特定の顧客を更新 (IDが1の顧客が存在する場合)
    if new_customer_id: # 最初に追加した顧客のIDを使う
        print(f"\nUpdating customer ID {new_customer_id}...")
        success = update_customer(
            customer_id=new_customer_id,
            customer_name="株式会社テスト商事（更新済）",
            contact_person_name="試験 太郎",
            phone_number="03-1111-2222",
            email="test-updated@example.com",
            address="東京都試験区試験1-2-3 試験ビル5F",
            notes="情報を更新しました。"
        )
        if success:
            updated_customer = get_customer_by_id(new_customer_id)
            print("Updated customer data:", updated_customer)

    # 特定の顧客を削除 (IDが2の顧客が存在する場合。IDは環境によって変わるので注意)
    # テスト実行の際は、実際に存在するIDを指定するか、削除処理をコメントアウトしてください。
    # customers_for_delete_test = get_all_customers()
    # if len(customers_for_delete_test) > 1:
    #    last_customer_id = customers_for_delete_test[-1][0] # 最後の顧客のIDを取得
    #    print(f"\nDeleting customer ID {last_customer_id}...")
    #    delete_customer(last_customer_id)
    #    print("\nAll customers after deletion:")
    #    customers_after_delete = get_all_customers()
    #    for cust_tuple in customers_after_delete:
    #        print(cust_tuple)

    # database_operations.py に追記
    # database_operations.py の if __name__ == '__main__': ブロックの最後に追記

    print("\n--- Testing Project Operations ---")

    # 有効な customer_id を準備してください (例: 1)。
    # もし顧客データがなければ、先に顧客登録テストを実行してください。
    valid_customer_id = 1 # 仮。実際のDBに存在するIDに置き換えるか、顧客登録テストを先に実行

    # 最初の案件を追加
    print("\nAdding first project...")
    project_id_1 = add_project(
        project_code="P2025-001",
        project_name="山田様邸 外壁塗装工事",
        customer_id=valid_customer_id, # 存在する顧客IDを指定
        parent_project_id=None, # 親案件なし
        site_address="東京都〇〇区△△1-2-3",
        reception_date="2025-05-17",
        start_date_scheduled="2025-06-01",
        completion_date_scheduled="2025-06-30",
        actual_completion_date=None,
        responsible_staff_name="佐藤一郎",
        estimated_amount=1200000,
        status="見積提出済",
        remarks="特記事項なし"
    )
    print(f"Result of adding first project: {project_id_1}")

    # 同じ案件コードで再度追加 (重複エラーのテスト)
    if isinstance(project_id_1, int): # 最初の案件追加が成功した場合のみ実行
        print("\nAdding project with duplicate project_code (P2025-001)...")
        duplicate_result = add_project(
            project_code="P2025-001", # ★同じ案件コード
            project_name="鈴木様邸 屋根修繕（重複テスト）",
            customer_id=valid_customer_id,
            parent_project_id=None,
            site_address="神奈川県〇〇市...",
            reception_date="2025-05-18",
            start_date_scheduled="2025-06-10",
            completion_date_scheduled="2025-06-20",
            actual_completion_date=None,
            responsible_staff_name="田中次郎",
            estimated_amount=800000,
            status="見積中",
            remarks="案件コード重複テスト"
        )
        print(f"Result of adding duplicate project: {duplicate_result}") # "DUPLICATE_CODE" が返るはず

    # 必須項目（project_code）なしで追加（NOT NULL制約違反テスト）
    print("\nAdding project with no project_code...")
    missing_code_result = add_project(
        project_code=None, # ★案件コードなし
        project_name="高橋様邸 内装工事（コードなしテスト）",
        customer_id=valid_customer_id,
        parent_project_id=None,
        site_address="埼玉県〇〇市...",
        reception_date="2025-05-19",
        start_date_scheduled="2025-07-01",
        completion_date_scheduled="2025-07-15",
        actual_completion_date=None,
        responsible_staff_name="渡辺三郎",
        estimated_amount=500000,
        status="見積依頼",
        remarks="コードなしテスト"
    )
    print(f"Result of adding project with missing code: {missing_code_result}") # "NOT_NULL_VIOLATION" が返るはず
    # database_operations.py の if __name__ == '__main__': ブロックの最後に追記

    print("\nGetting all projects...")
    all_projects = get_all_projects()
    if all_projects:
        print(f"Found {len(all_projects)} project(s):")
        for project_tuple in all_projects:
            print(project_tuple)
    else:
        print("No projects found or error fetching projects.")
    # database_operations.py の if __name__ == '__main__': ブロックの最後に追記

    print("\nGetting project by ID (e.g., ID 1)...")
    # project_id_1 が整数IDで取得できているか、または固定のIDでテスト
    # 今回のログでは project_id_1 が "DUPLICATE_CODE" になっている可能性があるため、
    # 確実に存在するID (例: 1) でテストします。
    # データベースに ID=1 の案件が確実に存在することを前提とします。
    test_project_id = 1 
    project_detail = get_project_by_id(test_project_id)
    if project_detail:
        print(f"Details for project ID {test_project_id}:")
        print(project_detail)
    else:
        print(f"Project ID {test_project_id} not found or error fetching project details.")

    print("\nGetting project by non-existent ID (e.g., ID 999)...")
    non_existent_project = get_project_by_id(999) # 存在しないID
    if non_existent_project:
        print("Error: Found a project that should not exist:")
        print(non_existent_project)
    else:
        print("Correctly found no project for non-existent ID 999 (or error occurred).")
    # database_operations.py の if __name__ == '__main__': ブロックの最後に追記

    print("\n--- Testing Project Update ---")
    # project_id = 1 の案件を更新するテスト
    # 事前に project_id = 1 の案件が存在することを前提とします。
    # また、project_id = 2 の案件が存在しないこと、または異なる project_code を持つことを前提とします（重複コードテストのため）。
    
    project_to_update_id = 1
    original_project = get_project_by_id(project_to_update_id)

    if original_project:
        print(f"Original project data (ID: {project_to_update_id}): {original_project}")
        
        # 1. 通常の更新テスト
        print(f"\nUpdating project ID {project_to_update_id} (normal update)...")
        update_success = update_project(
            project_id=project_to_update_id,
            project_code=original_project[1], # project_code は変更しない
            project_name=original_project[2] + " (更新テスト)", # 案件名を変更
            customer_id=original_project[3], # customer_id は変更しない
            parent_project_id=original_project[5], # parent_project_id は変更しない
            site_address=original_project[7] + " 更新後住所", # 現場住所を変更
            reception_date=original_project[8],
            start_date_scheduled=original_project[9],
            completion_date_scheduled=original_project[10],
            actual_completion_date="2025-07-01", # 実際の完了日をセット
            responsible_staff_name="新しい担当者", # 担当者を変更
            estimated_amount=original_project[13] + 10000, # 見積金額を変更
            status="施工中", # ステータスを変更
            remarks=original_project[15] + " 更新備考。" # 備考を追記
        )
        print(f"Update result: {update_success}")
        if update_success is True:
            updated_project_data = get_project_by_id(project_to_update_id)
            print(f"Updated project data (ID: {project_to_update_id}): {updated_project_data}")

        # 2. 案件コードを、既に存在する別の案件コードに変更しようとするテスト (重複エラー)
        #    そのためには、別の案件コード(例: P2025-002)を事前に登録しておく必要があります。
        #    ここでは P2025-001 を P2025-001 のまま更新するので、このテストはスキップするか、
        #    事前に P2025-002 を持つ案件を作成し、P2025-001 を P2025-002 に変えようとするテストにします。
        #    今回は、このテストを簡単にするため、あえて別の案件を作成してそのコードを使ってみます。
        
        print("\nAttempting to update project ID {project_to_update_id} to a duplicate project_code...")
        # まず、重複させるための別の案件コードを持つ案件を一時的に作成 (もしなければ)
        temp_project_code_for_dup_test = "P-DUP-TEST"
        existing_dup_project = False
        all_projs_for_test = get_all_projects()
        for proj in all_projs_for_test:
            if proj[1] == temp_project_code_for_dup_test:
                existing_dup_project = True
                break
        if not existing_dup_project:
             add_project(temp_project_code_for_dup_test, "重複テスト用仮案件", original_project[3], None, "仮住所", "2025-01-01", "2025-01-01", "2025-01-01", None, "仮担当", 1000, "仮", "仮備考")

        # project_id_1 (P2025-001) の project_code を temp_project_code_for_dup_test に変えようとしてみる
        # (ただし、original_project[1] が P2025-001 である必要あり)
        if original_project[1] != temp_project_code_for_dup_test : # 更新対象のコードが重複テスト用コードと異なる場合のみ実行
            update_dup_code_result = update_project(
                project_id=project_to_update_id,
                project_code=temp_project_code_for_dup_test, # ★重複する可能性のあるコードに更新
                project_name=original_project[2],
                customer_id=original_project[3],
                parent_project_id=original_project[5],
                site_address=original_project[7],
                reception_date=original_project[8],
                start_date_scheduled=original_project[9],
                completion_date_scheduled=original_project[10],
                actual_completion_date=original_project[11],
                responsible_staff_name=original_project[12],
                estimated_amount=original_project[13],
                status=original_project[14],
                remarks=original_project[15]
            )
            print(f"Result of updating to duplicate project_code: {update_dup_code_result}") # "DUPLICATE_CODE" になるはず
            # テスト後は元のコードに戻しておく（任意）
            if update_dup_code_result == "DUPLICATE_CODE" and original_project[1] != temp_project_code_for_dup_test:
                 update_project(project_to_update_id, original_project[1], original_project[2], original_project[3], original_project[5], original_project[7], original_project[8], original_project[9], original_project[10], original_project[11], original_project[12], original_project[13], original_project[14], original_project[15])
        else:
            print(f"Skipping duplicate project_code update test as original code is already {temp_project_code_for_dup_test} or no other project exists to create conflict.")

    else:
        print(f"Project ID {project_to_update_id} not found, skipping update tests.")
    # database_operations.py の if __name__ == '__main__': ブロックの最後に追記

    print("\n--- Testing Project Delete ---")
    # 削除テスト用の案件を一時的に追加
    print("Adding a temporary project for delete test...")
    temp_delete_project_id = add_project(
        project_code="P-DEL-TEST",
        project_name="削除テスト用案件",
        customer_id=1, # 存在する顧客IDを指定
        parent_project_id=None,
        site_address="削除テスト住所",
        reception_date="2025-01-01",
        start_date_scheduled="2025-01-01",
        completion_date_scheduled="2025-01-01",
        actual_completion_date=None,
        responsible_staff_name="削除テスト担当",
        estimated_amount=1000,
        status="仮",
        remarks="この案件はテスト後に削除されます"
    )

    if isinstance(temp_delete_project_id, int):
        print(f"Temporary project added with ID: {temp_delete_project_id}")
        
        # 削除処理の実行
        print(f"\nDeleting project ID {temp_delete_project_id}...")
        delete_result = delete_project(temp_delete_project_id)
        print(f"Delete result: {delete_result}")

        if delete_result is True:
            print(f"Verifying project ID {temp_delete_project_id} is deleted...")
            deleted_project_check = get_project_by_id(temp_delete_project_id)
            if deleted_project_check is None:
                print(f"Project ID {temp_delete_project_id} successfully deleted and not found.")
            else:
                print(f"Error: Project ID {temp_delete_project_id} was found after deletion attempt.")
        
        # 存在しないIDの削除テスト
        print("\nAttempting to delete non-existent project ID 999...")
        delete_non_existent_result = delete_project(999)
        print(f"Result of deleting non-existent project: {delete_non_existent_result}") # "NOT_FOUND" になるはず

        # (オプション) 親案件として参照されている案件の削除テスト
        # これをテストするには、まず親案件P-PARENTと、その子案件P-CHILDを作成し、
        # P-PARENTを削除しようとして FK_CONSTRAINT_FAILED が返るか確認します。
        # print("\nTesting deletion of a project that is a parent...")
        # parent_id_for_test = add_project("P-PARENT", "親案件テスト", 1, None, "親住所", "2025-01-01", "2025-01-01", "2025-01-01", None, "親担当", 1000, "仮", "親")
        # if isinstance(parent_id_for_test, int):
        #     child_id_for_test = add_project("P-CHILD", "子案件テスト", 1, parent_id_for_test, "子住所", "2025-01-01", "2025-01-01", "2025-01-01", None, "子担当", 500, "仮", "子")
        #     if isinstance(child_id_for_test, int):
        #         delete_parent_result = delete_project(parent_id_for_test)
        #         print(f"Result of deleting parent project ID {parent_id_for_test}: {delete_parent_result}") # "FK_CONSTRAINT_FAILED" になるはず
        #         # テスト用の子案件と親案件を個別に削除（子から先に）
        #         delete_project(child_id_for_test)
        #         delete_project(parent_id_for_test) # 今度は成功するはず
    else:
        print(f"Could not add temporary project for delete test. Result: {temp_delete_project_id}")
# database_operations.py の if __name__ == '__main__': ブロックの最後に追記

    print("\n--- Testing Employee Operations ---")

    # 最初の社員を追加
    print("\nAdding first employee...")
    emp_id_1 = add_employee(
        employee_code="EMP001",
        full_name="社員 一郎",
        name_kana="シャイン イチロウ",
        ccus_id="12345678901234", # 14桁
        date_of_birth="1980-04-01",
        gender="男性",
        position="部長",
        address="東京都本社1-1",
        phone_number="090-1111-1111",
        job_title="塗装工",
        employment_date="2000-04-01",
        experience_years_trade=20.5,
        emergency_contact_name="社員 花子",
        emergency_contact_phone="080-1111-1112",
        emergency_contact_relationship="妻",
        last_health_check_date="2025-04-10",
        blood_type="A型",
        social_insurance_status_notes="健康保険、厚生年金、雇用保険加入",
        retirement_allowance_notes="建退共加入",
        qualifications_notes="一級塗装技能士",
        paid_leave_days_notes="残り10日",
        is_active=True, # True または 1
        remarks="リーダー"
    )
    print(f"Result of adding first employee: {emp_id_1}")

    # 重複する社員コードで追加 (エラーテスト)
    if isinstance(emp_id_1, int): # 最初の社員追加が成功した場合
        print("\nAdding employee with duplicate employee_code (EMP001)...")
        dup_emp_code_result = add_employee(
            employee_code="EMP001", # ★同じ社員コード
            full_name="社員 二郎（重複コード）", name_kana="シャイン ジロウ", ccus_id="98765432109876",
            date_of_birth="1985-05-05", gender="男性", position="課長", address="東京都支社2-2",
            phone_number="090-2222-2222", job_title="営業", employment_date="2005-04-01",
            experience_years_trade=15.0, emergency_contact_name="社員 良子",
            emergency_contact_phone="080-2222-2223", emergency_contact_relationship="妻",
            last_health_check_date="2025-03-15", blood_type="B型",
            social_insurance_status_notes="加入", retirement_allowance_notes="未加入",
            qualifications_notes="宅建", paid_leave_days_notes="残り5日",
            is_active=True, remarks="コード重複テスト"
        )
        print(f"Result of adding employee with duplicate employee_code: {dup_emp_code_result}")

    # 重複するCCUS IDで追加 (エラーテスト)
    if isinstance(emp_id_1, int):
        print("\nAdding employee with duplicate CCUS ID (12345678901234)...")
        dup_ccus_result = add_employee(
            employee_code="EMP003", full_name="社員 三郎（重複CCUS）", name_kana="シャイン サブロウ",
            ccus_id="12345678901234", # ★同じCCUS ID
            date_of_birth="1990-06-06", gender="男性", position="主任", address="東京都現場3-3",
            phone_number="090-3333-3333", job_title="現場監督", employment_date="2010-04-01",
            experience_years_trade=10.0, emergency_contact_name="社員 愛子",
            emergency_contact_phone="080-3333-3334", emergency_contact_relationship="妻",
            last_health_check_date="2025-02-20", blood_type="O型",
            social_insurance_status_notes="完備", retirement_allowance_notes="加入",
            qualifications_notes="1級施工管理技士", paid_leave_days_notes="残り12日",
            is_active=True, remarks="CCUS ID重複テスト"
        )
        print(f"Result of adding employee with duplicate CCUS ID: {dup_ccus_result}")

    # 必須項目（full_name）なしで追加（NOT NULL制約違反テスト）
    print("\nAdding employee with no full_name...")
    missing_name_result = add_employee(
        employee_code="EMP004", full_name=None, name_kana="ナシ", ccus_id="11223344556677", # ★氏名なし
        date_of_birth="1995-07-07", gender="女性", position="一般", address="東京都仮住まい4-4",
        phone_number="090-4444-4444", job_title="事務", employment_date="2015-04-01",
        experience_years_trade=5.0, emergency_contact_name="社員 博",
        emergency_contact_phone="080-4444-4445", emergency_contact_relationship="夫",
        last_health_check_date="2025-01-25", blood_type="AB型",
        social_insurance_status_notes="一部加入", retirement_allowance_notes="検討中",
        qualifications_notes="簿記2級", paid_leave_days_notes="残り7日",
        is_active=False, remarks="氏名なしテスト"
    )
    print(f"Result of adding employee with missing full_name: {missing_name_result}")
# database_operations.py の if __name__ == '__main__': ブロックの最後に追記

    print("\nGetting all employees...")
    all_employees = get_all_employees()
    if all_employees:
        print(f"Found {len(all_employees)} employee(s):")
        for emp_tuple in all_employees:
            print(emp_tuple)
    else:
        print("No employees found or error fetching employees.")
# database_operations.py の if __name__ == '__main__': ブロックの最後に追記

    print("\nGetting employee by ID (e.g., ID 1)...")
    # データベースに ID=1 の社員が確実に存在することを前提とします。
    test_employee_id = 1 
    employee_detail = get_employee_by_id(test_employee_id)
    if employee_detail:
        print(f"Details for employee ID {test_employee_id}:")
        print(employee_detail)
    else:
        print(f"Employee ID {test_employee_id} not found or error fetching employee details.")

    print("\nGetting employee by non-existent ID (e.g., ID 999)...")
    non_existent_employee = get_employee_by_id(999) # 存在しないID
    if non_existent_employee:
        print("Error: Found an employee that should not exist:")
        print(non_existent_employee)
    else:
        print("Correctly found no employee for non-existent ID 999 (or error occurred).")
# database_operations.py の if __name__ == '__main__': ブロックの最後に追記

    print("\n--- Testing Employee Update ---")
    # employee_id = 1 の社員を更新するテスト
    # 事前に employee_id = 1 の社員が存在することを前提とします。
    
    emp_to_update_id = 1
    original_emp = get_employee_by_id(emp_to_update_id)

    if original_emp:
        print(f"Original employee data (ID: {emp_to_update_id}): {original_emp}")
        
        # 1. 通常の更新テスト (役職と備考を変更)
        print(f"\nUpdating employee ID {emp_to_update_id} (normal update)...")
        update_success_1 = update_employee(
            employee_id=emp_to_update_id,
            employee_code=original_emp[1], # employee_code は変更しない
            full_name=original_emp[2],     # full_name は変更しない
            name_kana=original_emp[3],
            ccus_id=original_emp[4],       # ccus_id は変更しない
            date_of_birth=original_emp[5],
            gender=original_emp[6],
            position="シニアマネージャー", # 役職を変更
            address=original_emp[8],
            phone_number=original_emp[9],
            job_title=original_emp[10],
            employment_date=original_emp[11],
            experience_years_trade=original_emp[12],
            emergency_contact_name=original_emp[13],
            emergency_contact_phone=original_emp[14],
            emergency_contact_relationship=original_emp[15],
            last_health_check_date=original_emp[16],
            blood_type=original_emp[17],
            social_insurance_status_notes=original_emp[18],
            retirement_allowance_notes=original_emp[19],
            qualifications_notes=original_emp[20],
            paid_leave_days_notes=original_emp[21],
            is_active=original_emp[22],
            remarks="役職変更のテスト更新。" # 備考を変更
        )
        print(f"Update result 1: {update_success_1}")
        if update_success_1 is True:
            updated_emp_data_1 = get_employee_by_id(emp_to_update_id)
            print(f"Updated employee data 1 (ID: {emp_to_update_id}): {updated_emp_data_1}")

        # 2. 別の社員を作成して、その社員コードに更新しようとするテスト (重複エラー)
        print("\nAttempting to update employee ID {emp_to_update_id} to a duplicate employee_code...")
        # まず、重複させるための別の社員コードを持つ社員を一時的に作成 (もしなければ)
        temp_emp_code_for_dup_test = "EMP-DUP"
        add_employee(temp_emp_code_for_dup_test, "重複テスト用社員", "カブリ テスト", "00000000000000", "2000-01-01", "不明", "テスト", "仮住所", "000", "テスト職", "2000-01-01", 1, "","","", "", "", "", "", "", "", True, "")

        update_dup_code_result = update_employee(
            employee_id=emp_to_update_id,
            employee_code=temp_emp_code_for_dup_test, # ★重複する可能性のある社員コードに更新
            full_name=original_emp[2], name_kana=original_emp[3], ccus_id=original_emp[4],
            date_of_birth=original_emp[5], gender=original_emp[6], position=original_emp[7],
            address=original_emp[8], phone_number=original_emp[9], job_title=original_emp[10],
            employment_date=original_emp[11], experience_years_trade=original_emp[12],
            emergency_contact_name=original_emp[13], emergency_contact_phone=original_emp[14],
            emergency_contact_relationship=original_emp[15], last_health_check_date=original_emp[16],
            blood_type=original_emp[17], social_insurance_status_notes=original_emp[18],
            retirement_allowance_notes=original_emp[19], qualifications_notes=original_emp[20],
            paid_leave_days_notes=original_emp[21], is_active=original_emp[22], remarks=original_emp[24]
        )
        print(f"Result of updating to duplicate employee_code: {update_dup_code_result}") # "DUPLICATE_EMP_CODE" になるはず
        
        # テスト用に作成した EMP-DUP を削除 (任意)
        # delete_employee_by_code(temp_emp_code_for_dup_test) # (delete_employee_by_code は未作成)
        # または、IDが分かれば delete_employee(id)
        # 今回はテストなので、手動でDB Browserから消すか、DB再作成で対応でもOK

    else:
        print(f"Employee ID {emp_to_update_id} not found, skipping update tests.")
# database_operations.py の if __name__ == '__main__': ブロックの最後に追記

    print("\n--- Testing Employee Delete ---")
    # 削除テスト用の社員を一時的に追加
    print("Adding a temporary employee for delete test...")
    temp_del_emp_code = "EMP-DEL-TEST"
    temp_del_ccus_id = "99999999999999" # 他と重複しない一時的なCCUS ID
    
    # 既存の社員とコードやCCUS IDが重複しないように注意
    # 先に同じコードやCCUS IDの社員がいないか確認する方がより安全ですが、テストなので進めます。
    # もしこの追加でエラーが出る場合、上記のコードやCCUS IDが既存のデータと重複している可能性があります。
    # その場合は、temp_del_emp_code や temp_del_ccus_id の値を変更してください。
    
    temp_delete_emp_id = add_employee(
        employee_code=temp_del_emp_code,
        full_name="削除テスト 太郎", name_kana="サクジョテスト タロウ", ccus_id=temp_del_ccus_id,
        date_of_birth="1999-12-31", gender="男性", position="短期", address="一時的住所",
        phone_number="000-0000-0000", job_title="テスト要員", employment_date="2025-01-01",
        experience_years_trade=1, emergency_contact_name="緊急連絡なし",
        emergency_contact_phone="", emergency_contact_relationship="",
        last_health_check_date="2025-01-01", blood_type="不明",
        social_insurance_status_notes="テスト用", retirement_allowance_notes="なし",
        qualifications_notes="なし", paid_leave_days_notes="0",
        is_active=True, remarks="この社員はテスト後に削除されます"
    )

    if isinstance(temp_delete_emp_id, int): # 社員追加が成功した場合のみ実行
        print(f"Temporary employee for delete test added with ID: {temp_delete_emp_id}")
        
        # 削除処理の実行
        print(f"\nDeleting employee ID {temp_delete_emp_id}...")
        delete_result = delete_employee(temp_delete_emp_id)
        print(f"Delete result: {delete_result}")

        if delete_result is True:
            print(f"Verifying employee ID {temp_delete_emp_id} is deleted...")
            deleted_employee_check = get_employee_by_id(temp_delete_emp_id)
            if deleted_employee_check is None:
                print(f"Employee ID {temp_delete_emp_id} successfully deleted and not found.")
            else:
                print(f"Error: Employee ID {temp_delete_emp_id} was found after deletion attempt.")
        
        # 存在しないIDの削除テスト
        print("\nAttempting to delete non-existent employee ID 888...")
        delete_non_existent_result = delete_employee(888) # 存在しないであろうID
        print(f"Result of deleting non-existent employee: {delete_non_existent_result}") # "NOT_FOUND" になるはず
    elif temp_delete_emp_id in ["DUPLICATE_EMP_CODE", "DUPLICATE_CCUS_ID"]:
        print(f"Could not add temporary employee for delete test due to duplicate data: {temp_delete_emp_id}")
        print("Please ensure 'EMP-DEL-TEST' and CCUS ID '99999999999999' are not already in use, or clear DB and re-run.")
    else:
        print(f"Could not add temporary employee for delete test. Add result: {temp_delete_emp_id}")
# database_operations.py の if __name__ == '__main__': ブロックの最後に追記

    print("\n--- Testing Quotation Operations ---")

    # 有効な project_id と employee_id を準備してください
    # これまでのテストで ID=1 のプロジェクトと社員が作成されていることを期待
    valid_project_id = 1 
    valid_employee_id = 1 

    # 1. 最初の見積ヘッダーを追加
    print("\nAdding first quotation...")
    quotation_id_1 = add_quotation(
        project_id=valid_project_id,
        quotation_staff_id=valid_employee_id,
        quotation_code="Q2025-P001-01",
        quotation_date="2025-05-18",
        customer_name_at_quote="髙惣建設株式会社 (見積時)", # get_customer_by_id などで取得しても良い
        project_name_at_quote="山田様邸 外壁塗装工事 (見積)", # get_project_by_id などで取得しても良い
        site_address_at_quote="東京都〇〇区△△1-2-3 (見積時)",
        construction_period_notes="契約後 約1ヶ月",
        total_amount_exclusive_tax=1100000, # 税抜合計 (明細がないので仮の値)
        tax_rate=0.10,
        tax_amount=110000, # 消費税額 (仮)
        total_amount_inclusive_tax=1210000, # 税込合計 (仮)
        validity_period_notes="見積提出後30日間",
        payment_terms_notes="完了後現金払い",
        status="作成中",
        remarks="初期見積"
    )
    print(f"Result of adding first quotation: {quotation_id_1}")

    # 2. 同じ見積番号で再度追加 (重複エラーのテスト)
    if isinstance(quotation_id_1, int): # 最初の見積追加が成功した場合のみ実行
        print("\nAdding quotation with duplicate quotation_code (Q2025-P001-01)...")
        duplicate_q_result = add_quotation(
            project_id=valid_project_id, quotation_staff_id=valid_employee_id,
            quotation_code="Q2025-P001-01", quotation_date="2025-05-19", # ★同じ見積番号
            customer_name_at_quote="顧客A", project_name_at_quote="案件B",
            site_address_at_quote="住所B", construction_period_notes="工期B",
            total_amount_exclusive_tax=500000, tax_rate=0.1, tax_amount=50000,
            total_amount_inclusive_tax=550000, validity_period_notes="有効期限B",
            payment_terms_notes="支払条件B", status="作成中", remarks="見積番号重複テスト"
        )
        print(f"Result of adding duplicate quotation: {duplicate_q_result}") # "DUPLICATE_QUOTATION_CODE" を期待

    # 3. 必須項目（例: quotation_code）なしで追加（NOT NULL制約違反テスト）
    print("\nAdding quotation with no quotation_code...")
    missing_code_q_result = add_quotation(
        project_id=valid_project_id, quotation_staff_id=valid_employee_id,
        quotation_code=None, quotation_date="2025-05-20", # ★見積番号なし
        customer_name_at_quote="顧客C", project_name_at_quote="案件C",
        site_address_at_quote="住所C", construction_period_notes="工期C",
        total_amount_exclusive_tax=200000, tax_rate=0.1, tax_amount=20000,
        total_amount_inclusive_tax=220000, validity_period_notes="有効期限C",
        payment_terms_notes="支払条件C", status="作成中", remarks="見積番号なしテスト"
    )
    print(f"Result of adding quotation with missing code: {missing_code_q_result}") # "NOT_NULL_VIOLATION" を期待

    # 4. 存在しない project_id で追加 (外部キー制約違反テスト)
    print("\nAdding quotation with non-existent project_id (999)...")
    fk_error_q_result = add_quotation(
        project_id=999, quotation_staff_id=valid_employee_id, # ★存在しない project_id
        quotation_code="Q-FK-ERROR", quotation_date="2025-05-21",
        customer_name_at_quote="顧客D", project_name_at_quote="案件D",
        site_address_at_quote="住所D", construction_period_notes="工期D",
        total_amount_exclusive_tax=300000, tax_rate=0.1, tax_amount=30000,
        total_amount_inclusive_tax=330000, validity_period_notes="有効期限D",
        payment_terms_notes="支払条件D", status="作成中", remarks="外部キーエラーテスト"
    )
    print(f"Result of adding quotation with FK error: {fk_error_q_result}") # "FK_CONSTRAINT_FAILED" を期待
# database_operations.py の if __name__ == '__main__': ブロックの最後に追記

    print("\n--- Testing Quotation Item Operations ---")

    # add_quotation のテストで quotation_id_1 が整数で取得できているか確認
    # もし quotation_id_1 がエラー文字列の場合は、固定のID (例: 1) を使用
    # このテストの前に、ID=1 の見積ヘッダーが存在することを前提とします。
    test_quotation_id = 1 
    # if isinstance(quotation_id_1, int):
    #     test_quotation_id = quotation_id_1
    # else:
    #     # データベースにID=1の見積もりが存在すると仮定
    #     print(f"Warning: quotation_id_1 was not a valid ID ({quotation_id_1}). Using hardcoded ID {test_quotation_id} for item tests.")
    #     # (必要であれば、ここで get_quotation_by_code などでIDを再取得するロジックも考えられる)

    # 1. 見積明細を追加 (明細1)
    print(f"\nAdding first item to quotation ID {test_quotation_id}...")
    item_id_1 = add_quotation_item(
        quotation_id=test_quotation_id,
        display_order=10,
        name="外壁シリコン塗装",
        specification="下塗り・中塗り・上塗り含む、SK化研クリーンマイルドシリコン使用",
        quantity=120.5,
        unit="m²",
        unit_price=2500,
        amount=int(120.5 * 2500), # アプリケーション側で計算・丸め想定
        remarks="足場代別途"
    )
    print(f"Result of adding first item: {item_id_1}")

    # 2. 見積明細を追加 (明細2)
    if isinstance(item_id_1, int): # 最初の明細追加が成功した場合
        print(f"\nAdding second item to quotation ID {test_quotation_id}...")
        item_id_2 = add_quotation_item(
            quotation_id=test_quotation_id,
            display_order=20,
            name="屋根遮熱塗装",
            specification="日本ペイント サーモアイSi使用",
            quantity=80.0,
            unit="m²",
            unit_price=3000,
            amount=int(80.0 * 3000),
            remarks=""
        )
        print(f"Result of adding second item: {item_id_2}")

    # 3. 必須項目（例: name）なしで追加 (NOT NULL制約違反テスト)
    print(f"\nAdding item with no name to quotation ID {test_quotation_id}...")
    missing_name_item_result = add_quotation_item(
        quotation_id=test_quotation_id, display_order=30, name=None, specification="名称なしテスト", # ★名称なし
        quantity=1, unit="式", unit_price=10000, amount=10000, remarks="名称なし"
    )
    print(f"Result of adding item with missing name: {missing_name_item_result}") # "NOT_NULL_VIOLATION" を期待

    # 4. 存在しない quotation_id で追加 (外部キー制約違反テスト)
    print("\nAdding item with non-existent quotation_id (999)...")
    fk_error_item_result = add_quotation_item(
        quotation_id=999, display_order=40, name="外部キーエラーテスト品", specification="", # ★存在しない見積ID
        quantity=1, unit="式", unit_price=5000, amount=5000, remarks="外部キーエラー"
    )
    print(f"Result of adding item with FK error: {fk_error_item_result}") # "FK_CONSTRAINT_FAILED" を期待
# database_operations.py の if __name__ == '__main__': ブロックの最後に追記

    print(f"\nGetting items for quotation ID {test_quotation_id}...")
    items = get_items_for_quotation(test_quotation_id) # test_quotation_id は前のテストで使用したID
    if items:
        print(f"Found {len(items)} item(s) for quotation ID {test_quotation_id}:")
        for item_tuple in items:
            print(item_tuple)
    else:
        print(f"No items found for quotation ID {test_quotation_id} or error fetching items.")

    print(f"\nGetting items for non-existent quotation ID 888...")
    no_items = get_items_for_quotation(888) # 存在しない見積ID
    if not no_items: # 空のリストが返るはず
        print(f"Correctly found no items for non-existent quotation ID 888.")
    else:
        print(f"Error: Found items for non-existent quotation ID 888: {no_items}")
# database_operations.py の if __name__ == '__main__': ブロックの最後に追記

    print("\nGetting quotation by ID (e.g., ID 1)...")
    # test_quotation_id は前のテストで使用したID (例: 1)
    quotation_header_detail = get_quotation_by_id(test_quotation_id)
    if quotation_header_detail:
        print(f"Details for quotation header ID {test_quotation_id}:")
        print(quotation_header_detail)
    else:
        print(f"Quotation header ID {test_quotation_id} not found.")

    print("\nGetting all quotations...")
    all_quotations = get_all_quotations()
    if all_quotations:
        print(f"Found {len(all_quotations)} quotation(s):")
        for q_tuple in all_quotations:
            print(q_tuple)
    else:
        print("No quotations found or error fetching quotations.")
# database_operations.py の if __name__ == '__main__': ブロックの最後に追記

    print("\n--- Testing Quotation Update ---")
    # quotation_id = 1 の見積を更新するテスト
    # 事前に quotation_id = 1 の見積が存在することを前提とします。
    # また、quotation_id = 2 (または別のID) の見積が存在しないか、
    # 異なる quotation_code を持つことを前提とします（重複コードテストのため）。
    
    quotation_to_update_id = 1 
    original_quotation = get_quotation_by_id(quotation_to_update_id)

    if original_quotation:
        print(f"Original quotation data (ID: {quotation_to_update_id}): {original_quotation}")
        
        # 1. 通常の更新テスト (ステータスと備考を変更)
        print(f"\nUpdating quotation ID {quotation_to_update_id} (normal update)...")
        # オリジナルの値を取得して、一部だけ変更する
        # (0:q.quotation_id, 1:q.project_id, 2:original_project_code,
        #  3:q.quotation_staff_id, 4:staff_name, 5:q.quotation_code, 6:q.quotation_date, 
        #  7:q.customer_name_at_quote, 8:q.project_name_at_quote, 
        #  9:q.site_address_at_quote, 10:q.construction_period_notes, 
        #  11:q.total_amount_exclusive_tax, 12:q.tax_rate, 13:q.tax_amount, 
        #  14:q.total_amount_inclusive_tax, 15:q.validity_period_notes, 
        #  16:q.payment_terms_notes, 17:q.status, 18:q.remarks, ...)
        
        update_success_1 = update_quotation(
            quotation_id=quotation_to_update_id,
            project_id=original_quotation[1], 
            quotation_staff_id=original_quotation[3],
            quotation_code=original_quotation[5], # 見積番号は変更しない
            quotation_date=original_quotation[6],
            customer_name_at_quote=original_quotation[7],
            project_name_at_quote=original_quotation[8],
            site_address_at_quote=original_quotation[9],
            construction_period_notes=original_quotation[10] + "（納期厳守）", # 工期備考を更新
            total_amount_exclusive_tax=original_quotation[11],
            tax_rate=original_quotation[12],
            tax_amount=original_quotation[13],
            total_amount_inclusive_tax=original_quotation[14],
            validity_period_notes=original_quotation[15],
            payment_terms_notes=original_quotation[16],
            status="提出済", # ステータスを変更
            remarks=original_quotation[18] + " 内容確認済み。" # 備考を更新
        )
        print(f"Update result 1: {update_success_1}")
        if update_success_1 is True:
            updated_quotation_data_1 = get_quotation_by_id(quotation_to_update_id)
            print(f"Updated quotation data 1 (ID: {quotation_to_update_id}): {updated_quotation_data_1}")

        # 2. 見積番号を、既に存在する別の見積番号に変更しようとするテスト (重複エラー)
        #    このテストのためには、事前に別の見積(例: Q-DUP-TEST)を作成しておく必要があります。
        print("\nAttempting to update quotation ID {quotation_to_update_id} to a duplicate quotation_code...")
        temp_q_code_for_dup = "Q-DUP-TEST"
        # 一時的に重複させるための見積を作成 (もしなければ)
        add_quotation(original_quotation[1], original_quotation[3], temp_q_code_for_dup, "2025-01-01", "仮顧客", "仮案件", "仮住所", "仮工期", 1000, 0.1, 100, 1100, "仮有効期限", "仮支払条件", "仮ステータス", "重複テスト用")
        
        # original_quotation[5] は元の見積コード (Q2025-P001-01)
        if original_quotation[5] != temp_q_code_for_dup:
            update_dup_code_result = update_quotation(
                quotation_id=quotation_to_update_id,
                project_id=original_quotation[1], quotation_staff_id=original_quotation[3],
                quotation_code=temp_q_code_for_dup, # ★重複する可能性のある見積番号に更新
                quotation_date=original_quotation[6], customer_name_at_quote=original_quotation[7],
                project_name_at_quote=original_quotation[8], site_address_at_quote=original_quotation[9],
                construction_period_notes=original_quotation[10], total_amount_exclusive_tax=original_quotation[11],
                tax_rate=original_quotation[12], tax_amount=original_quotation[13],
                total_amount_inclusive_tax=original_quotation[14], validity_period_notes=original_quotation[15],
                payment_terms_notes=original_quotation[16], status=original_quotation[17], remarks=original_quotation[18]
            )
            print(f"Result of updating to duplicate quotation_code: {update_dup_code_result}") # "DUPLICATE_QUOTATION_CODE" になるはず
            # テスト後は元の見積コードに戻す (任意)
            if update_dup_code_result == "DUPLICATE_QUOTATION_CODE":
                 update_quotation(quotation_to_update_id, original_quotation[1], original_quotation[3], original_quotation[5], original_quotation[6], original_quotation[7], original_quotation[8], original_quotation[9], original_quotation[10], original_quotation[11], original_quotation[12], original_quotation[13], original_quotation[14], original_quotation[15], original_quotation[16], original_quotation[17], original_quotation[18])
        else:
            print(f"Skipping duplicate quotation_code update test as original code might be {temp_q_code_for_dup}.")
            
    else:
        print(f"Quotation ID {quotation_to_update_id} not found, skipping update tests.")
# database_operations.py の if __name__ == '__main__': ブロックの最後に追記

    print("\n--- Testing Quotation Delete ---")
    # 削除テスト用の見積ヘッダーと明細を一時的に追加
    print("Adding a temporary quotation with items for delete test...")
    temp_del_q_code = "Q-DEL-TEST"
    # 既存の project_id と quotation_staff_id を使用 (例: 1)
    # (これらのIDが存在することを前提とします)
    temp_del_project_id = 1
    temp_del_staff_id = 1

    # 重複しないように、もし既存ならテストをスキップするか、事前に削除しておく
    # 簡単のため、ここではそのまま追加を試みます。テストの繰り返しで重複エラーが出る場合は、
    # このテストの前に temp_del_q_code の見積もりを手動で削除するか、コードを変えてください。
    
    temp_delete_quotation_id = add_quotation(
        project_id=temp_del_project_id, quotation_staff_id=temp_del_staff_id,
        quotation_code=temp_del_q_code, quotation_date="2025-01-01",
        customer_name_at_quote="削除テスト顧客", project_name_at_quote="削除テスト案件",
        site_address_at_quote="削除テスト住所", construction_period_notes="削除テスト工期",
        total_amount_exclusive_tax=10000, tax_rate=0.1, tax_amount=1000,
        total_amount_inclusive_tax=11000, validity_period_notes="削除テスト有効",
        payment_terms_notes="削除テスト支払", status="仮", remarks="この見積はテスト後に削除されます"
    )

    if isinstance(temp_delete_quotation_id, int):
        print(f"Temporary quotation added with ID: {temp_delete_quotation_id}")
        # その見積に明細をいくつか追加
        add_quotation_item(temp_delete_quotation_id, 10, "明細A(削除テスト)", "", 1, "式", 5000, 5000, "")
        add_quotation_item(temp_delete_quotation_id, 20, "明細B(削除テスト)", "", 2, "個", 2500, 5000, "")
        
        # 明細が追加されたか確認 (任意)
        temp_items = get_items_for_quotation(temp_delete_quotation_id)
        print(f"Temporary items for quotation ID {temp_delete_quotation_id}: {len(temp_items)} items found.")

        # 見積ヘッダーの削除処理の実行
        print(f"\nDeleting quotation ID {temp_delete_quotation_id}...")
        delete_q_result = delete_quotation(temp_delete_quotation_id)
        print(f"Delete quotation result: {delete_q_result}")

        if delete_q_result is True:
            print(f"Verifying quotation header ID {temp_delete_quotation_id} is deleted...")
            deleted_q_check = get_quotation_by_id(temp_delete_quotation_id)
            if deleted_q_check is None:
                print(f"Quotation header ID {temp_delete_quotation_id} successfully deleted and not found.")
            else:
                print(f"Error: Quotation header ID {temp_delete_quotation_id} was found after deletion attempt.")

            print(f"Verifying items for quotation ID {temp_delete_quotation_id} are also deleted (due to CASCADE)...")
            deleted_q_items_check = get_items_for_quotation(temp_delete_quotation_id)
            if not deleted_q_items_check: # 空のリストのはず
                print(f"Items for quotation ID {temp_delete_quotation_id} successfully deleted.")
            else:
                print(f"Error: Items found for quotation ID {temp_delete_quotation_id} after header deletion: {len(deleted_q_items_check)} items.")
        
    elif temp_delete_quotation_id == "DUPLICATE_QUOTATION_CODE":
        print(f"Could not add temporary quotation for delete test due to DUPLICATE_QUOTATION_CODE: {temp_del_q_code}")
        print("Please ensure quotation code 'Q-DEL-TEST' is not already in use, or clear DB and re-run.")
    else:
        print(f"Could not add temporary quotation for delete test. Add result: {temp_delete_quotation_id}")

    # 存在しないIDの削除テスト
    print("\nAttempting to delete non-existent quotation ID 777...")
    delete_non_existent_q_result = delete_quotation(777) # 存在しないであろうID
    print(f"Result of deleting non-existent quotation: {delete_non_existent_q_result}") # "NOT_FOUND" になるはず
# database_operations.py の if __name__ == '__main__': ブロックの最後に追記

    print("\n--- Testing Quotation Item Update ---")
    # quotation_id = 1 に属する最初の明細を更新するテスト
    # 事前に quotation_id = 1 に明細が存在することを前提とします。
    # (これまでのテストで item_id 1, 3, 5, 7, 9 などが quotation_id 1 に追加されているはず)
    
    quotation_id_for_item_test = 1
    items_before_update = get_items_for_quotation(quotation_id_for_item_test)

    if items_before_update:
        item_to_update_id = items_before_update[0][0] # 取得した最初の明細のitem_id
        original_item = items_before_update[0]
        print(f"Original item data (ID: {item_to_update_id} from Quotation ID: {quotation_id_for_item_test}): {original_item}")
        
        # 明細の情報を変更 (例: 名称、数量、単価、金額、備考)
        updated_name = original_item[3] + " (改訂)"
        updated_quantity = (original_item[5] or 0) + 10 # quantity is index 5, REAL
        updated_unit_price = (original_item[7] or 0) + 50 # unit_price is index 7, INTEGER
        updated_amount = int(updated_quantity * updated_unit_price) # 再計算
        updated_remarks = (original_item[9] or "") + " 更新テスト。" # remarks is index 9

        print(f"\nUpdating quotation item ID {item_to_update_id}...")
        update_item_success = update_quotation_item(
            item_id=item_to_update_id,
            display_order=original_item[2], # display_order は変更しない (index 2)
            name=updated_name,
            specification=original_item[4], # specification は変更しない (index 4)
            quantity=updated_quantity,
            unit=original_item[6], # unit は変更しない (index 6)
            unit_price=updated_unit_price,
            amount=updated_amount,
            remarks=updated_remarks
        )
        print(f"Update item result: {update_item_success}")

        if update_item_success is True:
            print(f"Verifying updated item ID {item_to_update_id}...")
            items_after_update = get_items_for_quotation(quotation_id_for_item_test)
            found_updated = False
            for item in items_after_update:
                if item[0] == item_to_update_id:
                    print(f"Updated item data: {item}")
                    if item[3] == updated_name and item[5] == updated_quantity: # 名称と数量で簡易チェック
                        print("Item data appears to be updated correctly.")
                    else:
                        print("Error: Item data does not seem to reflect updates.")
                    found_updated = True
                    break
            if not found_updated:
                 print(f"Error: Updated item ID {item_to_update_id} not found in list after update.")
    else:
        print(f"No items found for quotation ID {quotation_id_for_item_test} to test update.")
# database_operations.py の if __name__ == '__main__': ブロックの最後に追記

    print("\n--- Testing Quotation Item Update ---")
    # quotation_id = 1 に属する最初の明細を更新するテスト
    # 事前に quotation_id = 1 に明細が存在することを前提とします。
    # (これまでのテストで item_id 1, 3, 5, 7, 9 などが quotation_id 1 に追加されているはず)
    
    quotation_id_for_item_test = 1
    items_before_update = get_items_for_quotation(quotation_id_for_item_test)

    if items_before_update:
        item_to_update_id = items_before_update[0][0] # 取得した最初の明細のitem_id
        original_item = items_before_update[0]
        print(f"Original item data (ID: {item_to_update_id} from Quotation ID: {quotation_id_for_item_test}): {original_item}")
        
        # 明細の情報を変更 (例: 名称、数量、単価、金額、備考)
        updated_name = original_item[3] + " (改訂)"
        updated_quantity = (original_item[5] or 0) + 10 # quantity is index 5, REAL
        updated_unit_price = (original_item[7] or 0) + 50 # unit_price is index 7, INTEGER
        updated_amount = int(updated_quantity * updated_unit_price) # 再計算
        updated_remarks = (original_item[9] or "") + " 更新テスト。" # remarks is index 9

        print(f"\nUpdating quotation item ID {item_to_update_id}...")
        update_item_success = update_quotation_item(
            item_id=item_to_update_id,
            display_order=original_item[2], # display_order は変更しない (index 2)
            name=updated_name,
            specification=original_item[4], # specification は変更しない (index 4)
            quantity=updated_quantity,
            unit=original_item[6], # unit は変更しない (index 6)
            unit_price=updated_unit_price,
            amount=updated_amount,
            remarks=updated_remarks
        )
        print(f"Update item result: {update_item_success}")

        if update_item_success is True:
            print(f"Verifying updated item ID {item_to_update_id}...")
            items_after_update = get_items_for_quotation(quotation_id_for_item_test)
            found_updated = False
            for item in items_after_update:
                if item[0] == item_to_update_id:
                    print(f"Updated item data: {item}")
                    if item[3] == updated_name and item[5] == updated_quantity: # 名称と数量で簡易チェック
                        print("Item data appears to be updated correctly.")
                    else:
                        print("Error: Item data does not seem to reflect updates.")
                    found_updated = True
                    break
            if not found_updated:
                 print(f"Error: Updated item ID {item_to_update_id} not found in list after update.")
    else:
        print(f"No items found for quotation ID {quotation_id_for_item_test} to test update.")
# database_operations.py の if __name__ == '__main__': ブロックの最後に追記

    print("\n--- Testing Quotation Item Delete ---")
    # quotation_id = 1 に属する明細を削除するテスト
    # 事前に quotation_id = 1 に複数の明細が存在することを前提とします。
    
    quotation_id_for_item_delete_test = 1
    items_before_delete = get_items_for_quotation(quotation_id_for_item_delete_test)

    if items_before_delete and len(items_before_delete) > 0:
        item_to_delete_id = items_before_delete[0][0] # 取得した最初の明細のitem_id
        item_to_delete_name = items_before_delete[0][3] # 削除対象の名称 (ログ用)
        print(f"Items before delete for quotation ID {quotation_id_for_item_delete_test}: {len(items_before_delete)} items.")
        print(f"Attempting to delete item ID {item_to_delete_id} ('{item_to_delete_name}')...")
        
        delete_item_result = delete_quotation_item(item_to_delete_id)
        print(f"Delete item result: {delete_item_result}")

        if delete_item_result is True:
            print(f"Verifying item ID {item_to_delete_id} is deleted...")
            items_after_delete = get_items_for_quotation(quotation_id_for_item_delete_test)
            print(f"Items after delete for quotation ID {quotation_id_for_item_delete_test}: {len(items_after_delete)} items.")
            
            found_after_delete = False
            for item in items_after_delete:
                if item[0] == item_to_delete_id:
                    found_after_delete = True
                    break
            if not found_after_delete:
                print(f"Item ID {item_to_delete_id} successfully deleted.")
            else:
                print(f"Error: Item ID {item_to_delete_id} was still found after deletion attempt.")
    else:
        print(f"No items found for quotation ID {quotation_id_for_item_delete_test} to test item deletion, or add_quotation_item test failed earlier.")

    # 存在しないIDの削除テスト
    print("\nAttempting to delete non-existent item ID 888...")
    delete_non_existent_item_result = delete_quotation_item(888) # 存在しないであろうID
    print(f"Result of deleting non-existent item: {delete_non_existent_item_result}") # "NOT_FOUND" になるはず










