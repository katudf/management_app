# project_management_window.py

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime
import database_operations as db_ops
from tkcalendar import DateEntry
from quotation_management_window import QuotationListWindow
import re

class ProjectManagementWindow(tk.Toplevel):
    # --- UIモード定義 ---
    MODE_INITIAL = "initial"           # 初期状態（何も選択されていない、またはフォームクリア直後）
    MODE_DISPLAY = "display"           # 既存案件を選択し、表示している状態
    MODE_EDITING = "editing"           # 既存案件を編集中
    MODE_CREATING_NEW = "creating_new" # 新規案件を作成中

    def __init__(self, master):
        super().__init__(master)
        self.title("案件管理")
        # self.geometry("1150x750")

        if hasattr(master, 'db_ops'):
            self.db_ops = master.db_ops
        else:
            messagebox.showerror("エラー", "データベース操作モジュールが見つかりません。", parent=self)
            self.destroy()
            return

        self.parent_window = master
        self.selected_project_id = None
        self.current_mode = None # 現在のUIモードを保持
        self._programmatic_selection_clear = False # ★★★ フラグを追加 ★★★

        self.project_id_var = tk.StringVar()
        self.project_code_var = tk.StringVar()
        self.parent_project_id_var = tk.StringVar()
        self.parent_project_display_var = tk.StringVar()
        self.reception_date_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.project_name_var = tk.StringVar()
        self.responsible_staff_var = tk.StringVar()
        self.customer_id_var = tk.StringVar()
        self.customer_display_var = tk.StringVar()
        self.site_address_var = tk.StringVar()
        self.start_date_scheduled_var = tk.StringVar()
        self.completion_date_scheduled_var = tk.StringVar()
        self.actual_completion_date_var = tk.StringVar()
        
        self.customer_choices_map = {}
        self.parent_project_choices_map = {}
        self.status_options = ["見積依頼", "見積中", "見積提出済", "受注", "施工中", "完了", "請求済", "入金済", "失注", "キャンセル"]

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._create_widgets()
        self.load_customers_to_combobox()
        self.load_parent_projects_to_combobox()
        self.load_projects_to_treeview()
        
        self.clear_form_and_set_mode(new_project_mode=True) # 初期状態は新規案件準備モード

    def _create_widgets(self): # ★★★★★ ここが _create_widgets メソッドの定義開始部分です ★★★★★
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        style = ttk.Style(self)
        tree_font = ("メイリオ", 10)
        style.configure("Treeview", font=tree_font, rowheight=int(tree_font[1] * 2.0))
        style.configure("Treeview.Heading", font=(tree_font[0], tree_font[1], "bold"))

        form_frame = ttk.LabelFrame(main_frame, text="案件情報入力", padding="10")
        form_frame.pack(fill=tk.X, pady=5)

        date_entry_options = {"width": 12, "date_pattern": "yyyy-mm-dd", "locale": "ja_JP"}

        fields_layout = [
            # 1行目
            ("案件コード:", self.project_code_var, "project_code_entry", "Entry", {"width": 18}, (0,0)),
            ("親案件:", self.parent_project_display_var, "parent_project_id_combobox", "Combobox", {"state": "readonly", "width": 22}, (0,2)),
            ("受付日:", self.reception_date_var, "reception_date_entry", "DateEntry", date_entry_options.copy(), (0,4)),
            ("状況 (必須):", self.status_var, "status_combobox", "Combobox", {"state": "readonly", "width": 12, "values": self.status_options}, (0,6)),

            # 2行目
            ("案件名 (必須):", self.project_name_var, "project_name_entry", "Entry", {"width": 35}, (1,0), 3),
            ("担当者名:", self.responsible_staff_var, "responsible_staff_entry", "Entry", {"width": 20}, (1,4), 3),

            # 3行目
            ("顧客 (必須):", self.customer_display_var, "customer_id_combobox", "Combobox", {"state": "readonly", "width": 35}, (2,0), 3),
            ("現場住所:", self.site_address_var, "site_address_entry", "Entry", {"width": 20}, (2,4), 3),

            # 4行目
            ("着工予定日:", self.start_date_scheduled_var, "start_date_scheduled_entry", "DateEntry", date_entry_options.copy(), (3,0)),
            ("完了予定日:", self.completion_date_scheduled_var, "completion_date_scheduled_entry", "DateEntry", date_entry_options.copy(), (3,2)),
            ("実完了日:", self.actual_completion_date_var, "actual_completion_date_entry", "DateEntry", date_entry_options.copy(), (3,4)),

            # 5行目
            ("備考:", None, "remarks_text", "Text", {"width": 60, "height": 4}, (4,0), 7)
        ]

        self.form_entries = {}
        for label_text, var_instance, widget_attr_name, widget_type, widget_options, grid_pos, *span_info in fields_layout:
            r, c = grid_pos
            label_widget = ttk.Label(form_frame, text=label_text)
            label_widget.grid(row=r, column=c, padx=(10,2), pady=3, sticky=tk.W)
            actual_widget = None
            if widget_type == "Entry":
                actual_widget = ttk.Entry(form_frame, textvariable=var_instance, **widget_options)
            elif widget_type == "Combobox":
                actual_widget = ttk.Combobox(form_frame, textvariable=var_instance, **widget_options)
                if "values" in widget_options:
                    actual_widget['values'] = widget_options["values"]
            elif widget_type == "Text":
                actual_widget = tk.Text(form_frame, **widget_options)
            elif widget_type == "DateEntry":
                actual_widget = DateEntry(form_frame, textvariable=var_instance, **widget_options)

            if actual_widget:
                columnspan_val = span_info[0] if span_info else 1
                actual_widget.grid(row=r, column=c+1, padx=(0,5), pady=3, sticky=tk.EW, columnspan=columnspan_val)
                setattr(self, widget_attr_name, actual_widget)
                key_name = widget_attr_name.replace("_entry","").replace("_combobox","").replace("_customdate","").replace("_text","")
                self.form_entries[key_name] = actual_widget

        form_frame.columnconfigure(1, weight=1)
        form_frame.columnconfigure(3, weight=1)
        form_frame.columnconfigure(5, weight=1)
        form_frame.columnconfigure(7, weight=1)

        if hasattr(self, 'status_combobox') and self.status_options:
            self.status_combobox.set(self.status_var.get() or self.status_options[0])

        button_action_frame = ttk.Frame(main_frame)
        button_action_frame.pack(fill=tk.X, pady=5, padx=5)
        # ... (ボタンの作成と配置) ...

        self.add_button = ttk.Button(button_action_frame, text="案件追加", command=self.add_project_data)
        self.add_button.pack(side=tk.LEFT, padx=5)

        self.start_edit_project_button = ttk.Button(button_action_frame, text="案件編集開始", command=self.start_project_edit_mode, state=tk.DISABLED)
        self.start_edit_project_button.pack(side=tk.LEFT, padx=5)

        self.update_button = ttk.Button(button_action_frame, text="案件更新", command=self.update_project_data, state=tk.DISABLED)
        self.update_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = ttk.Button(button_action_frame, text="案件削除", command=self.confirm_delete_project, state=tk.DISABLED)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        self.form_clear_button = ttk.Button(button_action_frame, text="フォームクリア", command=lambda: self.clear_form_and_set_mode(new_project_mode=False)) # clear_form_and_set_mode を使用
        self.form_clear_button.pack(side=tk.LEFT, padx=5)

        self.new_project_prep_button = ttk.Button(button_action_frame, text="新規案件準備", command=self.prepare_new_project_without_clear) # クリアせず新規準備
        self.new_project_prep_button.pack(side=tk.LEFT, padx=5)

        self.open_quotations_for_project_button = ttk.Button(
            button_action_frame, text="この案件の見積管理",
            command=self.open_quotations_for_selected_project, state=tk.DISABLED
        )
        self.open_quotations_for_project_button.pack(side=tk.LEFT, padx=10)

        list_frame = ttk.LabelFrame(main_frame, text="案件一覧", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        if hasattr(self, '_create_project_treeview'):
            self._create_project_treeview(list_frame) # ここで _create_project_treeview が呼ばれています
        else:
            print("エラー: _create_project_treeview メソッドが定義されていません。")

    def _set_ui_mode(self, mode):
        """UIのモードに応じてフィールドとボタンの状態を設定する"""
        self.current_mode = mode
        print(f"UI Mode set to: {self.current_mode}")

        # デフォルトのフィールド状態
        field_state_map = {
            "project_code": "readonly", # 基本的にreadonly、モードによってnormalに
            "project_name": "readonly",
            "customer_id": "disabled", # Comboboxはdisabled
            "parent_project_id": "disabled",
            "site_address": "readonly",
            "reception_date": "readonly", # DateEntryはreadonlyでもカレンダーは開く
            "start_date_scheduled": "readonly",
            "completion_date_scheduled": "readonly",
            "actual_completion_date": "readonly",
            "responsible_staff": "readonly",
            "status": "disabled",
            "remarks": tk.DISABLED, # Textウィジェット用
        }

        # デフォルトのボタン状態
        button_state_map = {
            "add": tk.DISABLED,
            "start_edit": tk.DISABLED,
            "update": tk.DISABLED,
            "delete": tk.DISABLED,
            "open_quotations": tk.DISABLED,
            "form_clear": tk.NORMAL, # クリア系は常に有効
            "new_project_prep": tk.NORMAL,
        }

        if mode == self.MODE_INITIAL:
            field_state_map["project_code"] = "normal" # 手入力可能
            button_state_map["add"] = tk.NORMAL
            for key in ["project_name", "site_address", "responsible_staff"]:
                field_state_map[key] = "normal"
            for key in ["customer_id", "parent_project_id", "status"]:
                field_state_map[key] = "readonly" # Comboboxはreadonlyで選択可能
            for key in ["reception_date", "start_date_scheduled", "completion_date_scheduled", "actual_completion_date"]:
                field_state_map[key] = "normal" # DateEntryはnormalで入力/カレンダー
            field_state_map["remarks"] = tk.NORMAL

        elif mode == self.MODE_DISPLAY:
            # フィールドはすべて読み取り専用（デフォルトのまま）
            button_state_map["start_edit"] = tk.NORMAL
            button_state_map["delete"] = tk.NORMAL
            button_state_map["open_quotations"] = tk.NORMAL

        elif mode == self.MODE_CREATING_NEW:
            # ★★★ 案件コード入力欄をnormalにして、_suggest_project_codeで制御 ★★★
            field_state_map["project_code"] = "normal"
            for key in field_state_map:
                if key != "project_code": # 案件コードは _suggest または on_parent_selected で readonly
                    if key.endswith("_id") or key == "status": # Combobox
                        field_state_map[key] = "readonly"
                    elif key.endswith("_date"): # DateEntry
                         field_state_map[key] = "normal"
                    elif key == "remarks":
                        field_state_map[key] = tk.NORMAL
                    else: # Entry
                        field_state_map[key] = "normal"


            button_state_map["add"] = tk.NORMAL

        elif mode == self.MODE_EDITING:
            field_state_map["project_code"] = "readonly" # 編集モードでは案件コードは常にreadonly
            # 案件コード以外は編集可能
            for key in field_state_map:
                if key != "project_code":
                    if key.endswith("_id") or key == "status":
                        field_state_map[key] = "readonly"
                    elif key.endswith("_date"):
                         field_state_map[key] = "normal"
                    elif key == "remarks":
                        field_state_map[key] = tk.NORMAL
                    else:
                        field_state_map[key] = "normal"
            button_state_map["update"] = tk.NORMAL

        # フォームフィールドの状態を設定
        for field_key, widget_obj in self.form_entries.items():
            state_to_set = field_state_map.get(field_key)
            if widget_obj and state_to_set is not None: # state_to_set が None でないことを確認
                if isinstance(widget_obj, tk.Text):
                    widget_obj.config(state=state_to_set, bg="white" if state_to_set == tk.NORMAL else "#f0f0f0")
                elif isinstance(widget_obj, (ttk.Entry, DateEntry, ttk.Combobox)):
                    widget_obj.config(state=state_to_set)
            elif field_key == "project_code" and hasattr(self, 'project_code_entry'): # field_state_map に project_code がない場合も考慮
                 self.project_code_entry.config(state=field_state_map.get("project_code", "readonly"))

        # ボタンの状態を設定
        if hasattr(self, 'add_button'): self.add_button.config(state=button_state_map["add"])
        if hasattr(self, 'start_edit_project_button'): self.start_edit_project_button.config(state=button_state_map["start_edit"])
        if hasattr(self, 'update_button'): self.update_button.config(state=button_state_map["update"])
        if hasattr(self, 'delete_button'): self.delete_button.config(state=button_state_map["delete"])
        if hasattr(self, 'open_quotations_for_project_button'): self.open_quotations_for_project_button.config(state=button_state_map["open_quotations"])
        if hasattr(self, 'form_clear_button'): self.form_clear_button.config(state=button_state_map["form_clear"])
        if hasattr(self, 'new_project_prep_button'): self.new_project_prep_button.config(state=button_state_map["new_project_prep"])
        # ... (他のボタンも同様)
        if hasattr(self, 'start_edit_project_button'): self.start_edit_project_button.config(state=button_state_map["start_edit"])
        if hasattr(self, 'update_button'): self.update_button.config(state=button_state_map["update"])
        if hasattr(self, 'delete_button'): self.delete_button.config(state=button_state_map["delete"])
        if hasattr(self, 'open_quotations_for_project_button'): self.open_quotations_for_project_button.config(state=button_state_map["open_quotations"])
        if hasattr(self, 'form_clear_button'): self.form_clear_button.config(state=button_state_map["form_clear"])
        if hasattr(self, 'new_project_prep_button'): self.new_project_prep_button.config(state=button_state_map["new_project_prep"])

        # フォーカス設定
        if mode == self.MODE_INITIAL:
            if hasattr(self, 'project_code_entry'): self.project_code_entry.focus_set()
        elif mode == self.MODE_CREATING_NEW:
            if hasattr(self, 'project_name_entry'): self.project_name_entry.focus_set()
        elif mode == self.MODE_EDITING:
            if hasattr(self, 'project_name_entry'): self.project_name_entry.focus_set()

    def _get_project_data_from_form(self):
        """フォームからデータを取得し、辞書として返す。バリデーションも行う。"""
        data = {}
        data["project_code"] = self.project_code_var.get().strip()
        data["project_name"] = self.project_name_var.get().strip()
        data["customer_id_str"] = self.customer_id_var.get().strip()
        data["parent_project_id_str"] = self.parent_project_id_var.get().strip()
        data["site_address"] = self.site_address_var.get().strip()
        data["reception_date"] = self.reception_date_var.get().strip()
        data["start_date_scheduled"] = self.start_date_scheduled_var.get().strip()
        data["completion_date_scheduled"] = self.completion_date_scheduled_var.get().strip()
        data["actual_completion_date"] = self.actual_completion_date_var.get().strip()
        data["responsible_staff_name"] = self.responsible_staff_var.get().strip()
        data["status"] = self.status_var.get().strip()
        data["remarks"] = self.remarks_text.get("1.0", tk.END).strip() if hasattr(self, 'remarks_text') else ""

        # バリデーション
        if not data["project_code"]:
            messagebox.showerror("入力エラー", "案件コードは必須です。", parent=self)
            if hasattr(self, 'project_code_entry'): self.project_code_entry.focus_set()
            return None
        if not data["project_name"]:
            messagebox.showerror("入力エラー", "案件名は必須です。", parent=self)
            if hasattr(self, 'project_name_entry'): self.project_name_entry.focus_set()
            return None
        if not data["customer_id_str"]: # IDが空かチェック
            messagebox.showerror("入力エラー", "顧客は必須です。", parent=self)
            if hasattr(self, 'customer_id_combobox'): self.customer_id_combobox.focus_set()
            return None
        if not data["status"]:
            messagebox.showerror("入力エラー", "状況は必須です。", parent=self)
            if hasattr(self, 'status_combobox'): self.status_combobox.focus_set()
            return None

        try:
            data["customer_id"] = int(data["customer_id_str"]) if data["customer_id_str"] else None
            data["parent_project_id"] = int(data["parent_project_id_str"]) if data["parent_project_id_str"] else None
        except ValueError:
            messagebox.showerror("入力エラー", "顧客ID、親案件IDの形式が正しくありません。", parent=self)
            return None
        
        return data

    def clear_form_and_set_mode(self, new_project_mode=False):
        """フォームをクリアし、指定されたモードに応じてUI状態を設定する"""
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
        self.status_var.set(self.status_options[0] if hasattr(self, 'status_options') and self.status_options else "")
        if hasattr(self, 'status_combobox'):
             self.status_combobox.set(self.status_var.get())
        if hasattr(self, 'remarks_text'):
            self.remarks_text.config(state=tk.NORMAL)
            self.remarks_text.delete("1.0", tk.END)

        self.selected_project_id = None # 内部的な選択IDもクリア

        # ★★★ Treeviewの選択解除時にイベントがトリガーされるのを防ぐ ★★★
        if hasattr(self, 'project_tree') and self.project_tree.winfo_exists(): # ウィジェット存在確認
            if self.project_tree.selection():
                self._programmatic_selection_clear = True # ★★★ フラグをセット ★★★
                print("プログラムによる選択解除を開始します。")
                self.project_tree.selection_remove(self.project_tree.selection())
                print("プログラムによる選択解除を完了しました。")
                self._programmatic_selection_clear = False # ★★★ フラグをリセット ★★★
        print(f"if 前Project form cleared. Mode set to: {self.current_mode}")
        if new_project_mode:
            self._set_ui_mode(self.MODE_CREATING_NEW) # 先にUIモードを設定（ここで案件コード欄がnormalになる）
            self._suggest_project_code() # 次に案件コードを提案（ここでreadonlyになる）
            self.reception_date_var.set(datetime.now().strftime("%Y-%m-%d"))
            print(f"if 中Project form cleared. Mode set to: {self.current_mode}")
            if hasattr(self, 'status_combobox') and self.status_options:
                self.status_var.set("見積中")
                self.status_combobox.set("見積中")
        else:
            self._set_ui_mode(self.MODE_INITIAL)
        
        print(f"if 後Project form cleared. Mode set to: {self.current_mode}")

    def prepare_new_project_without_clear(self):
        """
        案件コードの自動提案・受付日・状況以外の項目はクリアし、
        UIモードのみ新規案件準備状態に変更する。
        """
        # 案件名、顧客、親案件、現場住所、着工予定日、完了予定日、実完了日、担当者、備考をクリア
        self.project_name_var.set("")
        self.customer_id_var.set("")
        self.customer_display_var.set(self.customer_choices_map.get("-----", "-----") if hasattr(self, 'customer_choices_map') and "-----" in self.customer_choices_map else "-----")
        self.parent_project_id_var.set("")
        self.parent_project_display_var.set(self.parent_project_choices_map.get("-----", "-----") if hasattr(self, 'parent_project_choices_map') and "-----" in self.parent_project_choices_map else "-----")
        self.site_address_var.set("")
        self.start_date_scheduled_var.set("")
        self.completion_date_scheduled_var.set("")
        self.actual_completion_date_var.set("")
        self.responsible_staff_var.set("")
        if hasattr(self, 'remarks_text'):
            self.remarks_text.config(state=tk.NORMAL)
            self.remarks_text.delete("1.0", tk.END)
        # 案件コード・受付日・状況は初期化
        self._set_ui_mode(self.MODE_CREATING_NEW)
        self._suggest_project_code()
        self.reception_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        if hasattr(self, 'status_combobox') and self.status_options:
            self.status_var.set("見積中")
            self.status_combobox.set("見積中")
        print(f"prepare_new_project_without_clear: Mode set to: {self.current_mode}")

    def on_project_tree_select(self, event):
        if self._programmatic_selection_clear: # ★★★ フラグをチェック ★★★
            print("on_project_tree_select: プログラムによる選択解除のため処理をスキップします。")
            return # プログラムによる選択解除の場合は何もしない

        selected_items = self.project_tree.selection()
        print(f"on_project_tree_select: ユーザー操作による選択変更。選択アイテム: {selected_items}")

        if not selected_items:
            print("on_project_tree_select: ユーザー操作により選択が解除されました。")
            self.clear_form_and_set_mode(new_project_mode=False)
            return

        selected_iid = selected_items[0]
        self.selected_project_id = selected_iid
        project_data_tuple = self.db_ops.get_project_by_id(self.selected_project_id)

        if project_data_tuple:
            self.project_id_var.set(project_data_tuple[0] or "")
            self.project_code_var.set(project_data_tuple[1] or "")
            self.project_name_var.set(project_data_tuple[2] or "")
            customer_id = project_data_tuple[3]
            self.customer_id_var.set(str(customer_id) if customer_id is not None else "")
            # ... (他のフィールドへのセット処理は変更なし) ...
            customer_display_val = "-----"
            if customer_id is not None and hasattr(self, 'customer_choices_map'):
                for disp, c_id_map in self.customer_choices_map.items():
                    if c_id_map == customer_id: customer_display_val = disp; break
            self.customer_display_var.set(customer_display_val)
            parent_project_id = project_data_tuple[5]
            self.parent_project_id_var.set(str(parent_project_id) if parent_project_id is not None else "")
            parent_project_display_val = "-----"
            if parent_project_id is not None and hasattr(self, 'parent_project_choices_map'):
                for disp, p_id_map in self.parent_project_choices_map.items():
                    if p_id_map == parent_project_id: parent_project_display_val = disp; break
            self.parent_project_display_var.set(parent_project_display_val)
            self.site_address_var.set(project_data_tuple[7] or "")
            self.reception_date_var.set(project_data_tuple[8] or "")
            self.start_date_scheduled_var.set(project_data_tuple[9] or "")
            self.completion_date_scheduled_var.set(project_data_tuple[10] or "")
            self.actual_completion_date_var.set(project_data_tuple[11] or "")
            self.responsible_staff_var.set(project_data_tuple[12] or "")
            self.status_var.set(project_data_tuple[13] or (self.status_options[0] if self.status_options else ""))
            if hasattr(self, 'status_combobox'): self.status_combobox.set(self.status_var.get())
            if hasattr(self, 'remarks_text'):
                self.remarks_text.config(state=tk.NORMAL)
        self._set_ui_mode(self.MODE_EDITING)


    def add_project_data(self):
        form_data = self._get_project_data_from_form()
        if form_data is None:
            return # バリデーションエラー

        result = self.db_ops.add_project(
            form_data["project_code"], form_data["project_name"], form_data["customer_id"],
            form_data["parent_project_id"], form_data["site_address"], form_data["reception_date"],
            form_data["start_date_scheduled"], form_data["completion_date_scheduled"],
            form_data["actual_completion_date"], form_data["responsible_staff_name"],
            form_data["status"], form_data["remarks"]
        )
        if isinstance(result, int):
            messagebox.showinfo("成功", f"案件「{form_data['project_name']}」を登録しました。 (ID: {result})", parent=self)
            self.load_projects_to_treeview()
            self.clear_form_and_set_mode(new_project_mode=True) # 次の新規準備へ
        # ... (エラー処理は同様)
        elif result == "DUPLICATE_CODE": messagebox.showerror("登録エラー", f"案件コード「{form_data['project_code']}」は既に登録されています。", parent=self)
        elif result == "NOT_NULL_VIOLATION": messagebox.showerror("登録エラー", "必須項目が入力されていません。", parent=self)
        elif result == "FK_CONSTRAINT_FAILED": messagebox.showerror("登録エラー", "指定された顧客IDまたは親案件IDが存在しません。", parent=self)
        else: messagebox.showerror("登録エラー", f"案件の登録に失敗しました: {result}", parent=self)


    def update_project_data(self):
        if not self.selected_project_id or self.current_mode != self.MODE_EDITING:
            messagebox.showwarning("警告", "案件が選択されていないか、編集モードではありません。", parent=self)
            return

        form_data = self._get_project_data_from_form()
        if form_data is None:
            return # バリデーションエラー

        result = self.db_ops.update_project(
            project_id=self.selected_project_id,
            project_code=form_data["project_code"], project_name=form_data["project_name"],
            customer_id=form_data["customer_id"], parent_project_id=form_data["parent_project_id"],
            site_address=form_data["site_address"], reception_date=form_data["reception_date"],
            start_date_scheduled=form_data["start_date_scheduled"],
            completion_date_scheduled=form_data["completion_date_scheduled"],
            actual_completion_date=form_data["actual_completion_date"],
            responsible_staff_name=form_data["responsible_staff_name"],
            status=form_data["status"], remarks=form_data["remarks"]
        )
        if result is True:
            messagebox.showinfo("成功", f"案件「{form_data['project_name']}」を更新しました。", parent=self)
            current_selected_id = self.selected_project_id # 更新後も選択状態を維持するためIDを保持
            self.load_projects_to_treeview()
            if current_selected_id and hasattr(self, 'project_tree') and self.project_tree.exists(str(current_selected_id)):
                self.project_tree.selection_set(str(current_selected_id)) # 再選択
                self.project_tree.focus(str(current_selected_id))
                self.on_project_tree_select(None) # フォームを再表示し、表示モードに
            else:
                self.clear_form_and_set_mode(new_project_mode=False) # 見つからなければ初期状態
        # ... (エラー処理は同様) ...
        elif result == "DUPLICATE_CODE": messagebox.showerror("更新エラー", f"案件コード「{form_data['project_code']}」は既に他の案件で使用されています。", parent=self)
        elif result == "NOT_FOUND": messagebox.showerror("更新エラー", f"更新対象の案件 (ID: {self.selected_project_id}) が見つかりませんでした。", parent=self)
        # ... 他のエラーハンドリング

    def on_parent_project_selected(self, event=None):
        selected_display_name = self.parent_project_display_var.get()
        parent_project_id_str = str(self.parent_project_choices_map.get(selected_display_name, ""))
        self.parent_project_id_var.set(parent_project_id_str)
        print(f"Parent project selected: Display='{selected_display_name}', ID='{parent_project_id_str}'")

        if self.current_mode == self.MODE_CREATING_NEW: # 新規案件準備モードの場合のみ実行
            if parent_project_id_str and parent_project_id_str != "":
                parent_project_id = int(parent_project_id_str)
                parent_project_info = self.db_ops.get_project_by_id(parent_project_id)
                if parent_project_info:
                    parent_project_code = parent_project_info[1]
                    child_project_codes = self.db_ops.get_child_project_codes(parent_project_id)
                    max_branch_num = 0
                    for code in child_project_codes:
                        match = re.search(rf"^{re.escape(parent_project_code)}-(\d+)$", code) # 親コードに完全一致で始まる枝番
                        if match:
                            branch_num = int(match.group(1))
                            if branch_num > max_branch_num:
                                max_branch_num = branch_num
                    new_branch_num = max_branch_num + 1
                    new_project_code = f"{parent_project_code}-{new_branch_num:02d}"
                    self.project_code_var.set(new_project_code)
                    if hasattr(self, 'project_code_entry'):
                        self.project_code_entry.config(state="readonly")
                else:
                    self._suggest_project_code() # 親情報が取れなければ月次提案
                    if hasattr(self, 'project_code_entry'):
                        self.project_code_entry.config(state="normal") # 親情報不備なら手入力可能に
                    self._suggest_project_code() # 通常提案に戻し、stateは_suggestが制御
            else: # 親案件の選択が解除された場合
                self._suggest_project_code() # 通常の案件コード提案に戻す
                if hasattr(self, 'project_code_entry'):
                    self.project_code_entry.config(state="normal") # まず normal に戻す
                self._suggest_project_code() # これで月次連番が提案され、成功すればreadonlyになる

    # _suggest_project_code は、親が選択されていない場合にのみ呼び出されるようにする
    # または、呼び出し側でモードを判定する
    def _suggest_project_code(self):
        # この関数は、親案件が選択されていない場合に、月次の連番を提案する。
        # 呼び出し元で self.current_mode == self.MODE_CREATING_NEW であることを確認済みと想定。
        if not self.parent_project_id_var.get(): # 親が選択されていない場合のみ実行 (MODE_CREATING_NEWのチェックは呼び出し元で行う想定)
            try:
                now = datetime.now()
                year_month_str = now.strftime("%Y%m")
                next_seq = self.db_ops.get_next_project_code_sequence_for_month(year_month_str)
                if next_seq is not None:
                    suggested_code = f"P-{year_month_str}-{next_seq:03d}"
                    self.project_code_var.set(suggested_code)
                    if hasattr(self, 'project_code_entry'):
                        self.project_code_entry.config(state="readonly")
                else:
                    # (エラー処理は変更なし)
                    messagebox.showerror("エラー", "案件コードの自動採番に失敗しました。\n手動で入力してください。", parent=self)
                    self.project_code_var.set("")
                    if hasattr(self, 'project_code_entry'): self.project_code_entry.config(state="normal")
            except Exception as e:
                # (エラー処理は変更なし)
                messagebox.showerror("エラー", f"案件コード生成中にエラー: {e}", parent=self)
                self.project_code_var.set("")
                if hasattr(self, 'project_code_entry'): self.project_code_entry.config(state="normal")
        # 親が選択されている場合は、on_parent_project_selected が案件コードと状態を制御するので何もしない


    # ... (confirm_delete_project, open_quotations_for_selected_project, _create_project_treeview, on_close, mainブロック等は変更なし) ...
    def _create_project_treeview(self, parent_frame):
        columns = ("project_code", "project_name", "customer_name", "status", "reception_date", "responsible_staff_name")
        self.project_tree = ttk.Treeview(parent_frame, columns=columns, show="headings", height=10, style="Treeview")
        self.project_tree.heading("project_code", text="案件CD"); self.project_tree.column("project_code", width=100)
        self.project_tree.heading("project_name", text="案件名"); self.project_tree.column("project_name", width=220)
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
                # get_all_projects の返り値のインデックス (estimated_amount 削除済み)
                # 0:id, 1:code, 2:name, 3:cust_id, 4:cust_name, ..., 8:recept_date, ..., 12:resp_staff, 13:status
                display_values = (
                    project_tuple[1], # project_code
                    project_tuple[2], # project_name
                    project_tuple[4] or "", # customer_name
                    project_tuple[13] or "", # status
                    project_tuple[8] or "", # reception_date
                    project_tuple[12] or "" # responsible_staff_name
                )
                self.project_tree.insert("", tk.END, values=display_values, iid=project_tuple[0])
        # Treeviewの選択がクリアされたときの処理を on_project_tree_select に任せるか、
        # ここで明示的に初期モードに設定するか検討。
        # load_projects_to_treeview の後に on_project_tree_select(None) が呼ばれるケースは少ないが、
        # もし呼ばれるなら、その中で clear_form_and_set_mode が呼ばれ初期化される。
        # 通常はリスト更新後、選択は維持されないので、clear_form_and_set_mode(False) で初期モードが良い。
        if not self.project_tree.selection(): # 何も選択されていなければ初期モードへ
            self.clear_form_and_set_mode(new_project_mode=False)


    def load_customers_to_combobox(self):
        if not hasattr(self, 'customer_id_combobox'): return
        try:
            customers_data = self.db_ops.get_all_customers()
            self.customer_choices_map = {} 
            combobox_values = ["-----"] 
            if customers_data:
                for row in customers_data: 
                    display_name = f"{row[1]} (ID:{row[0]})"
                    combobox_values.append(display_name)
                    self.customer_choices_map[display_name] = row[0] 
            self.customer_id_combobox['values'] = combobox_values
            self.customer_display_var.set(combobox_values[0]) 
            self.customer_id_var.set("") 
        except Exception as e:
            print(f"Error loading customers: {e}")
            self.customer_id_combobox['values'] = ["-----"]
            self.customer_display_var.set("-----")
        self.customer_id_combobox.bind("<<ComboboxSelected>>", self.on_customer_selected)

    def load_parent_projects_to_combobox(self):
        if not hasattr(self, 'parent_project_id_combobox'): return
        try:
            projects_data = self.db_ops.get_all_projects() # ここで取得するデータは案件IDと表示名だけでよい
            self.parent_project_choices_map = {}
            combobox_values = ["-----"]
            if projects_data:
                for row in projects_data: # row[0] is project_id, row[1] is project_code, row[2] is project_name
                    # 編集中の案件を親案件候補から除外 (現在のselected_project_idと比較)
                    # ただし、selected_project_id が文字列で、row[0]が数値の場合があるので型変換注意
                    try:
                        current_editing_id = int(self.selected_project_id) if self.selected_project_id else None
                    except ValueError:
                        current_editing_id = None

                    if current_editing_id is not None and row[0] == current_editing_id:
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

    def on_project_double_click(self, event):
        if self.project_tree.selection():
            if self.selected_project_id:
                self.open_quotations_for_selected_project()
            else:
                messagebox.showwarning("情報なし", "選択された案件のIDが取得できませんでした。", parent=self)

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
            self.clear_form_and_set_mode(new_project_mode=False) # 削除後は初期モードへ
        elif result == "NOT_FOUND": messagebox.showerror("削除エラー", f"削除対象の案件 (ID: {self.selected_project_id}) が見つかりませんでした。", parent=self)
        elif result == "FK_CONSTRAINT_FAILED": messagebox.showerror("削除エラー", "この案件は他のデータ（例：見積もり、子案件）から参照されているため削除できません。", parent=self)
        else: messagebox.showerror("削除エラー", f"案件の削除に失敗しました: {result}", parent=self)

    def open_quotations_for_selected_project(self):
        if not self.selected_project_id:
            messagebox.showwarning("未選択", "案件が選択されていません。", parent=self)
            return
        print(f"Opening quotation list for project ID: {self.selected_project_id}")
        quotation_list_win = QuotationListWindow(self, project_filter_id=self.selected_project_id)

    def start_project_edit_mode(self):
        """
        選択中の案件を編集モードに切り替える
        """
        if not self.selected_project_id:
            messagebox.showwarning("未選択", "編集する案件が選択されていません。", parent=self)
            return
        self._set_ui_mode(self.MODE_EDITING)

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