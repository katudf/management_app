# project_management_window.py

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import database_operations as db_ops
from datetime import datetime
from quotation_management_window import QuotationListWindow

class ProjectManagementWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("案件管理")
        self.geometry("1100x750")

        if hasattr(master, 'db_ops'):
            self.db_ops = master.db_ops
        else:
            messagebox.showerror("エラー", "データベース操作モジュールが見つかりません。", parent=self)
            self.destroy()
            return

        self.parent_window = master
        self.selected_project_id = None

        # --- フォームフィールド変数 ---
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
        style.configure("Treeview", font=("メイリオ", 10), rowheight=25)
        style.configure("Treeview.Heading", font=("メイリオ", 10, "bold"))

        form_frame = ttk.LabelFrame(main_frame, text="案件情報入力", padding="10")
        form_frame.pack(fill=tk.X, pady=5)

        fields_data = [
            (0, 0, "案件ID:", "project_id_var", "Entry", {"width": 20, "state": "readonly"}, tk.W, tk.EW),
            (0, 2, "案件コード:", "project_code_var", "Entry", {"width": 20}, tk.W, tk.EW),
            (1, 0, "案件名 (必須):", "project_name_var", "Entry", {"width": 40}, tk.W, tk.EW),
            (1, 2, "顧客 (必須):", "customer_id_combobox", "Combobox", {"width": 38, "textvariable": self.customer_display_var, "state": "readonly"}, tk.W, tk.EW),
            (2, 0, "親案件:", "parent_project_id_combobox", "Combobox", {"width": 38, "textvariable": self.parent_project_display_var, "state": "readonly"}, tk.W, tk.EW),
            (2, 2, "現場住所:", "site_address_var", "Entry", {"width": 40}, tk.W, tk.EW),
            (3, 0, "受付日:", "reception_date_var", "Entry", {"width": 20}, tk.W, tk.EW),
            (3, 2, "担当者名:", "responsible_staff_var", "Entry", {"width": 20}, tk.W, tk.EW),
            (4, 0, "見積金額(税抜):", "estimated_amount_var", "Entry", {"width": 20}, tk.W, tk.EW),
            (4, 2, "状況 (必須):", "status_combobox", "Combobox", {"width": 18, "textvariable": self.status_var, "state": "readonly"}, tk.W, tk.EW),
            (5, 0, "着工予定日:", "start_date_scheduled_var", "Entry", {"width": 20}, tk.W, tk.EW),
            (5, 2, "完了予定日:", "completion_date_scheduled_var", "Entry", {"width": 20}, tk.W, tk.EW),
            (6, 0, "実完了日:", "actual_completion_date_var", "Entry", {"width": 20}, tk.W, tk.EW),
            (7, 0, "備考:", "remarks_text", "Text", {"width": 40, "height": 3}, tk.NW, tk.NSEW)
        ]

        self.form_entries = {}

        for r_offset, (r_form, c_form, label, widget_name_or_var, widget_type, options, sticky_l, sticky_w) in enumerate(fields_data):
            actual_row = r_form
            ttk.Label(form_frame, text=label).grid(row=actual_row, column=c_form, padx=5, pady=3, sticky=sticky_l)
            widget = None
            if widget_type == "Entry":
                var_instance = getattr(self, widget_name_or_var)
                widget = ttk.Entry(form_frame, textvariable=var_instance, **options)
                setattr(self, widget_name_or_var.replace("_var", "_entry"), widget)
            elif widget_type == "Combobox":
                widget = ttk.Combobox(form_frame, **options)
                setattr(self, widget_name_or_var, widget)
            elif widget_type == "Text":
                widget = tk.Text(form_frame, **options)
                setattr(self, widget_name_or_var, widget)
            if widget:
                colspan = options.get("colspan", 1)
                rowspan = options.get("rowspan", 1)
                widget.grid(row=actual_row, column=c_form + 1, padx=5, pady=3, sticky=sticky_w, columnspan=colspan)
                entry_key = widget_name_or_var.replace("_var","").replace("_combobox","").replace("_text","")
                self.form_entries[entry_key] = widget

        form_frame.columnconfigure(1, weight=1)
        form_frame.columnconfigure(3, weight=1)

        self.status_options = ["見積依頼", "見積中", "見積提出済", "受注", "施工中", "完了", "請求済", "入金済", "失注", "キャンセル"]
        if hasattr(self, 'status_combobox'):
            self.status_combobox['values'] = self.status_options
            if self.status_options:
                self.status_combobox.set(self.status_options[0])

        button_action_frame = ttk.Frame(main_frame)
        button_action_frame.pack(fill=tk.X, pady=5, padx=5)

        self.add_button = ttk.Button(button_action_frame, text="案件追加", command=self.add_project_data)
        self.add_button.pack(side=tk.LEFT, padx=5)
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
        self.project_tree = ttk.Treeview(parent_frame, columns=columns, show="headings", height=10)
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
                display_values = (
                    project_tuple[0],
                    project_tuple[1],
                    project_tuple[2],
                    project_tuple[4] or "",
                    project_tuple[14] or "",
                    project_tuple[8] or "",
                    project_tuple[12] or ""
                )
                self.project_tree.insert("", tk.END, values=display_values, iid=project_tuple[0])
        self.on_project_tree_select(None)

    def load_customers_to_combobox(self):
        if not hasattr(self, 'customer_id_combobox'):
            return
        try:
            customers_data = self.db_ops.get_all_customers()
            if customers_data:
                self.customer_choices = [("-----", None)] + [(f"{row[1]} (ID:{row[0]})", row[0]) for row in customers_data]
                self.customer_id_combobox['values'] = [choice[0] for choice in self.customer_choices]
                self.customer_id_combobox.set(self.customer_choices[0][0])
            else:
                self.customer_id_combobox['values'] = [("-----", None)]
                self.customer_id_combobox.set(self.customer_choices[0][0])
        except Exception as e:
            print(f"Error loading customers to combobox: {e}")
            if hasattr(self, 'customer_id_combobox'):
                self.customer_id_combobox['values'] = [("-----", None)]
                self.customer_id_combobox.set(self.customer_choices[0][0])
        self.customer_id_combobox.bind("<<ComboboxSelected>>", self.on_customer_selected)

    def load_parent_projects_to_combobox(self):
        if not hasattr(self, 'parent_project_id_combobox'):
            return
        try:
            projects_data = self.db_ops.get_all_projects()
            if projects_data:
                self.parent_project_choices = [("-----", None)] + [(f"{row[1]}: {row[2]} (ID:{row[0]})", row[0]) for row in projects_data]
                self.parent_project_id_combobox['values'] = [choice[0] for choice in self.parent_project_choices]
                self.parent_project_id_combobox.set(self.parent_project_choices[0][0])
            else:
                self.parent_project_id_combobox['values'] = [("-----", None)]
                self.parent_project_id_combobox.set(self.parent_project_choices[0][0])
        except Exception as e:
            print(f"Error loading parent projects to combobox: {e}")
            if hasattr(self, 'parent_project_id_combobox'):
                self.parent_project_id_combobox['values'] = [("-----", None)]
                self.parent_project_id_combobox.set(self.parent_project_choices[0][0])
        self.parent_project_id_combobox.bind("<<ComboboxSelected>>", self.on_parent_project_selected)

    def on_customer_selected(self, event=None):
        if not hasattr(self, 'customer_choices') or not self.customer_choices: return
        selected_display_name = self.customer_display_var.get()
        for display, c_id in self.customer_choices:
            if display == selected_display_name:
                self.customer_id_var.set(str(c_id) if c_id is not None else "")
                return
        self.customer_id_var.set("")

    def on_parent_project_selected(self, event=None):
        if not hasattr(self, 'parent_project_choices') or not self.parent_project_choices: return
        selected_display_name = self.parent_project_display_var.get()
        for display, p_id in self.parent_project_choices:
            if display == selected_display_name:
                self.parent_project_id_var.set(str(p_id) if p_id is not None else "")
                return
        self.parent_project_id_var.set("")

    def on_project_tree_select(self, event):
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
            customer_display_value = ""
            if customer_id is not None and hasattr(self, 'customer_choices'):
                for display, c_id_choice in self.customer_choices:
                    if c_id_choice == customer_id:
                        customer_display_value = display
                        break
            self.customer_display_var.set(customer_display_value)
            parent_project_id = project_data_tuple[5]
            self.parent_project_id_var.set(str(parent_project_id) if parent_project_id is not None else "")
            parent_project_display_value = ""
            if parent_project_id is not None and hasattr(self, 'parent_project_choices'):
                for display, p_id_choice in self.parent_project_choices:
                    if p_id_choice == parent_project_id:
                        parent_project_display_value = display
                        break
            self.parent_project_display_var.set(parent_project_display_value)
            self.site_address_var.set(project_data_tuple[7] or "")
            self.reception_date_var.set(project_data_tuple[8] or "")
            self.start_date_scheduled_var.set(project_data_tuple[9] or "")
            self.completion_date_scheduled_var.set(project_data_tuple[10] or "")
            self.actual_completion_date_var.set(project_data_tuple[11] or "")
            self.responsible_staff_var.set(project_data_tuple[12] or "")
            estimated_amount = project_data_tuple[13]
            self.estimated_amount_var.set(f"{estimated_amount:,}" if estimated_amount is not None else "0")
            self.status_var.set(project_data_tuple[14] or "")
            self.remarks_text.delete("1.0", tk.END)
            self.remarks_text.insert("1.0", project_data_tuple[15] or "")
            for key, widget in self.form_entries.items():
                if isinstance(widget, tk.Text): widget.config(state=tk.DISABLED)
                elif isinstance(widget, ttk.Combobox): widget.config(state="disabled")
                else: widget.config(state="readonly")
            if hasattr(self, 'update_button'): self.update_button.config(state=tk.NORMAL)
            if hasattr(self, 'delete_button'): self.delete_button.config(state=tk.NORMAL)
            if hasattr(self, 'add_button'): self.add_button.config(state=tk.DISABLED)
            if hasattr(self, 'open_quotations_for_project_button'):
                self.open_quotations_for_project_button.config(state=tk.NORMAL)
        else:
            messagebox.showerror("エラー", f"案件ID {self.selected_project_id} の詳細情報取得に失敗しました。", parent=self)
            self.clear_form(for_new_project=False)

    def on_project_double_click(self, event):
        if self.selected_project_id:
            pass

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
        self.project_id_var.set("")
        self.project_code_var.set("")
        self.project_name_var.set("")
        self.customer_id_var.set("")
        self.customer_display_var.set(self.customer_choices[0][0] if hasattr(self, 'customer_choices') and self.customer_choices else "")
        self.parent_project_id_var.set("")
        self.parent_project_display_var.set(self.parent_project_choices[0][0] if hasattr(self, 'parent_project_choices') and self.parent_project_choices else "")
        self.site_address_var.set("")
        self.reception_date_var.set("")
        self.start_date_scheduled_var.set("")
        self.completion_date_scheduled_var.set("")
        self.actual_completion_date_var.set("")
        self.responsible_staff_var.set("")
        self.estimated_amount_var.set("0")
        self.status_var.set(self.status_options[0] if hasattr(self, 'status_options') and self.status_options else "")
        if hasattr(self, 'remarks_text'): self.remarks_text.delete("1.0", tk.END)
        for key, widget in self.form_entries.items():
            if isinstance(widget, tk.Text): widget.config(state=tk.NORMAL)
            elif isinstance(widget, ttk.Combobox): widget.config(state="readonly")
            else: widget.config(state="normal")
        if hasattr(self, 'project_id_entry'):
            self.project_id_entry.config(state="readonly")
        if for_new_project:
            self._suggest_project_code()
            self.reception_date_var.set(datetime.now().strftime("%Y-%m-%d"))
            self.status_var.set("見積中")
            if hasattr(self, 'project_name_entry'): self.project_name_entry.focus_set()
        else:
            if hasattr(self, 'project_code_entry'): self.project_code_entry.config(state="normal")
            if hasattr(self, 'project_code_entry'): self.project_code_entry.focus_set()
        self.selected_project_id = None
        if hasattr(self, 'project_tree') and self.project_tree.selection():
            self.project_tree.selection_remove(self.project_tree.selection())
        if hasattr(self, 'add_button'): self.add_button.config(state=tk.NORMAL)
        if hasattr(self, 'update_button'): self.update_button.config(state=tk.DISABLED)
        if hasattr(self, 'delete_button'): self.delete_button.config(state=tk.DISABLED)
        if hasattr(self, 'open_quotations_for_project_button'):
            self.open_quotations_for_project_button.config(state=tk.DISABLED)
        print("Project form cleared.")

    def add_project_data(self):
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
            messagebox.showerror("入力エラー", "顧客ID、親案件ID、見積金額には数値を入力してください。", parent=self)
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

    def update_project_data(self):
        if not self.selected_project_id:
            messagebox.showerror("エラー", "更新する案件が選択されていません。", parent=self)
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
        try:
            customer_id = int(customer_id_str) if customer_id_str else None
            parent_project_id = int(parent_project_id_str) if parent_project_id_str else None
            estimated_amount = int(estimated_amount_str) if estimated_amount_str else 0
        except ValueError:
            messagebox.showerror("入力エラー", "顧客ID、親案件ID、見積金額には数値を入力してください。", parent=self)
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
            self.load_projects_to_treeview()
            self.clear_form(for_new_project=True)

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

    def open_quotations_for_selected_project(self):
        if not self.selected_project_id:
            messagebox.showwarning("未選択", "案件が選択されていません。", parent=self)
            return
        print(f"Opening quotation list for project ID: {self.selected_project_id}")
        quotation_list_win = QuotationListWindow(self)

    def on_close(self):
        self.destroy()