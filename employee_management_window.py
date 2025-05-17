# employee_management_window.py

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime # ### datetimeオブジェクトを扱うためにインポート ###
import database_operations as db_ops # データベース操作関数をインポート

class EmployeeManagementWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("社員管理")
        # 社員情報は項目が多いため、ウィンドウサイズを大きめにします
        self.geometry("1100x750") 
        self.db_ops = db_ops
        self.selected_employee_id = None # 選択中の社員IDを保持

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self._create_widgets()
        self.load_employees_to_treeview() # 後で実装

    def _create_widgets(self):
        # --- メインフレーム ---
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- スタイル設定 (オプション) ---
        style = ttk.Style(self)
        # Treeviewのフォントや行の高さを調整したければここで設定
        style.configure("Treeview", font=("メイリオ", 10)) 
        style.configure("Treeview.Heading", font=("メイリオ", 10, "bold"))

        # --- 入力フォームフレーム ---
        form_frame = ttk.LabelFrame(main_frame, text="社員情報入力", padding="10")
        form_frame.pack(fill=tk.X, pady=5)
        self._create_form_fields(form_frame) # 入力フィールド作成メソッド呼び出し

        # --- 操作ボタンフレーム ---
        action_frame = ttk.Frame(main_frame, padding=(0, 5, 0, 10))
        action_frame.pack(fill=tk.X)
        self._create_action_buttons(action_frame) # 操作ボタン作成メソッド呼び出し

        # --- 一覧表示フレーム ---
        tree_frame = ttk.LabelFrame(main_frame, text="社員一覧", padding="10")
        tree_frame.pack(fill=tk.BOTH, expand=True)
        self._create_treeview(tree_frame) # 一覧表示Treeview作成メソッド呼び出し

# employee_management_window.py の _create_form_fields メソッドを修正・実装

    def _create_form_fields(self, parent_frame):
        # 各入力ウィジェットは self.変数名 でアクセスできるようにする
        # フィールドをいくつかの列に分けて配置 (例: 3xN グリッド + 備考)
        
        # --- 1列目 ---
        row_offset = 0
        ttk.Label(parent_frame, text="社員コード:").grid(row=row_offset, column=0, padx=5, pady=2, sticky=tk.W)
        self.employee_code_entry = ttk.Entry(parent_frame, width=20)
        self.employee_code_entry.grid(row=row_offset, column=1, padx=5, pady=2, sticky=tk.EW)
        row_offset += 1

        ttk.Label(parent_frame, text="氏名 (必須):").grid(row=row_offset, column=0, padx=5, pady=2, sticky=tk.W)
        self.full_name_entry = ttk.Entry(parent_frame, width=25)
        self.full_name_entry.grid(row=row_offset, column=1, padx=5, pady=2, sticky=tk.EW)
        row_offset += 1

        ttk.Label(parent_frame, text="氏名かな:").grid(row=row_offset, column=0, padx=5, pady=2, sticky=tk.W)
        self.name_kana_entry = ttk.Entry(parent_frame, width=25)
        self.name_kana_entry.grid(row=row_offset, column=1, padx=5, pady=2, sticky=tk.EW)
        row_offset += 1
        
        ttk.Label(parent_frame, text="CCUS ID:").grid(row=row_offset, column=0, padx=5, pady=2, sticky=tk.W)
        self.ccus_id_entry = ttk.Entry(parent_frame, width=20)
        self.ccus_id_entry.grid(row=row_offset, column=1, padx=5, pady=2, sticky=tk.EW)
        row_offset += 1

        ttk.Label(parent_frame, text="生年月日:").grid(row=row_offset, column=0, padx=5, pady=2, sticky=tk.W)
        self.date_of_birth_entry = ttk.Entry(parent_frame, width=15)
        self.date_of_birth_entry.grid(row=row_offset, column=1, padx=5, pady=2, sticky=tk.W)
        self.date_of_birth_entry.insert(0, "YYYY-MM-DD") # プレースホルダ
        row_offset += 1

        ttk.Label(parent_frame, text="性別:").grid(row=row_offset, column=0, padx=5, pady=2, sticky=tk.W)
        self.gender_options = ["男性", "女性", "その他"]
        self.gender_combobox = ttk.Combobox(parent_frame, values=self.gender_options, width=12, state="readonly")
        self.gender_combobox.grid(row=row_offset, column=1, padx=5, pady=2, sticky=tk.W)
        row_offset += 1
        
        ttk.Label(parent_frame, text="役職:").grid(row=row_offset, column=0, padx=5, pady=2, sticky=tk.W)
        self.position_entry = ttk.Entry(parent_frame, width=20)
        self.position_entry.grid(row=row_offset, column=1, padx=5, pady=2, sticky=tk.EW)
        row_offset += 1
        
        # --- 2列目 ---
        row_offset = 0
        ttk.Label(parent_frame, text="職種 (必須):").grid(row=row_offset, column=2, padx=5, pady=2, sticky=tk.W)
        self.job_title_entry = ttk.Entry(parent_frame, width=25)
        self.job_title_entry.grid(row=row_offset, column=3, padx=5, pady=2, sticky=tk.EW)
        row_offset += 1

        ttk.Label(parent_frame, text="雇入年月日:").grid(row=row_offset, column=2, padx=5, pady=2, sticky=tk.W)
        self.employment_date_entry = ttk.Entry(parent_frame, width=15)
        self.employment_date_entry.grid(row=row_offset, column=3, padx=5, pady=2, sticky=tk.W)
        self.employment_date_entry.insert(0, "YYYY-MM-DD")
        row_offset += 1
        
        ttk.Label(parent_frame, text="経験年数(職種):").grid(row=row_offset, column=2, padx=5, pady=2, sticky=tk.W)
        self.experience_years_trade_entry = ttk.Entry(parent_frame, width=10)
        self.experience_years_trade_entry.grid(row=row_offset, column=3, padx=5, pady=2, sticky=tk.W)
        row_offset += 1

        ttk.Label(parent_frame, text="電話番号:").grid(row=row_offset, column=2, padx=5, pady=2, sticky=tk.W)
        self.phone_number_entry = ttk.Entry(parent_frame, width=20)
        self.phone_number_entry.grid(row=row_offset, column=3, padx=5, pady=2, sticky=tk.EW)
        row_offset += 1

        ttk.Label(parent_frame, text="健康診断受診日:").grid(row=row_offset, column=2, padx=5, pady=2, sticky=tk.W)
        self.last_health_check_date_entry = ttk.Entry(parent_frame, width=15)
        self.last_health_check_date_entry.grid(row=row_offset, column=3, padx=5, pady=2, sticky=tk.W)
        self.last_health_check_date_entry.insert(0, "YYYY-MM-DD")
        row_offset += 1

        ttk.Label(parent_frame, text="血液型:").grid(row=row_offset, column=2, padx=5, pady=2, sticky=tk.W)
        self.blood_type_entry = ttk.Entry(parent_frame, width=10) # またはCombobox
        self.blood_type_entry.grid(row=row_offset, column=3, padx=5, pady=2, sticky=tk.W)
        row_offset += 1
        
        ttk.Label(parent_frame, text="在籍状況:").grid(row=row_offset, column=2, padx=5, pady=2, sticky=tk.W)
        self.is_active_options = ["在籍中", "退職"] # 表示用
        self.is_active_combobox = ttk.Combobox(parent_frame, values=self.is_active_options, width=12, state="readonly")
        self.is_active_combobox.grid(row=row_offset, column=3, padx=5, pady=2, sticky=tk.W)
        self.is_active_combobox.set("在籍中") # デフォルト
        row_offset += 1

        # --- 3列目 (緊急連絡先など) ---
        row_offset = 0
        ttk.Label(parent_frame, text="緊急連絡先氏名:").grid(row=row_offset, column=4, padx=5, pady=2, sticky=tk.W)
        self.emergency_contact_name_entry = ttk.Entry(parent_frame, width=25)
        self.emergency_contact_name_entry.grid(row=row_offset, column=5, padx=5, pady=2, sticky=tk.EW)
        row_offset += 1

        ttk.Label(parent_frame, text="緊急連絡先電話:").grid(row=row_offset, column=4, padx=5, pady=2, sticky=tk.W)
        self.emergency_contact_phone_entry = ttk.Entry(parent_frame, width=20)
        self.emergency_contact_phone_entry.grid(row=row_offset, column=5, padx=5, pady=2, sticky=tk.EW)
        row_offset += 1

        ttk.Label(parent_frame, text="緊急連絡先続柄:").grid(row=row_offset, column=4, padx=5, pady=2, sticky=tk.W)
        self.emergency_contact_relationship_entry = ttk.Entry(parent_frame, width=15)
        self.emergency_contact_relationship_entry.grid(row=row_offset, column=5, padx=5, pady=2, sticky=tk.EW)
        row_offset += 1
        
        # --- 住所 (幅広) ---
        current_row_for_address = 7 # 他の列の最大行数に合わせて調整
        ttk.Label(parent_frame, text="住所:").grid(row=current_row_for_address, column=0, padx=5, pady=2, sticky=tk.NW)
        self.address_entry = ttk.Entry(parent_frame, width=40) # Textウィジェットも可
        self.address_entry.grid(row=current_row_for_address, column=1, columnspan=5, padx=5, pady=2, sticky=tk.EW)

        # --- 各種備考欄 (Textウィジェットを使用) ---
        notes_start_row = current_row_for_address + 1
        
        ttk.Label(parent_frame, text="社会保険(備考):").grid(row=notes_start_row, column=0, padx=5, pady=2, sticky=tk.NW)
        self.social_insurance_notes_text = tk.Text(parent_frame, width=30, height=2)
        self.social_insurance_notes_text.grid(row=notes_start_row, column=1, rowspan=2, padx=5, pady=2, sticky=tk.NSEW)

        ttk.Label(parent_frame, text="退職金共済(備考):").grid(row=notes_start_row, column=2, padx=5, pady=2, sticky=tk.NW)
        self.retirement_allowance_notes_text = tk.Text(parent_frame, width=30, height=2)
        self.retirement_allowance_notes_text.grid(row=notes_start_row, column=3, rowspan=2, padx=5, pady=2, sticky=tk.NSEW)

        ttk.Label(parent_frame, text="保有資格(備考):").grid(row=notes_start_row, column=4, padx=5, pady=2, sticky=tk.NW)
        self.qualifications_notes_text = tk.Text(parent_frame, width=30, height=2)
        self.qualifications_notes_text.grid(row=notes_start_row, column=5, rowspan=2, padx=5, pady=2, sticky=tk.NSEW)
        
        notes_start_row += 2 # 次の備考欄の開始行

        ttk.Label(parent_frame, text="有給残(備考):").grid(row=notes_start_row, column=0, padx=5, pady=2, sticky=tk.NW)
        self.paid_leave_notes_text = tk.Text(parent_frame, width=30, height=2)
        self.paid_leave_notes_text.grid(row=notes_start_row, column=1, rowspan=2, padx=5, pady=2, sticky=tk.NSEW)

        ttk.Label(parent_frame, text="その他備考:").grid(row=notes_start_row, column=2, padx=5, pady=2, sticky=tk.NW)
        self.remarks_text = tk.Text(parent_frame, width=30, height=2)
        self.remarks_text.grid(row=notes_start_row, column=3, rowspan=2, columnspan=3, padx=5, pady=2, sticky=tk.NSEW) # 幅広に

        # フォームフレームの列の伸縮設定 (入力欄がウィンドウ幅に応じて広がるように)
        for i in [1, 3, 5, 7]: # Entry/Textウィジェットがある列番号
             parent_frame.columnconfigure(i, weight=1)
        for i in range(notes_start_row + 2): # フォーム全体の行
            parent_frame.rowconfigure(i, weight=1 if i >= notes_start_row -2 else 0) # 備考欄の高さを伸縮
# employee_management_window.py の _create_action_buttons メソッドを修正・実装

    def _create_action_buttons(self, parent_frame):
        # 「登録」「更新」「削除」「フォームクリア」ボタンを配置
        
        self.add_button = ttk.Button(parent_frame, text="登録", command=self.add_new_employee)
        self.add_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.update_button = ttk.Button(parent_frame, text="更新", command=self.update_selected_employee, state=tk.DISABLED)
        self.update_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.delete_button = ttk.Button(parent_frame, text="削除", command=self.delete_selected_employee, state=tk.DISABLED)
        self.delete_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.clear_button = ttk.Button(parent_frame, text="フォームクリア", command=self.clear_employee_form)
        self.clear_button.pack(side=tk.LEFT, padx=5, pady=5)

    # --- ボタンのコマンド (プレースホルダ) ---
    # これらは後で本格的に実装します
# employee_management_window.py の add_new_employee メソッドを修正

    def add_new_employee(self):
        # フォームから値を取得
        employee_code = self.employee_code_entry.get().strip()
        full_name = self.full_name_entry.get().strip()
        name_kana = self.name_kana_entry.get().strip()
        ccus_id = self.ccus_id_entry.get().strip()
        date_of_birth = self.date_of_birth_entry.get().strip()
        gender = self.gender_combobox.get()
        position = self.position_entry.get().strip()
        address = self.address_entry.get().strip()
        phone_number = self.phone_number_entry.get().strip()
        job_title = self.job_title_entry.get().strip()
        employment_date = self.employment_date_entry.get().strip()
        experience_years_str = self.experience_years_trade_entry.get().strip()
        emergency_contact_name = self.emergency_contact_name_entry.get().strip()
        emergency_contact_phone = self.emergency_contact_phone_entry.get().strip()
        emergency_contact_relationship = self.emergency_contact_relationship_entry.get().strip()
        last_health_check_date = self.last_health_check_date_entry.get().strip()
        blood_type = self.blood_type_entry.get().strip()
        social_insurance_status_notes = self.social_insurance_notes_text.get("1.0", tk.END).strip()
        retirement_allowance_notes = self.retirement_allowance_notes_text.get("1.0", tk.END).strip()
        qualifications_notes = self.qualifications_notes_text.get("1.0", tk.END).strip()
        paid_leave_days_notes = self.paid_leave_notes_text.get("1.0", tk.END).strip()
        is_active_str = self.is_active_combobox.get()
        remarks = self.remarks_text.get("1.0", tk.END).strip()

        # --- 入力値のバリデーション ---
        if not full_name:
            messagebox.showerror("入力エラー", "氏名は必須です。")
            self.full_name_entry.focus_set()
            return
        if not job_title:
            messagebox.showerror("入力エラー", "職種は必須です。")
            self.job_title_entry.focus_set()
            return
        
        # employee_code と ccus_id は空文字をNoneとして扱う (UNIQUE制約はNULLを複数許容するため)
        employee_code_to_db = employee_code if employee_code else None
        ccus_id_to_db = ccus_id if ccus_id else None

        # --- データ型の変換とさらなるチェック ---
        experience_years_trade = None
        if experience_years_str:
            try:
                experience_years_trade = float(experience_years_str) # 小数点も可
            except ValueError:
                messagebox.showerror("入力エラー", "経験年数は有効な数値を入力してください。")
                self.experience_years_trade_entry.focus_set()
                return

        is_active = 1 if is_active_str == "在籍中" else 0 # Comboboxの表示名からDB保存用の値(1 or 0)へ変換

        # 日付フィールドがプレースホルダのままなら空文字（またはNone）として扱う
        date_of_birth_to_db = date_of_birth if date_of_birth != "YYYY-MM-DD" else None
        employment_date_to_db = employment_date if employment_date != "YYYY-MM-DD" else None
        last_health_check_date_to_db = last_health_check_date if last_health_check_date != "YYYY-MM-DD" else None
        
        # TODO: 日付形式の厳密なバリデーション (YYYY-MM-DD) も追加するとより堅牢

        # データベースに追加
        result = self.db_ops.add_employee(
            employee_code_to_db, full_name, name_kana, ccus_id_to_db, 
            date_of_birth_to_db, gender, position, address, phone_number, 
            job_title, employment_date_to_db, experience_years_trade, 
            emergency_contact_name, emergency_contact_phone, 
            emergency_contact_relationship, last_health_check_date_to_db, 
            blood_type, social_insurance_status_notes, 
            retirement_allowance_notes, qualifications_notes, 
            paid_leave_days_notes, is_active, remarks
        )

        if isinstance(result, int): # 成功時 (新しい employee_id が返る)
            messagebox.showinfo("登録成功", f"社員「{full_name}」を登録しました。(ID: {result})")
            self.clear_employee_form()
            self.load_employees_to_treeview() # 一覧を更新
        elif result == "DUPLICATE_EMP_CODE":
            messagebox.showerror("登録エラー", f"社員コード「{employee_code}」は既に登録されています。")
            self.employee_code_entry.focus_set()
        elif result == "DUPLICATE_CCUS_ID":
            messagebox.showerror("登録エラー", f"CCUS ID「{ccus_id}」は既に登録されています。")
            self.ccus_id_entry.focus_set()
        elif result == "NOT_NULL_VIOLATION":
            messagebox.showerror("登録エラー", "必須項目（氏名や職種など）が入力されていません。")
        elif result == "INTEGRITY_ERROR":
            messagebox.showerror("登録エラー", "データベースの整合性エラーが発生しました。")
        elif result == "CONNECTION_ERROR" or result == "OTHER_DB_ERROR" or result is None:
            messagebox.showerror("登録エラー", "データベースエラーにより社員情報の登録に失敗しました。")
        else: # 想定外の戻り値
            messagebox.showerror("登録エラー", f"不明なエラーが発生しました。({result})")

# employee_management_window.py の update_selected_employee メソッドを修正

    def update_selected_employee(self):
        if not self.selected_employee_id:
            messagebox.showwarning("未選択", "更新する社員が選択されていません。")
            return

        # フォームから現在の入力値を取得 (add_new_employee と同様)
        employee_code = self.employee_code_entry.get().strip()
        full_name = self.full_name_entry.get().strip()
        name_kana = self.name_kana_entry.get().strip()
        ccus_id = self.ccus_id_entry.get().strip()
        date_of_birth = self.date_of_birth_entry.get().strip()
        gender = self.gender_combobox.get()
        position = self.position_entry.get().strip()
        address = self.address_entry.get().strip()
        phone_number = self.phone_number_entry.get().strip()
        job_title = self.job_title_entry.get().strip()
        employment_date = self.employment_date_entry.get().strip()
        experience_years_str = self.experience_years_trade_entry.get().strip()
        emergency_contact_name = self.emergency_contact_name_entry.get().strip()
        emergency_contact_phone = self.emergency_contact_phone_entry.get().strip()
        emergency_contact_relationship = self.emergency_contact_relationship_entry.get().strip()
        last_health_check_date = self.last_health_check_date_entry.get().strip()
        blood_type = self.blood_type_entry.get().strip()
        social_insurance_status_notes = self.social_insurance_notes_text.get("1.0", tk.END).strip()
        retirement_allowance_notes = self.retirement_allowance_notes_text.get("1.0", tk.END).strip()
        qualifications_notes = self.qualifications_notes_text.get("1.0", tk.END).strip()
        paid_leave_days_notes = self.paid_leave_notes_text.get("1.0", tk.END).strip()
        is_active_str = self.is_active_combobox.get()
        remarks = self.remarks_text.get("1.0", tk.END).strip()

        # --- 入力値のバリデーション ---
        if not full_name:
            messagebox.showerror("入力エラー", "氏名は必須です。")
            self.full_name_entry.focus_set()
            return
        if not job_title:
            messagebox.showerror("入力エラー", "職種は必須です。")
            self.job_title_entry.focus_set()
            return
        
        employee_code_to_db = employee_code if employee_code else None
        ccus_id_to_db = ccus_id if ccus_id else None

        # --- データ型の変換とさらなるチェック ---
        experience_years_trade = None
        if experience_years_str:
            try:
                experience_years_trade = float(experience_years_str)
            except ValueError:
                messagebox.showerror("入力エラー", "経験年数は有効な数値を入力してください。")
                self.experience_years_trade_entry.focus_set()
                return

        is_active = 1 if is_active_str == "在籍中" else 0

        date_of_birth_to_db = date_of_birth if date_of_birth != "YYYY-MM-DD" else None
        employment_date_to_db = employment_date if employment_date != "YYYY-MM-DD" else None
        last_health_check_date_to_db = last_health_check_date if last_health_check_date != "YYYY-MM-DD" else None

        # 更新確認
        confirm_message = f"社員「{full_name}」(コード: {employee_code or 'N/A'}) の情報を本当に更新しますか？"
        confirm = messagebox.askyesno("更新確認", confirm_message)
        if not confirm:
            messagebox.showinfo("キャンセル", "更新はキャンセルされました。")
            return

        # データベースの更新処理を呼び出す
        result = self.db_ops.update_employee(
            self.selected_employee_id, # 更新対象のID
            employee_code_to_db, full_name, name_kana, ccus_id_to_db, 
            date_of_birth_to_db, gender, position, address, phone_number, 
            job_title, employment_date_to_db, experience_years_trade, 
            emergency_contact_name, emergency_contact_phone, 
            emergency_contact_relationship, last_health_check_date_to_db, 
            blood_type, social_insurance_status_notes, 
            retirement_allowance_notes, qualifications_notes, 
            paid_leave_days_notes, is_active, remarks
        )

        if result is True: # 成功時
            messagebox.showinfo("更新成功", f"社員「{full_name}」(コード: {employee_code or 'N/A'}) の情報を更新しました。")
            self.clear_employee_form()
            self.load_employees_to_treeview() # 一覧を更新
        elif result == "DUPLICATE_EMP_CODE":
            messagebox.showerror("更新エラー", f"社員コード「{employee_code}」は既に他の社員に使用されています。")
            self.employee_code_entry.focus_set()
        elif result == "DUPLICATE_CCUS_ID":
            messagebox.showerror("更新エラー", f"CCUS ID「{ccus_id}」は既に他の社員に使用されています。")
            self.ccus_id_entry.focus_set()
        elif result == "NOT_FOUND":
            messagebox.showerror("更新エラー", f"更新対象の社員 (ID: {self.selected_employee_id}) が見つかりませんでした。一覧を再読み込みしてください。")
            self.clear_employee_form()
            self.load_employees_to_treeview()
        elif result == "NOT_NULL_VIOLATION":
            messagebox.showerror("更新エラー", "必須項目（氏名や職種など）が入力されていません。")
        elif result == "INTEGRITY_ERROR":
            messagebox.showerror("更新エラー", "データベースの整合性エラーが発生しました。")
        elif result == "CONNECTION_ERROR" or result == "OTHER_DB_ERROR":
            messagebox.showerror("更新エラー", "データベースエラーにより社員情報の更新に失敗しました。")
        else: # 想定外の戻り値
            messagebox.showerror("更新エラー", f"不明なエラーが発生しました。({result})")

# employee_management_window.py の delete_selected_employee メソッドを修正

# employee_management_window.py の delete_selected_employee メソッドを修正

    def delete_selected_employee(self):
        if not self.selected_employee_id:
            messagebox.showwarning("未選択", "削除する社員が選択されていません。")
            return
        
        # データベースから最新の社員情報を取得して氏名などを確認メッセージに含める
        employee_info = self.db_ops.get_employee_by_id(self.selected_employee_id)
        employee_display_name = employee_info[2] if employee_info else f"ID: {self.selected_employee_id}" # full_name at index 2

        confirm_message = f"社員「{employee_display_name}」(ID: {self.selected_employee_id}) の情報を本当に削除しますか？\n"
        confirm_message += "この操作は元に戻せません。"
        # TODO: もし社員が何らかの作業や案件に割り当てられている場合、
        #       削除できないようにするか、警告を出すなどの考慮が将来的には必要かもしれません。
        #       現状のDBスキーマでは直接的な参照制約は少ないですが、運用上は重要です。

        confirm = messagebox.askyesno("削除確認", confirm_message)
        
        if confirm:
            result = self.db_ops.delete_employee(self.selected_employee_id)
            
            if result is True: # データベース操作関数が True を返したら成功
                messagebox.showinfo("削除成功", f"社員「{employee_display_name}」(ID: {self.selected_employee_id}) の情報を削除しました。")
                self.clear_employee_form() 
                self.load_employees_to_treeview() 
            elif result == "NOT_FOUND":
                messagebox.showerror("削除エラー", f"削除対象の社員 (ID: {self.selected_employee_id}) が見つかりませんでした。一覧を再読み込みしてください。")
                self.clear_employee_form()
                self.load_employees_to_treeview()
            # delete_employee 関数が返す可能性のある他のエラーコードもここに追加できます
            # (例: "FK_CONSTRAINT_FAILED" など、もしあれば)
            elif result == "CONNECTION_ERROR" or result == "OTHER_DB_ERROR":
                messagebox.showerror("削除エラー", "データベースエラーにより社員情報の削除に失敗しました。")
            else: # 想定外の戻り値やその他のエラー
                messagebox.showerror("削除エラー", f"不明なエラーが発生しました。({result})")
        else:
            messagebox.showinfo("キャンセル", "削除はキャンセルされました。")

    def clear_employee_form(self):
        # messagebox.showinfo("未実装", "フォームクリア処理は未実装です。")
        # 顧客管理画面や案件管理画面の clear_form を参考に、各エントリーをクリアします
        # (後で本格的に実装しますが、枠組みとして簡単なクリア処理を入れておきます)
        
        # Entryウィジェットのクリア
        entry_widgets = [
            self.employee_code_entry, self.full_name_entry, self.name_kana_entry,
            self.ccus_id_entry, self.date_of_birth_entry, self.position_entry,
            self.address_entry, self.phone_number_entry, self.job_title_entry,
            self.employment_date_entry, self.experience_years_trade_entry,
            self.emergency_contact_name_entry, self.emergency_contact_phone_entry,
            self.emergency_contact_relationship_entry, self.last_health_check_date_entry,
            self.blood_type_entry
        ]
        for entry in entry_widgets:
            entry.delete(0, tk.END)

        # Comboboxのクリア (またはデフォルト値に設定)
        self.gender_combobox.set("") # または self.gender_options[0] など
        self.is_active_combobox.set("在籍中") # デフォルト値

        # Textウィジェットのクリア
        text_widgets = [
            self.social_insurance_notes_text, self.retirement_allowance_notes_text,
            self.qualifications_notes_text, self.paid_leave_notes_text, self.remarks_text
        ]
        for text_widget in text_widgets:
            text_widget.delete("1.0", tk.END)

        # 日付フィールドのプレースホルダを再表示 (任意)
        self.date_of_birth_entry.insert(0, "YYYY-MM-DD")
        self.employment_date_entry.insert(0, "YYYY-MM-DD")
        self.last_health_check_date_entry.insert(0, "YYYY-MM-DD")
        
        self.selected_employee_id = None
        # if hasattr(self, 'employee_tree') and self.employee_tree.selection():
        #     self.employee_tree.selection_remove(self.employee_tree.selection()[0])
        self.update_button.config(state=tk.DISABLED)
        self.delete_button.config(state=tk.DISABLED)
        self.employee_code_entry.focus() # フォーカスを社員コードへ
        print("Employee form cleared.")
# employee_management_window.py に以下のメソッドを追加（または既存のプレースホルダを置き換え）

# employee_management_window.py の load_employees_to_treeview メソッドを修正

    def load_employees_to_treeview(self):
        """データベースから社員情報を読み込み、Treeviewに表示する"""
        if hasattr(self, 'update_button'): 
            self.update_button.config(state=tk.DISABLED)
        if hasattr(self, 'delete_button'):
            self.delete_button.config(state=tk.DISABLED)
        self.selected_employee_id = None
        
        for item in self.employee_tree.get_children():
            self.employee_tree.delete(item)
        
        employees_data = self.db_ops.get_all_employees()
        
        if employees_data:
            today = datetime.today().date() # ### 年齢計算用に今日の日付を取得 ###
            for emp_tuple in employees_data:
                # get_all_employees() が返すタプルのインデックス:
                # (0:employee_id, ..., 5:date_of_birth, ...)

                date_of_birth_str = emp_tuple[5] or ""
                age_display = "" # デフォルトは空

                # ### 年齢計算ロジックを追加 ###
                if date_of_birth_str:
                    try:
                        birth_date = datetime.strptime(date_of_birth_str, "%Y-%m-%d").date()
                        age = today.year - birth_date.year - \
                              ((today.month, today.day) < (birth_date.month, birth_date.day))
                        age_display = str(age)
                    except ValueError:
                        age_display = "無効な日付" # または "" (空文字)
                # ### 年齢計算ロジックここまで ###

                display_values = (
                    emp_tuple[0],        # employee_id
                    emp_tuple[1] or "",  # employee_code
                    emp_tuple[2],        # full_name
                    emp_tuple[10],       # job_title
                    emp_tuple[7] or "",  # position
                    emp_tuple[9] or "",  # phone_number
                    date_of_birth_str,   # date_of_birth
                    age_display          # age (計算結果またはエラー表示)
                )
                self.employee_tree.insert("", tk.END, values=display_values, iid=emp_tuple[0])
# employee_management_window.py の _create_treeview メソッドを修正
# employee_management_window.py に以下のメソッドを追加
# (例えば、load_employees_to_treeview の後、ボタンのコマンドメソッドの前など)

    def on_employee_tree_select(self, event):
        """Employee Treeviewで項目が選択されたときに呼び出される"""
        selected_items = self.employee_tree.selection() 

        if not selected_items: 
            self.selected_employee_id = None
            # フォームクリアは clear_employee_form に任せるが、ボタンの状態はここで制御
            if hasattr(self, 'update_button'): self.update_button.config(state=tk.DISABLED)
            if hasattr(self, 'delete_button'): self.delete_button.config(state=tk.DISABLED)
            return

        selected_iid = selected_items[0] 
        self.selected_employee_id = selected_iid 

        # データベースから完全な社員情報を取得
        # get_employee_by_id が返すタプルのインデックスを確認
        # (0:employee_id, 1:employee_code, 2:full_name, 3:name_kana, 4:ccus_id, 
        #  5:date_of_birth, 6:gender, 7:position, 8:address, 9:phone_number, 
        #  10:job_title, 11:employment_date, 12:experience_years_trade, 
        #  13:emergency_contact_name, 14:emergency_contact_phone, 
        #  15:emergency_contact_relationship, 16:last_health_check_date, 
        #  17:blood_type, 18:social_insurance_status_notes, 
        #  19:retirement_allowance_notes, 20:qualifications_notes, 
        #  21:paid_leave_days_notes, 22:is_active, 23:remarks, ...)
        emp_data = self.db_ops.get_employee_by_id(self.selected_employee_id)

        if emp_data:
            # フォームの既存の値をクリア (個別にクリア)
            entries_to_clear = [
                self.employee_code_entry, self.full_name_entry, self.name_kana_entry,
                self.ccus_id_entry, self.date_of_birth_entry, self.position_entry,
                self.address_entry, self.phone_number_entry, self.job_title_entry,
                self.employment_date_entry, self.experience_years_trade_entry,
                self.emergency_contact_name_entry, self.emergency_contact_phone_entry,
                self.emergency_contact_relationship_entry, self.last_health_check_date_entry,
                self.blood_type_entry
            ]
            for entry in entries_to_clear:
                entry.delete(0, tk.END)
            
            texts_to_clear = [
                self.social_insurance_notes_text, self.retirement_allowance_notes_text,
                self.qualifications_notes_text, self.paid_leave_notes_text, self.remarks_text
            ]
            for text_widget in texts_to_clear:
                text_widget.delete("1.0", tk.END)

            self.gender_combobox.set("")
            self.is_active_combobox.set("")

            # フォームに値を設定
            if emp_data[1] is not None: self.employee_code_entry.insert(0, emp_data[1])
            self.full_name_entry.insert(0, emp_data[2] or "")
            if emp_data[3] is not None: self.name_kana_entry.insert(0, emp_data[3])
            if emp_data[4] is not None: self.ccus_id_entry.insert(0, emp_data[4])
            if emp_data[5] is not None: self.date_of_birth_entry.insert(0, emp_data[5])
            
            if emp_data[6] in self.gender_options: # 性別
                self.gender_combobox.set(emp_data[6])
            
            if emp_data[7] is not None: self.position_entry.insert(0, emp_data[7])
            if emp_data[8] is not None: self.address_entry.insert(0, emp_data[8])
            if emp_data[9] is not None: self.phone_number_entry.insert(0, emp_data[9])
            self.job_title_entry.insert(0, emp_data[10] or "")
            if emp_data[11] is not None: self.employment_date_entry.insert(0, emp_data[11])
            if emp_data[12] is not None: self.experience_years_trade_entry.insert(0, str(emp_data[12]))
            
            if emp_data[13] is not None: self.emergency_contact_name_entry.insert(0, emp_data[13])
            if emp_data[14] is not None: self.emergency_contact_phone_entry.insert(0, emp_data[14])
            if emp_data[15] is not None: self.emergency_contact_relationship_entry.insert(0, emp_data[15])
            
            if emp_data[16] is not None: self.last_health_check_date_entry.insert(0, emp_data[16])
            if emp_data[17] is not None: self.blood_type_entry.insert(0, emp_data[17])
            
            if emp_data[18] is not None: self.social_insurance_notes_text.insert("1.0", emp_data[18])
            if emp_data[19] is not None: self.retirement_allowance_notes_text.insert("1.0", emp_data[19])
            if emp_data[20] is not None: self.qualifications_notes_text.insert("1.0", emp_data[20])
            if emp_data[21] is not None: self.paid_leave_notes_text.insert("1.0", emp_data[21])
            
            # is_active (0 or 1) を表示用の文字列に変換してComboboxにセット
            is_active_value = emp_data[22]
            if is_active_value == 1:
                self.is_active_combobox.set("在籍中")
            elif is_active_value == 0:
                self.is_active_combobox.set("退職")
            else:
                self.is_active_combobox.set("") # 不明な場合は空

            if emp_data[23] is not None: self.remarks_text.insert("1.0", emp_data[23])

            # 日付フィールドが空文字などでクリアされてしまった場合、プレースホルダを再表示
            if not self.date_of_birth_entry.get(): self.date_of_birth_entry.insert(0, "YYYY-MM-DD")
            if not self.employment_date_entry.get(): self.employment_date_entry.insert(0, "YYYY-MM-DD")
            if not self.last_health_check_date_entry.get(): self.last_health_check_date_entry.insert(0, "YYYY-MM-DD")

            if hasattr(self, 'update_button'): self.update_button.config(state=tk.NORMAL)
            if hasattr(self, 'delete_button'): self.delete_button.config(state=tk.NORMAL)
        else:
            messagebox.showwarning("データ取得エラー", f"社員ID {self.selected_employee_id} の情報取得に失敗しました。")
            self.clear_employee_form() # フォームをクリアし、ボタンを無効化

    def _create_treeview(self, parent_frame):
        # 社員一覧を表示するttk.Treeviewを配置
        
        # ### 変更点: 表示カラムの変更 ###
        columns = (
            "employee_id", "employee_code", "full_name", "job_title", 
            "position", "phone_number", "date_of_birth", "age" # is_active を削除し、生年月日と年齢を追加
        )
        self.employee_tree = ttk.Treeview(parent_frame, columns=columns, show="headings", height=12)

        # 各列のヘッダーテキストと幅などを設定
        self.employee_tree.heading("employee_id", text="ID")
        self.employee_tree.column("employee_id", width=40, anchor=tk.CENTER)
        
        self.employee_tree.heading("employee_code", text="社員コード")
        self.employee_tree.column("employee_code", width=100)

        self.employee_tree.heading("full_name", text="氏名")
        self.employee_tree.column("full_name", width=150)

        self.employee_tree.heading("job_title", text="職種")
        self.employee_tree.column("job_title", width=120)

        self.employee_tree.heading("position", text="役職")
        self.employee_tree.column("position", width=100)
        
        self.employee_tree.heading("phone_number", text="電話番号")
        self.employee_tree.column("phone_number", width=120)

        # ### 追加: 生年月日の列設定 ###
        self.employee_tree.heading("date_of_birth", text="生年月日")
        self.employee_tree.column("date_of_birth", width=100, anchor=tk.CENTER)

        # ### 追加: 年齢の列設定 (表示内容は後で実装) ###
        self.employee_tree.heading("age", text="年齢")
        self.employee_tree.column("age", width=50, anchor=tk.CENTER)
        
        # ### 削除: is_active の列設定は不要になったので削除 ###
        # self.employee_tree.heading("is_active", text="在籍状況")
        # self.employee_tree.column("is_active", width=70, anchor=tk.CENTER)

        # スクロールバーの追加 (変更なし)
        scrollbar_y = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.employee_tree.yview)
        scrollbar_x = ttk.Scrollbar(parent_frame, orient=tk.HORIZONTAL, command=self.employee_tree.xview)
        self.employee_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.employee_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")   
        scrollbar_x.grid(row=1, column=0, sticky="ew")   

        parent_frame.grid_rowconfigure(0, weight=1)   
        parent_frame.grid_columnconfigure(0, weight=1)

        # Treeview選択時のイベント設定 (これは後で本格実装します)
        self.employee_tree.bind("<<TreeviewSelect>>", self.on_employee_tree_select)
        
    def on_close(self):
        self.destroy()

# このファイル単体でテスト実行するためのコード
if __name__ == '__main__':
    root = tk.Tk()
    root.title("メインウィンドウ (テスト用)")
    
    def open_employee_window():
        if not hasattr(root, 'db_ops'): 
            root.db_ops = db_ops 
        employee_win = EmployeeManagementWindow(root)
        employee_win.grab_set() 
    
    open_button = ttk.Button(root, text="社員管理を開く", command=open_employee_window)
    open_button.pack(padx=20, pady=20)
    
    root.mainloop()