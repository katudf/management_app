# quotation_management_window.py

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import database_operations as db_ops
from datetime import datetime


class QuotationListWindow(tk.Toplevel):
    # __init__ メソッドの引数に project_filter_id を追加
    def __init__(self, master, project_filter_id=None): # <- 変更点
        super().__init__(master)
        # self.title("見積一覧") # タイトル設定は後で動的に行う
        self.geometry("900x500")
        if hasattr(master, 'db_ops'):
            self.db_ops = master.db_ops
        else:
            messagebox.showerror("エラー", "データベース操作モジュールが見つかりません。", parent=self)
            self.destroy()
            return

        self.parent_window = master
        self.selected_quotation_id_for_detail = None
        self.project_filter_id = project_filter_id # <- 追加: 受け取った案件IDを保持

        # フィルタリングされている案件の情報を取得してタイトルに設定
        if self.project_filter_id:
            project_info = self.db_ops.get_project_by_id(self.project_filter_id)
            if project_info:
                project_code_for_title = project_info[1] or "コード不明" # project_code はインデックス1
                project_name_for_title = project_info[2] or "名称不明" # project_name はインデックス2
                self.title(f"見積一覧 (案件: {project_code_for_title} - {project_name_for_title})")
            else:
                self.title("見積一覧 (指定案件の情報取得不可)")
        else:
            self.title("見積一覧 (全ての案件)")


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

        headers_list_frame = ttk.LabelFrame(main_frame, text="見積一覧", padding="5") # このテキストも動的に変更可能
        if self.project_filter_id:
            headers_list_frame.config(text=f"見積一覧 (フィルタリング中)") # 例
        headers_list_frame.pack(fill=tk.BOTH, expand=True, pady=(5,0))


        self._create_headers_treeview(headers_list_frame)

        style = ttk.Style(self)
        tree_font_family = "メイリオ"
        tree_font_size = 10
        tree_row_height = tree_font_size + 10
        style.configure("Treeview", font=(tree_font_family, tree_font_size), rowheight=tree_row_height)
        style.configure("Treeview.Heading", font=(tree_font_family, tree_font_size, "bold"))

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

        quotation_headers_data = []
        # project_filter_id に基づいて取得するデータを変更
        if self.project_filter_id: # <- 変更点: フィルタIDがある場合
            quotation_headers_data = self.db_ops.get_quotations_by_project_id(self.project_filter_id)
        else: # フィルタIDがない場合は全件取得
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
                    total_amount_display, # total_amount_inclusive_tax
                    q_header_tuple[11], # status
                    q_header_tuple[7] or "" # staff_name
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

    def open_new_quotation_detail(self):
        # from project_management_window import ProjectManagementWindow # ここでのimportは不要かも
        project_id_to_use = None
        # 親ウィンドウが ProjectManagementWindow のインスタンスで、
        # selected_project_id 属性を持っているか確認
        # もし、このQuotationListWindowがフィルタリングされて開かれているなら、その案件IDを使う
        if self.project_filter_id: # <- 変更点: まずフィルタIDを確認
            project_id_to_use = self.project_filter_id
            print(f"DEBUG: Creating new quotation, using project_filter_id {project_id_to_use} from QuotationListWindow context.")
        elif isinstance(self.master, tk.Toplevel) and hasattr(self.master, 'selected_project_id') and self.master.selected_project_id is not None:
            # 親がProjectManagementWindowで、そこから直接開かれた場合 (これは通常 project_filter_id が設定されるはず)
             project_id_to_use = self.master.selected_project_id
             print(f"DEBUG: Creating new quotation, using project_id {project_id_to_use} from parent (ProjectManagementWindow).")


        detail_win = QuotationManagementWindow(
            self,
            quotation_id=None,
            refresh_callback=self.load_quotation_headers_to_treeview,
            project_id_for_new=project_id_to_use # フィルタリングされた案件ID、または親から受け取った案件IDを渡す
        )
        # detail_win.grab_set()

    def open_selected_quotation_detail(self):
        if not self.selected_quotation_id_for_detail:
            messagebox.showwarning("未選択", "表示/編集する見積が選択されていません。", parent=self)
            self.lift()
            return
        # QuotationManagementWindow を呼び出す際、project_id_for_new は不要 (既存の見積のため)
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

# --- QuotationManagementWindow クラス (変更なし) ---
class QuotationManagementWindow(tk.Toplevel): # 詳細ウィンドウとしての役割
    def __init__(self, master, quotation_id=None, refresh_callback=None, project_id_for_new=None): # ★ project_id_for_new を追加
        super().__init__(master)

        # ... (既存のdb_ops, parent_list_window の設定) ...
        if hasattr(master, 'db_ops'): # master は QuotationListWindow or ProjectManagementWindow
            self.db_ops = master.db_ops
        elif hasattr(master, 'parent_window') and hasattr(master.parent_window, 'db_ops'): # masterが詳細ウィンドウで、その親がListWindowの場合など
             self.db_ops = master.parent_window.db_ops
        else:
            messagebox.showerror("致命的なエラー", "データベース操作モジュールが見つかりません。", parent=self) # selfをparentに
            self.after(100, self.destroy)
            return

        self.parent_list_window = master # masterがQuotationListWindowであると期待
        self.current_quotation_id = quotation_id
        self.refresh_callback = refresh_callback
        self.project_id_for_new_quotation_context = project_id_for_new # ★ 受け取った案件IDを保持

        # ... (既存のフラグ初期化、タイトル設定、geometry設定など) ...
        self._preparing_new_quotation_flag = False
        self._is_editing_header = False

        if self.current_quotation_id is None: # 新規モード
            self.title("見積作成 - 新規")
            if self.project_id_for_new_quotation_context:
                # 案件IDが指定されていれば、それもタイトルに含めても良い
                project_info_for_title = self.db_ops.get_project_by_id(self.project_id_for_new_quotation_context)
                if project_info_for_title:
                    project_code_for_title = project_info_for_title[1] or "コード不明"
                    self.title(f"見積作成 - 新規 (案件: {project_code_for_title})")
                else:
                    self.title("見積作成 - 新規 (指定案件不明)")


        else:
            # DBから見積情報を取得してタイトルに表示することも可能 (get_quotation_by_id がタプルを返す)
            header_info_for_title = self.db_ops.get_quotation_by_id(self.current_quotation_id)
            title_quot_code = header_info_for_title[5] if header_info_for_title and len(header_info_for_title) > 5 else ""
            self.title(f"見積詳細/編集 - {title_quot_code} (ID: {self.current_quotation_id})")

        self.geometry("850x700") # 詳細ウィンドウ用のサイズに調整

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._create_detail_widgets()

        if self.current_quotation_id is None:
            self.prepare_new_quotation() # 新規モードの準備
        else:
            self._load_quotation_for_display(self.current_quotation_id) # 既存データの読み込み

    def _create_detail_widgets(self):
        # PanedWindowを使ってヘッダーフォームと明細一覧を上下に配置
        details_pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        details_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 上部：見積ヘッダーの詳細フォーム
        header_form_frame = ttk.LabelFrame(details_pane, text="見積ヘッダー詳細", padding="5")
        details_pane.add(header_form_frame, weight=1) # weight調整 (例: ヘッダー部を狭く)
        self._create_header_detail_form(header_form_frame)

        # 下部：見積ヘッダーの明細一覧
        items_list_frame = ttk.LabelFrame(details_pane, text="見積明細一覧", padding="5")
        details_pane.add(items_list_frame, weight=4) # weight調整 (例: 明細部を広く)

        self.item_action_frame = ttk.Frame(items_list_frame)
        self.item_action_frame.pack(fill=tk.X, pady=(0, 5))
        self._create_item_action_buttons(self.item_action_frame)

        self._create_items_treeview(items_list_frame)

        style = ttk.Style(self)
        tree_font_family = "メイリオ"
        tree_font_size = 10
        tree_row_height = tree_font_size + 10
        # このウィンドウのTreeview(items_tree)用のスタイル設定
        style.configure("Detail.Treeview", font=(tree_font_family, tree_font_size), rowheight=tree_row_height)
        style.configure("Detail.Treeview.Heading", font=(tree_font_family, tree_font_size, "bold"))
        if hasattr(self, 'items_tree'): # items_tree が作成された後でスタイルを適用
            self.items_tree.configure(style="Detail.Treeview")

        # 最下部：操作ボタンフレーム
        detail_action_frame = ttk.Frame(self, padding="5")
        detail_action_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(0,5))
        self._create_detail_action_buttons(detail_action_frame)

    def _create_header_detail_form(self, parent_frame):
        # ボタン配置用フレームをフォームの上に追加
        header_button_frame = ttk.Frame(parent_frame)
        header_button_frame.grid(row=0, column=0, columnspan=4, pady=(0, 10), sticky=tk.E)

        self.start_edit_header_button = ttk.Button(header_button_frame, text="ヘッダー編集", command=self.start_header_edit_mode, state=tk.DISABLED)
        self.start_edit_header_button.pack(side=tk.LEFT, padx=5)

        self.save_quotation_button = ttk.Button(header_button_frame, text="この見積を保存", command=self.save_quotation_data, state=tk.DISABLED)
        self.save_quotation_button.pack(side=tk.LEFT, padx=5)

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
        # フォームレイアウトの開始行を row=1 からに変更
        form_layout = [
            ("見積番号:", "quotation_code", 1, 0), ("見積日:", "quotation_date", 1, 2),
            ("宛名:", "customer_name_at_quote", 2, 0), ("件名:", "project_name_at_quote", 2, 2),
            ("案件ID (必須):", "project_id", 3, 0), ("元案件コード:", "original_project_code", 3, 2),
            ("見積担当者ID:", "quotation_staff_id", 4, 0), ("見積担当者名:", "staff_name", 4, 2),
            ("現場住所:", "site_address_at_quote", 5, 0, 3), ("工期:", "construction_period_notes", 6, 0, 3),
            ("有効期限:", "validity_period_notes", 7, 0), ("支払条件:", "payment_terms_notes", 7, 2),
            ("状況:", "status", 8, 0), ("税率(%):", "tax_rate", 8, 2),
            ("税抜合計:", "total_amount_exclusive_tax", 9, 0), ("消費税額:", "tax_amount", 9, 2),
            ("見積金額(税込):", "total_amount_inclusive_tax", 10, 0), ("備考:", "remarks", 11, 0, 3)
        ]
        for label_text, key, r, c, *span in form_layout:
            ttk.Label(parent_frame, text=label_text).grid(row=r, column=c, padx=5, pady=2, sticky=tk.W)
            entry_width = 35 if len(span) > 0 and span[0] == 3 else 18
            if key in ["remarks", "construction_period_notes", "validity_period_notes", "payment_terms_notes", "site_address_at_quote"]:
                # TextウィジェットではなくEntryで対応している場合
                entry = ttk.Entry(parent_frame, textvariable=self.detail_vars[key], width=entry_width)
            elif key == "status":
                # ここは status_options を使ったComboboxに変更しても良い
                entry = ttk.Entry(parent_frame, textvariable=self.detail_vars[key], width=entry_width, state="readonly") # デフォルトは readonly
            elif key in ["total_amount_exclusive_tax", "tax_amount", "total_amount_inclusive_tax", "staff_name", "original_project_code"]:
                entry = ttk.Entry(parent_frame, textvariable=self.detail_vars[key], width=entry_width, state="readonly")
            else:
                entry = ttk.Entry(parent_frame, textvariable=self.detail_vars[key], width=entry_width)
            entry.grid(row=r, column=c + 1, padx=5, pady=2, sticky=tk.EW, columnspan=(span[0] if span else 1))
            self.header_form_entries[key] = entry
        parent_frame.columnconfigure(1, weight=1)
        parent_frame.columnconfigure(3, weight=1)

    def _create_items_treeview(self, parent_frame):
        columns = ("no", "name", "specification", "quantity", "unit", "unit_price", "amount", "remarks")
        self.items_tree = ttk.Treeview(parent_frame, columns=columns, show="headings", height=3, style="Detail.Treeview") # heightとstyle適用
        self.items_tree.heading("no", text="No."); self.items_tree.column("no", width=40, anchor=tk.CENTER)
        self.items_tree.heading("name", text="名称"); self.items_tree.column("name", width=150) # 幅調整
        self.items_tree.heading("specification", text="仕様"); self.items_tree.column("specification", width=150) # 幅調整
        self.items_tree.heading("quantity", text="数量"); self.items_tree.column("quantity", width=60, anchor=tk.E)
        self.items_tree.heading("unit", text="単位"); self.items_tree.column("unit", width=60, anchor=tk.CENTER)
        self.items_tree.heading("unit_price", text="単価"); self.items_tree.column("unit_price", width=90, anchor=tk.E)
        self.items_tree.heading("amount", text="金額"); self.items_tree.column("amount", width=90, anchor=tk.E)
        self.items_tree.heading("remarks", text="備考"); self.items_tree.column("remarks", width=100) # 幅調整
        scrollbar_y = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        scrollbar_x = ttk.Scrollbar(parent_frame, orient=tk.HORIZONTAL, command=self.items_tree.xview)
        self.items_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.items_tree.bind("<<TreeviewSelect>>", self.on_item_tree_select)

    def _create_item_action_buttons(self, parent_frame):
        self.add_item_button = ttk.Button(parent_frame, text="明細追加", command=self.open_add_item_dialog, state=tk.DISABLED)
        self.add_item_button.pack(side=tk.LEFT, padx=5)
        self.edit_item_button = ttk.Button(parent_frame, text="明細編集", command=self.open_edit_item_dialog, state=tk.DISABLED)
        self.edit_item_button.pack(side=tk.LEFT, padx=5)
        self.delete_item_button = ttk.Button(parent_frame, text="明細削除", command=self.delete_selected_item, state=tk.DISABLED)
        self.delete_item_button.pack(side=tk.LEFT, padx=5)

    def _create_detail_action_buttons(self, parent_frame):
        # 「ヘッダー編集」「この見積を保存」は _create_header_detail_form に移動済み
        self.close_button = ttk.Button(parent_frame, text="閉じる", command=self.on_close)
        self.close_button.pack(side=tk.RIGHT, padx=5, pady=5)

    def _load_quotation_for_display(self, quotation_id):
        if quotation_id is None:
            self.prepare_new_quotation()
            return
        self.current_quotation_id = quotation_id
        header_data = self.db_ops.get_quotation_by_id(self.current_quotation_id)
        if header_data:
            self._is_editing_header = False
            # get_quotation_by_id の戻り値のインデックスに注意してマッピング
            # 0:q.quotation_id, 1:q.project_id, 2:original_project_code,
            # 3:q.quotation_staff_id, 4:staff_name, 5:q.quotation_code, 6:q.quotation_date,
            # 7:q.customer_name_at_quote, 8:q.project_name_at_quote,
            # 9:q.site_address_at_quote, 10:q.construction_period_notes,
            # 11:q.total_amount_exclusive_tax, 12:q.tax_rate, 13:q.tax_amount,
            # 14:q.total_amount_inclusive_tax, 15:q.validity_period_notes,
            # 16:q.payment_terms_notes, 17:q.status, 18:q.remarks,
            self.detail_vars["project_id"].set(str(header_data[1]) if header_data[1] is not None else "")
            self.detail_vars["original_project_code"].set(header_data[2] or "")
            self.detail_vars["quotation_staff_id"].set(str(header_data[3]) if header_data[3] is not None else "")
            self.detail_vars["staff_name"].set(header_data[4] or "")
            self.detail_vars["quotation_code"].set(header_data[5] or "")
            self.detail_vars["quotation_date"].set(header_data[6] or "")
            self.detail_vars["customer_name_at_quote"].set(header_data[7] or "")
            self.detail_vars["project_name_at_quote"].set(header_data[8] or "")
            self.detail_vars["site_address_at_quote"].set(header_data[9] or "")
            self.detail_vars["construction_period_notes"].set(header_data[10] or "")
            self.detail_vars["total_amount_exclusive_tax"].set(f"{header_data[11]:,}" if header_data[11] is not None else "0")
            self.detail_vars["tax_rate"].set(f"{header_data[12]*100:.0f}" if header_data[12] is not None else "0") # %表示
            self.detail_vars["tax_amount"].set(f"{header_data[13]:,}" if header_data[13] is not None else "0")
            self.detail_vars["total_amount_inclusive_tax"].set(f"{header_data[14]:,}" if header_data[14] is not None else "0")
            self.detail_vars["validity_period_notes"].set(header_data[15] or "")
            self.detail_vars["payment_terms_notes"].set(header_data[16] or "")
            self.detail_vars["status"].set(header_data[17] or "")
            self.detail_vars["remarks"].set(header_data[18] or "")


            for key, entry_widget in self.header_form_entries.items():
                entry_widget.config(state="readonly")
            self.load_selected_quotation_items(self.current_quotation_id)

            if hasattr(self, 'save_quotation_button'): self.save_quotation_button.config(state=tk.DISABLED)
            if hasattr(self, 'start_edit_header_button'): self.start_edit_header_button.config(state=tk.NORMAL)
            if hasattr(self, 'add_item_button'): self.add_item_button.config(state=tk.NORMAL) # 既存見積表示時は明細追加可能
            if hasattr(self, 'edit_item_button'): self.edit_item_button.config(state=tk.DISABLED)
            if hasattr(self, 'delete_item_button'): self.delete_item_button.config(state=tk.DISABLED)
        else:
            messagebox.showerror("エラー", f"見積ID {quotation_id} の情報取得に失敗しました。", parent=self)
            self.on_close()

    def prepare_new_quotation(self):
        if getattr(self, '_is_editing_header', False): # 既存の編集モードは解除
            self._is_editing_header = False
        self.current_quotation_id = None
        for key in self.detail_vars: self.detail_vars[key].set("") # 全てのStringVarをクリア

        project_info = None
        if self.project_id_for_new_quotation_context is not None:
            project_info = self.db_ops.get_project_by_id(self.project_id_for_new_quotation_context)
            if project_info:
                # get_project_by_id の戻り値のインデックスを確認
                # 0:p.project_id, 1:p.project_code, 2:p.project_name, 4:c.customer_name, 7:p.site_address
                self.detail_vars["project_id"].set(str(project_info[0]))
                self.detail_vars["original_project_code"].set(project_info[1] or "")
                self.detail_vars["customer_name_at_quote"].set(project_info[4] or "")
                self.detail_vars["project_name_at_quote"].set(project_info[2] or "")
                self.detail_vars["site_address_at_quote"].set(project_info[7] or "")
                # 案件IDがセットされたら、そのフィールドは readonly にする
                if "project_id" in self.header_form_entries:
                    self.header_form_entries["project_id"].config(state="readonly")
            else:
                messagebox.showwarning("注意", f"指定された案件ID ({self.project_id_for_new_quotation_context}) の情報が見つかりません。案件IDを手動で入力してください。", parent=self)
                if "project_id" in self.header_form_entries:
                    self.header_form_entries["project_id"].config(state="normal") # 手動入力可能に
        else: # project_id_for_new_quotation_context が None の場合
            if "project_id" in self.header_form_entries:
                 self.header_form_entries["project_id"].config(state="normal")


        # 新規作成時のデフォルト値設定
        self.detail_vars["quotation_date"].set(datetime.now().strftime("%Y-%m-%d"))
        self.detail_vars["status"].set("作成中")
        self.detail_vars["tax_rate"].set("10") # デフォルト税率10%
        self.detail_vars["total_amount_exclusive_tax"].set("0")
        self.detail_vars["tax_amount"].set("0")
        self.detail_vars["total_amount_inclusive_tax"].set("0")

        # フォーム要素の状態を設定
        for key, entry_widget in self.header_form_entries.items():
            # 案件IDが自動セットされている場合はreadonly、それ以外はnormal
            if key == "project_id" and self.project_id_for_new_quotation_context and project_info:
                entry_widget.config(state="readonly")
            # 金額関連、担当者名、元案件コードは表示専用(readonly)
            elif key in ["total_amount_exclusive_tax", "tax_amount", "total_amount_inclusive_tax", "staff_name", "original_project_code"]:
                entry_widget.config(state="readonly")
            else: # それ以外のフィールドは入力可能 (normal)
                entry_widget.config(state="normal")

        if hasattr(self, 'items_tree'):
            for item in self.items_tree.get_children(): self.items_tree.delete(item)


        # フォーカス設定
        if self.project_id_for_new_quotation_context and project_info:
             if "quotation_code" in self.header_form_entries:
                self.header_form_entries["quotation_code"].focus_set()
        elif "project_id" in self.header_form_entries and self.header_form_entries["project_id"]["state"] == "normal":
            self.header_form_entries["project_id"].focus_set()
        elif "quotation_code" in self.header_form_entries:
            self.header_form_entries["quotation_code"].focus_set()

        # ボタン状態設定
        if hasattr(self, 'save_quotation_button'): self.save_quotation_button.config(state="normal") # 新規作成なので保存可能
        if hasattr(self, 'start_edit_header_button'): self.start_edit_header_button.config(state=tk.DISABLED) # 新規作成なので編集開始は不要
        if hasattr(self, 'add_item_button'): self.add_item_button.config(state=tk.DISABLED) # ヘッダー保存後に明細追加可能にする
        if hasattr(self, 'edit_item_button'): self.edit_item_button.config(state=tk.DISABLED)
        if hasattr(self, 'delete_item_button'): self.delete_item_button.config(state=tk.DISABLED)

    def save_quotation_data(self): # 新規保存と更新保存を統合
        window_destroyed = False # destroy()が呼ばれたかどうかのフラグ
        try:
            # フォームから値を取得
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
            remarks = self.detail_vars["remarks"].get().strip() # remarksはEntryなのでget()
            
            # 金額関連の取得と変換 (カンマ除去、数値変換)
            total_amount_exclusive_tax_str = self.detail_vars["total_amount_exclusive_tax"].get().replace(',', '')
            tax_amount_str = self.detail_vars["tax_amount"].get().replace(',', '')
            total_amount_inclusive_tax_str = self.detail_vars["total_amount_inclusive_tax"].get().replace(',', '')

            # バリデーション
            if not project_id_str: messagebox.showerror("入力エラー", "元となる案件IDは必須です。", parent=self); return
            if not quotation_code: messagebox.showerror("入力エラー", "見積番号は必須です。", parent=self); self.header_form_entries["quotation_code"].focus_set(); return
            if not quotation_date: messagebox.showerror("入力エラー", "見積日は必須です。", parent=self); self.header_form_entries["quotation_date"].focus_set(); return
            if not customer_name_at_quote: messagebox.showerror("入力エラー", "宛名は必須です。", parent=self); self.header_form_entries["customer_name_at_quote"].focus_set(); return
            if not project_name_at_quote: messagebox.showerror("入力エラー", "件名は必須です。", parent=self); self.header_form_entries["project_name_at_quote"].focus_set(); return
            if not status: messagebox.showerror("入力エラー", "状況は必須です。", parent=self); self.header_form_entries["status"].focus_set(); return

            # 型変換
            project_id = int(project_id_str)
            quotation_staff_id = int(quotation_staff_id_str) if quotation_staff_id_str.isdigit() else None
            tax_rate_for_db = float(tax_rate_str) / 100.0 if tax_rate_str else 0.0 # %から小数へ
            
            # 金額は明細から再計算されたものが表示されているはずだが、念のため変換
            total_amount_exclusive_tax = int(total_amount_exclusive_tax_str) if total_amount_exclusive_tax_str.replace('.', '', 1).isdigit() else 0
            tax_amount = int(tax_amount_str) if tax_amount_str.replace('.', '', 1).isdigit() else 0
            total_amount_inclusive_tax = int(total_amount_inclusive_tax_str) if total_amount_inclusive_tax_str.replace('.', '', 1).isdigit() else 0
            
            # current_quotation_id と _is_editing_header フラグに基づいて新規か更新かを判断
            if self.current_quotation_id is not None and self._is_editing_header: # 更新モード
                quotation_id_to_update = self.current_quotation_id
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
                    messagebox.showinfo("更新成功", f"見積「{quotation_code}」を更新しました。", parent=self.parent_list_window) # 親ウィンドウに通知
                    self._is_editing_header = False # 編集モード解除
                    if self.refresh_callback: self.refresh_callback() # 親の一覧を更新
                    window_destroyed = True; self.destroy() # ウィンドウを閉じる
                # ... (既存のエラーハンドリング) ...
                elif update_result == "DUPLICATE_QUOTATION_CODE": messagebox.showerror("更新エラー", f"見積番号「{quotation_code}」は既に他の見積で使用されています。", parent=self); self.header_form_entries["quotation_code"].focus_set()
                elif update_result == "NOT_FOUND": messagebox.showerror("更新エラー", f"更新対象の見積 (ID: {quotation_id_to_update}) が見つかりませんでした。", parent=self)
                elif update_result == "NOT_NULL_VIOLATION": messagebox.showerror("更新エラー", "必須項目が入力されていません。", parent=self)
                elif update_result == "FK_CONSTRAINT_FAILED": messagebox.showerror("更新エラー", "指定された案件IDまたは見積担当者IDが存在しません。", parent=self)
                else: messagebox.showerror("更新エラー", f"データベースエラーにより見積情報の更新に失敗しました。({update_result})", parent=self)

            elif self.current_quotation_id is None and not self._is_editing_header: # 新規作成モード
                # 新規作成時は、明細がない状態なので、合計金額は0または手入力されたものとして扱う
                # 通常はヘッダー保存後に明細を追加し、そのタイミングで合計が再計算・更新される
                # ここでは、初期のヘッダー情報としてDBに追加する
                
                # 新規作成時の金額は、もし明細がないなら一旦0として、後で明細追加時に再計算・更新する
                # もしユーザーが手入力で金額を入れた場合はそれを使うが、通常は明細からの計算を期待
                if not self.items_tree.get_children(): # 明細がまだない場合
                    total_amount_exclusive_tax_for_db = 0
                    tax_amount_for_db = 0
                    total_amount_inclusive_tax_for_db = 0
                else: # 万が一、新規作成フローで明細が先に追加されるケースがあれば、その合計を使う
                      # (通常はヘッダーIDがないと明細追加できないので、この分岐はほぼ通らない想定)
                    total_amount_exclusive_tax_for_db = total_amount_exclusive_tax
                    tax_amount_for_db = tax_amount
                    total_amount_inclusive_tax_for_db = total_amount_inclusive_tax

                result = self.db_ops.add_quotation(
                    project_id, quotation_staff_id, quotation_code, quotation_date,
                    customer_name_at_quote, project_name_at_quote, site_address_at_quote,
                    construction_period_notes, total_amount_exclusive_tax_for_db, tax_rate_for_db,
                    tax_amount_for_db, total_amount_inclusive_tax_for_db, validity_period_notes,
                    payment_terms_notes, status, remarks
                )
                if isinstance(result, int): # 新しい見積IDが返る
                    self.current_quotation_id = result # 新しく採番されたIDを保持
                    messagebox.showinfo("登録成功", f"見積ヘッダー「{quotation_code}」を登録しました。(ID: {self.current_quotation_id})\n続けて明細を追加してください。", parent=self)
                    # ヘッダー保存後は、明細追加が可能になるようにボタン状態を変更
                    if hasattr(self, 'add_item_button'): self.add_item_button.config(state="normal")
                    if hasattr(self, 'save_quotation_button'): self.save_quotation_button.config(state="disabled") # 一旦保存したら無効化（変更があれば編集モードへ）
                    if hasattr(self, 'start_edit_header_button'): self.start_edit_header_button.config(state="normal") # 編集モードに入れるように
                    # タイトルも更新
                    self.title(f"見積詳細/編集 - {quotation_code} (ID: {self.current_quotation_id})")
                    # フォームを読み取り専用に（編集モードに入るまで）
                    for key, entry_widget in self.header_form_entries.items():
                        entry_widget.config(state="readonly")
                    if self.refresh_callback: self.refresh_callback() # 親の一覧を更新
                    # ウィンドウは閉じないで、明細追加を促す
                # ... (既存のエラーハンドリング) ...
                elif result == "DUPLICATE_QUOTATION_CODE": messagebox.showerror("登録エラー", f"見積番号「{quotation_code}」は既に登録されています。", parent=self); self.header_form_entries["quotation_code"].focus_set()
                elif result == "NOT_NULL_VIOLATION": messagebox.showerror("登録エラー", "必須項目が入力されていません。", parent=self)
                elif result == "FK_CONSTRAINT_FAILED": messagebox.showerror("登録エラー", "指定された案件IDまたは見積担当者IDが存在しません。", parent=self)
                else: messagebox.showerror("登録エラー", f"データベースエラーにより見積情報の登録に失敗しました。({result})", parent=self)
            else:
                messagebox.showwarning("不正な操作", "保存処理を実行するための条件が満たされていません（不明な状態です）。", parent=self)

        except ValueError as ve:
            messagebox.showerror("入力エラー", f"数値項目の入力値が正しくありません。\n詳細: {ve}", parent=self)
        except Exception as e:
            messagebox.showerror("システムエラー", f"予期せぬエラーが発生しました: {e}", parent=self)
        finally:
            # destroy()が呼ばれていない、かつウィンドウが存在する場合のみlift()
            if not window_destroyed and self.winfo_exists():
                self.lift()


    def start_header_edit_mode(self):
        if self.current_quotation_id is None: # 新規作成フロー中ではなく、既存の見積もりが選択されていない場合
            messagebox.showwarning("未選択", "編集する見積ヘッダーが選択されていません（または新規作成中です）。", parent=self)
            self.lift()
            return
        self._is_editing_header = True
        # 編集可能にするフィールドのキー
        editable_fields = [
            "quotation_code", "quotation_date", "customer_name_at_quote",
            "project_name_at_quote", "site_address_at_quote",
            "construction_period_notes", "tax_rate",
            "validity_period_notes", "payment_terms_notes",
            "status", "remarks", "project_id", "quotation_staff_id"
        ]
        for key, entry_widget in self.header_form_entries.items():
            if key in editable_fields:
                if key == "status" and isinstance(entry_widget, ttk.Combobox): # もしComboboxなら
                     entry_widget.config(state="readonly") # 選択のみ可能
                else: # Entryなら
                    entry_widget.config(state="normal")
            else: # 編集不可のフィールド (ID、金額関連、担当者名、元案件コードなど)
                entry_widget.config(state="readonly")

        if hasattr(self, 'save_quotation_button'): self.save_quotation_button.config(state="normal") # 保存ボタンを有効化
        if hasattr(self, 'start_edit_header_button'): self.start_edit_header_button.config(state="disabled") # 編集開始ボタンを無効化
        if "quotation_code" in self.header_form_entries: # 見積番号にフォーカス
            self.header_form_entries["quotation_code"].focus_set()
        self.lift()


    def on_item_tree_select(self, event):
        selected_items = self.items_tree.selection()
        if selected_items:
            if hasattr(self, 'edit_item_button'): self.edit_item_button.config(state=tk.NORMAL)
            if hasattr(self, 'delete_item_button'): self.delete_item_button.config(state=tk.NORMAL)
        else:
            if hasattr(self, 'edit_item_button'): self.edit_item_button.config(state=tk.DISABLED)
            if hasattr(self, 'delete_item_button'): self.delete_item_button.config(state=tk.DISABLED)

    def open_add_item_dialog(self):
        if self.current_quotation_id is None:
            messagebox.showwarning("ヘッダー未保存", "明細を追加する前に、まず見積ヘッダー情報を保存してください。", parent=self)
            self.lift()
            return
        dialog = QuotationItemDialog(self, title="見積明細 - 新規追加", quotation_id=self.current_quotation_id)
        if dialog.result:
            item_data = dialog.result
            # add_quotation_item は display_order を自動採番するので、引数から削除
            new_item_id_or_error = self.db_ops.add_quotation_item(
                quotation_id=item_data["quotation_id"], name=item_data["name"],
                specification=item_data["specification"], quantity=item_data["quantity"],
                unit=item_data["unit"], unit_price=item_data["unit_price"],
                amount=item_data["amount"], remarks=item_data["remarks"]
            )
            if isinstance(new_item_id_or_error, int):
                messagebox.showinfo("成功", "見積明細を追加しました。", parent=self)
                self.load_selected_quotation_items(self.current_quotation_id) # 明細一覧を更新
                self.recalculate_and_update_quotation_totals(self.current_quotation_id) # 合計を再計算・更新
            else:
                messagebox.showerror("エラー", f"明細の追加に失敗しました: {new_item_id_or_error}", parent=self)
        self.lift()

    def open_edit_item_dialog(self):
        selected_item_refs = self.items_tree.selection()
        if not selected_item_refs:
            messagebox.showwarning("未選択", "編集する明細が選択されていません。", parent=self); self.lift(); return
        selected_item_id = selected_item_refs[0] # iid (item_id)
        item_to_edit = self.db_ops.get_quotation_item_by_id(selected_item_id) # item_idで詳細取得
        if not item_to_edit: # 辞書で返る想定
            messagebox.showerror("エラー", f"選択された明細 (ID: {selected_item_id}) のデータ取得に失敗しました。", parent=self); self.lift(); return

        dialog = QuotationItemDialog(self, title="見積明細 - 編集", item_data=item_to_edit, quotation_id=self.current_quotation_id)
        if dialog.result:
            edited_item_data = dialog.result
            # update_quotation_item は display_order も引数に取る
            # display_order は item_to_edit から取得
            current_display_order = item_to_edit.get("display_order") # 元の表示順を渡す
            update_success_or_error = self.db_ops.update_quotation_item(
                item_id=edited_item_data["item_id"], display_order=current_display_order,
                name=edited_item_data["name"], specification=edited_item_data["specification"],
                quantity=edited_item_data["quantity"], unit=edited_item_data["unit"],
                unit_price=edited_item_data["unit_price"], amount=edited_item_data["amount"],
                remarks=edited_item_data["remarks"]
            )
            if update_success_or_error is True:
                messagebox.showinfo("成功", "見積明細を更新しました。", parent=self)
                self.load_selected_quotation_items(self.current_quotation_id)
                self.recalculate_and_update_quotation_totals(self.current_quotation_id)
            else:
                messagebox.showerror("エラー", f"明細の更新に失敗しました: {update_success_or_error}", parent=self)
        self.lift()

    def delete_selected_item(self):
        selected_item_refs = self.items_tree.selection()
        if not selected_item_refs:
            messagebox.showwarning("未選択", "削除する明細が選択されていません。", parent=self); self.lift(); return
        selected_item_id = selected_item_refs[0]
        item_values = self.items_tree.item(selected_item_id, 'values')
        item_name_to_confirm = item_values[1] if len(item_values) > 1 else f"ID {selected_item_id}" # 1は"name"列
        confirm_message = f"明細「{item_name_to_confirm}」(ID: {selected_item_id}) を本当に削除しますか？"
        if not messagebox.askyesno("削除確認", confirm_message, parent=self):
            self.lift(); return

        delete_result = self.db_ops.delete_quotation_item(selected_item_id)
        if delete_result is True:
            messagebox.showinfo("成功", f"明細 (ID: {selected_item_id}) を削除しました。", parent=self)
            self.load_selected_quotation_items(self.current_quotation_id)
            self.recalculate_and_update_quotation_totals(self.current_quotation_id)
            # 選択解除後のボタン状態更新
            if hasattr(self, 'edit_item_button'): self.edit_item_button.config(state=tk.DISABLED)
            if hasattr(self, 'delete_item_button'): self.delete_item_button.config(state=tk.DISABLED)
        elif delete_result == "NOT_FOUND":
            messagebox.showerror("エラー", f"削除対象の明細 (ID: {selected_item_id}) が見つかりませんでした。", parent=self)
        else: # OTHER_DB_ERROR など
            messagebox.showerror("エラー", f"明細の削除に失敗しました: {delete_result}", parent=self)
        self.lift()


    def load_selected_quotation_items(self, quotation_id):
        if hasattr(self, 'items_tree'): # items_treeの存在確認
            for item in self.items_tree.get_children():
                self.items_tree.delete(item)
        else: # items_treeがなければ何もしない
            return

        if quotation_id is None: return # quotation_idがない場合はロードしない
        items_data = self.db_ops.get_items_for_quotation(quotation_id) # タプルのリストが返る
        if items_data:
            for index, item_tuple in enumerate(items_data):
                # item_tupleのインデックス:
                # 0:item_id, 1:quotation_id, 2:display_order, 3:name, 4:specification,
                # 5:quantity, 6:unit, 7:unit_price, 8:amount, 9:remarks, ...
                quantity_display = f"{item_tuple[5]:.2f}" if item_tuple[5] is not None else ""
                unit_price_display = f"{item_tuple[7]:,}" if item_tuple[7] is not None else ""
                amount_display = f"{item_tuple[8]:,}" if item_tuple[8] is not None else ""
                display_values = (
                    item_tuple[2] or (index + 1), # display_order があればそれ、なければ行番号
                    item_tuple[3],                # name
                    item_tuple[4] or "",          # specification
                    quantity_display,             # quantity
                    item_tuple[6] or "",          # unit
                    unit_price_display,           # unit_price
                    amount_display,               # amount
                    item_tuple[9] or ""           # remarks
                )
                self.items_tree.insert("", tk.END, values=display_values, iid=item_tuple[0]) # iidにitem_idを設定

    def recalculate_and_update_quotation_totals(self, quotation_id):
        if quotation_id is None: # 見積IDがない場合は計算不可
            self.detail_vars["total_amount_exclusive_tax"].set("0")
            self.detail_vars["tax_amount"].set("0")
            self.detail_vars["total_amount_inclusive_tax"].set("0")
            # self.detail_vars["tax_rate"].set("0") # 税率は変更しないでおくか、初期値に戻す
            return

        items = self.db_ops.get_items_for_quotation(quotation_id)
        total_exclusive = sum(item_tuple[8] for item_tuple in items if item_tuple[8] is not None) # amount はインデックス8

        # 現在のヘッダー情報を取得して税率などを保持
        current_header_data_for_tax_info = self.db_ops.get_quotation_by_id(quotation_id)
        if not current_header_data_for_tax_info:
            messagebox.showerror("エラー", "合計再計算のための見積ヘッダー情報取得に失敗しました。", parent=self)
            return

        # DBから取得した税率 (例: 0.10)
        db_tax_rate_value = current_header_data_for_tax_info[12] if current_header_data_for_tax_info[12] is not None else 0.0

        tax_amount = int(total_exclusive * db_tax_rate_value)
        total_inclusive = total_exclusive + tax_amount

        # 表示用StringVarを更新
        self.detail_vars["total_amount_exclusive_tax"].set(f"{total_exclusive:,}")
        self.detail_vars["tax_rate"].set(f"{db_tax_rate_value*100:.0f}") # %なしの数値で表示
        self.detail_vars["tax_amount"].set(f"{tax_amount:,}")
        self.detail_vars["total_amount_inclusive_tax"].set(f"{total_inclusive:,}")

        # DBの見積ヘッダーの金額情報も更新
        update_result = self.db_ops.update_quotation(
            quotation_id=quotation_id,
            project_id=current_header_data_for_tax_info[1], # project_id
            quotation_staff_id=current_header_data_for_tax_info[3], # quotation_staff_id
            quotation_code=current_header_data_for_tax_info[5], # quotation_code
            quotation_date=current_header_data_for_tax_info[6], # quotation_date
            customer_name_at_quote=current_header_data_for_tax_info[7],
            project_name_at_quote=current_header_data_for_tax_info[8],
            site_address_at_quote=current_header_data_for_tax_info[9],
            construction_period_notes=current_header_data_for_tax_info[10],
            total_amount_exclusive_tax=total_exclusive, # 更新された税抜合計
            tax_rate=db_tax_rate_value, # 税率は変わらない
            tax_amount=tax_amount, # 更新された消費税額
            total_amount_inclusive_tax=total_inclusive, # 更新された税込合計
            validity_period_notes=current_header_data_for_tax_info[15],
            payment_terms_notes=current_header_data_for_tax_info[16],
            status=current_header_data_for_tax_info[17], # status
            remarks=current_header_data_for_tax_info[18] # remarks
        )

        if update_result is True:
            print(f"Quotation ID {quotation_id} totals updated in DB successfully.")
            if self.refresh_callback and callable(self.refresh_callback): # 親の一覧画面も更新
                self.refresh_callback()
        else:
            messagebox.showerror("エラー", f"見積合計金額のデータベース更新に失敗しました: {update_result}", parent=self)


    def on_close(self): # このメソッドは必須
        self.destroy()

# --- QuotationItemDialog クラス (変更なし) ---
class QuotationItemDialog(tk.Toplevel):
    def __init__(self, parent, title="見積明細入力", item_data=None, quotation_id=None):
        super().__init__(parent)
        self.transient(parent)
        self.title(title)
        self.parent = parent
        self.result = None
        self.item_data = item_data # 編集時は既存の明細データ (辞書型を期待)
        self.quotation_id = quotation_id # この明細が属する見積ヘッダーのID

        self.resizable(False, False) # サイズ変更不可

        form_frame = ttk.Frame(self, padding="10")
        form_frame.pack(expand=True, fill=tk.BOTH)

        # フィールド定義 (ラベル、行、列、幅、タイプ、高さ(Text用))
        fields = {
            "name": {"label": "名称 (必須):", "row": 0, "col": 0, "width": 40, "type": "entry"},
            "specification": {"label": "仕様:", "row": 1, "col": 0, "width": 40, "type": "text", "height": 3},
            "quantity": {"label": "数量:", "row": 2, "col": 0, "width": 10, "type": "entry"},
            "unit": {"label": "単位:", "row": 2, "col": 2, "width": 10, "type": "entry"},
            "unit_price": {"label": "単価:", "row": 3, "col": 0, "width": 15, "type": "entry"},
            "remarks": {"label": "備考:", "row": 4, "col": 0, "width": 40, "type": "text", "height": 3}
        }

        self.entries = {} # ウィジェット自体を保持
        self.string_vars = {} # Entry用のStringVarを保持

        for key, field_info in fields.items():
            ttk.Label(form_frame, text=field_info["label"]).grid(
                row=field_info["row"], column=field_info["col"], padx=5, pady=3,
                sticky=tk.NW if field_info["type"] == "text" else tk.W
            )
            if field_info["type"] == "entry":
                self.string_vars[key] = tk.StringVar()
                entry = ttk.Entry(form_frame, textvariable=self.string_vars[key], width=field_info["width"])
                entry.grid(row=field_info["row"], column=field_info["col"] + 1, padx=5, pady=3, sticky=tk.EW,
                           columnspan=3 if field_info["col"] == 0 and field_info.get("type") != "text" and key not in ["quantity", "unit_price"] else 1) # 名称などは幅広に
                self.entries[key] = entry
            elif field_info["type"] == "text":
                text_widget = tk.Text(form_frame, width=field_info["width"], height=field_info["height"])
                text_widget.grid(row=field_info["row"], column=field_info["col"] + 1, padx=5, pady=3, sticky=tk.NSEW, columnspan=3)
                self.entries[key] = text_widget

        form_frame.columnconfigure(1, weight=1) # Entry/Textがある列の伸縮設定
        form_frame.columnconfigure(3, weight=1) # Entry/Textがある列の伸縮設定

        # ボタンフレーム
        button_frame = ttk.Frame(self, padding=(10, 5, 10, 10)) # 上以外のpaddingを少し増やす
        button_frame.pack(fill=tk.X, side=tk.BOTTOM) # 下部に配置

        ttk.Button(button_frame, text="キャンセル", command=self.on_cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="保存", command=self.on_save).pack(side=tk.RIGHT, padx=5)

        # item_data があればフォームに値をセット (編集モード)
        if self.item_data: # item_dataは辞書型を期待
            self.string_vars["name"].set(self.item_data.get("name", ""))
            self.entries["specification"].insert("1.0", self.item_data.get("specification", ""))
            self.string_vars["quantity"].set(str(self.item_data.get("quantity", "")))
            self.string_vars["unit"].set(self.item_data.get("unit", ""))
            self.string_vars["unit_price"].set(str(self.item_data.get("unit_price", "")))
            self.entries["remarks"].insert("1.0", self.item_data.get("remarks", ""))

        self.entries["name"].focus_set() # 最初は名称入力にフォーカス

        # ウィンドウサイズを内容に合わせて調整し、親ウィンドウの中央に表示
        self.geometry("") # これで内容に合わせたサイズになる
        self.update_idletasks() # ウィジェットのサイズ計算を強制
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()

        position_x = parent_x + (parent_width // 2) - (dialog_width // 2)
        position_y = parent_y + (parent_height // 2) - (dialog_height // 2)
        self.geometry(f"+{position_x}+{position_y}")


        self.grab_set() # モーダルにする
        self.wait_window(self) # ダイアログが閉じるまで待つ

    def on_save(self):
        name = self.string_vars["name"].get().strip()
        if not name:
            messagebox.showerror("入力エラー", "名称は必須です。", parent=self)
            self.entries["name"].focus_set()
            return

        try:
            quantity_str = self.string_vars["quantity"].get().strip()
            quantity = float(quantity_str) if quantity_str else 0.0 # 未入力は0として扱う

            unit_price_str = self.string_vars["unit_price"].get().strip()
            unit_price = int(unit_price_str) if unit_price_str else 0 # 未入力は0として扱う
            # (単価が小数の場合も考慮するならfloatに)
        except ValueError:
            messagebox.showerror("入力エラー", "数量、単価には有効な数値を入力してください。", parent=self)
            return

        amount = int(quantity * unit_price) # 金額を計算 (ここでは整数丸め)

        self.result = {
            "quotation_id": self.quotation_id, # この明細が属する見積ID
            "name": name,
            "specification": self.entries["specification"].get("1.0", tk.END).strip(),
            "quantity": quantity,
            "unit": self.string_vars["unit"].get().strip(),
            "unit_price": unit_price,
            "amount": amount,
            "remarks": self.entries["remarks"].get("1.0", tk.END).strip()
        }

        if self.item_data and "item_id" in self.item_data: # 編集の場合、item_idも結果に含める
            self.result["item_id"] = self.item_data["item_id"]
            # 編集時は表示順 (display_order) も必要ならここで含める
            if "display_order" in self.item_data:
                self.result["display_order"] = self.item_data["display_order"]


        self.destroy()

    def on_cancel(self):
        self.result = None # キャンセル時は結果をNoneに
        self.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    root.title("メインウィンドウ (テスト用)")

    try:
        if not hasattr(root, 'db_ops'):
             import database_operations as db_ops_module
             root.db_ops = db_ops_module
    except ImportError:
        messagebox.showerror("テストエラー", "database_operations.py が見つかりません。")
        root.destroy()
        exit()

    def open_quotation_list_window_all(): # 全件表示用
        list_win = QuotationListWindow(root) # project_filter_idなしで呼び出し

    def open_quotation_list_window_filtered(): # フィルタリング表示用 (テストのため固定ID)
        test_project_id = 1 # 存在する案件IDでテストしてください
        project_info = root.db_ops.get_project_by_id(test_project_id)
        if not project_info:
            messagebox.showinfo("テスト情報", f"案件ID {test_project_id} が存在しません。テストできません。", parent=root)
            return
        list_win = QuotationListWindow(root, project_filter_id=test_project_id)


    open_all_button = ttk.Button(root, text="見積一覧を開く (全件)", command=open_quotation_list_window_all)
    open_all_button.pack(padx=20, pady=5)

    open_filtered_button = ttk.Button(root, text="見積一覧を開く (案件ID:1でフィルタ)", command=open_quotation_list_window_filtered)
    open_filtered_button.pack(padx=20, pady=5)


    root.mainloop()