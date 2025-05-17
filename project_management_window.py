# project_management_window.py

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import database_operations as db_ops # データベース操作関数をインポート

class ProjectManagementWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("案件管理")
        self.geometry("1000x700") # ウィンドウサイズを適宜調整してください
        self.db_ops = db_ops
        self.selected_project_id = None # 選択中の案件IDを保持

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self._create_widgets()
        self.load_projects_to_treeview()

    def _create_widgets(self):
        # --- メインフレーム ---
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- スタイル設定 (オプション) ---
        style = ttk.Style(self)
        style.configure("Treeview", font=("メイリオ", 10)) # Treeviewのフォント例
        style.configure("Treeview.Heading", font=("メイリオ", 10, "bold"))

        # --- 入力フォームフレーム ---
        form_frame = ttk.LabelFrame(main_frame, text="案件情報入力", padding="10")
        form_frame.pack(fill=tk.X, pady=5)
        
        # 入力フィールドの配置 (詳細は次のステップで)
        self._create_form_fields(form_frame)

        # --- 操作ボタンフレーム ---
        action_frame = ttk.Frame(main_frame, padding=(0, 5, 0, 10))
        action_frame.pack(fill=tk.X)
        self._create_action_buttons(action_frame)

        # --- 一覧表示フレーム ---
        tree_frame = ttk.LabelFrame(main_frame, text="案件一覧", padding="10")
        tree_frame.pack(fill=tk.BOTH, expand=True)
        self._create_treeview(tree_frame)

# project_management_window.py の _create_form_fields メソッドを修正

    def _create_form_fields(self, parent_frame):
        # ラベルと入力ウィジェットを配置
        # 各エントリーウィジェットは self.変数名 でアクセスできるようにする
        
        # --- 1列目 ---
        ttk.Label(parent_frame, text="案件コード:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.project_code_entry = ttk.Entry(parent_frame, width=20)
        self.project_code_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)

        ttk.Label(parent_frame, text="案件名:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.project_name_entry = ttk.Entry(parent_frame, width=40)
        self.project_name_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=2, sticky=tk.EW) # 幅広に

        ttk.Label(parent_frame, text="顧客ID:").grid(row=2, column=0, padx=5, pady=2, sticky=tk.W)
        self.customer_id_entry = ttk.Entry(parent_frame, width=10)
        self.customer_id_entry.grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)
        # TODO: 将来的には顧客選択ボタンやComboboxに変更すると良い

        ttk.Label(parent_frame, text="親案件ID:").grid(row=3, column=0, padx=5, pady=2, sticky=tk.W)
        self.parent_project_id_entry = ttk.Entry(parent_frame, width=10)
        self.parent_project_id_entry.grid(row=3, column=1, padx=5, pady=2, sticky=tk.W)
        # TODO: 親案件を選択する仕組みを検討

        ttk.Label(parent_frame, text="現場住所:").grid(row=4, column=0, padx=5, pady=2, sticky=tk.W)
        self.site_address_entry = ttk.Entry(parent_frame, width=40)
        self.site_address_entry.grid(row=4, column=1, columnspan=3, padx=5, pady=2, sticky=tk.EW)

        # --- 2列目 (日付など) ---
        ttk.Label(parent_frame, text="受付日:").grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)
        self.reception_date_entry = ttk.Entry(parent_frame, width=12)
        self.reception_date_entry.grid(row=0, column=3, padx=5, pady=2, sticky=tk.W)
        # TODO: 日付ピッカーの導入検討 (例: YYYY-MM-DD)

        ttk.Label(parent_frame, text="着工予定日:").grid(row=0, column=4, padx=5, pady=2, sticky=tk.W)
        self.start_date_scheduled_entry = ttk.Entry(parent_frame, width=12)
        self.start_date_scheduled_entry.grid(row=0, column=5, padx=5, pady=2, sticky=tk.W)

        ttk.Label(parent_frame, text="完了予定日:").grid(row=1, column=4, padx=5, pady=2, sticky=tk.W) # 行を変更
        self.completion_date_scheduled_entry = ttk.Entry(parent_frame, width=12)
        self.completion_date_scheduled_entry.grid(row=1, column=5, padx=5, pady=2, sticky=tk.W)

        ttk.Label(parent_frame, text="実際の完了日:").grid(row=2, column=4, padx=5, pady=2, sticky=tk.W) # 行を変更
        self.actual_completion_date_entry = ttk.Entry(parent_frame, width=12)
        self.actual_completion_date_entry.grid(row=2, column=5, padx=5, pady=2, sticky=tk.W)
        
        # --- 3列目 (担当、金額、ステータスなど) ---
        ttk.Label(parent_frame, text="担当社員名:").grid(row=0, column=6, padx=5, pady=2, sticky=tk.W) # 新しい列
        self.responsible_staff_entry = ttk.Entry(parent_frame, width=15)
        self.responsible_staff_entry.grid(row=0, column=7, padx=5, pady=2, sticky=tk.EW)

        ttk.Label(parent_frame, text="見積金額(円):").grid(row=1, column=6, padx=5, pady=2, sticky=tk.W)
        self.estimated_amount_entry = ttk.Entry(parent_frame, width=15)
        self.estimated_amount_entry.grid(row=1, column=7, padx=5, pady=2, sticky=tk.EW)
        # TODO: 数値のみ入力可とするバリデーション

        ttk.Label(parent_frame, text="状況:").grid(row=2, column=6, padx=5, pady=2, sticky=tk.W)
        # 状況は選択式が良いので Combobox を使用
        self.status_options = [
            "見積中", "契約済", "施工中", "完了", "見積依頼", "見積提出済", 
            "失注", "請求済", "入金済", "キャンセル", "休止中", "保留", 
            "決済中", "クレーム対応"
        ]
        self.status_combobox = ttk.Combobox(parent_frame, values=self.status_options, width=13, state="readonly")
        self.status_combobox.grid(row=2, column=7, padx=5, pady=2, sticky=tk.EW)
        if self.status_options: # デフォルト値設定
            self.status_combobox.set(self.status_options[0])


        ttk.Label(parent_frame, text="備考:").grid(row=5, column=0, padx=5, pady=2, sticky=tk.NW) # NWで左上に寄せる
        self.remarks_text = tk.Text(parent_frame, width=40, height=4)
        self.remarks_text.grid(row=5, column=1, columnspan=7, rowspan=2, padx=5, pady=2, sticky=tk.NSEW) # 幅と高さを広くとる

        # グリッドの列と行の伸縮設定 (オプション)
        for i in range(8): # 0から7列目まで
            parent_frame.columnconfigure(i, weight=1 if i % 2 == 1 else 0) # 入力欄の列を伸縮
        parent_frame.rowconfigure(5, weight=1) # 備考欄の行を伸縮

    # ... (_create_form_fields メソッドは実装済みとして) ...

    def _create_action_buttons(self, parent_frame):
        # 「登録」「更新」「削除」「フォームクリア」ボタンを配置
        
        self.add_button = ttk.Button(parent_frame, text="登録", command=self.add_new_project)
        self.add_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.update_button = ttk.Button(parent_frame, text="更新", command=self.update_selected_project, state=tk.DISABLED)
        self.update_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.delete_button = ttk.Button(parent_frame, text="削除", command=self.delete_selected_project, state=tk.DISABLED)
        self.delete_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.clear_button = ttk.Button(parent_frame, text="フォームクリア", command=self.clear_project_form)
        self.clear_button.pack(side=tk.LEFT, padx=5, pady=5)

    def _create_treeview(self, parent_frame):
        # 案件一覧を表示するttk.Treeviewを配置
        # 表示するカラムを定義 (get_all_projects で取得する順番と内容を考慮)
        # (p.project_id, p.project_code, p.project_name, 
        #  p.customer_id, c.customer_name, 
        #  p.parent_project_id, pp.parent_project_code, 
        #  p.site_address, p.reception_date, p.start_date_scheduled, 
        #  p.completion_date_scheduled, p.actual_completion_date, 
        #  p.responsible_staff_name, p.estimated_amount, p.status, 
        #  p.remarks, p.created_at, p.updated_at)
        
        # Treeviewに表示する主なカラムを選択
        columns = (
            "project_id", "project_code", "project_name", "customer_name", 
            "status", "reception_date", "start_date_scheduled", "completion_date_scheduled", 
            "responsible_staff_name", "estimated_amount"
        )
        self.project_tree = ttk.Treeview(parent_frame, columns=columns, show="headings", height=15)

        # 各列のヘッダーテキストと幅などを設定
        self.project_tree.heading("project_id", text="ID")
        self.project_tree.column("project_id", width=40, anchor=tk.CENTER)
        
        self.project_tree.heading("project_code", text="案件コード")
        self.project_tree.column("project_code", width=100)

        self.project_tree.heading("project_name", text="案件名")
        self.project_tree.column("project_name", width=200)

        self.project_tree.heading("customer_name", text="顧客名")
        self.project_tree.column("customer_name", width=150)

        self.project_tree.heading("status", text="状況")
        self.project_tree.column("status", width=80)

        self.project_tree.heading("reception_date", text="受付日")
        self.project_tree.column("reception_date", width=90, anchor=tk.CENTER)
        
        self.project_tree.heading("start_date_scheduled", text="着工予定")
        self.project_tree.column("start_date_scheduled", width=90, anchor=tk.CENTER)

        self.project_tree.heading("completion_date_scheduled", text="完了予定")
        self.project_tree.column("completion_date_scheduled", width=90, anchor=tk.CENTER)

        self.project_tree.heading("responsible_staff_name", text="担当者")
        self.project_tree.column("responsible_staff_name", width=80)

        self.project_tree.heading("estimated_amount", text="見積金額(円)")
        self.project_tree.column("estimated_amount", width=100, anchor=tk.E) # Eは右寄せ

        # スクロールバーの追加
        scrollbar_y = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.project_tree.yview)
        scrollbar_x = ttk.Scrollbar(parent_frame, orient=tk.HORIZONTAL, command=self.project_tree.xview)
        self.project_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.project_tree.grid(row=0, column=0, sticky="nsew") # Treeviewを配置
        scrollbar_y.grid(row=0, column=1, sticky="ns")    # 縦スクロールバー
        scrollbar_x.grid(row=1, column=0, sticky="ew")    # 横スクロールバー

        parent_frame.grid_rowconfigure(0, weight=1)    # Treeviewの行が伸縮するように
        parent_frame.grid_columnconfigure(0, weight=1) # Treeviewの列が伸縮するように

        # Treeview選択時のイベント設定 (後で実装)
        self.project_tree.bind("<<TreeviewSelect>>", self.on_project_tree_select)

    def load_projects_to_treeview(self):
        """データベースから案件情報を読み込み、Treeviewに表示する"""
        # 更新・削除ボタンを無効化し、選択IDをクリア (一覧更新時の初期化)
        if hasattr(self, 'update_button'): # ボタンが作成されていれば
            self.update_button.config(state=tk.DISABLED)
        if hasattr(self, 'delete_button'):
            self.delete_button.config(state=tk.DISABLED)
        self.selected_project_id = None
        
        # Treeviewの既存のアイテムをすべて削除
        for item in self.project_tree.get_children():
            self.project_tree.delete(item)
        
        projects_data = self.db_ops.get_all_projects() # データベースから全案件データを取得
        
        if projects_data:
            for project_tuple in projects_data:
                # get_all_projects() が返すタプルの内容とインデックス:
                # (0:p.project_id, 1:p.project_code, 2:p.project_name, 
                #  3:p.customer_id, 4:c.customer_name, 
                #  5:p.parent_project_id, 6:pp.parent_project_code, 
                #  7:p.site_address, 8:p.reception_date, 9:p.start_date_scheduled, 
                #  10:p.completion_date_scheduled, 11:p.actual_completion_date, 
                #  12:p.responsible_staff_name, 13:p.estimated_amount, 14:p.status, 
                #  15:p.remarks, 16:p.created_at, 17:p.updated_at)

                # Treeviewに表示する値を選択して整形
                # Treeviewのcolumns: ("project_id", "project_code", "project_name", "customer_name", 
                #                     "status", "reception_date", "start_date_scheduled", 
                #                     "completion_date_scheduled", "responsible_staff_name", "estimated_amount")
                display_values = (
                    project_tuple[0],  # project_id
                    project_tuple[1],  # project_code
                    project_tuple[2],  # project_name
                    project_tuple[4],  # customer_name (c.customer_name)
                    project_tuple[14], # status
                    project_tuple[8],  # reception_date
                    project_tuple[9],  # start_date_scheduled
                    project_tuple[10], # completion_date_scheduled
                    project_tuple[12], # responsible_staff_name
                    f"{project_tuple[13]:,}" if project_tuple[13] is not None else "" # estimated_amount (桁区切り)
                )
                # Treeviewにアイテムを挿入 (iid に project_id を設定すると後で便利)
                self.project_tree.insert("", tk.END, values=display_values, iid=project_tuple[0])
        # else:
            # messagebox.showinfo("情報", "登録されている案件情報はありません。") # 必要に応じて
    def on_project_tree_select(self, event):
        """Project Treeviewで項目が選択されたときに呼び出される"""
        selected_items = self.project_tree.selection() # 選択されたアイテムのiidのタプル

        if not selected_items: # 何も選択されていない場合（選択が外れた場合など）
            # フォームをクリアし、ボタンを無効化（clear_project_formが既に行う）
            # ただし、clear_project_form内で選択解除も行うため、ここでは何もしないか、
            # selected_project_id のリセットのみ行う
            self.selected_project_id = None
            self.update_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)
            # clear_project_form() をここで呼ぶと無限ループになる可能性があるので注意
            return

        selected_iid = selected_items[0] # 最初の選択アイテムのiid (project_id)
        self.selected_project_id = selected_iid # 選択されたproject_idを保持

        # データベースから完全な案件情報を取得
        # get_project_by_id が返すタプルのインデックスを確認しながらフォームに値をセット
        # (0:project_id, 1:project_code, 2:project_name, 3:customer_id, 4:customer_name, 
        #  5:parent_project_id, 6:parent_project_code, 7:site_address, 8:reception_date, 
        #  9:start_date_scheduled, 10:completion_date_scheduled, 11:actual_completion_date, 
        #  12:responsible_staff_name, 13:estimated_amount, 14:status, 15:remarks, ...)
        project_data_tuple = self.db_ops.get_project_by_id(self.selected_project_id)

        if project_data_tuple:
            # フォームの既存の値をクリア (clear_project_form は Treeview の選択も解除してしまうため、個別にクリア)
            self.project_code_entry.delete(0, tk.END)
            self.project_name_entry.delete(0, tk.END)
            self.customer_id_entry.delete(0, tk.END)
            self.parent_project_id_entry.delete(0, tk.END)
            self.site_address_entry.delete(0, tk.END)
            self.reception_date_entry.delete(0, tk.END)
            self.start_date_scheduled_entry.delete(0, tk.END)
            self.completion_date_scheduled_entry.delete(0, tk.END)
            self.actual_completion_date_entry.delete(0, tk.END)
            self.responsible_staff_entry.delete(0, tk.END)
            self.estimated_amount_entry.delete(0, tk.END)
            self.status_combobox.set("") # Comboboxをクリア
            self.remarks_text.delete("1.0", tk.END)

            # フォームに値を設定
            self.project_code_entry.insert(0, project_data_tuple[1] or "")      # project_code
            self.project_name_entry.insert(0, project_data_tuple[2] or "")      # project_name
            self.customer_id_entry.insert(0, str(project_data_tuple[3]) if project_data_tuple[3] is not None else "") # customer_id
            self.parent_project_id_entry.insert(0, str(project_data_tuple[5]) if project_data_tuple[5] is not None else "") # parent_project_id
            self.site_address_entry.insert(0, project_data_tuple[7] or "")    # site_address
            self.reception_date_entry.insert(0, project_data_tuple[8] or "")  # reception_date
            self.start_date_scheduled_entry.insert(0, project_data_tuple[9] or "") # start_date_scheduled
            self.completion_date_scheduled_entry.insert(0, project_data_tuple[10] or "")# completion_date_scheduled
            self.actual_completion_date_entry.insert(0, project_data_tuple[11] or "") # actual_completion_date
            self.responsible_staff_entry.insert(0, project_data_tuple[12] or "")# responsible_staff_name
            self.estimated_amount_entry.insert(0, str(project_data_tuple[13]) if project_data_tuple[13] is not None else "") # estimated_amount
            
            # status_combobox の設定 (値がリストにあれば選択、なければ空欄または先頭)
            status_value = project_data_tuple[14]
            if status_value in self.status_options:
                self.status_combobox.set(status_value)
            elif self.status_options: # リストにあれば先頭、なければ空
                self.status_combobox.set("") # または self.status_options[0]
            
            self.remarks_text.insert("1.0", project_data_tuple[15] or "")     # remarks

            self.update_button.config(state=tk.NORMAL) # 更新ボタンを有効化
            self.delete_button.config(state=tk.NORMAL) # 削除ボタンを有効化
        else:
            messagebox.showwarning("データ取得エラー", f"案件ID {self.selected_project_id} の情報取得に失敗しました。")
            self.clear_project_form() # フォームをクリアし、ボタンを無効化

    # --- ボタンのコマンド (プレースホルダ) ---
    # これらは後で本格的に実装します
    def add_new_project(self):
        # フォームから値を取得
        project_code = self.project_code_entry.get().strip()
        project_name = self.project_name_entry.get().strip()
        
        customer_id_str = self.customer_id_entry.get().strip()
        parent_project_id_str = self.parent_project_id_entry.get().strip()
        
        site_address = self.site_address_entry.get().strip()
        reception_date = self.reception_date_entry.get().strip() # YYYY-MM-DD形式を期待
        start_date_scheduled = self.start_date_scheduled_entry.get().strip()
        completion_date_scheduled = self.completion_date_scheduled_entry.get().strip()
        actual_completion_date = self.actual_completion_date_entry.get().strip()
        
        responsible_staff_name = self.responsible_staff_entry.get().strip()
        estimated_amount_str = self.estimated_amount_entry.get().strip()
        
        status = self.status_combobox.get()
        remarks = self.remarks_text.get("1.0", tk.END).strip()

        # --- 入力値のバリデーション ---
        if not project_code:
            messagebox.showerror("入力エラー", "案件コードは必須です。")
            self.project_code_entry.focus_set()
            return
        if not project_name:
            messagebox.showerror("入力エラー", "案件名は必須です。")
            self.project_name_entry.focus_set()
            return
        if not customer_id_str: # 顧客IDも必須とする場合
            messagebox.showerror("入力エラー", "顧客IDは必須です。")
            self.customer_id_entry.focus_set()
            return

        # --- データ型の変換とさらなるチェック ---
        try:
            customer_id = int(customer_id_str)
        except ValueError:
            messagebox.showerror("入力エラー", "顧客IDは有効な数値を入力してください。")
            self.customer_id_entry.focus_set()
            return

        parent_project_id = None # デフォルトはNone
        if parent_project_id_str: # 入力があれば変換を試みる
            try:
                parent_project_id = int(parent_project_id_str)
            except ValueError:
                messagebox.showerror("入力エラー", "親案件IDは有効な数値を入力してください（空欄可）。")
                self.parent_project_id_entry.focus_set()
                return
        
        estimated_amount = 0 # デフォルトは0
        if estimated_amount_str: # 入力があれば変換を試みる
            try:
                estimated_amount = int(estimated_amount_str) # 小数点なしの整数として扱う
            except ValueError:
                messagebox.showerror("入力エラー", "見積金額は有効な数値を入力してください（小数点なし）。")
                self.estimated_amount_entry.focus_set()
                return
        
        # TODO: 日付形式のバリデーション (例: YYYY-MM-DD) も追加するとより堅牢になります

        # データベースに追加
        result = self.db_ops.add_project(
            project_code, project_name, customer_id, parent_project_id,
            site_address, reception_date, start_date_scheduled,
            completion_date_scheduled, actual_completion_date,
            responsible_staff_name, estimated_amount, status, remarks
        )

        if isinstance(result, int): # 成功時 (新しい project_id が返る)
            messagebox.showinfo("登録成功", f"案件「{project_name}」(コード: {project_code}) を登録しました。(ID: {result})")
            self.clear_project_form()
            self.load_projects_to_treeview() # 一覧を更新
        elif result == "DUPLICATE_CODE":
            messagebox.showerror("登録エラー", f"案件コード「{project_code}」は既に登録されています。")
            self.project_code_entry.focus_set()
        elif result == "NOT_NULL_VIOLATION":
            messagebox.showerror("登録エラー", "必須項目（案件コードや案件名など）が入力されていません。")
        elif result == "FK_CONSTRAINT_FAILED":
            messagebox.showerror("登録エラー", "指定された顧客IDまたは親案件IDが存在しません。確認してください。")
            # どちらのIDが問題か特定するには、db_ops側でより詳細なエラーコードを返すか、
            # GUI側で事前にIDの存在確認をする必要があります。
        elif result == "INTEGRITY_ERROR":
            messagebox.showerror("登録エラー", "データベースの整合性エラーが発生しました。")
        elif result == "CONNECTION_ERROR" or result == "OTHER_DB_ERROR" or result is None:
            messagebox.showerror("登録エラー", "データベースエラーにより案件情報の登録に失敗しました。")
        else: # 想定外の戻り値
            messagebox.showerror("登録エラー", f"不明なエラーが発生しました。({result})")

    def update_selected_project(self):
        if not self.selected_project_id:
            messagebox.showwarning("未選択", "更新する案件が選択されていません。")
            return

        # フォームから現在の入力値を取得 (add_new_project と同様)
        project_code = self.project_code_entry.get().strip()
        project_name = self.project_name_entry.get().strip()
        customer_id_str = self.customer_id_entry.get().strip()
        parent_project_id_str = self.parent_project_id_entry.get().strip()
        site_address = self.site_address_entry.get().strip()
        reception_date = self.reception_date_entry.get().strip()
        start_date_scheduled = self.start_date_scheduled_entry.get().strip()
        completion_date_scheduled = self.completion_date_scheduled_entry.get().strip()
        actual_completion_date = self.actual_completion_date_entry.get().strip()
        responsible_staff_name = self.responsible_staff_entry.get().strip()
        estimated_amount_str = self.estimated_amount_entry.get().strip()
        status = self.status_combobox.get()
        remarks = self.remarks_text.get("1.0", tk.END).strip()

        # --- 入力値のバリデーション ---
        if not project_code:
            messagebox.showerror("入力エラー", "案件コードは必須です。")
            self.project_code_entry.focus_set()
            return
        if not project_name:
            messagebox.showerror("入力エラー", "案件名は必須です。")
            self.project_name_entry.focus_set()
            return
        if not customer_id_str: # 顧客IDも必須とする
            messagebox.showerror("入力エラー", "顧客IDは必須です。")
            self.customer_id_entry.focus_set()
            return

        # --- データ型の変換とさらなるチェック ---
        try:
            customer_id = int(customer_id_str)
        except ValueError:
            messagebox.showerror("入力エラー", "顧客IDは有効な数値を入力してください。")
            self.customer_id_entry.focus_set()
            return

        parent_project_id = None
        if parent_project_id_str:
            try:
                parent_project_id = int(parent_project_id_str)
            except ValueError:
                messagebox.showerror("入力エラー", "親案件IDは有効な数値を入力してください（空欄可）。")
                self.parent_project_id_entry.focus_set()
                return
        
        estimated_amount = 0
        if estimated_amount_str:
            try:
                estimated_amount = int(estimated_amount_str)
            except ValueError:
                messagebox.showerror("入力エラー", "見積金額は有効な数値を入力してください（小数点なし）。")
                self.estimated_amount_entry.focus_set()
                return

        # 更新確認
        confirm_message = f"案件「{project_name}」(コード: {project_code}) の情報を本当に更新しますか？"
        confirm = messagebox.askyesno("更新確認", confirm_message)
        if not confirm:
            messagebox.showinfo("キャンセル", "更新はキャンセルされました。")
            return

        # データベースの更新処理を呼び出す
        result = self.db_ops.update_project(
            self.selected_project_id, # 更新対象のID
            project_code, project_name, customer_id, parent_project_id,
            site_address, reception_date, start_date_scheduled,
            completion_date_scheduled, actual_completion_date,
            responsible_staff_name, estimated_amount, status, remarks
        )

        if result is True: # 成功時
            messagebox.showinfo("更新成功", f"案件「{project_name}」(コード: {project_code}) の情報を更新しました。")
            self.clear_project_form()
            self.load_projects_to_treeview() # 一覧を更新
        elif result == "DUPLICATE_CODE":
            messagebox.showerror("更新エラー", f"案件コード「{project_code}」は既に他の案件に使用されています。")
            self.project_code_entry.focus_set()
        elif result == "NOT_FOUND":
            messagebox.showerror("更新エラー", f"更新対象の案件 (ID: {self.selected_project_id}) が見つかりませんでした。一覧を再読み込みしてください。")
            self.clear_project_form() # 対象がないのでフォームクリア
            self.load_projects_to_treeview()
        elif result == "NOT_NULL_VIOLATION":
            messagebox.showerror("更新エラー", "必須項目（案件コードや案件名など）が入力されていません。")
        elif result == "FK_CONSTRAINT_FAILED":
            messagebox.showerror("更新エラー", "指定された顧客IDまたは親案件IDが存在しません。確認してください。")
        elif result == "INTEGRITY_ERROR":
            messagebox.showerror("更新エラー", "データベースの整合性エラーが発生しました。")
        elif result == "CONNECTION_ERROR" or result == "OTHER_DB_ERROR":
            messagebox.showerror("更新エラー", "データベースエラーにより案件情報の更新に失敗しました。")
        else: # 想定外の戻り値
            messagebox.showerror("更新エラー", f"不明なエラーが発生しました。({result})")

    def delete_selected_project(self):
        if not self.selected_project_id:
            messagebox.showwarning("未選択", "削除する案件が選択されていません。")
            return
        
        # データベースから最新の案件情報を取得して案件名などを確認メッセージに含める
        project_info = self.db_ops.get_project_by_id(self.selected_project_id)
        project_display_name = f"コード: {project_info[1]}, 名称: {project_info[2]}" if project_info else f"ID: {self.selected_project_id}"

        confirm_message = f"案件「{project_display_name}」の情報を本当に削除しますか？\n"
        confirm_message += "この操作は元に戻せません。"
        # 親案件の場合の注意喚起 (ON DELETE RESTRICT のため)
        # 実際に子案件があるかどうかをチェックしてメッセージを変えることも可能ですが、ここでは一般的な注意とします。
        confirm_message += "\n\n注意: この案件が他の案件の「親案件」として設定されている場合、削除できません。"


        confirm = messagebox.askyesno("削除確認", confirm_message)
        
        if confirm:
            result = self.db_ops.delete_project(self.selected_project_id)
            
            if result is True: # データベース操作関数が True を返したら成功
                messagebox.showinfo("削除成功", f"案件「{project_display_name}」の情報を削除しました。")
                self.clear_project_form() 
                self.load_projects_to_treeview() 
            elif result == "NOT_FOUND":
                messagebox.showerror("削除エラー", f"削除対象の案件 (ID: {self.selected_project_id}) が見つかりませんでした。一覧を再読み込みしてください。")
                self.clear_project_form()
                self.load_projects_to_treeview()
            elif result == "FK_CONSTRAINT_FAILED":
                messagebox.showerror("削除エラー", f"案件 (ID: {self.selected_project_id}) を削除できませんでした。\nこの案件が他の案件の「親案件」として使用されている可能性があります。")
            elif result == "INTEGRITY_ERROR":
                messagebox.showerror("削除エラー", "データベースの整合性エラーにより削除できませんでした。")
            elif result == "CONNECTION_ERROR" or result == "OTHER_DB_ERROR":
                messagebox.showerror("削除エラー", "データベースエラーにより案件情報の削除に失敗しました。")
            else: # 想定外の戻り値
                messagebox.showerror("削除エラー", f"不明なエラーが発生しました。({result})")
        else:
            messagebox.showinfo("キャンセル", "削除はキャンセルされました。")

    def clear_project_form(self):
        # messagebox.showinfo("未実装", "フォームクリア処理は未実装です。")
        # ひとまず主要なエントリーをクリアする例
        self.project_code_entry.delete(0, tk.END)
        self.project_name_entry.delete(0, tk.END)
        self.customer_id_entry.delete(0, tk.END)
        self.parent_project_id_entry.delete(0, tk.END)
        self.site_address_entry.delete(0, tk.END)
        self.reception_date_entry.delete(0, tk.END)
        self.start_date_scheduled_entry.delete(0, tk.END)
        self.completion_date_scheduled_entry.delete(0, tk.END)
        self.actual_completion_date_entry.delete(0, tk.END)
        self.responsible_staff_entry.delete(0, tk.END)
        self.estimated_amount_entry.delete(0, tk.END)
        if self.status_options:
             self.status_combobox.set(self.status_options[0]) # または空にする: self.status_combobox.set("")
        self.remarks_text.delete("1.0", tk.END)
        
        self.selected_project_id = None
        # if self.project_tree.selection():
        #     self.project_tree.selection_remove(self.project_tree.selection()[0])
        self.update_button.config(state=tk.DISABLED)
        self.delete_button.config(state=tk.DISABLED)
        self.project_code_entry.focus()
        print("Project form cleared.")

    def on_close(self):
        # ウィンドウを閉じる前に何か処理が必要な場合はここに記述
        self.destroy() # ウィンドウを破棄

# このファイル単体でテスト実行するためのコード
if __name__ == '__main__':
    root = tk.Tk()
    root.title("メインウィンドウ (テスト用)")
    
    def open_project_window():
        # テストのために、db_opsが利用可能であるようにする
        # 実際のアプリケーションではメインアプリから渡されるか、適切に初期化される
        if not hasattr(root, 'db_ops'): # 簡単な初期化
            root.db_ops = db_ops 

        project_win = ProjectManagementWindow(root)
        project_win.grab_set() 
    
    open_button = ttk.Button(root, text="案件管理を開く", command=open_project_window)
    open_button.pack(padx=20, pady=20)
    
    root.mainloop()