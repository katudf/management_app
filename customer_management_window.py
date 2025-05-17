import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import database_operations as db_ops

class CustomerManagementWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("顧客管理")
        self.geometry("850x600")
        self.db_ops = db_ops
        self.selected_customer_id = None # ### 追加 ### 選択中の顧客IDを保持する変数

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self._create_widgets()
        self.load_customers_to_treeview()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        style = ttk.Style(self)
        style.configure("Treeview", font=("メイリオ", 11)) # 例: 行の高さを調整
        style.configure("Treeview.Heading", font=("メイリオ", 11, "bold"))

        form_frame = ttk.LabelFrame(main_frame, text="顧客情報入力", padding="10")
        form_frame.pack(fill=tk.X, pady=5)

        field_configs = [
            ("顧客名:", "customer_name_entry", 40, 0, 0),
            ("担当者名:", "contact_person_entry", 40, 1, 0),
            ("電話番号:", "phone_entry", 30, 0, 2),
            ("メール:", "email_entry", 30, 1, 2),
            ("住所:", "address_entry", 40, 2, 0, 3),
            ("備考:", "notes_text", 40, 3, 0, 3, 3)
        ]
        for label_text, entry_name, width, row, col, *span_height in field_configs:
            ttk.Label(form_frame, text=label_text).grid(row=row, column=col, padx=5, pady=5, sticky=tk.W)
            if entry_name == "notes_text":
                widget_columnspan = span_height[0] if len(span_height) > 0 else 1
                widget_height = span_height[1] if len(span_height) > 1 else 3
                widget = tk.Text(form_frame, width=width, height=widget_height)
                widget.grid(row=row, column=col + 1, columnspan=widget_columnspan, padx=5, pady=5, sticky=tk.EW)
            else:
                widget_columnspan = span_height[0] if len(span_height) > 0 else 1
                widget = ttk.Entry(form_frame, width=width)
                widget.grid(row=row, column=col + 1, columnspan=widget_columnspan, padx=5, pady=5, sticky=tk.EW)
            setattr(self, entry_name, widget)

        form_frame.columnconfigure(1, weight=1)
        form_frame.columnconfigure(3, weight=1)

        action_frame = ttk.Frame(main_frame, padding=(0, 5, 0, 10))
        action_frame.pack(fill=tk.X)

        self.add_button = ttk.Button(action_frame, text="登録", command=self.add_new_customer)
        self.add_button.pack(side=tk.LEFT, padx=5)

        # ### 変更点 ### 更新・削除ボタンのコメントアウトを解除し、初期状態を無効に
        self.update_button = ttk.Button(action_frame, text="更新", command=self.update_selected_customer, state=tk.DISABLED)
        self.update_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = ttk.Button(action_frame, text="削除", command=self.delete_selected_customer, state=tk.DISABLED)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(action_frame, text="フォームクリア", command=self.clear_form)
        self.clear_button.pack(side=tk.LEFT, padx=5)

        tree_frame = ttk.LabelFrame(main_frame, text="顧客一覧", padding="10")
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("customer_id", "customer_name", "contact_person_name", "phone_number", "email")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10, selectmode="browse") # ### 変更点 ### selectmode追加

        col_configs = [
            ("customer_id", "ID", 50, tk.CENTER),
            ("customer_name", "顧客名", 200, tk.W),
            ("contact_person_name", "担当者名", 150, tk.W),
            ("phone_number", "電話番号", 120, tk.W),
            ("email", "メールアドレス", 200, tk.W)
        ]
        for col_id, text, width, anchor in col_configs:
            self.tree.heading(col_id, text=text)
            self.tree.column(col_id, width=width, anchor=anchor, minwidth=width)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # ### 変更点 ### Treeviewで項目が選択されたときのイベントを設定
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def load_customers_to_treeview(self):
        self.selected_customer_id = None # ### 追加 ### 読み込み時に選択解除
        self.update_button.config(state=tk.DISABLED) # ### 追加 ### ボタンを無効化
        self.delete_button.config(state=tk.DISABLED) # ### 追加 ### ボタンを無効化
        for item in self.tree.get_children():
            self.tree.delete(item)
        customers_data = self.db_ops.get_all_customers()
        if customers_data:
            for customer_tuple in customers_data:
                display_values = (
                    customer_tuple[0], customer_tuple[1], customer_tuple[2],
                    customer_tuple[3], customer_tuple[4]
                )
                self.tree.insert("", tk.END, values=display_values, iid=customer_tuple[0]) # ### 変更点 ### iidにIDを設定

    def on_tree_select(self, event):
        selected_items = self.tree.selection() # イベント発生時の選択状態を取得
        # ### 変更点 ### selected_items の内容を常に表示する
        print(f"### デバッグ用プリント ### on_tree_select が呼び出されました。現在の選択アイテム: {selected_items}") 

        if not selected_items:
            print("### デバッグ用プリント ### 何も選択されていません。フォームをクリアします。(on_tree_select冒頭)")
            # ... (以降のクリア処理は変更なし) ...
            self.customer_name_entry.delete(0, tk.END)
            self.contact_person_entry.delete(0, tk.END)
            self.phone_entry.delete(0, tk.END)
            self.email_entry.delete(0, tk.END)
            self.address_entry.delete(0, tk.END)
            self.notes_text.delete("1.0", tk.END)
            self.selected_customer_id = None
            self.update_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)
            return

        selected_iid = selected_items[0]
        self.selected_customer_id = selected_iid
        print(f"### デバッグ用プリント ### 選択されたIID (customer_id): {self.selected_customer_id}")

        customer_data_tuple = self.db_ops.get_customer_by_id(self.selected_customer_id)
        print(f"### デバッグ用プリント ### データベースから取得した顧客データ: {customer_data_tuple}")

        if customer_data_tuple:
            # ### 修正箇所 スタート ###
            # self.clear_form() # ← この呼び出しを削除またはコメントアウト
            
            # 代わりに、各入力フィールドを直接クリアする
            self.customer_name_entry.delete(0, tk.END)
            self.contact_person_entry.delete(0, tk.END)
            self.phone_entry.delete(0, tk.END)
            self.email_entry.delete(0, tk.END)
            self.address_entry.delete(0, tk.END)
            self.notes_text.delete("1.0", tk.END)
            # ### 修正箇所 エンド ###
            
            print("### デバッグ用プリント ### フォームに値を設定します...")
            self.customer_name_entry.insert(0, customer_data_tuple[1] or "")
            self.contact_person_entry.insert(0, customer_data_tuple[2] or "")
            self.phone_entry.insert(0, customer_data_tuple[3] or "")
            self.email_entry.insert(0, customer_data_tuple[4] or "")
            self.address_entry.insert(0, customer_data_tuple[5] or "")
            self.notes_text.insert("1.0", customer_data_tuple[8] or "")
            print("### デバッグ用プリント ### フォームへの値設定完了。ボタンを有効化します。")

            self.update_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.NORMAL)
        else:
            messagebox.showwarning("エラー", f"顧客ID {self.selected_customer_id} の情報取得に失敗しました。")
            print(f"### デバッグ用プリント ### 顧客ID {self.selected_customer_id} の情報取得失敗。")
            # データ取得失敗時もフォームをクリアし、ボタンを無効化
            self.customer_name_entry.delete(0, tk.END)
            self.contact_person_entry.delete(0, tk.END)
            self.phone_entry.delete(0, tk.END)
            self.email_entry.delete(0, tk.END)
            self.address_entry.delete(0, tk.END)
            self.notes_text.delete("1.0", tk.END)
            self.update_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)
    def add_new_customer(self):
        # ... (変更なし) ...
        customer_name = self.customer_name_entry.get().strip()
        contact_person = self.contact_person_entry.get().strip()
        phone = self.phone_entry.get().strip()
        email = self.email_entry.get().strip()
        address = self.address_entry.get().strip()
        notes = self.notes_text.get("1.0", tk.END).strip()

        if not customer_name:
            messagebox.showerror("入力エラー", "顧客名は必須です。")
            return

        result = self.db_ops.add_customer(customer_name, contact_person, phone, email, address, notes)

        if isinstance(result, int): # 成功時 (IDが返る)
            messagebox.showinfo("成功", f"顧客「{customer_name}」を登録しました。(ID: {result})")
            self.clear_form()
            self.load_customers_to_treeview()
        elif result == "DUPLICATE_NAME":
            messagebox.showerror("登録エラー", f"顧客名「{customer_name}」は既に登録されています。")
        elif result == "INTEGRITY_ERROR":
            messagebox.showerror("登録エラー", "データベースの整合性エラーが発生しました。入力内容を確認してください。")
        elif result == "OTHER_DB_ERROR" or result is None: # Noneは接続エラー等の場合
            messagebox.showerror("登録エラー", "データベースエラーにより顧客情報の登録に失敗しました。")  
            

    def clear_form(self): # ### 変更点 ###
        self.customer_name_entry.delete(0, tk.END)
        self.contact_person_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)
        self.address_entry.delete(0, tk.END)
        self.notes_text.delete("1.0", tk.END)
        
        self.selected_customer_id = None # 選択IDをクリア
        if self.tree.selection(): # Treeviewで何か選択されていれば解除
            self.tree.selection_remove(self.tree.selection()[0])
        
        self.update_button.config(state=tk.DISABLED) # 更新ボタンを無効化
        self.delete_button.config(state=tk.DISABLED) # 削除ボタンを無効化
        self.customer_name_entry.focus() # 顧客名入力欄にフォーカスを戻す

    def update_selected_customer(self):
        if not self.selected_customer_id:
            messagebox.showwarning("未選択", "更新する顧客が選択されていません。")
            return

        # フォームから現在の入力値を取得
        customer_name = self.customer_name_entry.get().strip()
        contact_person = self.contact_person_entry.get().strip()
        phone = self.phone_entry.get().strip()
        email = self.email_entry.get().strip()
        address = self.address_entry.get().strip()
        notes = self.notes_text.get("1.0", tk.END).strip()

        if not customer_name:
            messagebox.showerror("入力エラー", "顧客名は必須です。")
            return

        confirm = messagebox.askyesno("更新確認", f"顧客ID {self.selected_customer_id} ({customer_name}) の情報を本当に更新しますか？")
        if not confirm:
            messagebox.showinfo("キャンセル", "更新はキャンセルされました。")
            return

        result = self.db_ops.update_customer(
            self.selected_customer_id, 
            customer_name, 
            contact_person, 
            phone, 
            email, 
            address, 
            notes
        )

        if result is True: # データベース操作関数が True を返したら成功
            messagebox.showinfo("成功", f"顧客ID {self.selected_customer_id} ({customer_name}) の情報を更新しました。")
            self.clear_form() 
            self.load_customers_to_treeview() 
        elif result == "DUPLICATE_NAME":
            messagebox.showerror("更新エラー", f"顧客名「{customer_name}」は既に他の顧客に使われています。別の名前に変更してください。")
        elif result == "NOT_FOUND":
            messagebox.showerror("更新エラー", f"更新対象の顧客 (ID: {self.selected_customer_id}) が見つかりませんでした。一覧を更新して再度お試しください。")
        elif result == "INTEGRITY_ERROR":
            messagebox.showerror("更新エラー", "データベースの整合性エラーが発生しました。入力内容を確認してください。")
        else: # CONNECTION_ERROR, OTHER_DB_ERROR など
            messagebox.showerror("更新エラー", f"顧客情報の更新に失敗しました。(エラータイプ: {result})")

# customer_management_window.py の中の delete_selected_customer メソッド
    def delete_selected_customer(self):
        if not self.selected_customer_id:
            messagebox.showwarning("未選択", "削除する顧客が選択されていません。")
            return
        
        # データベースから最新の顧客情報を取得して顧客名を表示する（任意）
        customer_info = self.db_ops.get_customer_by_id(self.selected_customer_id)
        customer_name_for_confirm = customer_info[1] if customer_info else f"ID: {self.selected_customer_id}"

        confirm_message = f"顧客「{customer_name_for_confirm}」(ID: {self.selected_customer_id}) の情報を本当に削除しますか？\n"
        confirm_message += "この操作は元に戻せません。\n"
        confirm_message += "（この顧客に関連する案件情報からは、この顧客への関連付けのみ解除されます）"

        confirm = messagebox.askyesno("削除確認", confirm_message)
        
        if confirm:
            result = self.db_ops.delete_customer(self.selected_customer_id)
            
            if result is True: # データベース操作関数が True を返したら成功
                messagebox.showinfo("成功", f"顧客「{customer_name_for_confirm}」(ID: {self.selected_customer_id}) の情報を削除しました。")
                self.clear_form() 
                self.load_customers_to_treeview() 
            elif result == "NOT_FOUND":
                messagebox.showerror("削除エラー", f"削除対象の顧客 (ID: {self.selected_customer_id}) が見つかりませんでした。一覧を更新して再度お試しください。")
            else: # CONNECTION_ERROR, OTHER_DB_ERROR など
                messagebox.showerror("削除エラー", f"顧客情報の削除に失敗しました。(エラータイプ: {result})")
        else:
            messagebox.showinfo("キャンセル", "削除はキャンセルされました。")

    def on_close(self):
        self.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    root.title("メインウィンドウ (テスト用)")
    def open_customer_window():
        customer_win = CustomerManagementWindow(root)
        customer_win.grab_set()
    open_button = ttk.Button(root, text="顧客管理を開く", command=open_customer_window)
    open_button.pack(padx=20, pady=20)
    root.mainloop()