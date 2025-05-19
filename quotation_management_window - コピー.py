# quotation_management_window.py

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import database_operations as db_ops
from datetime import datetime

class QuotationListWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("見積一覧")
        self.geometry("900x500")
        if hasattr(master, 'db_ops'):
            self.db_ops = master.db_ops
        else:
            messagebox.showerror("エラー", "データベース操作モジュールが見つかりません。", parent=self)
            self.destroy()
            return

        self.parent_window = master
        self.selected_quotation_id_for_detail = None

        self._create_list_widgets()
        self.load_quotation_headers_to_treeview()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _create_list_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        action_button_frame = ttk.Frame(main_frame)
        action_button_frame.pack(fill=tk.X, pady=(0, 5))

        self.new_button = ttk.Button(action_button_frame, text="新規見積作成", command=self.open_new_quotation_detail)
        self.new_button.pack(side=tk.LEFT, padx=5)

        self.edit_button = ttk.Button(action_button_frame, text="見積表示/編集", command=self.open_selected_quotation_detail, state=tk.DISABLED)
        self.edit_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = ttk.Button(action_button_frame, text="見積削除", command=self.confirm_delete_selected_header, state=tk.DISABLED)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        self.refresh_button = ttk.Button(action_button_frame, text="一覧更新", command=self.load_quotation_headers_to_treeview)
        self.refresh_button.pack(side=tk.LEFT, padx=5)

        headers_list_frame = ttk.LabelFrame(main_frame, text="見積一覧", padding="5")
        headers_list_frame.pack(fill=tk.BOTH, expand=True, pady=(5,0))

        self._create_headers_treeview(headers_list_frame)

        # --- ここから追加: Treeviewのフォントサイズ設定 ---
        style = ttk.Style(self)
        tree_font_family = "メイリオ"  # 必要に応じて変更
        tree_font_size = 10            # 一覧用のフォントサイズ
        tree_row_height = tree_font_size + 10
        style.configure("Treeview", font=(tree_font_family, tree_font_size), rowheight=tree_row_height)
        style.configure("Treeview.Heading", font=(tree_font_family, tree_font_size, "bold"))
        # --- ここまで追加 ---

    def _create_headers_treeview(self, parent_frame):
        columns = (
            "quotation_id", "quotation_code", "quotation_date", "customer_name_at_quote",
            "project_name_at_quote", "total_amount_inclusive_tax", "status", "staff_name"
        )
        self.headers_tree = ttk.Treeview(parent_frame, columns=columns, show="headings", height=15)

        self.headers_tree.heading("quotation_id", text="ID")
        self.headers_tree.column("quotation_id", width=40, anchor=tk.CENTER)
        self.headers_tree.heading("quotation_code", text="見積番号")
        self.headers_tree.column("quotation_code", width=130)
        self.headers_tree.heading("quotation_date", text="見積日")
        self.headers_tree.column("quotation_date", width=90, anchor=tk.CENTER)
        self.headers_tree.heading("customer_name_at_quote", text="宛名")
        self.headers_tree.column("customer_name_at_quote", width=180)
        self.headers_tree.heading("project_name_at_quote", text="件名")
        self.headers_tree.column("project_name_at_quote", width=200)
        self.headers_tree.heading("total_amount_inclusive_tax", text="見積金額(税込)")
        self.headers_tree.column("total_amount_inclusive_tax", width=100, anchor=tk.E)
        self.headers_tree.heading("status", text="状況")
        self.headers_tree.column("status", width=80)
        self.headers_tree.heading("staff_name", text="担当者")
        self.headers_tree.column("staff_name", width=100)

        scrollbar_y = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.headers_tree.yview)
        self.headers_tree.configure(yscrollcommand=scrollbar_y.set)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.headers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.headers_tree.bind("<<TreeviewSelect>>", self.on_list_header_tree_select)
        self.headers_tree.bind("<Double-1>", self.on_header_double_click)

    def load_quotation_headers_to_treeview(self):
        if hasattr(self, 'headers_tree'):
            for item in self.headers_tree.get_children():
                self.headers_tree.delete(item)
        else:
            return

        quotation_headers_data = self.db_ops.get_all_quotations()

        if quotation_headers_data:
            for q_header_tuple in quotation_headers_data:
                total_amount_display = f"{q_header_tuple[10]:,}" if q_header_tuple[10] is not None else ""
                display_values = (
                    q_header_tuple[0],  # quotation_id
                    q_header_tuple[1],  # quotation_code
                    q_header_tuple[2],  # quotation_date
                    q_header_tuple[8],  # customer_name_at_quote
                    q_header_tuple[9],  # project_name_at_quote
                    total_amount_display,
                    q_header_tuple[11],
                    q_header_tuple[7] or ""
                )
                self.headers_tree.insert("", tk.END, values=display_values, iid=q_header_tuple[0])

        self.on_list_header_tree_select(None)

    def on_list_header_tree_select(self, event):
        selected_items = self.headers_tree.selection()
        if selected_items:
            self.selected_quotation_id_for_detail = selected_items[0]
            if hasattr(self, 'edit_button'): self.edit_button.config(state=tk.NORMAL)
            if hasattr(self, 'delete_button'): self.delete_button.config(state=tk.NORMAL)
        else:
            self.selected_quotation_id_for_detail = None
            if hasattr(self, 'edit_button'): self.edit_button.config(state=tk.DISABLED)
            if hasattr(self, 'delete_button'): self.delete_button.config(state=tk.DISABLED)

    def on_header_double_click(self, event):
        if self.headers_tree.selection():
            self.open_selected_quotation_detail()

    # QuotationListWindow 内のメソッド (再掲、修正)
    def open_new_quotation_detail(self):
        # QuotationManagementWindow (改修後) を呼び出す
        detail_win = QuotationManagementWindow(self, quotation_id=None, refresh_callback=self.load_quotation_headers_to_treeview)
        # detail_win.grab_set() # 必要に応じて

    def open_selected_quotation_detail(self):
        if not self.selected_quotation_id_for_detail:
            messagebox.showwarning("未選択", "表示/編集する見積が選択されていません。", parent=self)
            self.lift()
            return
        detail_win = QuotationManagementWindow(self, quotation_id=self.selected_quotation_id_for_detail, refresh_callback=self.load_quotation_headers_to_treeview)
        # detail_win.grab_set() # 必要に応じて

    def confirm_delete_selected_header(self):
        if not self.selected_quotation_id_for_detail:
            messagebox.showwarning("未選択", "削除する見積が選択されていません。", parent=self)
            self.lift()
            return

        quotation_code_to_confirm = ""
        if hasattr(self, 'headers_tree') and self.headers_tree.exists(str(self.selected_quotation_id_for_detail)):
            try:
                item_values = self.headers_tree.item(str(self.selected_quotation_id_for_detail), 'values')
                if len(item_values) > 1: quotation_code_to_confirm = item_values[1]
            except Exception: pass

        confirm_message = f"見積「{quotation_code_to_confirm}」(ID: {self.selected_quotation_id_for_detail}) を本当に削除しますか？\n関連する全ての明細も削除されます。"
        if not messagebox.askyesno("見積削除確認", confirm_message, parent=self):
            self.lift()
            return

        delete_result = self.db_ops.delete_quotation(self.selected_quotation_id_for_detail)
        if delete_result is True:
            messagebox.showinfo("削除成功", f"見積 (ID: {self.selected_quotation_id_for_detail}) を削除しました。", parent=self)
            self.load_quotation_headers_to_treeview()
        elif delete_result == "NOT_FOUND":
            messagebox.showerror("エラー", f"削除対象の見積 (ID: {self.selected_quotation_id_for_detail}) が見つかりませんでした。", parent=self)
        else:
            messagebox.showerror("エラー", f"見積の削除に失敗しました: {delete_result}", parent=self)
        self.lift()

    def on_close(self):
        self.destroy()

# quotation_management_window.py の既存の QuotationManagementWindow クラスを以下で置き換え

# quotation_management_window.py の既存の QuotationManagementWindow クラスの定義を以下で置き換える

class QuotationManagementWindow(tk.Toplevel): # クラス名はそのまま
    def __init__(self, master, quotation_id=None, refresh_callback=None): # ★ 引数変更
        super().__init__(master)
        
        # self.db_ops = db_ops # master (QuotationListWindow) から受け継ぐ
        if hasattr(master, 'db_ops'):
            self.db_ops = master.db_ops
        else: # 万が一 db_ops が渡されなかった場合のフォールバック
            messagebox.showerror("致命的なエラー", "データベース操作モジュールが設定されていません。", parent=self.master)
            self.after(100, self.destroy) # 少し遅れてウィンドウを閉じる
            return

        self.parent_list_window = master # 親ウィンドウ (QuotationListWindow) を保持
        self.current_quotation_id = quotation_id 
        self.refresh_callback = refresh_callback 

        # 状態管理フラグ (QuotationListWindowから渡されるわけではないので、ここで初期化)
        self._preparing_new_quotation_flag = False # 詳細ウィンドウ内では新規準備の際に使用
        self._is_editing_header = False

        if self.current_quotation_id is None:
            self.title("見積作成 - 新規")
        else:
            # DBから見積情報を取得してタイトルに表示することも可能 (get_quotation_by_id が辞書を返す前提なら)
            # header_info = self.db_ops.get_quotation_by_id(self.current_quotation_id) # get_quotation_by_id はタプルを返す
            # temp_code = header_info[5] if header_info and len(header_info) > 5 else ""
            # self.title(f"見積詳細/編集 - {temp_code} (ID: {self.current_quotation_id})")
            self.title(f"見積詳細/編集 (ID: {self.current_quotation_id})")
            
        self.geometry("850x950") 

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._create_detail_widgets() # ★ メソッド名を変更

        if self.current_quotation_id is None:
            self.prepare_new_quotation() # 新規モード
        else:
            self._load_quotation_for_display(self.current_quotation_id) # 表示/編集モード

    def _create_detail_widgets(self): # 旧 _create_widgets から改名・修正
        details_pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        details_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        header_form_frame = ttk.LabelFrame(details_pane, text="見積ヘッダー詳細", padding="5")
        details_pane.add(header_form_frame, weight=2) 
        self._create_header_detail_form(header_form_frame)

        items_list_frame = ttk.LabelFrame(details_pane, text="見積明細一覧", padding="5")
        details_pane.add(items_list_frame, weight=3)
        
        self.item_action_frame = ttk.Frame(items_list_frame)
        self.item_action_frame.pack(fill=tk.X, pady=(0, 5))
        self._create_item_action_buttons(self.item_action_frame)
        
        self._create_items_treeview(items_list_frame)
        
        style = ttk.Style(self)
        tree_font_family = "メイリオ" 
        tree_font_size = 10
        tree_row_height = tree_font_size + 10
        style.configure("Treeview", font=(tree_font_family, tree_font_size), rowheight=tree_row_height) 
        style.configure("Treeview.Heading", font=(tree_font_family, tree_font_size, "bold"))
        
        detail_action_frame = ttk.Frame(self, padding="5")
        detail_action_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(0,5))
        self._create_detail_action_buttons(detail_action_frame) # ★ メソッド名変更

    # _create_headers_treeview は削除 (QuotationListWindowへ移動済み)

    def _create_header_detail_form(self, parent_frame):
        # このメソッドは変更なし (StringVar, Entry作成)
        self.header_form_entries = {} 
        self.detail_vars = {
            "quotation_code": tk.StringVar(), "quotation_date": tk.StringVar(),
            "customer_name_at_quote": tk.StringVar(), "project_name_at_quote": tk.StringVar(),
            "site_address_at_quote": tk.StringVar(), "construction_period_notes": tk.StringVar(),
            "total_amount_exclusive_tax": tk.StringVar(), "tax_rate": tk.StringVar(),
            "tax_amount": tk.StringVar(), "total_amount_inclusive_tax": tk.StringVar(),
            "validity_period_notes": tk.StringVar(), "payment_terms_notes": tk.StringVar(),
            "status": tk.StringVar(), "staff_name": tk.StringVar(),
            "original_project_code": tk.StringVar(), "remarks": tk.StringVar(),
            "project_id": tk.StringVar(), "quotation_staff_id": tk.StringVar()
        }
        form_layout = [
            ("見積番号:", "quotation_code", 0, 0), ("見積日:", "quotation_date", 0, 2),
            ("宛名:", "customer_name_at_quote", 1, 0), ("件名:", "project_name_at_quote", 1, 2),
            ("案件ID (必須):", "project_id", 2, 0), 
            ("元案件コード:", "original_project_code", 2, 2),
            ("見積担当者ID:", "quotation_staff_id", 3, 0), 
            ("見積担当者名:", "staff_name", 3, 2),
            ("現場住所:", "site_address_at_quote", 4, 0, 3), 
            ("工期:", "construction_period_notes", 5, 0, 3), 
            ("有効期限:", "validity_period_notes", 6, 0), ("支払条件:", "payment_terms_notes", 6, 2), 
            ("状況:", "status", 7, 0), ("税率(%):", "tax_rate", 7, 2), 
            ("税抜合計:", "total_amount_exclusive_tax", 8, 0),  
            ("消費税額:", "tax_amount", 8, 2), 
            ("見積金額(税込):", "total_amount_inclusive_tax", 9, 0), 
            ("備考:", "remarks", 10, 0, 3) 
        ]
        for label_text, key, r, c, *span in form_layout:
            ttk.Label(parent_frame, text=label_text).grid(row=r, column=c, padx=5, pady=2, sticky=tk.W)
            entry_width = 35 if len(span) > 0 and span[0] == 3 else 18 
            if key == "remarks" or key == "construction_period_notes" or \
               key == "validity_period_notes" or key == "payment_terms_notes" or \
               key == "site_address_at_quote": 
                entry = ttk.Entry(parent_frame, textvariable=self.detail_vars[key], width=entry_width)
            elif key == "status": 
                 entry = ttk.Entry(parent_frame, textvariable=self.detail_vars[key], width=entry_width, state="readonly") 
            elif key in ["total_amount_exclusive_tax", "tax_amount", "total_amount_inclusive_tax", "staff_name", "original_project_code"]:
                entry = ttk.Entry(parent_frame, textvariable=self.detail_vars[key], width=entry_width, state="readonly")
            else:
                entry = ttk.Entry(parent_frame, textvariable=self.detail_vars[key], width=entry_width)
            entry.grid(row=r, column=c + 1, padx=5, pady=2, sticky=tk.EW, columnspan=(span[0] if span else 1))
            self.header_form_entries[key] = entry 
        parent_frame.columnconfigure(1, weight=1)
        parent_frame.columnconfigure(3, weight=1)

    def _create_items_treeview(self, parent_frame):
        # このメソッドは変更なし
        columns = ("no", "name", "specification", "quantity", "unit", "unit_price", "amount", "remarks")
        self.items_tree = ttk.Treeview(parent_frame, columns=columns, show="headings", height=10)
        self.items_tree.heading("no", text="No."); self.items_tree.column("no", width=40, anchor=tk.CENTER)
        self.items_tree.heading("name", text="名称"); self.items_tree.column("name", width=200)
        self.items_tree.heading("specification", text="仕様"); self.items_tree.column("specification", width=200)
        self.items_tree.heading("quantity", text="数量"); self.items_tree.column("quantity", width=60, anchor=tk.E)
        self.items_tree.heading("unit", text="単位"); self.items_tree.column("unit", width=60, anchor=tk.CENTER)
        self.items_tree.heading("unit_price", text="単価"); self.items_tree.column("unit_price", width=90, anchor=tk.E)
        self.items_tree.heading("amount", text="金額"); self.items_tree.column("amount", width=90, anchor=tk.E)
        self.items_tree.heading("remarks", text="備考"); self.items_tree.column("remarks", width=150)
        scrollbar_y = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        scrollbar_x = ttk.Scrollbar(parent_frame, orient=tk.HORIZONTAL, command=self.items_tree.xview)
        self.items_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.items_tree.bind("<<TreeviewSelect>>", self.on_item_tree_select)
        
    def _create_item_action_buttons(self, parent_frame):
        # このメソッドは変更なし
        self.add_item_button = ttk.Button(parent_frame, text="明細追加", command=self.open_add_item_dialog, state=tk.DISABLED)
        self.add_item_button.pack(side=tk.LEFT, padx=5)
        self.edit_item_button = ttk.Button(parent_frame, text="明細編集", command=self.open_edit_item_dialog, state=tk.DISABLED)
        self.edit_item_button.pack(side=tk.LEFT, padx=5)
        self.delete_item_button = ttk.Button(parent_frame, text="明細削除", command=self.delete_selected_item, state=tk.DISABLED)
        self.delete_item_button.pack(side=tk.LEFT, padx=5)

    def _create_detail_action_buttons(self, parent_frame): # 旧 _create_global_action_buttons から改名・修正
        # 「新規見積作成」ボタンはこのウィンドウには不要 (QuotationListWindowへ)
        # 「見積削除」ボタンもこのウィンドウには不要 (QuotationListWindowへ)

        self.start_edit_header_button = ttk.Button(parent_frame, text="ヘッダー編集", command=self.start_header_edit_mode, state=tk.DISABLED)
        self.start_edit_header_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.save_quotation_button = ttk.Button(parent_frame, text="この見積を保存", command=self.save_quotation_data, state=tk.DISABLED)
        self.save_quotation_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.close_button = ttk.Button(parent_frame, text="閉じる", command=self.on_close)
        self.close_button.pack(side=tk.RIGHT, padx=5, pady=5) # 右側に配置する例

    def _load_quotation_for_display(self, quotation_id): # ★ 新規メソッド
        if quotation_id is None:
            self.prepare_new_quotation()
            return

        self.current_quotation_id = quotation_id 
        header_data = self.db_ops.get_quotation_by_id(self.current_quotation_id) # quotation_id を使用
 
        if header_data:
            self._is_editing_header = False # 表示時は非編集モード

            self.detail_vars["quotation_code"].set(header_data[5] or "")
            self.detail_vars["quotation_date"].set(header_data[6] or "")
            self.detail_vars["customer_name_at_quote"].set(header_data[7] or "")
            self.detail_vars["project_name_at_quote"].set(header_data[8] or "")
            self.detail_vars["site_address_at_quote"].set(header_data[9] or "")
            self.detail_vars["construction_period_notes"].set(header_data[10] or "")
            self.detail_vars["total_amount_exclusive_tax"].set(f"{header_data[11]:,}" if header_data[11] is not None else "")
            self.detail_vars["tax_rate"].set(f"{header_data[12]*100:.0f}" if header_data[12] is not None else "")
            self.detail_vars["tax_amount"].set(f"{header_data[13]:,}" if header_data[13] is not None else "")
            self.detail_vars["total_amount_inclusive_tax"].set(f"{header_data[14]:,}" if header_data[14] is not None else "")
            self.detail_vars["validity_period_notes"].set(header_data[15] or "")
            self.detail_vars["payment_terms_notes"].set(header_data[16] or "")
            self.detail_vars["status"].set(header_data[17] or "")
            self.detail_vars["staff_name"].set(header_data[4] or "") 
            self.detail_vars["original_project_code"].set(header_data[2] or "") 
            self.detail_vars["remarks"].set(header_data[18] or "")
            self.detail_vars["project_id"].set(str(header_data[1]) if header_data[1] is not None else "")
            self.detail_vars["quotation_staff_id"].set(str(header_data[3]) if header_data[3] is not None else "")

            for key, entry_widget in self.header_form_entries.items():
                entry_widget.config(state="readonly")
            
            self.load_selected_quotation_items(self.current_quotation_id) # quotation_id を使用
            
            if hasattr(self, 'save_quotation_button'): self.save_quotation_button.config(state=tk.DISABLED)
            if hasattr(self, 'start_edit_header_button'): self.start_edit_header_button.config(state=tk.NORMAL)
            if hasattr(self, 'add_item_button'): self.add_item_button.config(state=tk.NORMAL)
            if hasattr(self, 'edit_item_button'): self.edit_item_button.config(state=tk.DISABLED)
            if hasattr(self, 'delete_item_button'): self.delete_item_button.config(state=tk.DISABLED)
        else:
            messagebox.showerror("エラー", f"見積ID {quotation_id} の情報取得に失敗しました。", parent=self)
            self.on_close()

    def prepare_new_quotation(self): # ★ 修正 (headers_tree 関連削除)
        if getattr(self, '_is_editing_header', False):
            self._is_editing_header = False
        
        self.current_quotation_id = None

        for key in self.detail_vars:
            self.detail_vars[key].set("") 

        for key, entry_widget in self.header_form_entries.items():
            if key in ["total_amount_exclusive_tax", "tax_amount", "total_amount_inclusive_tax", 
                       "staff_name", "original_project_code"]: 
                entry_widget.config(state="readonly")
            else:
                entry_widget.config(state="normal") 

        if hasattr(self, 'items_tree') and self.items_tree: 
            for item in self.items_tree.get_children():
                self.items_tree.delete(item)

        self.detail_vars["quotation_date"].set(datetime.now().strftime("%Y-%m-%d"))
        self.detail_vars["status"].set("作成中")
        self.detail_vars["tax_rate"].set("10")
        self.detail_vars["total_amount_exclusive_tax"].set("0")
        self.detail_vars["tax_amount"].set("0")
        self.detail_vars["total_amount_inclusive_tax"].set("0")

        if "project_id" in self.header_form_entries:
             self.header_form_entries["project_id"].config(state="normal")
        if "quotation_staff_id" in self.header_form_entries:
             self.header_form_entries["quotation_staff_id"].config(state="normal")

        if "quotation_code" in self.header_form_entries: 
            self.header_form_entries["quotation_code"].focus_set() 

        if hasattr(self, 'save_quotation_button'): self.save_quotation_button.config(state="normal") 
        if hasattr(self, 'start_edit_header_button'): self.start_edit_header_button.config(state=tk.DISABLED)
        if hasattr(self, 'add_item_button'): self.add_item_button.config(state=tk.DISABLED) # 新規ヘッダー時は保存後に明細追加可能とする
        if hasattr(self, 'edit_item_button'): self.edit_item_button.config(state=tk.DISABLED)
        if hasattr(self, 'delete_item_button'): self.delete_item_button.config(state=tk.DISABLED)
        
    def save_quotation_data(self): # ★ 修正 (refresh_callback と destroy 呼び出し)
        # --- ヘッダー編集モードでの更新処理 ---
        if self.current_quotation_id is not None and getattr(self, '_is_editing_header', False):
            try:
                quotation_id_to_update = self.current_quotation_id
                # (フォームからのデータ取得、バリデーション、型変換は変更なしなので省略)
                project_id_str = self.detail_vars["project_id"].get().strip()
                quotation_staff_id_str = self.detail_vars["quotation_staff_id"].get().strip()
                quotation_code = self.detail_vars["quotation_code"].get().strip()
                quotation_date = self.detail_vars["quotation_date"].get().strip()
                customer_name_at_quote = self.detail_vars["customer_name_at_quote"].get().strip()
                project_name_at_quote = self.detail_vars["project_name_at_quote"].get().strip()
                site_address_at_quote = self.detail_vars["site_address_at_quote"].get().strip()
                construction_period_notes = self.detail_vars["construction_period_notes"].get().strip()
                tax_rate_str = self.detail_vars["tax_rate"].get().strip().replace('%', '')
                validity_period_notes = self.detail_vars["validity_period_notes"].get().strip()
                payment_terms_notes = self.detail_vars["payment_terms_notes"].get().strip()
                status = self.detail_vars["status"].get().strip()
                remarks = self.detail_vars["remarks"].get().strip()
                total_amount_exclusive_tax_str = self.detail_vars["total_amount_exclusive_tax"].get().replace(',', '')
                tax_amount_str = self.detail_vars["tax_amount"].get().replace(',', '')
                total_amount_inclusive_tax_str = self.detail_vars["total_amount_inclusive_tax"].get().replace(',', '')

                if not project_id_str: messagebox.showerror("入力エラー", "元となる案件IDは必須です。", parent=self); return
                if not quotation_code: messagebox.showerror("入力エラー", "見積番号は必須です。", parent=self); self.header_form_entries["quotation_code"].focus_set(); return
                if not quotation_date: messagebox.showerror("入力エラー", "見積日は必須です。", parent=self); self.header_form_entries["quotation_date"].focus_set(); return
                if not customer_name_at_quote: messagebox.showerror("入力エラー", "宛名は必須です。", parent=self); self.header_form_entries["customer_name_at_quote"].focus_set(); return
                if not project_name_at_quote: messagebox.showerror("入力エラー", "件名は必須です。", parent=self); self.header_form_entries["project_name_at_quote"].focus_set(); return
                if not status: messagebox.showerror("入力エラー", "状況は必須です。", parent=self); self.header_form_entries["status"].focus_set(); return
                
                project_id = int(project_id_str)
                quotation_staff_id = int(quotation_staff_id_str) if quotation_staff_id_str.isdigit() else None
                tax_rate_for_db = float(tax_rate_str) / 100.0 if tax_rate_str else 0.0
                total_amount_exclusive_tax = int(total_amount_exclusive_tax_str) if total_amount_exclusive_tax_str.replace('.', '', 1).isdigit() else 0 # 小数点も考慮
                tax_amount = int(tax_amount_str) if tax_amount_str.replace('.', '', 1).isdigit() else 0
                total_amount_inclusive_tax = int(total_amount_inclusive_tax_str) if total_amount_inclusive_tax_str.replace('.', '', 1).isdigit() else 0


                update_result = self.db_ops.update_quotation(
                    quotation_id=quotation_id_to_update, project_id=project_id, quotation_staff_id=quotation_staff_id,
                    quotation_code=quotation_code, quotation_date=quotation_date, customer_name_at_quote=customer_name_at_quote,
                    project_name_at_quote=project_name_at_quote, site_address_at_quote=site_address_at_quote,
                    construction_period_notes=construction_period_notes, total_amount_exclusive_tax=total_amount_exclusive_tax,
                    tax_rate=tax_rate_for_db, tax_amount=tax_amount, total_amount_inclusive_tax=total_amount_inclusive_tax,
                    validity_period_notes=validity_period_notes, payment_terms_notes=payment_terms_notes,
                    status=status, remarks=remarks
                )

                if update_result is True:
                    messagebox.showinfo("更新成功", f"見積「{quotation_code}」を更新しました。", parent=self)
                    self._is_editing_header = False
                    if self.refresh_callback:
                        self.refresh_callback()
                    self.destroy() 
                # ... (エラー処理は変更なしなので省略) ...
                elif update_result == "DUPLICATE_QUOTATION_CODE": messagebox.showerror("更新エラー", f"見積番号「{quotation_code}」は既に他の見積で使用されています。", parent=self); self.header_form_entries["quotation_code"].focus_set()
                elif update_result == "NOT_FOUND": messagebox.showerror("更新エラー", f"更新対象の見積 (ID: {quotation_id_to_update}) が見つかりませんでした。", parent=self)
                elif update_result == "NOT_NULL_VIOLATION": messagebox.showerror("更新エラー", "必須項目が入力されていません。", parent=self)
                elif update_result == "FK_CONSTRAINT_FAILED": messagebox.showerror("更新エラー", "指定された案件IDまたは見積担当者IDが存在しません。", parent=self)
                else: messagebox.showerror("更新エラー", f"データベースエラーにより見積情報の更新に失敗しました。({update_result})", parent=self)
            except ValueError as ve: messagebox.showerror("入力エラー", f"数値項目の入力値が正しくありません。\n詳細: {ve}", parent=self)
            except Exception as e: messagebox.showerror("システムエラー", f"予期せぬエラーが発生しました: {e}", parent=self)
            finally: self.lift()

        # --- 新規見積ヘッダーの保存処理 ---
        elif self.current_quotation_id is None and not getattr(self, '_is_editing_header', False):
            try:
                # ... (フォームからのデータ取得、バリデーション、型変換は変更なしなので省略) ...
                project_id_str = self.detail_vars["project_id"].get().strip()
                quotation_staff_id_str = self.detail_vars["quotation_staff_id"].get().strip()
                quotation_code = self.detail_vars["quotation_code"].get().strip()
                quotation_date = self.detail_vars["quotation_date"].get().strip()
                customer_name_at_quote = self.detail_vars["customer_name_at_quote"].get().strip()
                project_name_at_quote = self.detail_vars["project_name_at_quote"].get().strip()
                site_address_at_quote = self.detail_vars["site_address_at_quote"].get().strip()
                construction_period_notes = self.detail_vars["construction_period_notes"].get().strip()
                tax_rate_str = self.detail_vars["tax_rate"].get().strip().replace('%', '')
                validity_period_notes = self.detail_vars["validity_period_notes"].get().strip()
                payment_terms_notes = self.detail_vars["payment_terms_notes"].get().strip()
                status = self.detail_vars["status"].get().strip()
                remarks = self.detail_vars["remarks"].get().strip()
                total_amount_exclusive_tax_str = self.detail_vars["total_amount_exclusive_tax"].get().replace(',', '')

                if not project_id_str: messagebox.showerror("入力エラー", "元となる案件IDは必須です。", parent=self); return
                if not quotation_code: messagebox.showerror("入力エラー", "見積番号は必須です。", parent=self); self.header_form_entries["quotation_code"].focus_set(); return
                if not quotation_date: messagebox.showerror("入力エラー", "見積日は必須です。", parent=self); self.header_form_entries["quotation_date"].focus_set(); return
                if not customer_name_at_quote: messagebox.showerror("入力エラー", "宛名は必須です。", parent=self); self.header_form_entries["customer_name_at_quote"].focus_set(); return
                if not project_name_at_quote: messagebox.showerror("入力エラー", "件名は必須です。", parent=self); self.header_form_entries["project_name_at_quote"].focus_set(); return
                if not status: messagebox.showerror("入力エラー", "状況は必須です。", parent=self); self.header_form_entries["status"].focus_set(); return

                project_id = int(project_id_str)
                quotation_staff_id = int(quotation_staff_id_str) if quotation_staff_id_str.isdigit() else None
                total_amount_exclusive_tax_for_db = int(total_amount_exclusive_tax_str) if total_amount_exclusive_tax_str.replace('.', '', 1).isdigit() else 0
                tax_rate_for_db = float(tax_rate_str) / 100.0 if tax_rate_str else 0.0
                tax_amount_for_db = int(total_amount_exclusive_tax_for_db * tax_rate_for_db)
                total_amount_inclusive_tax_for_db = total_amount_exclusive_tax_for_db + tax_amount_for_db
                
                result = self.db_ops.add_quotation(
                    project_id, quotation_staff_id, quotation_code, quotation_date,
                    customer_name_at_quote, project_name_at_quote, site_address_at_quote,
                    construction_period_notes, total_amount_exclusive_tax_for_db, tax_rate_for_db,
                    tax_amount_for_db, total_amount_inclusive_tax_for_db, validity_period_notes,
                    payment_terms_notes, status, remarks
                )

                if isinstance(result, int): 
                    messagebox.showinfo("登録成功", f"見積「{quotation_code}」を登録しました。(ID: {result})", parent=self)
                    if self.refresh_callback: # ★コールバック呼び出し
                        self.refresh_callback()
                    self.destroy() # ★ウィンドウを閉じる
                # ... (エラー処理は変更なしなので省略) ...
                elif result == "DUPLICATE_QUOTATION_CODE": messagebox.showerror("登録エラー", f"見積番号「{quotation_code}」は既に登録されています。", parent=self); self.header_form_entries["quotation_code"].focus_set()
                elif result == "NOT_NULL_VIOLATION": messagebox.showerror("登録エラー", "必須項目が入力されていません。", parent=self)
                elif result == "FK_CONSTRAINT_FAILED": messagebox.showerror("登録エラー", "指定された案件IDまたは見積担当者IDが存在しません。", parent=self)
                else: messagebox.showerror("登録エラー", f"データベースエラーにより見積情報の登録に失敗しました。({result})", parent=self)
            except ValueError as ve: messagebox.showerror("入力エラー", f"数値項目（案件ID、担当者ID、金額、税率など）の入力値が正しくありません。\n詳細: {ve}", parent=self)
            except Exception as e: messagebox.showerror("システムエラー", f"予期せぬエラーが発生しました: {e}", parent=self)
            finally: self.lift()
        else:
            messagebox.showwarning("不正な操作", "保存処理を実行するための条件が満たされていません。", parent=self)
            self.lift()

    # start_header_edit_mode, on_item_tree_select, load_selected_quotation_items,
    # open_add_item_dialog, open_edit_item_dialog, delete_selected_item,
    # recalculate_and_update_quotation_totals, on_close
    # は、前のターンで修正・確認した内容から大きな変更はありません (QuotationListWindowへの移動分を除く)
    # 必要に応じて微調整してください。
    
    # 以下のメソッドは QuotationListWindow に移動したので、このクラスからは削除します。
    # - (旧)_create_headers_treeview 
    # - (旧)load_quotation_headers_to_treeview 
    # - (旧)on_header_tree_select 
    # - (旧)confirm_delete_quotation 

    # on_close は既存のままでOK
    def on_close(self):
        self.destroy()

    # start_header_edit_mode は既存のままでOK (ただしボタン参照先は _create_detail_action_buttons で作成されたもの)
    def start_header_edit_mode(self):
        if self.current_quotation_id is None: # current_quotation_id を使用
            messagebox.showwarning("未選択", "編集する見積ヘッダーが選択されていません。", parent=self)
            self.lift()
            return

        self._is_editing_header = True 

        editable_fields = [
            "quotation_code", "quotation_date", "customer_name_at_quote", 
            "project_name_at_quote", "site_address_at_quote", 
            "construction_period_notes", "tax_rate", 
            "validity_period_notes", "payment_terms_notes", 
            "status", "remarks", "project_id", "quotation_staff_id"
        ]
        for key, entry_widget in self.header_form_entries.items():
            if key in editable_fields:
                if key == "status" and isinstance(entry_widget, ttk.Combobox):
                     entry_widget.config(state="readonly") 
                else:
                    entry_widget.config(state="normal")
            else:
                entry_widget.config(state="readonly")

        if hasattr(self, 'save_quotation_button'): self.save_quotation_button.config(state="normal")
        if hasattr(self, 'start_edit_header_button'): self.start_edit_header_button.config(state="disabled")
        # new_quotation_button, delete_quotation_button はこのウィンドウにはもう無い想定
        
        if "quotation_code" in self.header_form_entries:
            self.header_form_entries["quotation_code"].focus_set()
        self.lift()

    # 他の明細関連メソッド (open_add_item_dialog, open_edit_item_dialog, delete_selected_item, 
    # load_selected_quotation_items, on_item_tree_select, recalculate_and_update_quotation_totals)
    # は、QuotationListWindowへの移動や、それに伴うself.selected_quotation_id から
    # self.current_quotation_id への参照変更以外は、大きなロジック変更は不要なはずです。
    # (これらのメソッドはユーザーが既にアップロードしたコード内に存在し、大きな変更は加えていません)

    # 既存の on_item_tree_select, open_add_item_dialog, open_edit_item_dialog,
    # delete_selected_item, load_selected_quotation_items, recalculate_and_update_quotation_totals
    # メソッドは、QuotationManagementWindow (詳細ウィンドウ) の一部として残ります。
    # selected_quotation_id を current_quotation_id に置き換える必要があるかもしれません。
    # (ユーザーがアップロードした最新コードでは、これらは QuotationManagementWindow に残っていました)

    def on_item_tree_select(self, event): # 変更なしでOK
        selected_items = self.items_tree.selection()
        if selected_items:
            if hasattr(self, 'edit_item_button'): self.edit_item_button.config(state=tk.NORMAL)
            if hasattr(self, 'delete_item_button'): self.delete_item_button.config(state=tk.NORMAL)
        else:
            if hasattr(self, 'edit_item_button'): self.edit_item_button.config(state=tk.DISABLED)
            if hasattr(self, 'delete_item_button'): self.delete_item_button.config(state=tk.DISABLED)

    def open_add_item_dialog(self): # current_quotation_id を使用するように修正
        if self.current_quotation_id is None: # ★変更
            messagebox.showwarning("未選択", "明細を追加する見積ヘッダーが選択されていません。", parent=self)
            return
        dialog = QuotationItemDialog(self, title="見積明細 - 新規追加", quotation_id=self.current_quotation_id) # ★変更
        if dialog.result:
            item_data = dialog.result
            new_item_id_or_error = self.db_ops.add_quotation_item(
                quotation_id=item_data["quotation_id"], name=item_data["name"],
                specification=item_data["specification"], quantity=item_data["quantity"],
                unit=item_data["unit"], unit_price=item_data["unit_price"],
                amount=item_data["amount"], remarks=item_data["remarks"]
            )
            if isinstance(new_item_id_or_error, int):
                messagebox.showinfo("成功", "見積明細を追加しました。", parent=self)
                self.load_selected_quotation_items(self.current_quotation_id) # ★変更
                self.recalculate_and_update_quotation_totals(self.current_quotation_id) # ★変更
            else:
                messagebox.showerror("エラー", f"明細の追加に失敗しました: {new_item_id_or_error}", parent=self)
        self.lift()

    def open_edit_item_dialog(self): # current_quotation_id を使用するように修正
        selected_item_refs = self.items_tree.selection()
        if not selected_item_refs:
            messagebox.showwarning("未選択", "編集する明細が選択されていません。", parent=self); self.lift(); return
        selected_item_id = selected_item_refs[0]
        item_to_edit = self.db_ops.get_quotation_item_by_id(selected_item_id)
        if not item_to_edit:
            messagebox.showerror("エラー", f"選択された明細 (ID: {selected_item_id}) のデータ取得に失敗しました。", parent=self); self.lift(); return
        dialog = QuotationItemDialog(self, title="見積明細 - 編集", item_data=item_to_edit, quotation_id=self.current_quotation_id) # ★変更
        if dialog.result:
            edited_item_data = dialog.result
            current_display_order = item_to_edit.get("display_order")
            update_success_or_error = self.db_ops.update_quotation_item(
                item_id=edited_item_data["item_id"], display_order=current_display_order,
                name=edited_item_data["name"], specification=edited_item_data["specification"],
                quantity=edited_item_data["quantity"], unit=edited_item_data["unit"],
                unit_price=edited_item_data["unit_price"], amount=edited_item_data["amount"],
                remarks=edited_item_data["remarks"]
            )
            if update_success_or_error is True:
                messagebox.showinfo("成功", "見積明細を更新しました。", parent=self)
                self.load_selected_quotation_items(self.current_quotation_id) # ★変更
                self.recalculate_and_update_quotation_totals(self.current_quotation_id) # ★変更
            else:
                messagebox.showerror("エラー", f"明細の更新に失敗しました: {update_success_or_error}", parent=self)
        self.lift()

    def delete_selected_item(self): # current_quotation_id を使用するように修正
        selected_item_refs = self.items_tree.selection()
        if not selected_item_refs:
            messagebox.showwarning("未選択", "削除する明細が選択されていません。", parent=self); self.lift(); return
        selected_item_id = selected_item_refs[0]
        item_values = self.items_tree.item(selected_item_id, 'values')
        item_name_to_confirm = item_values[1] if len(item_values) > 1 else f"ID {selected_item_id}"
        confirm_message = f"明細「{item_name_to_confirm}」(ID: {selected_item_id}) を本当に削除しますか？"
        if not messagebox.askyesno("削除確認", confirm_message, parent=self):
            self.lift(); return
        delete_result = self.db_ops.delete_quotation_item(selected_item_id)
        if delete_result is True:
            messagebox.showinfo("成功", f"明細 (ID: {selected_item_id}) を削除しました。", parent=self)
            self.load_selected_quotation_items(self.current_quotation_id) # ★変更
            self.recalculate_and_update_quotation_totals(self.current_quotation_id) # ★変更
            if hasattr(self, 'edit_item_button'): self.edit_item_button.config(state=tk.DISABLED)
            if hasattr(self, 'delete_item_button'): self.delete_item_button.config(state=tk.DISABLED)
        elif delete_result == "NOT_FOUND": messagebox.showerror("エラー", f"削除対象の明細 (ID: {selected_item_id}) が見つかりませんでした。", parent=self)
        else: messagebox.showerror("エラー", f"明細の削除に失敗しました: {delete_result}", parent=self)
        self.lift()

    def load_selected_quotation_items(self, quotation_id): # 変更なしでOK (引数でquotation_id受け取るので)
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)
        if quotation_id is None: return
        items_data = self.db_ops.get_items_for_quotation(quotation_id)
        if items_data:
            for index, item_tuple in enumerate(items_data):
                quantity_display = f"{item_tuple[5]:.2f}" if item_tuple[5] is not None else ""
                unit_price_display = f"{item_tuple[7]:,}" if item_tuple[7] is not None else ""
                amount_display = f"{item_tuple[8]:,}" if item_tuple[8] is not None else ""
                display_values = (index + 1, item_tuple[3], item_tuple[4] or "", quantity_display,
                                  item_tuple[6] or "", unit_price_display, amount_display, item_tuple[9] or "")
                self.items_tree.insert("", tk.END, values=display_values, iid=item_tuple[0])

    def recalculate_and_update_quotation_totals(self, quotation_id): # 変更なしでOK
        if quotation_id is None:
            self.detail_vars["total_amount_exclusive_tax"].set("0")
            self.detail_vars["tax_amount"].set("0")
            self.detail_vars["total_amount_inclusive_tax"].set("0")
            self.detail_vars["tax_rate"].set("0%")
            return
        items = self.db_ops.get_items_for_quotation(quotation_id)
        total_exclusive = sum(item_tuple[8] for item_tuple in items if item_tuple[8] is not None)
        current_header_data_for_tax_info = self.db_ops.get_quotation_by_id(quotation_id)
        if not current_header_data_for_tax_info:
            messagebox.showerror("エラー", "合計計算のための見積ヘッダー情報取得に失敗しました。", parent=self); return
        db_tax_rate_value = current_header_data_for_tax_info[12] if current_header_data_for_tax_info[12] is not None else 0.0
        tax_amount = int(total_exclusive * db_tax_rate_value)
        total_inclusive = total_exclusive + tax_amount
        self.detail_vars["total_amount_exclusive_tax"].set(f"{total_exclusive:,}")
        self.detail_vars["tax_rate"].set(f"{db_tax_rate_value*100:.0f}%")
        self.detail_vars["tax_amount"].set(f"{tax_amount:,}")
        self.detail_vars["total_amount_inclusive_tax"].set(f"{total_inclusive:,}")
        update_result = self.db_ops.update_quotation(
            quotation_id=quotation_id, project_id=current_header_data_for_tax_info[1],
            quotation_staff_id=current_header_data_for_tax_info[3], quotation_code=current_header_data_for_tax_info[5],
            quotation_date=current_header_data_for_tax_info[6], customer_name_at_quote=current_header_data_for_tax_info[7],
            project_name_at_quote=current_header_data_for_tax_info[8], site_address_at_quote=current_header_data_for_tax_info[9],
            construction_period_notes=current_header_data_for_tax_info[10], total_amount_exclusive_tax=total_exclusive,
            tax_rate=db_tax_rate_value, tax_amount=tax_amount, total_amount_inclusive_tax=total_inclusive,
            validity_period_notes=current_header_data_for_tax_info[15], payment_terms_notes=current_header_data_for_tax_info[16],
            status=current_header_data_for_tax_info[17], remarks=current_header_data_for_tax_info[18]
        )
        if update_result is not True:
            messagebox.showerror("エラー", f"見積合計金額のDB更新に失敗しました: {update_result}", parent=self)
        # 更新後のheaders_treeの該当行の更新は、refresh_callback経由でListWindowが行う

# (QuotationItemDialog クラスの定義はそのまま)
# (if __name__ == '__main__': ブロックは、QuotationListWindow を開くように後で修正)
class QuotationItemDialog(tk.Toplevel):
    def __init__(self, parent, title="見積明細入力", item_data=None, quotation_id=None): 
        super().__init__(parent)
        self.transient(parent) 
        self.title(title)
        self.parent = parent 
        self.result = None   
        self.item_data = item_data 
        self.quotation_id = quotation_id 

        self.resizable(False, False)

        form_frame = ttk.Frame(self, padding="10")
        form_frame.pack(expand=True, fill=tk.BOTH)

        fields = {
            "name": {"label": "名称 (必須):", "row": 0, "col": 0, "width": 40, "type": "entry"}, 
            "specification": {"label": "仕様:", "row": 1, "col": 0, "width": 40, "type": "text", "height": 3}, 
            "quantity": {"label": "数量:", "row": 2, "col": 0, "width": 10, "type": "entry"}, 
            "unit": {"label": "単位:", "row": 2, "col": 2, "width": 10, "type": "entry"}, 
            "unit_price": {"label": "単価:", "row": 3, "col": 0, "width": 15, "type": "entry"}, 
            "remarks": {"label": "備考:", "row": 4, "col": 0, "width": 40, "type": "text", "height": 3} 
        }

        self.entries = {} 
        self.string_vars = {} 

        for key, field_info in fields.items():
            ttk.Label(form_frame, text=field_info["label"]).grid(
                row=field_info["row"], column=field_info["col"], padx=5, pady=3, sticky=tk.NW if field_info["type"] == "text" else tk.W
            )
            if field_info["type"] == "entry":
                self.string_vars[key] = tk.StringVar()
                entry = ttk.Entry(form_frame, textvariable=self.string_vars[key], width=field_info["width"])
                entry.grid(row=field_info["row"], column=field_info["col"] + 1, padx=5, pady=3, sticky=tk.EW, 
                           columnspan=3 if field_info["col"] == 0 and field_info.get("type") != "text" and key not in ["quantity", "unit_price"] else 1) 
                self.entries[key] = entry
            elif field_info["type"] == "text":
                text_widget = tk.Text(form_frame, width=field_info["width"], height=field_info["height"])
                text_widget.grid(row=field_info["row"], column=field_info["col"] + 1, padx=5, pady=3, sticky=tk.NSEW, columnspan=3)
                self.entries[key] = text_widget
        
        form_frame.columnconfigure(1, weight=1) 
        form_frame.columnconfigure(3, weight=1) 

        button_frame = ttk.Frame(self, padding=(10, 5, 10, 10)) 
        button_frame.pack(fill=tk.X, side=tk.BOTTOM) 

        ttk.Button(button_frame, text="キャンセル", command=self.on_cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="保存", command=self.on_save).pack(side=tk.RIGHT, padx=5)
        
        if self.item_data:
            self.string_vars["name"].set(self.item_data.get("name", ""))
            self.entries["specification"].insert("1.0", self.item_data.get("specification", ""))
            self.string_vars["quantity"].set(str(self.item_data.get("quantity", "")))
            self.string_vars["unit"].set(self.item_data.get("unit", ""))
            self.string_vars["unit_price"].set(str(self.item_data.get("unit_price", "")))
            self.entries["remarks"].insert("1.0", self.item_data.get("remarks", ""))

        self.entries["name"].focus_set() 
        
        self.geometry("") 
        self.update_idletasks() 
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        
        position_x = parent_x + (parent_width // 2) - (dialog_width // 2)
        position_y = parent_y + (parent_height // 2) - (dialog_height // 2)
        self.geometry(f"+{position_x}+{position_y}")

        self.grab_set()
        self.wait_window(self)

    def on_save(self):
        name = self.string_vars["name"].get().strip()
        if not name:
            messagebox.showerror("入力エラー", "名称は必須です。", parent=self)
            self.entries["name"].focus_set()
            return

        try:
            quantity_str = self.string_vars["quantity"].get().strip()
            quantity = float(quantity_str) if quantity_str else 0.0

            unit_price_str = self.string_vars["unit_price"].get().strip()
            unit_price = int(unit_price_str) if unit_price_str else 0
            
        except ValueError:
            messagebox.showerror("入力エラー", "数量、単価には有効な数値を入力してください。", parent=self)
            return

        amount = int(quantity * unit_price) 

        self.result = {
            "quotation_id": self.quotation_id,
            "name": name,
            "specification": self.entries["specification"].get("1.0", tk.END).strip(),
            "quantity": quantity,
            "unit": self.string_vars["unit"].get().strip(),
            "unit_price": unit_price,
            "amount": amount,
            "remarks": self.entries["remarks"].get("1.0", tk.END).strip()
        }
        
        if self.item_data and "item_id" in self.item_data: 
            self.result["item_id"] = self.item_data["item_id"]
            
        self.destroy()

    def on_cancel(self):
        self.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    root.title("メインウィンドウ (テスト用)")

    # db_ops を QuotationListWindow が期待する形で準備
    # (例: main_window.py と同様に root に db_ops 属性を持たせる)
    try:
        # import database_operations as db_ops # グローバルなdb_opsを期待する場合
        if not hasattr(root, 'db_ops'):
             # このテスト実行専用に db_ops を main_window.py と同様にセットアップ
             import database_operations as db_ops_module
             root.db_ops = db_ops_module
    except ImportError:
        messagebox.showerror("テストエラー", "database_operations.py が見つかりません。")
        root.destroy()
        exit() # ここで終了させる

    def open_quotation_list_window(): # 関数名を変更
        list_win = QuotationListWindow(root) # ★ QuotationListWindow を開く
        # list_win.grab_set() # 必要に応じて

    open_button = ttk.Button(root, text="見積一覧を開く", command=open_quotation_list_window) # ボタンテキストも変更
    open_button.pack(padx=20, pady=20)

    root.mainloop()