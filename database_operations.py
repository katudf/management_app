# database_operations.py

import sqlite3
from datetime import datetime
DATABASE_FILE = "komuten_kanri.db"

def get_current_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def create_connection(db_file=DATABASE_FILE):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.execute("PRAGMA foreign_keys = ON")
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
    return conn

# --- 顧客 (Customers) テーブル操作 ---
# (変更なし)
def add_customer(customer_name, contact_person_name, phone_number, email, address, notes):
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
        return cur.lastrowid
    except sqlite3.IntegrityError as e:
        if "unique constraint failed: customers.customer_name" in str(e).lower():
            return "DUPLICATE_NAME"
        else:
            return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error adding customer: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn: conn.close()

def get_all_customers():
    conn = create_connection()
    if not conn: return []
    try:
        cur = conn.cursor()
        cur.execute("SELECT customer_id, customer_name, contact_person_name, phone_number, email, address, notes, created_at, updated_at FROM customers ORDER BY customer_name")
        rows = cur.fetchall()
        return rows
    except sqlite3.Error as e:
        print(f"Error fetching customers: {e}")
        return []
    finally:
        if conn: conn.close()

def get_customer_by_id(customer_id):
    conn = create_connection()
    if not conn: return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM customers WHERE customer_id=?", (customer_id,))
        row = cur.fetchone()
        return row
    except sqlite3.Error as e:
        print(f"Error fetching customer by ID: {e}")
        return None
    finally:
        if conn: conn.close()

def update_customer(customer_id, customer_name, contact_person_name, phone_number, email, address, notes):
    conn = create_connection()
    if not conn: return "CONNECTION_ERROR"
    sql = ''' UPDATE customers
              SET customer_name = ?, contact_person_name = ?, phone_number = ?, email = ?, address = ?, updated_at = ?, notes = ?
              WHERE customer_id = ? '''
    current_time = get_current_timestamp()
    try:
        cur = conn.cursor()
        cur.execute(sql, (customer_name, contact_person_name, phone_number, email, address, current_time, notes, customer_id))
        conn.commit()
        if cur.rowcount == 0: return "NOT_FOUND"
        return True
    except sqlite3.IntegrityError as e:
        if "unique constraint failed: customers.customer_name" in str(e).lower():
            return "DUPLICATE_NAME"
        else:
            return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error updating customer ID {customer_id}: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn: conn.close()

def delete_customer(customer_id):
    conn = create_connection()
    if not conn: return "CONNECTION_ERROR"
    sql = 'DELETE FROM customers WHERE customer_id=?'
    try:
        cur = conn.cursor()
        cur.execute(sql, (customer_id,))
        conn.commit()
        if cur.rowcount == 0: return "NOT_FOUND"
        return True
    except sqlite3.Error as e:
        print(f"Error deleting customer ID {customer_id}: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn: conn.close()


# --- 案件 (Projects) テーブル操作 ---
# ★★★ add_project 関数の修正: estimated_amount 引数と関連箇所を削除 ★★★
def add_project(project_code, project_name, customer_id, parent_project_id,
                site_address, reception_date, start_date_scheduled,
                completion_date_scheduled, actual_completion_date,
                responsible_staff_name, status, remarks): # estimated_amount を削除
    conn = create_connection()
    if not conn:
        return "CONNECTION_ERROR"

    # SQL文から estimated_amount と対応するプレースホルダを削除
    sql = ''' INSERT INTO projects(project_code, project_name, customer_id, parent_project_id,
                                 site_address, reception_date, start_date_scheduled,
                                 completion_date_scheduled, actual_completion_date,
                                 responsible_staff_name, status, 
                                 created_at, updated_at, remarks)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?) ''' # プレースホルダを14個に
    
    current_time = get_current_timestamp()
    try:
        cur = conn.cursor()
        # executeの引数リストから estimated_amount を削除
        cur.execute(sql, (project_code, project_name, customer_id, parent_project_id,
                         site_address, reception_date, start_date_scheduled,
                         completion_date_scheduled, actual_completion_date,
                         responsible_staff_name, status,
                         current_time, current_time, remarks))
        conn.commit()
        print(f"Project '{project_name}' (Code: {project_code}) added successfully with ID: {cur.lastrowid}")
        return cur.lastrowid
    except sqlite3.IntegrityError as e:
        error_message_lower = str(e).lower()
        if "unique constraint failed: projects.project_code" in error_message_lower:
            return "DUPLICATE_CODE"
        elif "not null constraint failed" in error_message_lower:
             return "NOT_NULL_VIOLATION"
        elif "foreign key constraint failed" in error_message_lower:
            return "FK_CONSTRAINT_FAILED"
        else:
            return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error adding project: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn:
            conn.close()

# ★★★ get_all_projects 関数の修正: SELECT文から p.estimated_amount を削除 ★★★
def get_all_projects():
    conn = create_connection()
    if not conn:
        return []

    try:
        cur = conn.cursor()
        # SELECT文から p.estimated_amount を削除
        sql = """
            SELECT
                p.project_id, p.project_code, p.project_name,
                p.customer_id, c.customer_name, 
                p.parent_project_id, pp.project_code as parent_project_code, 
                p.site_address, p.reception_date, p.start_date_scheduled,
                p.completion_date_scheduled, p.actual_completion_date,
                p.responsible_staff_name, p.status, 
                p.remarks, p.created_at, p.updated_at
            FROM projects p
            LEFT JOIN customers c ON p.customer_id = c.customer_id
            LEFT JOIN projects pp ON p.parent_project_id = pp.project_id
            ORDER BY p.project_code
        """
        cur.execute(sql)
        rows = cur.fetchall()
        return rows
    except sqlite3.Error as e:
        print(f"Error fetching projects: {e}")
        return []
    finally:
        if conn:
            conn.close()

# ★★★ get_project_by_id 関数の修正: SELECT文から p.estimated_amount を削除 ★★★
def get_project_by_id(project_id):
    conn = create_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()
        # SELECT文から p.estimated_amount を削除
        sql = """
            SELECT
                p.project_id, p.project_code, p.project_name,
                p.customer_id, c.customer_name,
                p.parent_project_id, pp.project_code as parent_project_code,
                p.site_address, p.reception_date, p.start_date_scheduled,
                p.completion_date_scheduled, p.actual_completion_date,
                p.responsible_staff_name, p.status,
                p.remarks, p.created_at, p.updated_at
            FROM projects p
            LEFT JOIN customers c ON p.customer_id = c.customer_id
            LEFT JOIN projects pp ON p.parent_project_id = pp.project_id
            WHERE p.project_id = ?
        """
        cur.execute(sql, (project_id,))
        row = cur.fetchone()
        return row
    except sqlite3.Error as e:
        print(f"Error fetching project by ID ({project_id}): {e}")
        return None
    finally:
        if conn:
            conn.close()

# ★★★ update_project 関数の修正: estimated_amount 引数と関連箇所を削除 ★★★
def update_project(project_id, project_code, project_name, customer_id, parent_project_id,
                   site_address, reception_date, start_date_scheduled,
                   completion_date_scheduled, actual_completion_date,
                   responsible_staff_name, status, remarks): # estimated_amount を削除
    conn = create_connection()
    if not conn:
        return "CONNECTION_ERROR"

    # SQL文から estimated_amount = ?, を削除
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
                  status = ?,
                  remarks = ?,
                  updated_at = ?
              WHERE project_id = ? ''' # プレースホルダを1つ減らす
    
    current_time = get_current_timestamp()
    try:
        cur = conn.cursor()
        # executeの引数リストから estimated_amount を削除
        cur.execute(sql, (project_code, project_name, customer_id, parent_project_id,
                         site_address, reception_date, start_date_scheduled,
                         completion_date_scheduled, actual_completion_date,
                         responsible_staff_name, status, remarks,
                         current_time, project_id))
        conn.commit()
        if cur.rowcount == 0:
            return "NOT_FOUND"
        return True
    except sqlite3.IntegrityError as e:
        error_message_lower = str(e).lower()
        if "unique constraint failed: projects.project_code" in error_message_lower:
            return "DUPLICATE_CODE"
        elif "not null constraint failed" in error_message_lower:
             return "NOT_NULL_VIOLATION"
        elif "foreign key constraint failed" in error_message_lower:
            return "FK_CONSTRAINT_FAILED"
        else:
            return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error updating project ID {project_id}: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn:
            conn.close()

def delete_project(project_id):
    # (この関数は estimated_amount に依存しないため変更なし)
    conn = create_connection()
    if not conn: return "CONNECTION_ERROR"
    sql = 'DELETE FROM projects WHERE project_id = ?'
    try:
        cur = conn.cursor()
        cur.execute(sql, (project_id,))
        conn.commit()
        if cur.rowcount == 0: return "NOT_FOUND"
        return True
    except sqlite3.IntegrityError as e:
        if "foreign key constraint failed" in str(e).lower() or "constraint failed" in str(e).lower():
            return "FK_CONSTRAINT_FAILED"
        else:
            return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error deleting project ID {project_id}: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn: conn.close()

def get_next_project_code_sequence_for_month(year_month_str):
    # (この関数は estimated_amount に依存しないため変更なし)
    conn = create_connection()
    if not conn: return None
    prefix_to_search = f"P-{year_month_str}-"
    next_seq = 1
    try:
        cur = conn.cursor()
        prefix_len = len(prefix_to_search)
        query = f"SELECT MAX(CAST(SUBSTR(project_code, {prefix_len + 1}) AS INTEGER)) FROM projects WHERE project_code LIKE ?;"
        cur.execute(query, (f"{prefix_to_search}%",))
        max_seq_row = cur.fetchone()
        if max_seq_row and max_seq_row[0] is not None:
            next_seq = max_seq_row[0] + 1
    except sqlite3.Error as e:
        print(f"Error getting next project code sequence for {year_month_str}: {e}")
        next_seq = None
    finally:
        if conn: conn.close()
    return next_seq

# --- 社員 (Employees) テーブル操作 ---
# (変更なし)
def add_employee(employee_code, full_name, name_kana, ccus_id, 
                 date_of_birth, gender, position, address, phone_number, 
                 job_title, employment_date, experience_years_trade, 
                 emergency_contact_name, emergency_contact_phone, 
                 emergency_contact_relationship, last_health_check_date, 
                 blood_type, social_insurance_status_notes, 
                 retirement_allowance_notes, qualifications_notes, 
                 paid_leave_days_notes, is_active, remarks):
    conn = create_connection()
    if not conn: return "CONNECTION_ERROR"
    sql = ''' INSERT INTO employees(employee_code, full_name, name_kana, ccus_id, 
                                 date_of_birth, gender, position, address, phone_number, 
                                 job_title, employment_date, experience_years_trade, 
                                 emergency_contact_name, emergency_contact_phone, 
                                 emergency_contact_relationship, last_health_check_date, 
                                 blood_type, social_insurance_status_notes, 
                                 retirement_allowance_notes, qualifications_notes, 
                                 paid_leave_days_notes, is_active, remarks,
                                 created_at, updated_at)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) '''
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
                         current_time, current_time))
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError as e:
        error_message_lower = str(e).lower()
        if "unique constraint failed: employees.employee_code" in error_message_lower and employee_code:
            return "DUPLICATE_EMP_CODE"
        elif "unique constraint failed: employees.ccus_id" in error_message_lower and ccus_id:
            return "DUPLICATE_CCUS_ID"
        elif "not null constraint failed" in error_message_lower:
             return "NOT_NULL_VIOLATION"
        else:
            return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error adding employee: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn: conn.close()

def get_all_employees():
    conn = create_connection()
    if not conn: return []
    try:
        cur = conn.cursor()
        sql = """
            SELECT employee_id, employee_code, full_name, name_kana, ccus_id, date_of_birth, gender, position, address, phone_number, job_title, employment_date, experience_years_trade, emergency_contact_name, emergency_contact_phone, emergency_contact_relationship, last_health_check_date, blood_type, social_insurance_status_notes, retirement_allowance_notes, qualifications_notes, paid_leave_days_notes, is_active, remarks, created_at, updated_at
            FROM employees ORDER BY COALESCE(employee_code, full_name) """
        cur.execute(sql)
        rows = cur.fetchall()
        return rows
    except sqlite3.Error as e:
        print(f"Error fetching employees: {e}")
        return []
    finally:
        if conn: conn.close()

def get_employee_by_id(employee_id):
    conn = create_connection()
    if not conn: return None
    try:
        cur = conn.cursor()
        sql = """
            SELECT employee_id, employee_code, full_name, name_kana, ccus_id, date_of_birth, gender, position, address, phone_number, job_title, employment_date, experience_years_trade, emergency_contact_name, emergency_contact_phone, emergency_contact_relationship, last_health_check_date, blood_type, social_insurance_status_notes, retirement_allowance_notes, qualifications_notes, paid_leave_days_notes, is_active, remarks, created_at, updated_at
            FROM employees WHERE employee_id = ? """
        cur.execute(sql, (employee_id,))
        row = cur.fetchone()
        return row
    except sqlite3.Error as e:
        print(f"Error fetching employee by ID ({employee_id}): {e}")
        return None
    finally:
        if conn: conn.close()

def update_employee(employee_id, employee_code, full_name, name_kana, ccus_id, 
                    date_of_birth, gender, position, address, phone_number, 
                    job_title, employment_date, experience_years_trade, 
                    emergency_contact_name, emergency_contact_phone, 
                    emergency_contact_relationship, last_health_check_date, 
                    blood_type, social_insurance_status_notes, 
                    retirement_allowance_notes, qualifications_notes, 
                    paid_leave_days_notes, is_active, remarks):
    conn = create_connection()
    if not conn: return "CONNECTION_ERROR"
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
        if cur.rowcount == 0: return "NOT_FOUND"
        return True
    except sqlite3.IntegrityError as e:
        error_message_lower = str(e).lower()
        if "unique constraint failed: employees.employee_code" in error_message_lower and employee_code:
            return "DUPLICATE_EMP_CODE"
        elif "unique constraint failed: employees.ccus_id" in error_message_lower and ccus_id:
            return "DUPLICATE_CCUS_ID"
        elif "not null constraint failed" in error_message_lower:
             return "NOT_NULL_VIOLATION"
        else:
            return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error updating employee ID {employee_id}: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn: conn.close()

def delete_employee(employee_id):
    conn = create_connection()
    if not conn: return "CONNECTION_ERROR"
    sql = 'DELETE FROM employees WHERE employee_id = ?'
    try:
        cur = conn.cursor()
        cur.execute(sql, (employee_id,))
        conn.commit()
        if cur.rowcount == 0: return "NOT_FOUND"
        return True
    except sqlite3.Error as e:
        print(f"Error deleting employee ID {employee_id}: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn: conn.close()

# --- 見積ヘッダー (Quotations) テーブル操作 ---
# (変更なし)
def add_quotation(project_id, quotation_staff_id, quotation_code, quotation_date,
                  customer_name_at_quote, project_name_at_quote, site_address_at_quote,
                  construction_period_notes, total_amount_exclusive_tax, tax_rate,
                  tax_amount, total_amount_inclusive_tax, validity_period_notes,
                  payment_terms_notes, status, remarks):
    conn = create_connection()
    if not conn: return "CONNECTION_ERROR"
    sql = """INSERT INTO quotations (project_id, quotation_staff_id, quotation_code, quotation_date, customer_name_at_quote, project_name_at_quote, site_address_at_quote, construction_period_notes, total_amount_exclusive_tax, tax_rate, tax_amount, total_amount_inclusive_tax, validity_period_notes, payment_terms_notes, status, remarks, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    current_time = get_current_timestamp()
    try:
        cur = conn.cursor()
        cur.execute(sql, (project_id, quotation_staff_id, quotation_code, quotation_date, customer_name_at_quote, project_name_at_quote, site_address_at_quote, construction_period_notes, total_amount_exclusive_tax, tax_rate, tax_amount, total_amount_inclusive_tax, validity_period_notes, payment_terms_notes, status, remarks, current_time, current_time))
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError as e:
        error_message_lower = str(e).lower()
        if "unique constraint failed: quotations.quotation_code" in error_message_lower: return "DUPLICATE_QUOTATION_CODE"
        elif "not null constraint failed" in error_message_lower: return "NOT_NULL_VIOLATION"
        elif "foreign key constraint failed" in error_message_lower: return "FK_CONSTRAINT_FAILED"
        else: return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error adding quotation: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn: conn.close()

def add_quotation_item(quotation_id, name, specification, quantity, unit, unit_price, amount, remarks):
    conn = create_connection()
    if not conn: return "CONNECTION_ERROR"
    try:
        cur = conn.cursor()
        cur.execute("SELECT MAX(display_order) FROM quotation_items WHERE quotation_id = ?", (quotation_id,))
        max_order = cur.fetchone()[0]
        current_display_order = (max_order if max_order is not None else 0) + 10
        sql = """INSERT INTO quotation_items (quotation_id, display_order, name, specification, quantity, unit, unit_price, amount, remarks, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        current_time = get_current_timestamp()
        cur.execute(sql, (quotation_id, current_display_order, name, specification, quantity, unit, unit_price, amount, remarks, current_time, current_time))
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError as e:
        error_message_lower = str(e).lower()
        if "not null constraint failed" in error_message_lower: return "NOT_NULL_VIOLATION"
        elif "foreign key constraint failed" in error_message_lower: return "FK_CONSTRAINT_FAILED"
        else: return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error adding quotation item: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn: conn.close()

def get_items_for_quotation(quotation_id):
    conn = create_connection()
    if not conn: return []
    try:
        cur = conn.cursor()
        sql = "SELECT item_id, quotation_id, display_order, name, specification, quantity, unit, unit_price, amount, remarks, created_at, updated_at FROM quotation_items WHERE quotation_id = ? ORDER BY COALESCE(display_order, 999999), item_id"
        cur.execute(sql, (quotation_id,))
        rows = cur.fetchall()
        return rows
    except sqlite3.Error as e:
        print(f"Error fetching items for quotation ID ({quotation_id}): {e}")
        return []
    finally:
        if conn: conn.close()

def get_quotation_item_by_id(item_id):
    conn = create_connection()
    if not conn: return None
    query = "SELECT item_id, quotation_id, display_order, name, specification, quantity, unit, unit_price, amount, remarks, created_at, updated_at FROM quotation_items WHERE item_id = ?;"
    try:
        cur = conn.cursor()
        cur.execute(query, (item_id,))
        item_data_tuple = cur.fetchone()
        if item_data_tuple:
            columns = ["item_id", "quotation_id", "display_order", "name", "specification", "quantity", "unit", "unit_price", "amount", "remarks", "created_at", "updated_at"]
            return dict(zip(columns, item_data_tuple))
        else:
            return None
    except sqlite3.Error as e:
        print(f"Error getting quotation item by id {item_id}: {e}")
        return None
    finally:
        if conn: conn.close()

def get_all_quotations():
    conn = create_connection()
    if not conn: return []
    try:
        cur = conn.cursor()
        sql = """
            SELECT q.quotation_id, q.quotation_code, q.quotation_date, q.project_id, p.project_code AS original_project_code, p.project_name AS original_project_name, q.quotation_staff_id, e.full_name AS staff_name, q.customer_name_at_quote, q.project_name_at_quote, q.total_amount_inclusive_tax, q.status, q.validity_period_notes, q.updated_at
            FROM quotations q
            LEFT JOIN projects p ON q.project_id = p.project_id
            LEFT JOIN employees e ON q.quotation_staff_id = e.employee_id
            ORDER BY q.quotation_date DESC, q.quotation_code DESC """
        cur.execute(sql)
        rows = cur.fetchall()
        return rows
    except sqlite3.Error as e:
        print(f"Error fetching all quotations: {e}")
        return []
    finally:
        if conn: conn.close()

def get_quotation_by_id(quotation_id):
    conn = create_connection()
    if not conn: return None
    try:
        cur = conn.cursor()
        sql = """
            SELECT q.quotation_id, q.project_id, p.project_code AS original_project_code, q.quotation_staff_id, e.full_name AS staff_name, q.quotation_code, q.quotation_date, q.customer_name_at_quote, q.project_name_at_quote, q.site_address_at_quote, q.construction_period_notes, q.total_amount_exclusive_tax, q.tax_rate, q.tax_amount, q.total_amount_inclusive_tax, q.validity_period_notes, q.payment_terms_notes, q.status, q.remarks, q.created_at, q.updated_at
            FROM quotations q
            LEFT JOIN projects p ON q.project_id = p.project_id
            LEFT JOIN employees e ON q.quotation_staff_id = e.employee_id
            WHERE q.quotation_id = ? """
        cur.execute(sql, (quotation_id,))
        row = cur.fetchone()
        return row
    except sqlite3.Error as e:
        print(f"Error fetching quotation by ID ({quotation_id}): {e}")
        return None
    finally:
        if conn: conn.close()

def update_quotation(quotation_id, project_id, quotation_staff_id, quotation_code, quotation_date,
                     customer_name_at_quote, project_name_at_quote, site_address_at_quote,
                     construction_period_notes, total_amount_exclusive_tax, tax_rate,
                     tax_amount, total_amount_inclusive_tax, validity_period_notes,
                     payment_terms_notes, status, remarks):
    conn = create_connection()
    if not conn: return "CONNECTION_ERROR"
    sql = """ UPDATE quotations SET project_id = ?, quotation_staff_id = ?, quotation_code = ?, quotation_date = ?, customer_name_at_quote = ?, project_name_at_quote = ?, site_address_at_quote = ?, construction_period_notes = ?, total_amount_exclusive_tax = ?, tax_rate = ?, tax_amount = ?, total_amount_inclusive_tax = ?, validity_period_notes = ?, payment_terms_notes = ?, status = ?, remarks = ?, updated_at = ? WHERE quotation_id = ? """
    current_time = get_current_timestamp()
    try:
        cur = conn.cursor()
        cur.execute(sql, (project_id, quotation_staff_id, quotation_code, quotation_date, customer_name_at_quote, project_name_at_quote, site_address_at_quote, construction_period_notes, total_amount_exclusive_tax, tax_rate, tax_amount, total_amount_inclusive_tax, validity_period_notes, payment_terms_notes, status, remarks, current_time, quotation_id))
        conn.commit()
        if cur.rowcount == 0: return "NOT_FOUND"
        return True
    except sqlite3.IntegrityError as e:
        error_message_lower = str(e).lower()
        if "unique constraint failed: quotations.quotation_code" in error_message_lower: return "DUPLICATE_QUOTATION_CODE"
        elif "not null constraint failed" in error_message_lower: return "NOT_NULL_VIOLATION"
        elif "foreign key constraint failed" in error_message_lower: return "FK_CONSTRAINT_FAILED"
        else: return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error updating quotation ID {quotation_id}: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn: conn.close()

def delete_quotation_item(item_id):
    conn = create_connection()
    if not conn: return "CONNECTION_ERROR"
    sql = 'DELETE FROM quotation_items WHERE item_id = ?'
    try:
        cur = conn.cursor()
        cur.execute(sql, (item_id,))
        conn.commit()
        if cur.rowcount == 0: return "NOT_FOUND"
        return True
    except sqlite3.Error as e:
        print(f"Error deleting quotation item ID {item_id}: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn: conn.close()

def delete_quotation(quotation_id):
    conn = create_connection()
    if not conn: return "CONNECTION_ERROR"
    sql = 'DELETE FROM quotations WHERE quotation_id = ?'
    try:
        cur = conn.cursor()
        cur.execute(sql, (quotation_id,))
        conn.commit()
        if cur.rowcount == 0: return "NOT_FOUND"
        return True
    except sqlite3.IntegrityError as e:
        return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error deleting quotation ID {quotation_id}: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn: conn.close()

def update_quotation_item(item_id, display_order, name, specification,
                          quantity, unit, unit_price, amount, remarks):
    conn = create_connection()
    if not conn: return "CONNECTION_ERROR"
    sql = """ UPDATE quotation_items SET display_order = ?, name = ?, specification = ?, quantity = ?, unit = ?, unit_price = ?, amount = ?, remarks = ?, updated_at = ? WHERE item_id = ? """
    current_time = get_current_timestamp()
    try:
        cur = conn.cursor()
        cur.execute(sql, (display_order, name, specification, quantity, unit, unit_price, amount, remarks, current_time, item_id))
        conn.commit()
        if cur.rowcount == 0: return "NOT_FOUND"
        return True
    except sqlite3.IntegrityError as e:
        if "not null constraint failed" in str(e).lower(): return "NOT_NULL_VIOLATION"
        else: return "INTEGRITY_ERROR"
    except sqlite3.Error as e:
        print(f"Error updating quotation item ID {item_id}: {e}")
        return "OTHER_DB_ERROR"
    finally:
        if conn: conn.close()

        # database_operations.py に以下の関数を追加

def get_child_project_codes(parent_project_id):
    """指定された親案件IDを持つ子案件の案件コードリストを取得する"""
    conn = create_connection()
    if not conn:
        return []
    
    sql = "SELECT project_code FROM projects WHERE parent_project_id = ?"
    try:
        cur = conn.cursor()
        cur.execute(sql, (parent_project_id,))
        rows = cur.fetchall()
        return [row[0] for row in rows] # 案件コードのリストを返す
    except sqlite3.Error as e:
        print(f"Error fetching child project codes for parent_id {parent_project_id}: {e}")
        return []
    finally:
        if conn:
            conn.close()

# ★★★ get_quotations_by_project_id 関数の修正 (コピーミス修正) ★★★
def get_quotations_by_project_id(project_id):
    """指定された案件IDに紐づく全ての見積ヘッダー情報をデータベースから取得する"""
    conn = create_connection()
    if not conn:
        return []

    try:
        cur = conn.cursor()
        # get_all_quotations と同様のカラムを取得し、project_idでフィルタリング
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
            WHERE q.project_id = ?  -- 案件IDでフィルタ
            ORDER BY q.quotation_date DESC, q.quotation_code DESC
        """
        cur.execute(sql, (project_id,)) # project_id をタプルとして渡す
        rows = cur.fetchall()
        return rows
    except sqlite3.Error as e:
        print(f"Error fetching quotations by project_id ({project_id}): {e}")
        return []
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # (テストコードは変更なし)
    print("Running database operations tests...")
    # ... (既存のテストコード) ...