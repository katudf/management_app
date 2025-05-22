# project_management_window.py

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime
import database_operations as db_ops # データベース操作関数をインポート
# from datetime import datetime # 重複しているので削除
# QuotationListWindow をインポート (quotation_management_window.py から)
from tkcalendar import DateEntry # ★★★ tkcalendarのDateEntryをインポート ★★★
from quotation_management_window import QuotationListWindow

class ProjectManagementWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("案件管理")
        self.geometry("1150x750") # ウィンドウサイズ調整

        if hasattr(master, 'db_ops'):
            self.db_ops = master.db_ops
        else:
            messagebox.showerror("エラー", "データベース操作モジュールが見つかりません。", parent=self)
            self.destroy()
            return

        self.parent_window = master
        self.selected_project_id = None
        self._is_editing_project = False # ★ 案件編集中フラグを追加

        # --- フォームフィールドに対応するTkinter変数を定義 ---
        self.project_id_var = tk.StringVar()
        self.project_code_var = tk.StringVar()
        self.project_name_var = tk.StringVar()

        self.customer_id_var = tk.StringVar()
        self.customer_display_var = tk.StringVar()

        self.parent_project_id_var = tk.StringVar()
        self.parent_project_display_var = tk.StringVar()

        self.site_address_var = tk.StringVar()
        self.reception_date_var = tk.StringVar()
        self.start_date_scheduled_var = tk.StringVar()
        self.completion_date_scheduled_var = tk.StringVar()
        self.actual_completion_date_var = tk.StringVar()
        self.responsible_staff_var = tk.StringVar()
        self.estimated_amount_var = tk.StringVar()
        self.status_var = tk.StringVar()
        # self.remarks_text は Text ウィジェットなので StringVar は不要

        # Comboboxの選択肢とIDを保持する辞書
        self.customer_choices_map = {}  # 表示名 -> ID
        self.parent_project_choices_map = {} # 表示名 -> ID

        self.status_options = ["見積依頼", "見積中", "見積提出済", "受注", "施工中", "完了", "請求済", "入金済", "失注", "キャンセル"]


        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._create_widgets()
        self.load_customers_to_combobox()
        self.load_parent_projects_to_combobox()
        self.load_projects_to_treeview()
        self.clear_form(for_new_project=True)

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        style = ttk.Style(self)
        tree_font = ("メイリオ", 10) # Treeview用フォント
        style.configure("Treeview", font=tree_font, rowheight=int(tree_font[1] * 2.0)) # 行の高さをフォントサイズの2倍程度に
        style.configure("Treeview.Heading", font=(tree_font[0], tree_font[1], "bold"))


        form_frame = ttk.LabelFrame(main_frame, text="案件情報入力", padding="10")
        form_frame.pack(fill=tk.X, pady=5)

        # --- フォームフィールドの定義と配置 ---
        # (label_text, var_name, widget_name, widget_type, options, grid_options)
        # widget_name は self.<widget_name> としてアクセスできるように
        # var_name は self.<var_name> としてアクセスできる StringVar 名
        fields_layout = [
            ("案件ID:", self.project_id_var, "project_id_entry", "Entry", {"state": "readonly", "width": 15}, (0,0)),
            ("案件コード:", self.project_code_var, "project_code_entry", "Entry", {"width": 20}, (0,2)),
            ("案件名 (必須):", self.project_name_var, "project_name_entry", "Entry", {"width": 40}, (1,0), 3), # columnspan 3
            ("顧客 (必須):", self.customer_display_var, "customer_id_combobox", "Combobox", {"state": "readonly", "width": 38}, (2,0)),
            ("親案件:", self.parent_project_display_var, "parent_project_id_combobox", "Combobox", {"state": "readonly", "width": 38}, (2,2)),
            ("現場住所:", self.site_address_var, "site_address_entry", "Entry", {"width": 40}, (3,0), 3), # columnspan 3
            ("受付日:", self.reception_date_var, "reception_date_entry", "CustomDate", {"entry_width": 18}, (4,0)), # ★★★ EntryからCustomDateに変更 ★★★
            ("担当者名:", self.responsible_staff_var, "responsible_staff_entry", "Entry", {"width": 20}, (4,2)),
            ("見積金額(税抜):", self.estimated_amount_var, "estimated_amount_entry", "Entry", {"width": 20}, (5,0)),
            ("状況 (必須):", self.status_var, "status_combobox", "Combobox", {"state": "readonly", "width": 18, "values": self.status_options}, (5,2)),
            ("着工予定日:", self.start_date_scheduled_var, "start_date_scheduled_entry", "Entry", {"width": 20}, (6,0)), # TODO: DateEntry
            ("完了予定日:", self.completion_date_scheduled_var, "completion_date_scheduled_entry", "Entry", {"width": 20}, (6,2)), # TODO: DateEntry
            ("実完了日:", self.actual_completion_date_var, "actual_completion_date_entry", "Entry", {"width": 20}, (7,0)), # TODO: DateEntry
            ("備考:", None, "remarks_text", "Text", {"width": 40, "height": 3}, (8,0), 3) # columnspan 3 for remarks_text
        ]

        self.form_entries = {} # ウィジェットを保持 (状態変更用)

        for label_text, var_instance, widget_attr_name, widget_type, widget_options, grid_pos, *span_info in fields_layout:
            r, c = grid_pos
            ttk.Label(form_frame, text=label_text).grid(row=r, column=c, padx=5, pady=3, sticky=tk.W)
            widget = None
            if widget_type == "Entry":
                widget = ttk.Entry(form_frame, textvariable=var_instance, **widget_options)
            elif widget_type == "Combobox":
                # Comboboxの場合、textvariableは直接指定せず、Comboboxのインスタンスに .set() や .get() でアクセスする
                # または、textvariableにvar_instanceを渡す場合は、Combobox側でそれを処理する
                # ここでは、customer_display_var や parent_project_display_var が Combobox の表示に使われる想定
                if var_instance: # var_instance がNoneでない場合のみtextvariableを設定
                    widget = ttk.Combobox(form_frame, textvariable=var_instance, **widget_options)
                else:
                    widget = ttk.Combobox(form_frame, **widget_options)

            elif widget_type == "Text":
                widget = tk.Text(form_frame, **widget_options)
            elif widget_type == "DateEntry": # tkcalendarのDateEntry
                # DateEntryはtextvariableをサポートしていない。代わりにget_date() / set_date() を使うか、
                # date_patternを指定して文字列として扱う。
                # ここでは、StringVarを直接渡さず、後で値の取得・設定を行う形にするか、
                # または、DateEntry自体がStringVarのように振る舞うようにラップする必要がある。
                # 簡単な対応として、DateEntryにはtextvariableを直接渡さないでおく。
                # 値の設定は .set_date() 、取得は .get_date() を使う。
                # もしStringVarと連携させたい場合は、StringVarのtraceを利用するなどの工夫が必要。
                # 今回は、CustomDateというタイプを用意して、そちらでStringVarと連携させる。
                widget_options_copy = widget_options.copy()
                # DateEntryにtextvariableを渡すとエラーになることがあるので、
                # widget_options_copyからtextvariableのキーを削除するか、
                # DateEntryがtextvariableを適切に処理できるか確認が必要。
                # 一旦、そのまま渡してみる。
                widget = DateEntry(form_frame, textvariable=var_instance, **widget_options_copy)


            elif widget_type == "CustomDate":
                custom_frame = ttk.Frame(form_frame)
                entry_width = widget_options.get("entry_width", 12)
                date_display_entry = ttk.Entry(custom_frame, textvariable=var_instance, width=entry_width, state="readonly")
                date_display_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

                # Assign button and command based on the field
                if widget_attr_name == "reception_date_entry":
                    self.reception_date_select_button = ttk.Button(custom_frame, text="日付選択", command=self._open_reception_date_dialog)
                    self.reception_date_select_button.pack(side=tk.LEFT, padx=(5,0))
                # Add elif for other CustomDate fields here if they are added in the future
                widget = custom_frame

            if widget:
                columnspan = span_info[0] if span_info else 1
                widget.grid(row=r, column=c+1, padx=5, pady=3, sticky=tk.EW, columnspan=columnspan)
                setattr(self, widget_attr_name, widget)
                # form_entriesには、StringVarと関連付けないウィジェットもそのまま格納する
                self.form_entries[widget_attr_name.replace("_entry",""
                ).replace("_combobox",""
                ).replace("_text","")] = widget


        form_frame.columnconfigure(1, weight=1)
        form_frame.columnconfigure(3, weight=1)
        if hasattr(self, 'status_combobox') and self.status_options: # 初期値を設定
            self.status_combobox.set(self.status_options[0]) # status_combobox は直接 .set() を使う


        button_action_frame = ttk.Frame(main_frame)
        button_action_frame.pack(fill=tk.X, pady=5, padx=5)

        self.add_button = ttk.Button(button_action_frame, text="案件追加", command=self.add_project_data)
        self.add_button.pack(side=tk.LEFT, padx=5)
        self.start_edit_project_button = ttk.Button(button_action_frame, text="案件編集開始", command=self.start_project_edit_mode, state=tk.DISABLED)
        self.start_edit_project_button.pack(side=tk.LEFT, padx=5)
        self.update_button = ttk.Button(button_action_frame, text="案件更新", command=self.update_project_data, state=tk.DISABLED)
        self.update_button.pack(side=tk.LEFT, padx=5)
        self.delete_button = ttk.Button(button_action_frame, text="案件削除", command=self.confirm_delete_project, state=tk.DISABLED)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        self.clear_button = ttk.Button(button_action_frame, text="クリア/新規", command=lambda: self.clear_form(for_new_project=True))
        self.clear_button.pack(side=tk.LEFT, padx=5)
        self.open_quotations_for_project_button = ttk.Button(
            button_action_frame, text="この案件の見積管理",
            command=self.open_quotations_for_selected_project, state=tk.DISABLED
        )
        self.open_quotations_for_project_button.pack(side=tk.LEFT, padx=10)

        list_frame = ttk.LabelFrame(main_frame, text="案件一覧", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self._create_project_treeview(list_frame)


    def _create_project_treeview(self, parent_frame):
        columns = ("project_id", "project_code", "project_name", "customer_name", "status", "reception_date", "responsible_staff_name")
        self.project_tree = ttk.Treeview(parent_frame, columns=columns, show="headings", height=10, style="Treeview")

        self.project_tree.heading("project_id", text="ID"); self.project_tree.column("project_id", width=40, anchor=tk.CENTER)
        self.project_tree.heading("project_code", text="案件CD"); self.project_tree.column("project_code", width=100)
        self.project_tree.heading("project_name", text="案件名"); self.project_tree.column("project_name", width=250)
        self.project_tree.heading("customer_name", text="顧客名"); self.project_tree.column("customer_name", width=150)
        self.project_tree.heading("status", text="状況"); self.project_tree.column("status", width=80)
        self.project_tree.heading("reception_date", text="受付日"); self.project_tree.column("reception_date", width=90, anchor=tk.CENTER)
        self.project_tree.heading("responsible_staff_name", text="担当者"); self.project_tree.column("responsible_staff_name", width=100)

        scrollbar_y = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.project_tree.yview)
        self.project_tree.configure(yscrollcommand=scrollbar_y.set)
        scrollbar_x = ttk.Scrollbar(parent_frame, orient=tk.HORIZONTAL, command=self.project_tree.xview)
        self.project_tree.configure(xscrollcommand=scrollbar_x.set)

        self.project_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        parent_frame.grid_rowconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(0, weight=1)

        self.project_tree.bind("<<TreeviewSelect>>", self.on_project_tree_select)
        self.project_tree.bind("<Double-1>", self.on_project_double_click)


    def load_projects_to_treeview(self):
        if hasattr(self, 'project_tree'):
            for item in self.project_tree.get_children():
                self.project_tree.delete(item)

        projects_data = self.db_ops.get_all_projects()
        if projects_data:
            for project_tuple in projects_data:
                # db_ops.get_all_projects() の返り値のインデックスに合わせる
                # 0:p.project_id, 1:p.project_code, 2:p.project_name, 3:p.customer_id, 4:c.customer_name,
                # ... 8:p.reception_date, ... 12:p.responsible_staff_name, ... 14:p.status
                display_values = (
                    project_tuple[0], # project_id
                    project_tuple[1], # project_code
                    project_tuple[2], # project_name
                    project_tuple[4] or "", # customer_name
                    project_tuple[14] or "",# status
                    project_tuple[8] or "", # reception_date
                    project_tuple[12] or "" # responsible_staff_name
                )
                self.project_tree.insert("", tk.END, values=display_values, iid=project_tuple[0])
        self.on_project_tree_select(None)

    def load_customers_to_combobox(self):
        if not hasattr(self, 'customer_id_combobox'): return
        try:
            customers_data = self.db_ops.get_all_customers()
            self.customer_choices_map = {} # 表示名 -> ID のマップをクリア
            combobox_values = ["-----"] # 初期選択肢
            if customers_data:
                for row in customers_data: # row[0] is id, row[1] is name
                    display_name = f"{row[1]} (ID:{row[0]})"
                    combobox_values.append(display_name)
                    self.customer_choices_map[display_name] = row[0] # IDをマップに保存
            self.customer_id_combobox['values'] = combobox_values
            self.customer_display_var.set(combobox_values[0]) # 初期値を「-----」に
            self.customer_id_var.set("") # ID変数はクリア
        except Exception as e:
            print(f"Error loading customers: {e}")
            self.customer_id_combobox['values'] = ["-----"]
            self.customer_display_var.set("-----")
        self.customer_id_combobox.bind("<<ComboboxSelected>>", self.on_customer_selected)

    def load_parent_projects_to_combobox(self):
        if not hasattr(self, 'parent_project_id_combobox'): return
        try:
            projects_data = self.db_ops.get_all_projects()
            self.parent_project_choices_map = {}
            combobox_values = ["-----"] # 親案件なしも選択肢
            if projects_data:
                for row in projects_data: # row[0] is id, row[1] is code, row[2] is name
                    # 現在編集中の案件IDと異なるものだけを親案件候補とする (編集中でIDが確定している場合)
                    if self.selected_project_id and row[0] == int(self.selected_project_id):
                        continue
                    display_name = f"{row[1]}: {row[2]} (ID:{row[0]})"
                    combobox_values.append(display_name)
                    self.parent_project_choices_map[display_name] = row[0]
            self.parent_project_id_combobox['values'] = combobox_values
            self.parent_project_display_var.set(combobox_values[0])
            self.parent_project_id_var.set("")
        except Exception as e:
            print(f"Error loading parent projects: {e}")
            self.parent_project_id_combobox['values'] = ["-----"]
            self.parent_project_display_var.set("-----")
        self.parent_project_id_combobox.bind("<<ComboboxSelected>>", self.on_parent_project_selected)


    def on_customer_selected(self, event=None):
        selected_display_name = self.customer_display_var.get()
        customer_id = self.customer_choices_map.get(selected_display_name)
        self.customer_id_var.set(str(customer_id) if customer_id is not None else "")
        print(f"Customer selected: Display='{selected_display_name}', ID='{self.customer_id_var.get()}'")


    def on_parent_project_selected(self, event=None):
        selected_display_name = self.parent_project_display_var.get()
        parent_project_id = self.parent_project_choices_map.get(selected_display_name)
        self.parent_project_id_var.set(str(parent_project_id) if parent_project_id is not None else "")
        print(f"Parent project selected: Display='{selected_display_name}', ID='{self.parent_project_id_var.get()}'")


    def on_project_tree_select(self, event):
            # ★ もし編集中に別のアイテムが選択されたら、編集モードをキャンセル（元のデータを再表示）
        if self._is_editing_project:
            # ここで「変更が保存されていません。編集を破棄しますか？」と確認しても良い
            self._is_editing_project = False # 編集モードを解除
            # ボタン状態は後続の処理で設定される
        selected_items = self.project_tree.selection()
        if not selected_items:
            self.clear_form(for_new_project=False)
            if hasattr(self, 'project_code_entry'): self.project_code_entry.config(state="normal")
            self.selected_project_id = None
            if hasattr(self, 'update_button'): self.update_button.config(state=tk.DISABLED)
            if hasattr(self, 'delete_button'): self.delete_button.config(state=tk.DISABLED)
            if hasattr(self, 'add_button'): self.add_button.config(state=tk.NORMAL)
            if hasattr(self, 'open_quotations_for_project_button'):
                self.open_quotations_for_project_button.config(state=tk.DISABLED)
            if hasattr(self, 'start_edit_project_button'): self.start_edit_project_button.config(state=tk.DISABLED) # ★追加
            return

        selected_iid = selected_items[0]
        self.selected_project_id = selected_iid
        project_data_tuple = self.db_ops.get_project_by_id(self.selected_project_id)

        if project_data_tuple:
            # db_ops.get_project_by_id の返り値のインデックス (再確認):
            # 0:p.project_id, 1:p.project_code, 2:p.project_name, 3:p.customer_id, 4:c.customer_name,
            # 5:p.parent_project_id, 6:pp.project_code (parent_project_code),
            # 7:p.site_address, 8:p.reception_date, 9:p.start_date_scheduled,
            # 10:p.completion_date_scheduled, 11:p.actual_completion_date,
            # 12:p.responsible_staff_name, 13:p.estimated_amount, 14:p.status, 15:p.remarks

            self.project_id_var.set(project_data_tuple[0] or "")
            self.project_code_var.set(project_data_tuple[1] or "")
            self.project_name_var.set(project_data_tuple[2] or "")

            customer_id = project_data_tuple[3]
            self.customer_id_var.set(str(customer_id) if customer_id is not None else "")
            customer_display_val = "-----" # デフォルト
            if customer_id is not None and hasattr(self, 'customer_choices_map'):
                for disp, c_id_map in self.customer_choices_map.items():
                    if c_id_map == customer_id:
                        customer_display_val = disp
                        break
            self.customer_display_var.set(customer_display_val)

            parent_project_id = project_data_tuple[5]
            self.parent_project_id_var.set(str(parent_project_id) if parent_project_id is not None else "")
            parent_project_display_val = "-----" # デフォルト
            if parent_project_id is not None and hasattr(self, 'parent_project_choices_map'):
                for disp, p_id_map in self.parent_project_choices_map.items():
                    if p_id_map == parent_project_id:
                        parent_project_display_val = disp
                        break
            self.parent_project_display_var.set(parent_project_display_val)
            self.site_address_var.set(project_data_tuple[7] or "")
            self.reception_date_var.set(project_data_tuple[8] or "")
            self.start_date_scheduled_var.set(project_data_tuple[9] or "")
            self.completion_date_scheduled_var.set(project_data_tuple[10] or "")
            self.actual_completion_date_var.set(project_data_tuple[11] or "")
            self.responsible_staff_var.set(project_data_tuple[12] or "")

            estimated_amount = project_data_tuple[13]
            self.estimated_amount_var.set(f"{estimated_amount:,}" if estimated_amount is not None else "0")

            # status_var に値をセットし、status_combobox にも反映
            self.status_var.set(project_data_tuple[14] or (self.status_options[0] if self.status_options else ""))
            if hasattr(self, 'status_combobox'):
                self.status_combobox.set(self.status_var.get())


            self.remarks_text.delete("1.0", tk.END)
            self.remarks_text.insert("1.0", project_data_tuple[15] or "")

            # フォームのフィールドを読み取り専用に設定
            for field_key, widget_from_dict in self.form_entries.items():
                if field_key == "project_id":
                    widget_from_dict.config(state="readonly")
                    continue

                if field_key == "reception_date": # Handle CustomDate specifically
                    if hasattr(self, 'reception_date_select_button'):
                        self.reception_date_select_button.config(state=tk.DISABLED)
                    if hasattr(self, 'reception_date_entry'): # Entry part of CustomDate
                        # reception_date_entryはFrameなので、その中のEntryウィジェットの状態を変更
                        # date_display_entryがそれに該当するが、直接アクセスできるようにする必要がある
                        # ここではform_entriesに格納されているのがFrameなので、その中のEntryを探すか、
                        # form_entriesの構造を見直す。
                        # 今回は、reception_date_entryはFrameなので、その中のEntryは別途制御するか、
                        # reception_date_entryを直接readonlyにするのは効果がない。
                        # date_display_entryをselfに持たせて制御するのが良い。
                        # 仮に reception_date_entry が ttk.Entry なら以下でOK
                        # widget_from_dict.config(state="readonly")
                        pass # CustomDateのEntry部分はtextvariable経由なので、ボタンで制御
                    continue

                if isinstance(widget_from_dict, tk.Text):
                    widget_from_dict.config(state=tk.DISABLED)
                    if field_key == "remarks": # remarks_text is the key from form_entries
                        widget_from_dict.config(bg="#f0f0f0")
                elif isinstance(widget_from_dict, ttk.Combobox):
                    widget_from_dict.config(state="disabled")
                elif isinstance(widget_from_dict, ttk.Entry):
                    widget_from_dict.config(state="readonly")
                # If widget_from_dict is a Frame (other than handled CustomDate), its state is not set here.

            if hasattr(self, 'project_code_entry'): self.project_code_entry.config(state='readonly')

            # ボタンの状態を更新
            if hasattr(self, 'update_button'): self.update_button.config(state=tk.DISABLED) # 更新ボタンは編集モード開始時に有効化
            if hasattr(self, 'delete_button'): self.delete_button.config(state=tk.NORMAL)
            if hasattr(self, 'add_button'): self.add_button.config(state=tk.DISABLED)
            if hasattr(self, 'open_quotations_for_project_button'):
                self.open_quotations_for_project_button.config(state=tk.NORMAL)
            if hasattr(self, 'start_edit_project_button'): self.start_edit_project_button.config(state=tk.NORMAL) # ★追加: 選択時は編集開始を有効化
        else:
            messagebox.showerror("エラー", f"案件ID {self.selected_project_id} の詳細情報取得に失敗しました。", parent=self)
            self.clear_form(for_new_project=False)
            if hasattr(self, 'start_edit_project_button'): self.start_edit_project_button.config(state=tk.DISABLED) # ★追加

    def on_project_double_click(self, event):
        if self.selected_project_id:
            # ダブルクリックで編集モードに入るか、あるいは見積もり画面を開くなど
            # ここでは、編集ボタンを押したのと同じ動作（編集モードに入る）をさせると仮定
            # self.start_project_edit_mode() # そのようなメソッドがあれば
            # または、見積管理を開く
            self.open_quotations_for_selected_project()


    def _suggest_project_code(self):
        try:
            now = datetime.now()
            year_month_str = now.strftime("%Y%m")
            next_seq = self.db_ops.get_next_project_code_sequence_for_month(year_month_str)
            if next_seq is not None:
                suggested_code = f"P-{year_month_str}-{next_seq:03d}"
                self.project_code_var.set(suggested_code)
                if hasattr(self, 'project_code_entry'): self.project_code_entry.config(state="readonly")
            else:
                messagebox.showerror("エラー", "案件コードの自動採番に失敗しました。\n手動で入力してください。", parent=self)
                self.project_code_var.set("")
                if hasattr(self, 'project_code_entry'): self.project_code_entry.config(state="normal")
        except Exception as e:
            messagebox.showerror("エラー", f"案件コード生成中にエラー: {e}", parent=self)
            self.project_code_var.set("")
            if hasattr(self, 'project_code_entry'): self.project_code_entry.config(state="normal")

    def clear_form(self, for_new_project=False):
        if self._is_editing_project:  # 編集中にクリアされたら編集モード解除
            self._is_editing_project = False

        self.project_id_var.set("")
        self.project_code_var.set("")
        self.project_name_var.set("")
        self.customer_id_var.set("")
        self.customer_display_var.set(self.customer_choices_map.get("-----", "-----") if hasattr(self, 'customer_choices_map') and "-----" in self.customer_choices_map else "-----")
        self.parent_project_id_var.set("")
        self.parent_project_display_var.set(self.parent_project_choices_map.get("-----", "-----") if hasattr(self, 'parent_project_choices_map') and "-----" in self.parent_project_choices_map else "-----")
        self.site_address_var.set("")
        self.reception_date_var.set("")
        self.start_date_scheduled_var.set("")
        self.completion_date_scheduled_var.set("")
        self.actual_completion_date_var.set("")
        self.responsible_staff_var.set("")
        self.estimated_amount_var.set("0")
        self.status_var.set(self.status_options[0] if hasattr(self, 'status_options') and self.status_options else "")
        if hasattr(self, 'status_combobox'): # status_combobox にも値を反映
             self.status_combobox.set(self.status_var.get())

        if hasattr(self, 'remarks_text'): self.remarks_text.delete("1.0", tk.END)

        for field_key, widget_from_dict in self.form_entries.items():
            # project_id は常に readonly
            if field_key == "project_id":
                if hasattr(self, 'project_id_entry'): # Ensure self.project_id_entry exists
                    self.project_id_entry.config(state="readonly")
                continue

            if field_key == "reception_date": # Handle CustomDate's button
                if hasattr(self, 'reception_date_select_button'):
                    self.reception_date_select_button.config(state=tk.NORMAL)
                # CustomDate内のEntryはtextvariable経由でクリアされる
                continue

            if isinstance(widget_from_dict, tk.Text):
                widget_from_dict.config(state=tk.NORMAL)
                if field_key == "remarks" and hasattr(self, 'remarks_text'):
                    self.remarks_text.config(bg="white")
            elif isinstance(widget_from_dict, ttk.Combobox):
                widget_from_dict.config(state="readonly")
            elif isinstance(widget_from_dict, ttk.Entry):
                 # project_code_entry might be set to readonly by _suggest_project_code if for_new_project is true
                if not (for_new_project and field_key == "project_code"):
                    widget_from_dict.config(state="normal")
            # Other widget types (like unhandled Frames) in form_entries are not configured here.

        if hasattr(self, 'project_id_entry'):
            self.project_id_entry.config(state="readonly")

        if for_new_project:
            self._suggest_project_code()
            self.reception_date_var.set(datetime.now().strftime("%Y-%m-%d"))
            if hasattr(self, 'status_combobox') and self.status_options:
                self.status_var.set("見積中")
                self.status_combobox.set("見積中")  # Combobox自体にも明示的にセット
            if hasattr(self, 'project_name_entry'):
                self.project_name_entry.focus_set()
        else:
            if hasattr(self, 'project_code_entry'):
                self.project_code_entry.config(state="normal")
            if hasattr(self, 'project_code_entry'):
                self.project_code_entry.focus_set()

        self.selected_project_id = None
        if hasattr(self, 'project_tree') and self.project_tree.selection():
            self.project_tree.selection_remove(self.project_tree.selection())

        if hasattr(self, 'add_button'): self.add_button.config(state=tk.NORMAL)
        if hasattr(self, 'update_button'): self.update_button.config(state=tk.DISABLED)
        if hasattr(self, 'delete_button'): self.delete_button.config(state=tk.DISABLED)
        if hasattr(self, 'open_quotations_for_project_button'):
            self.open_quotations_for_project_button.config(state=tk.DISABLED)
        if hasattr(self, 'start_edit_project_button'): self.start_edit_project_button.config(state=tk.DISABLED)
        print("Project form cleared.")

    def add_project_data(self):
        project_code = self.project_code_var.get().strip()
        project_name = self.project_name_var.get().strip()
        customer_id_str = self.customer_id_var.get().strip() # 選択されたIDを取得
        print(f"DEBUG add_project_data: customer_id_str = '{customer_id_str}'") # ★デバッグ用にprint追加
        parent_project_id_str = self.parent_project_id_var.get().strip() # 選択されたIDを取得
        site_address = self.site_address_var.get().strip()
        reception_date = self.reception_date_var.get().strip()
        start_date_scheduled = self.start_date_scheduled_var.get().strip()
        completion_date_scheduled = self.completion_date_scheduled_var.get().strip()
        actual_completion_date = self.actual_completion_date_var.get().strip()
        responsible_staff_name = self.responsible_staff_var.get().strip()
        estimated_amount_str = self.estimated_amount_var.get().replace(',', '').strip()
        status = self.status_var.get().strip()
        remarks = self.remarks_text.get("1.0", tk.END).strip()

        if not project_code: messagebox.showerror("入力エラー", "案件コードは必須です。", parent=self); return
        if not project_name: messagebox.showerror("入力エラー", "案件名は必須です。", parent=self); return
        if not customer_id_str: messagebox.showerror("入力エラー", "顧客は必須です。", parent=self); return # IDが空かチェック
        if not status: messagebox.showerror("入力エラー", "状況は必須です。", parent=self); return

        try:
            customer_id = int(customer_id_str) if customer_id_str else None
            parent_project_id = int(parent_project_id_str) if parent_project_id_str else None
            estimated_amount = int(estimated_amount_str) if estimated_amount_str else 0
        except ValueError:
            messagebox.showerror("入力エラー", "顧客ID、親案件ID、見積金額には有効な数値を入力してください。", parent=self)
            return

        result = self.db_ops.add_project(
            project_code, project_name, customer_id, parent_project_id,
            site_address, reception_date, start_date_scheduled,
            completion_date_scheduled, actual_completion_date,
            responsible_staff_name, estimated_amount, status, remarks
        )
        if isinstance(result, int):
            messagebox.showinfo("成功", f"案件「{project_name}」を登録しました。 (ID: {result})", parent=self)
            self.load_projects_to_treeview()
            self.clear_form(for_new_project=True)
        elif result == "DUPLICATE_CODE": messagebox.showerror("登録エラー", f"案件コード「{project_code}」は既に登録されています。", parent=self)
        elif result == "NOT_NULL_VIOLATION": messagebox.showerror("登録エラー", "必須項目が入力されていません。", parent=self)
        elif result == "FK_CONSTRAINT_FAILED": messagebox.showerror("登録エラー", "指定された顧客IDまたは親案件IDが存在しません。", parent=self)
        else: messagebox.showerror("登録エラー", f"案件の登録に失敗しました: {result}", parent=self)

    def start_project_edit_mode(self):
        if not self.selected_project_id:
            messagebox.showwarning("未選択", "編集する案件が選択されていません。", parent=self)
            return

        self._is_editing_project = True

        # 編集可能にするフィールド (案件ID、案件コードは通常編集不可)
        editable_fields_keys = [ # form_entries のキーに対応
            "project_name", "customer_id", "parent_project_id",
            "site_address", "reception_date", "start_date_scheduled",
            "completion_date_scheduled", "actual_completion_date",
            "responsible_staff", "estimated_amount", "status",
            "remarks"
        ]

        for field_key, widget_from_dict in self.form_entries.items():
            if field_key in editable_fields_keys:
                if field_key == "reception_date": # Handle CustomDate specifically
                    if hasattr(self, 'reception_date_select_button'):
                        self.reception_date_select_button.config(state=tk.NORMAL)
                    # CustomDate内のEntryはtextvariable経由なので、ボタンで制御
                    continue

                if isinstance(widget_from_dict, tk.Text):
                    widget_from_dict.config(state=tk.NORMAL)
                    if field_key == "remarks" and hasattr(self, 'remarks_text'): # remarks_text は widget_from_dict と同じはず
                        widget_from_dict.config(bg="white")
                elif isinstance(widget_from_dict, ttk.Combobox):
                     widget_from_dict.config(state="readonly") # Comboboxはreadonlyで選択可能
                elif isinstance(widget_from_dict, ttk.Entry):
                    widget_from_dict.config(state="normal")
            elif field_key not in ["project_id", "project_code"]: # 編集不可だが、IDやコードでもないもの
                if isinstance(widget_from_dict, tk.Text):
                    widget_from_dict.config(state=tk.DISABLED)
                elif isinstance(widget_from_dict, (ttk.Entry, ttk.Combobox)):
                    widget_from_dict.config(state="readonly" if isinstance(widget_from_dict, ttk.Entry) else "disabled")


        # 案件コードは自動採番の結果なので通常編集不可、IDも表示専用
        if hasattr(self, 'project_code_entry'): self.project_code_entry.config(state="readonly")
        if hasattr(self, 'project_id_entry'): self.project_id_entry.config(state="readonly")


        if hasattr(self, 'update_button'): self.update_button.config(state=tk.NORMAL)
        if hasattr(self, 'add_button'): self.add_button.config(state=tk.DISABLED)
        if hasattr(self, 'start_edit_project_button'): self.start_edit_project_button.config(state=tk.DISABLED)
        if hasattr(self, 'delete_button'): self.delete_button.config(state=tk.DISABLED) # 編集中は削除不可
        if hasattr(self, 'open_quotations_for_project_button'): self.open_quotations_for_project_button.config(state=tk.DISABLED) # 編集中は他画面遷移を制限

        if hasattr(self, 'project_name_entry'): # 案件名にフォーカス
            self.project_name_entry.focus_set()

        print("Entered project edit mode.")

    def update_project_data(self):
        if not self.selected_project_id:
            messagebox.showerror("エラー", "更新する案件が選択されていません。", parent=self)
            return
        if not self._is_editing_project:
            messagebox.showwarning("警告", "案件編集モードではありません。「案件編集開始」ボタンを押してください。", parent=self)
            return

        project_code = self.project_code_var.get().strip()
        project_name = self.project_name_var.get().strip()
        customer_id_str = self.customer_id_var.get().strip()
        parent_project_id_str = self.parent_project_id_var.get().strip()
        site_address = self.site_address_var.get().strip()
        reception_date = self.reception_date_var.get().strip()
        start_date_scheduled = self.start_date_scheduled_var.get().strip()
        completion_date_scheduled = self.completion_date_scheduled_var.get().strip()
        actual_completion_date = self.actual_completion_date_var.get().strip()
        responsible_staff_name = self.responsible_staff_var.get().strip()
        estimated_amount_str = self.estimated_amount_var.get().replace(',', '').strip()
        status = self.status_var.get().strip()
        remarks = self.remarks_text.get("1.0", tk.END).strip()

        if not project_code: messagebox.showerror("入力エラー", "案件コードは必須です。", parent=self); return
        if not project_name: messagebox.showerror("入力エラー", "案件名は必須です。", parent=self); return
        if not customer_id_str: messagebox.showerror("入力エラー", "顧客は必須です。", parent=self); return
        if not status: messagebox.showerror("入力エラー", "状況は必須です。", parent=self); return


        try:
            customer_id = int(customer_id_str) if customer_id_str else None
            parent_project_id = int(parent_project_id_str) if parent_project_id_str else None
            estimated_amount = int(estimated_amount_str) if estimated_amount_str else 0
        except ValueError:
            messagebox.showerror("入力エラー", "顧客ID、親案件ID、見積金額には有効な数値を入力してください。", parent=self)
            return

        result = self.db_ops.update_project(
            project_id=self.selected_project_id,
            project_code=project_code, project_name=project_name, customer_id=customer_id,
            parent_project_id=parent_project_id, site_address=site_address,
            reception_date=reception_date, start_date_scheduled=start_date_scheduled,
            completion_date_scheduled=completion_date_scheduled, actual_completion_date=actual_completion_date,
            responsible_staff_name=responsible_staff_name, estimated_amount=estimated_amount,
            status=status, remarks=remarks
        )
        if result is True:
            messagebox.showinfo("成功", f"案件「{project_name}」を更新しました。", parent=self)
            self._is_editing_project = False

            current_selected_id = self.selected_project_id
            self.load_projects_to_treeview()
            if current_selected_id and hasattr(self, 'project_tree') and self.project_tree.exists(str(current_selected_id)):
                self.project_tree.selection_set(str(current_selected_id))
                self.project_tree.focus(str(current_selected_id)) # フォーカスも設定
                # Treeview選択イベントを手動でトリガーしてフォームを再描画
                self.on_project_tree_select(None)

            else:
                self.clear_form(for_new_project=True)
        elif result == "DUPLICATE_CODE": messagebox.showerror("更新エラー", f"案件コード「{project_code}」は既に他の案件で使用されています。", parent=self)
        elif result == "NOT_FOUND": messagebox.showerror("更新エラー", f"更新対象の案件 (ID: {self.selected_project_id}) が見つかりませんでした。", parent=self)
        elif result == "NOT_NULL_VIOLATION": messagebox.showerror("更新エラー", "必須項目が入力されていません。", parent=self)
        elif result == "FK_CONSTRAINT_FAILED": messagebox.showerror("更新エラー", "指定された顧客IDまたは親案件IDが存在しません。", parent=self)
        else: messagebox.showerror("更新エラー", f"案件の更新に失敗しました: {result}", parent=self)

    def confirm_delete_project(self):
        if not self.selected_project_id:
            messagebox.showwarning("未選択", "削除する案件が選択されていません。", parent=self)
            return
        project_code_to_confirm = self.project_code_var.get()
        project_name_to_confirm = self.project_name_var.get()
        confirm_msg = f"案件「{project_name_to_confirm}」(コード: {project_code_to_confirm}) を本当に削除しますか？\nこの操作は元に戻せません。"
        if not messagebox.askyesno("削除確認", confirm_msg, parent=self):
            return
        result = self.db_ops.delete_project(self.selected_project_id)
        if result is True:
            messagebox.showinfo("成功", "案件を削除しました。", parent=self)
            self.load_projects_to_treeview()
            self.clear_form(for_new_project=True)
        elif result == "NOT_FOUND": messagebox.showerror("削除エラー", f"削除対象の案件 (ID: {self.selected_project_id}) が見つかりませんでした。", parent=self)
        elif result == "FK_CONSTRAINT_FAILED": messagebox.showerror("削除エラー", "この案件は他のデータ（例：見積もり、子案件）から参照されているため削除できません。", parent=self)
        else: messagebox.showerror("削除エラー", f"案件の削除に失敗しました: {result}", parent=self)

    def open_quotations_for_selected_project(self):
        if not self.selected_project_id:
            messagebox.showwarning("未選択", "案件が選択されていません。", parent=self)
            return
        print(f"Opening quotation list for project ID: {self.selected_project_id}")
        # ProjectManagementWindowがQuotationListWindowのmasterとなる
        quotation_list_win = QuotationListWindow(self)
        # quotation_list_win.grab_set() # 必要に応じて

    def _open_reception_date_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("日付選択")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)
        try:
            from tkcalendar import Calendar
        except ImportError:
            messagebox.showerror("エラー", "tkcalendarパッケージが必要です。", parent=self)
            if dialog.winfo_exists(): dialog.destroy()
            return

        current_date_str = self.reception_date_var.get()
        initial_selection_date = None
        if current_date_str:
            try:
                initial_selection_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
            except ValueError:
                initial_selection_date = datetime.now().date()
        else:
            initial_selection_date = datetime.now().date()

        cal = Calendar(dialog, selectmode='day', locale='ja_JP',
                       year=initial_selection_date.year,
                       month=initial_selection_date.month,
                       day=initial_selection_date.day,
                       date_pattern='yyyy-mm-dd') # date_pattern を設定
        cal.pack(padx=10, pady=10)

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=(0, 10), padx=10, fill='x')

        def on_ok():
            try:
                # tkcalendar から選択された日付を datetime.date オブジェクトとして取得
                selected_date = cal.selection_get() # selection_get() は datetime.date を返す
                if selected_date:
                    self.reception_date_var.set(selected_date.strftime("%Y-%m-%d"))
                else:
                    # 何も選択されなかった場合（通常は発生しづらいが念のため）
                    self.reception_date_var.set("")
            except Exception as e:
                # 予期せぬエラーが発生した場合の処理
                print(f"日付選択エラー: {e}")
                messagebox.showerror("エラー", f"日付の処理中にエラーが発生しました: {e}", parent=dialog)
            finally:
                # エラーの有無にかかわらずダイアログを閉じる
                if dialog.winfo_exists(): # ダイアログが存在する場合のみ閉じる
                    dialog.destroy()

        def on_cancel():
            if dialog.winfo_exists(): dialog.destroy()

        ok_button = ttk.Button(button_frame, text="OK", command=on_ok, width=10)
        cancel_button = ttk.Button(button_frame, text="キャンセル", command=on_cancel, width=10)

        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=0)
        button_frame.columnconfigure(2, weight=0)
        button_frame.columnconfigure(3, weight=1)
        ok_button.grid(row=0, column=1, padx=5)
        cancel_button.grid(row=0, column=2, padx=5)

        self.update_idletasks() # 親ウィンドウの更新を確実に行う
        dialog.update_idletasks() # ダイアログの更新

        master_win = self
        dialog_width = dialog.winfo_reqwidth()
        dialog_height = dialog.winfo_reqheight()

        # 親ウィンドウの中心にダイアログを配置
        x = master_win.winfo_x() + (master_win.winfo_width() // 2) - (dialog_width // 2)
        y = master_win.winfo_y() + (master_win.winfo_height() // 2) - (dialog_height // 2)

        # 画面外に出ないように調整
        screen_width = master_win.winfo_screenwidth()
        screen_height = master_win.winfo_screenheight()
        x = max(0, min(x, screen_width - dialog_width))
        y = max(0, min(y, screen_height - dialog_height))

        dialog.geometry(f'{dialog_width}x{dialog_height}+{x}+{y}')
        ok_button.focus_set()
        dialog.wait_window()

    def on_close(self):
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

    def open_project_management_window():
        project_win = ProjectManagementWindow(root)

    open_button = ttk.Button(root, text="案件管理を開く", command=open_project_management_window)
    open_button.pack(padx=20, pady=20)
    root.mainloop()