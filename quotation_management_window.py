# quotation_management_window.py

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import database_operations as db_ops # データベース操作関数をインポート
from datetime import datetime # ### この行を追加してください ###

class QuotationManagementWindow(tk.Toplevel):
    def __init__(self, master): # parent ではなく master を受け取るのが一般的ですが、どちらでも構いません
        super().__init__(master) # super().__init__(parent) でも可
        self.title("見積管理")    # ウィンドウタイトルを「見積管理」に設定
        self.geometry("1200x750") 
        self.db_ops = db_ops      # db_ops インスタンスを保持
        self.selected_quotation_id = None 
        self.selected_project_id_for_new_quotation = None # この行も必要に応じて
        self._preparing_new_quotation_flag = False  # ★ 新規見積準備中フラグ (以前の修正で導入)
        self._is_editing_header = False             # ★ ヘッダー編集中フラグ (今回の提案で導入)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._create_widgets() # ウィジェット作成メソッドを呼び出し
        self.load_quotation_headers_to_treeview()

    def _create_widgets(self):
        # --- メインフレーム (左右に分割) ---
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- 左側：見積ヘッダー一覧フレーム ---
        headers_list_frame = ttk.LabelFrame(main_pane, text="見積一覧", padding="5")
        main_pane.add(headers_list_frame, weight=1) # weightで幅の比率を指定
        self._create_headers_treeview(headers_list_frame)

        # --- 右側：詳細表示フレーム (ヘッダー情報と明細情報) ---
        details_pane = ttk.PanedWindow(main_pane, orient=tk.VERTICAL)
        main_pane.add(details_pane, weight=3) # weightで幅の比率を指定

        # 右側上部：選択された見積ヘッダーの詳細フォーム
        header_form_frame = ttk.LabelFrame(details_pane, text="見積ヘッダー詳細", padding="5")
        details_pane.add(header_form_frame, weight=2) # weightで高さの比率を指定
        self._create_header_detail_form(header_form_frame)

        # 右側下部：選択された見積ヘッダーの明細一覧
        items_list_frame = ttk.LabelFrame(details_pane, text="見積明細一覧", padding="5")
        details_pane.add(items_list_frame, weight=3) # weightで高さの比率を指定
        # ### 追加: 明細操作ボタン用フレーム ###
        self.item_action_frame = ttk.Frame(items_list_frame)
        self.item_action_frame.pack(fill=tk.X, pady=(0, 5)) # Treeviewの上に配置
        self._create_item_action_buttons(self.item_action_frame) # 明細操作ボタン作成メソッド呼び出し
        
        self._create_items_treeview(items_list_frame) # Treeview作成メソッド呼び出し
        # --- スタイル設定 (オプション) ---
        style = ttk.Style(self) # self を渡して、このウィンドウにスタイルを適用
        
        # ### Treeviewのフォントと行の高さを調整 ###
        # お使いの環境で見やすいフォント名とサイズを指定してください。
        # rowheight はピクセル単位の目安です。フォントサイズと合わせて調整します。
        tree_font_family = "メイリオ" # または "Yu Gothic UI", "MS Gothic", "Arial" など
        tree_font_size = 10        # 少し小さめなら9、標準なら10か11
        tree_row_height = tree_font_size + 10 # フォントサイズ + 適度な余白 (例: 20 や 25)

        style.configure("Treeview", font=(tree_font_family, tree_font_size), rowheight=tree_row_height) 
        style.configure("Treeview.Heading", font=(tree_font_family, tree_font_size, "bold"))
        # ### ここまで ###        
        # --- 最下部：操作ボタンフレーム ---
        # このボタンは、ヘッダー一覧に対する操作か、明細に対する操作かで配置を考える
        # まずはヘッダー一覧に対する「新規作成」ボタンなどを配置
        global_action_frame = ttk.Frame(self, padding="5")
        global_action_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(0,5))
        self._create_global_action_buttons(global_action_frame)

    # quotation_management_window.py に _create_item_action_buttons メソッドを追加

# 正しいコード（以前の提案通り）
    def _create_item_action_buttons(self, parent_frame):
        self.add_item_button = ttk.Button(parent_frame, text="明細追加", command=self.open_add_item_dialog, state=tk.DISABLED)
        self.add_item_button.pack(side=tk.LEFT, padx=5)

        self.edit_item_button = ttk.Button(parent_frame, text="明細編集", command=self.open_edit_item_dialog, state=tk.DISABLED)
        self.edit_item_button.pack(side=tk.LEFT, padx=5)

        self.delete_item_button = ttk.Button(parent_frame, text="明細削除", command=self.delete_selected_item, state=tk.DISABLED)
        self.delete_item_button.pack(side=tk.LEFT, padx=5)

    def _create_headers_treeview(self, parent_frame):
        # 見積ヘッダー一覧を表示するttk.Treeviewを配置
        
        # 表示するカラムを定義 (get_all_quotations で取得する情報を元に選択)
        # (0:q.quotation_id, 1:q.quotation_code, 2:q.quotation_date,
        #  3:q.project_id, 4:p.original_project_code, 5:p.original_project_name,
        #  6:q.quotation_staff_id, 7:e.staff_name,
        #  8:q.customer_name_at_quote, 9:q.project_name_at_quote,
        #  10:q.total_amount_inclusive_tax, 11:q.status, 12:q.validity_period_notes,
        #  13:q.updated_at)
        
        columns = (
            "quotation_id", "quotation_code", "quotation_date", "customer_name_at_quote", 
            "project_name_at_quote", "total_amount_inclusive_tax", "status", "staff_name"
        )
        self.headers_tree = ttk.Treeview(parent_frame, columns=columns, show="headings", height=10) # 高さは適宜調整

        # 各列のヘッダーテキストと幅などを設定
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

        # スクロールバーの追加
        scrollbar_y = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.headers_tree.yview)
        self.headers_tree.configure(yscrollcommand=scrollbar_y.set)

        # pack を使って配置 (parent_frame は main_pane.add で追加されているので、その中で pack や grid を使う)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.headers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Treeview選択時のイベント設定 (詳細は後ほど)
        self.headers_tree.bind("<<TreeviewSelect>>", self.on_header_tree_select)

    # quotation_management_window.py の _create_header_detail_form メソッドを実装

    def _create_header_detail_form(self, parent_frame):
        # 選択された見積ヘッダーの詳細を表示/編集するフォーム
        self.header_form_entries = {} # ### この行を追加してください ### Entryウィジェットを保持する
        # 各情報を表示するためのStringVarを用意
        self.detail_vars = {
            "quotation_code": tk.StringVar(), "quotation_date": tk.StringVar(),
            "customer_name_at_quote": tk.StringVar(), "project_name_at_quote": tk.StringVar(),
            "site_address_at_quote": tk.StringVar(), "construction_period_notes": tk.StringVar(),
            "total_amount_exclusive_tax": tk.StringVar(), "tax_rate": tk.StringVar(),
            "tax_amount": tk.StringVar(), "total_amount_inclusive_tax": tk.StringVar(),
            "validity_period_notes": tk.StringVar(), "payment_terms_notes": tk.StringVar(),
            "status": tk.StringVar(), "staff_name": tk.StringVar(),
            "original_project_code": tk.StringVar(), "remarks": tk.StringVar(),
            # 内部管理用 (フォームには直接表示しないが、保持しておくと便利なもの)
            "project_id": tk.StringVar(), "quotation_staff_id": tk.StringVar()
        }

        # ラベルテキストと対応するキーのリスト (表示順を制御)
        # キーはself.detail_varsのキー名と一致させる
        form_layout = [
            ("見積番号:", "quotation_code", 0, 0), ("見積日:", "quotation_date", 0, 2),
            ("宛名:", "customer_name_at_quote", 1, 0), ("件名:", "project_name_at_quote", 1, 2),
            ("案件ID (必須):", "project_id", 2, 0), 
            ("元案件コード:", "original_project_code", 2, 2),
            ("見積担当者ID:", "quotation_staff_id", 3, 0), 
            ("見積担当者名:", "staff_name", 3, 2),
            # ### 修正点: 行番号を修正 ###
            ("現場住所:", "site_address_at_quote", 4, 0, 3), # 行を4に変更
            ("工期:", "construction_period_notes", 5, 0, 3), # 行を5に変更
            ("有効期限:", "validity_period_notes", 6, 0), ("支払条件:", "payment_terms_notes", 6, 2), # 行を6に変更
            ("状況:", "status", 7, 0), ("税率(%):", "tax_rate", 7, 2), # 行を7に変更
            ("税抜合計:", "total_amount_exclusive_tax", 8, 0),  # 行を8に変更
            ("消費税額:", "tax_amount", 8, 2), # 行を8に変更
            ("見積金額(税込):", "total_amount_inclusive_tax", 9, 0), # 行を9に変更
            ("備考:", "remarks", 10, 0, 3) # 行を10に変更
        ]
        
        for label_text, key, r, c, *span in form_layout:
            ttk.Label(parent_frame, text=label_text).grid(row=r, column=c, padx=5, pady=2, sticky=tk.W)
            
            entry_width = 35 if len(span) > 0 and span[0] == 3 else 18 # columnspanで幅調整
            
            if key == "remarks" or key == "construction_period_notes" or \
               key == "validity_period_notes" or key == "payment_terms_notes" or \
               key == "site_address_at_quote": # 長いテキスト入力の可能性があるフィールド
                # (備考など複数行にしたい場合は tk.Text を使うが、ここではEntryで統一)
                entry = ttk.Entry(parent_frame, textvariable=self.detail_vars[key], width=entry_width)
            elif key == "status": # 状況はCombobox
                # (Comboboxの実装は後で _create_form_fields から移すか、ここで再定義)
                # 今回はEntryで進め、後でComboboxに置き換えることを検討します。
                # または、status_options をクラス変数で持つなど。
                # ここでは仮にEntryとしておきます。実際の値セット時にComboboxを検討。
                 entry = ttk.Entry(parent_frame, textvariable=self.detail_vars[key], width=entry_width, state="readonly") # 初期は読み取り専用
            elif key in ["total_amount_exclusive_tax", "tax_amount", "total_amount_inclusive_tax", "staff_name", "original_project_code"]:
                # これらは基本的に表示専用か、自動計算されるもの
                entry = ttk.Entry(parent_frame, textvariable=self.detail_vars[key], width=entry_width, state="readonly")
            else:
                entry = ttk.Entry(parent_frame, textvariable=self.detail_vars[key], width=entry_width)
            
            entry.grid(row=r, column=c + 1, padx=5, pady=2, sticky=tk.EW, columnspan=(span[0] if span else 1))
            self.header_form_entries[key] = entry # Entryウィジェットを辞書に保存

        parent_frame.columnconfigure(1, weight=1)
        parent_frame.columnconfigure(3, weight=1)
        # 必要に応じて他の列のweightも設定
        # TODO: 将来的には編集用にEntryウィジェットなどと切り替えられるようにする

    def start_header_edit_mode(self):
        if self.selected_quotation_id is None:
            messagebox.showwarning("未選択", "編集する見積ヘッダーが選択されていません。", parent=self)
            self.lift()
            return

        self._is_editing_header = True # ヘッダー編集中フラグを立てる

        # フォームの入力欄を編集可能にする (読み取り専用のフィールドは除く)
        editable_fields = [
            "quotation_code", "quotation_date", "customer_name_at_quote", 
            "project_name_at_quote", "site_address_at_quote", 
            "construction_period_notes", "tax_rate", 
            "validity_period_notes", "payment_terms_notes", 
            "status", "remarks", "project_id", "quotation_staff_id"
        ]
        # 注意: project_id や quotation_staff_id は直接編集させるか、
        #       別途選択ダイアログなどを用意するか検討が必要です。
        #       ここでは一旦、直接編集可能としています。
        #       total_amount_exclusive_tax, tax_amount, total_amount_inclusive_tax,
        #       staff_name, original_project_code は readonly のままが良いでしょう。

        for key, entry_widget in self.header_form_entries.items():
            if key in editable_fields:
                # 'status' はComboboxに変更する可能性があるため、その場合は扱いを調整
                if key == "status" and isinstance(entry_widget, ttk.Combobox):
                     entry_widget.config(state="readonly") # Comboboxはreadonlyで選択可能
                else:
                    entry_widget.config(state="normal")
            else:
                entry_widget.config(state="readonly") # 編集対象外はreadonlyを維持

        if hasattr(self, 'save_quotation_button'):
            self.save_quotation_button.config(state="normal")
        if hasattr(self, 'start_edit_header_button'):
            self.start_edit_header_button.config(state="disabled") # 編集開始ボタンは一旦無効化
        if hasattr(self, 'new_quotation_button'):
            self.new_quotation_button.config(state="disabled") # 新規作成ボタンも編集中は無効化 (推奨)
        if hasattr(self, 'delete_quotation_button'): 
            self.delete_quotation_button.config(state="disabled") # ★追加: ヘッダー編集中は削除不可

        
        # 必要であれば、編集をキャンセルするボタンを有効化する
        # (例: self.cancel_edit_header_button.config(state="normal"))

        # 編集開始時に、最初の編集可能フィールドにフォーカスを当てる (例: 見積番号)
        if "quotation_code" in self.header_form_entries:
            self.header_form_entries["quotation_code"].focus_set()
        
        print("### DEBUG: Entered header edit mode.")
        self.lift()


    def _create_items_treeview(self, parent_frame):
        # ### 変更点: 表示カラムの変更 ###
        columns = (
            "no", "name", "specification", "quantity", # item_id, display_order を削除し、no を追加
            "unit", "unit_price", "amount", "remarks"
        )
        self.items_tree = ttk.Treeview(parent_frame, columns=columns, show="headings", height=10)

        # 各列のヘッダーテキストと幅などを設定
        self.items_tree.heading("no", text="No.") # ### 追加 ###
        self.items_tree.column("no", width=40, anchor=tk.CENTER) # ### 追加 ###
        self.items_tree.heading("name", text="名称") 
        self.items_tree.heading("specification", text="仕様"); self.items_tree.column("specification", width=200)
        self.items_tree.heading("quantity", text="数量"); self.items_tree.column("quantity", width=60, anchor=tk.E)
        self.items_tree.heading("unit", text="単位"); self.items_tree.column("unit", width=60, anchor=tk.CENTER)
        self.items_tree.heading("unit_price", text="単価"); self.items_tree.column("unit_price", width=90, anchor=tk.E)
        self.items_tree.heading("amount", text="金額"); self.items_tree.column("amount", width=90, anchor=tk.E)
        self.items_tree.heading("remarks", text="備考"); self.items_tree.column("remarks", width=150)

        # スクロールバーの作成
        scrollbar_y = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        scrollbar_x = ttk.Scrollbar(parent_frame, orient=tk.HORIZONTAL, command=self.items_tree.xview)
        self.items_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # --- pack を使った配置に修正 ---
        # self.item_action_frame は parent_frame (items_list_frame) の中で既に pack されています。
        # それに合わせて、items_tree とスクロールバーも pack で配置します。

        # 縦スクロールバーを右側に配置
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        # 横スクロールバーを下部に配置 (Treeviewよりも後にpackすることで、Treeviewの下に来るようにします)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        # Treeviewを残りスペース全体に配置 (scrollbar_y の左、scrollbar_x の上)
        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 明細Treeview選択時のイベント設定
        self.items_tree.bind("<<TreeviewSelect>>", self.on_item_tree_select)

    def _create_global_action_buttons(self, parent_frame):
        self.new_quotation_button = ttk.Button(parent_frame, text="新規見積作成", command=self.prepare_new_quotation)
        self.new_quotation_button.pack(side=tk.LEFT, padx=5, pady=5)

        # 「ヘッダー編集開始」ボタンを追加
        self.start_edit_header_button = ttk.Button(parent_frame, text="ヘッダー編集開始", command=self.start_header_edit_mode, state=tk.DISABLED)
        self.start_edit_header_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.save_quotation_button = ttk.Button(parent_frame, text="見積保存", command=self.save_quotation_data, state=tk.DISABLED)
        self.save_quotation_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 「見積削除」ボタンを追加
        self.delete_quotation_button = ttk.Button(parent_frame, text="見積削除", command=self.confirm_delete_quotation, state=tk.DISABLED)
        self.delete_quotation_button.pack(side=tk.LEFT, padx=5, pady=5)

    def confirm_delete_quotation(self):
        if self.selected_quotation_id is None:
            messagebox.showwarning("未選択", "削除する見積ヘッダーが選択されていません。", parent=self)
            self.lift()
            return

        # 削除対象の見積情報を取得して確認メッセージに表示（より親切にするため）
        quotation_code_to_confirm = ""
        if hasattr(self, 'headers_tree') and self.headers_tree.exists(str(self.selected_quotation_id)):
            try:
                item_values = self.headers_tree.item(str(self.selected_quotation_id), 'values')
                # headers_tree の "quotation_code" は2番目(インデックス1)のカラムと想定
                # columns = ("quotation_id", "quotation_code", ...)
                if len(item_values) > 1:
                    quotation_code_to_confirm = item_values[1]
            except Exception as e:
                print(f"Error fetching quotation code from tree for confirmation: {e}")

        confirm_message = f"見積「{quotation_code_to_confirm}」(ID: {self.selected_quotation_id}) を本当に削除しますか？\n関連する全ての明細も削除されます。"

        if not messagebox.askyesno("見積削除確認", confirm_message, parent=self):
            self.lift()
            return

        # データベースから見積ヘッダーと関連明細を削除
        delete_result = self.db_ops.delete_quotation(self.selected_quotation_id)

        if delete_result is True:
            messagebox.showinfo("削除成功", f"見積 (ID: {self.selected_quotation_id}) を削除しました。", parent=self)

            # 見積ヘッダー一覧を再読み込み
            self.load_quotation_headers_to_treeview()

            # フォームクリアとボタン状態の更新は load_quotation_headers_to_treeview の後、
            # on_header_tree_select が選択なしの状態で呼ばれることで行われることを期待。
            # もし on_header_tree_select が呼ばれない、または不十分な場合は明示的にクリア/状態設定。
            # 通常、load_quotation_headers_to_treeview で全削除・再挿入すると選択は解除される。
            # 強制的に選択なしイベントを発生させたい場合は、一度unbindし、selection_clearし、bindし直すなどの方法もあるが、
            # まずはload後の on_header_tree_select の動作に期待。
            # 必要であれば、ここで self.prepare_new_quotation() を呼び出すか、
            # on_header_tree_select(None) のような形で手動トリガーを検討。
            # 今回は、on_header_tree_select が選択なしで呼ばれることを前提とする。
            # (もし呼ばれない場合は、load_quotation_headers_to_treeview の最後に self.headers_tree.selection_clear() を追加し、
            #  さらに on_header_tree_select(None) を呼ぶなど。)

            # 念のため、主要な状態をリセット
            self.selected_quotation_id = None
            for key in self.detail_vars: # ヘッダーフォームクリア
                self.detail_vars[key].set("")
            if hasattr(self, 'items_tree'): # 明細ツリークリア
                for item in self.items_tree.get_children():
                    self.items_tree.delete(item)

            # ボタン類の状態を初期化 (on_header_tree_select で処理される部分と重複する可能性あり)
            if hasattr(self, 'save_quotation_button'): self.save_quotation_button.config(state=tk.DISABLED)
            if hasattr(self, 'start_edit_header_button'): self.start_edit_header_button.config(state=tk.DISABLED)
            if hasattr(self, 'delete_quotation_button'): self.delete_quotation_button.config(state=tk.DISABLED) # 自分自身も無効化
            if hasattr(self, 'add_item_button'): self.add_item_button.config(state=tk.DISABLED)
            if hasattr(self, 'edit_item_button'): self.edit_item_button.config(state=tk.DISABLED)
            if hasattr(self, 'delete_item_button'): self.delete_item_button.config(state=tk.DISABLED)

 # TODO: 必要であれば他のグローバルボタン (印刷など) もここに追加

    def prepare_new_quotation(self):
        # ★ もしヘッダー編集中なら、それを解除する
        if getattr(self, '_is_editing_header', False):
            self._is_editing_header = False
            # 編集開始ボタンを有効に戻す (on_header_tree_selectで処理されるが、ここでも念のため)
            if hasattr(self, 'start_edit_header_button'):
                 self.start_edit_header_button.config(state=tk.DISABLED) # 新規準備中は編集開始は不可
      
        self._preparing_new_quotation_flag = True # ★ フラグを立てる
        if hasattr(self, 'headers_tree'):
            self.headers_tree.unbind("<<TreeviewSelect>>") # ### 変更点: メソッドの最初に移動 ###

        self.selected_quotation_id = None 

        if hasattr(self, 'headers_tree') and self.headers_tree.selection():
            self.headers_tree.selection_remove(self.headers_tree.selection())

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
        self.detail_vars["tax_rate"].set("10") # ### 追加: 税率のデフォルトを10 (%) として設定 ###

        if "project_id" in self.header_form_entries:
             self.header_form_entries["project_id"].config(state="normal")
        if "quotation_staff_id" in self.header_form_entries:
             self.header_form_entries["quotation_staff_id"].config(state="normal")

        if "quotation_code" in self.header_form_entries: 
            self.header_form_entries["quotation_code"].focus_set() 

        if hasattr(self, 'save_quotation_button'): 
            self.save_quotation_button.config(state="normal") 

        # --- メソッドの最後にイベントを再バインド ---
        if hasattr(self, 'headers_tree'):
            self.headers_tree.bind("<<TreeviewSelect>>", self.on_header_tree_select) # ### 変更点: メソッドの最後に移動 ###

# quotation_management_window.py の QuotationManagementWindow クラス内

    def save_quotation_data(self):
        # --- ヘッダー編集モードでの更新処理 ---
        if self.selected_quotation_id is not None and getattr(self, '_is_editing_header', False):
            try:
                quotation_id_to_update = self.selected_quotation_id

                # フォームから編集されたデータを取得
                project_id_str = self.detail_vars["project_id"].get().strip()
                quotation_staff_id_str = self.detail_vars["quotation_staff_id"].get().strip()
                quotation_code = self.detail_vars["quotation_code"].get().strip()
                quotation_date = self.detail_vars["quotation_date"].get().strip()
                customer_name_at_quote = self.detail_vars["customer_name_at_quote"].get().strip()
                project_name_at_quote = self.detail_vars["project_name_at_quote"].get().strip()
                site_address_at_quote = self.detail_vars["site_address_at_quote"].get().strip()
                construction_period_notes = self.detail_vars["construction_period_notes"].get().strip()
                tax_rate_str = self.detail_vars["tax_rate"].get().strip().replace('%', '') # %を除去
                validity_period_notes = self.detail_vars["validity_period_notes"].get().strip()
                payment_terms_notes = self.detail_vars["payment_terms_notes"].get().strip()
                status = self.detail_vars["status"].get().strip()
                remarks = self.detail_vars["remarks"].get().strip()

                # 合計金額関連は readonly のため、現在の detail_vars からそのまま取得 (カンマ除去)
                total_amount_exclusive_tax_str = self.detail_vars["total_amount_exclusive_tax"].get().replace(',', '')
                tax_amount_str = self.detail_vars["tax_amount"].get().replace(',', '')
                total_amount_inclusive_tax_str = self.detail_vars["total_amount_inclusive_tax"].get().replace(',', '')

                # --- 入力値のバリデーション ---
                if not project_id_str:
                    messagebox.showerror("入力エラー", "元となる案件IDは必須です。", parent=self)
                    self.header_form_entries.get("project_id", {}).focus_set() # .getで安全にアクセス
                    return
                if not quotation_code:
                    messagebox.showerror("入力エラー", "見積番号は必須です。", parent=self)
                    self.header_form_entries["quotation_code"].focus_set()
                    return
                if not quotation_date:
                    messagebox.showerror("入力エラー", "見積日は必須です。", parent=self)
                    self.header_form_entries["quotation_date"].focus_set()
                    return
                if not customer_name_at_quote:
                    messagebox.showerror("入力エラー", "宛名は必須です。", parent=self)
                    self.header_form_entries["customer_name_at_quote"].focus_set()
                    return
                if not project_name_at_quote:
                    messagebox.showerror("入力エラー", "件名は必須です。", parent=self)
                    self.header_form_entries["project_name_at_quote"].focus_set()
                    return
                if not status: # 状況も必須とする場合
                    messagebox.showerror("入力エラー", "状況は必須です。", parent=self)
                    self.header_form_entries["status"].focus_set()
                    return


                # --- データ型の変換 ---
                project_id = int(project_id_str)
                quotation_staff_id = int(quotation_staff_id_str) if quotation_staff_id_str.isdigit() else None # isdigitで数値か確認
                
                tax_rate_for_db = 0.0
                if tax_rate_str:
                    try:
                        tax_rate_for_db = float(tax_rate_str) / 100.0
                    except ValueError:
                        messagebox.showerror("入力エラー", "税率には数値を入力してください。", parent=self)
                        self.header_form_entries["tax_rate"].focus_set()
                        return
                
                total_amount_exclusive_tax = int(total_amount_exclusive_tax_str) if total_amount_exclusive_tax_str.isdigit() else 0
                tax_amount = int(tax_amount_str) if tax_amount_str.isdigit() else 0
                total_amount_inclusive_tax = int(total_amount_inclusive_tax_str) if total_amount_inclusive_tax_str.isdigit() else 0
                
                # データベースを更新
                update_result = self.db_ops.update_quotation(
                    quotation_id=quotation_id_to_update,
                    project_id=project_id, 
                    quotation_staff_id=quotation_staff_id, 
                    quotation_code=quotation_code, 
                    quotation_date=quotation_date,
                    customer_name_at_quote=customer_name_at_quote, 
                    project_name_at_quote=project_name_at_quote, 
                    site_address_at_quote=site_address_at_quote,
                    construction_period_notes=construction_period_notes, 
                    total_amount_exclusive_tax=total_amount_exclusive_tax,
                    tax_rate=tax_rate_for_db,
                    tax_amount=tax_amount,
                    total_amount_inclusive_tax=total_amount_inclusive_tax,
                    validity_period_notes=validity_period_notes,
                    payment_terms_notes=payment_terms_notes, 
                    status=status, 
                    remarks=remarks
                )

                if update_result is True:
                    messagebox.showinfo("更新成功", f"見積「{quotation_code}」を更新しました。", parent=self)
                    
                    current_selection_id = str(self.selected_quotation_id) # Treeviewのiidは文字列の場合がある
                    self.load_quotation_headers_to_treeview() 
                    
                    if current_selection_id and hasattr(self, 'headers_tree') and self.headers_tree.exists(current_selection_id):
                        self.headers_tree.selection_set(current_selection_id)
                        self.headers_tree.focus(current_selection_id)
                        # on_header_tree_select がトリガーされ、フォームのreadonly化とボタン状態更新が行われる
                    else:
                        # もし再選択に失敗した場合は、新規準備状態に戻すか、エラー表示など
                        self.prepare_new_quotation() 

                    self._is_editing_header = False 
                    # new_quotation_button は on_header_tree_select で通常状態に戻るはず
                    # start_edit_header_button も on_header_tree_select で通常状態に戻るはず
                    # save_quotation_button も on_header_tree_select で無効になるはず

                elif update_result == "DUPLICATE_QUOTATION_CODE":
                    messagebox.showerror("更新エラー", f"見積番号「{quotation_code}」は既に他の見積で使用されています。", parent=self)
                    self.header_form_entries["quotation_code"].focus_set()
                elif update_result == "NOT_FOUND":
                     messagebox.showerror("更新エラー", f"更新対象の見積 (ID: {quotation_id_to_update}) が見つかりませんでした。", parent=self)
                elif update_result == "NOT_NULL_VIOLATION":
                     messagebox.showerror("更新エラー", "必須項目が入力されていません。", parent=self)
                elif update_result == "FK_CONSTRAINT_FAILED":
                     messagebox.showerror("更新エラー", "指定された案件IDまたは見積担当者IDが存在しません。", parent=self)
                else: # INTEGRITY_ERROR, CONNECTION_ERROR, OTHER_DB_ERROR など
                    messagebox.showerror("更新エラー", f"データベースエラーにより見積情報の更新に失敗しました。({update_result})", parent=self)

            except ValueError as ve: # 主に int() や float() の変換エラー
                messagebox.showerror("入力エラー", f"数値項目の入力値が正しくありません。\n詳細: {ve}", parent=self)
            except Exception as e:
                messagebox.showerror("システムエラー", f"予期せぬエラーが発生しました: {e}", parent=self)
            finally:
                self.lift()

        # --- 新規見積ヘッダーの保存処理 ---
        elif self.selected_quotation_id is None and not getattr(self, '_is_editing_header', False):
            try:
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
                
                # 新規作成時は、これらの合計金額は明細がないため0か、手入力（ただしフォームではreadonlyなので通常0）
                # recalculate_and_update_quotation_totals で再計算されることを期待するが、
                # add_quotation 関数に渡す初期値としては0を設定しておく。
                # フォームの readonly の値を使う場合（通常は"0"のはず）
                total_amount_exclusive_tax_str = self.detail_vars["total_amount_exclusive_tax"].get().replace(',', '')
                # tax_amount_str = self.detail_vars["tax_amount"].get().replace(',', '') # 新規時は計算するので不要
                # total_amount_inclusive_tax_str = self.detail_vars["total_amount_inclusive_tax"].get().replace(',', '') # 新規時は計算するので不要

                # バリデーション (更新時と同様)
                if not project_id_str:
                    messagebox.showerror("入力エラー", "元となる案件IDは必須です。", parent=self); return
                if not quotation_code:
                    messagebox.showerror("入力エラー", "見積番号は必須です。", parent=self); self.header_form_entries["quotation_code"].focus_set(); return
                if not quotation_date:
                    messagebox.showerror("入力エラー", "見積日は必須です。", parent=self); self.header_form_entries["quotation_date"].focus_set(); return
                if not customer_name_at_quote:
                    messagebox.showerror("入力エラー", "宛名は必須です。", parent=self); self.header_form_entries["customer_name_at_quote"].focus_set(); return
                if not project_name_at_quote:
                    messagebox.showerror("入力エラー", "件名は必須です。", parent=self); self.header_form_entries["project_name_at_quote"].focus_set(); return
                if not status: # 状況も必須とする場合
                    messagebox.showerror("入力エラー", "状況は必須です。", parent=self); self.header_form_entries["status"].focus_set(); return

                # データ型変換 (更新時と同様)
                project_id = int(project_id_str)
                quotation_staff_id = int(quotation_staff_id_str) if quotation_staff_id_str.isdigit() else None
                
                total_amount_exclusive_tax_for_db = int(total_amount_exclusive_tax_str) if total_amount_exclusive_tax_str.isdigit() else 0
                
                tax_rate_for_db = 0.0
                if tax_rate_str:
                    try:
                        tax_rate_for_db = float(tax_rate_str) / 100.0
                    except ValueError:
                        messagebox.showerror("入力エラー", "税率には数値を入力してください。", parent=self); self.header_form_entries["tax_rate"].focus_set(); return
                
                # 新規登録時は、明細がないため、税額と税込合計は税抜と税率から計算
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
                    new_quotation_id = result
                    messagebox.showinfo("登録成功", f"見積「{quotation_code}」を登録しました。(ID: {new_quotation_id})", parent=self)
                    self.load_quotation_headers_to_treeview() 
                    
                    # 新規登録したアイテムを選択状態にする
                    if hasattr(self, 'headers_tree') and self.headers_tree.exists(str(new_quotation_id)):
                        self.headers_tree.selection_set(str(new_quotation_id))
                        self.headers_tree.focus(str(new_quotation_id))
                        # on_header_tree_select が呼ばれ、フォームがreadonlyになり、ボタン状態も更新される
                    else: # 念のため、再選択できなかった場合は新規準備状態へ
                        self.prepare_new_quotation()
                
                elif result == "DUPLICATE_QUOTATION_CODE":
                    messagebox.showerror("登録エラー", f"見積番号「{quotation_code}」は既に登録されています。", parent=self)
                    self.header_form_entries["quotation_code"].focus_set()
                elif result == "NOT_NULL_VIOLATION":
                    messagebox.showerror("登録エラー", "必須項目が入力されていません。", parent=self)
                elif result == "FK_CONSTRAINT_FAILED":
                    messagebox.showerror("登録エラー", "指定された案件IDまたは見積担当者IDが存在しません。", parent=self)
                else: 
                    messagebox.showerror("登録エラー", f"データベースエラーにより見積情報の登録に失敗しました。({result})", parent=self)

            except ValueError as ve:
                messagebox.showerror("入力エラー", f"数値項目（案件ID、担当者ID、金額、税率など）の入力値が正しくありません。\n詳細: {ve}", parent=self)
            except Exception as e:
                messagebox.showerror("システムエラー", f"予期せぬエラーが発生しました: {e}", parent=self)
            finally:
                self.lift()
        else:
            messagebox.showwarning("不正な操作", "保存処理を実行するための条件が満たされていません。\n(選択IDなし、または編集中ではない可能性があります)", parent=self)
            self.lift()

    def load_quotation_headers_to_treeview(self):
        """データベースから見積ヘッダー情報を読み込み、左側のTreeviewに表示する"""
        # 詳細フォームや明細リストをクリアするなどの初期化処理もここで行う (後ほど)
        # self.clear_header_detail_form() 
        # self.clear_items_treeview()
        # self.selected_quotation_id = None
        # (関連ボタンの無効化も)

        # Treeviewの既存のアイテムをすべて削除
        if hasattr(self, 'headers_tree'): # Treeviewが作成済みか確認
            for item in self.headers_tree.get_children():
                self.headers_tree.delete(item)
        else:
            return # Treeviewがまだなければ何もしない

        quotation_headers_data = self.db_ops.get_all_quotations()
        
        if quotation_headers_data:
            for q_header_tuple in quotation_headers_data:
                # get_all_quotations() が返すタプルの内容とインデックス:
                # (0:q.quotation_id, 1:q.quotation_code, 2:q.quotation_date,
                #  ... 4:p.original_project_code, 5:p.original_project_name, ...
                #  7:e.staff_name, 8:q.customer_name_at_quote, 9:q.project_name_at_quote,
                #  10:q.total_amount_inclusive_tax, 11:q.status, ...)

                # Treeviewに表示する値を選択して整形
                # columns = ("quotation_id", "quotation_code", "quotation_date", "customer_name_at_quote", 
                #            "project_name_at_quote", "total_amount_inclusive_tax", "status", "staff_name")
                
                total_amount_display = f"{q_header_tuple[10]:,}" if q_header_tuple[10] is not None else ""

                display_values = (
                    q_header_tuple[0],  # quotation_id
                    q_header_tuple[1],  # quotation_code
                    q_header_tuple[2],  # quotation_date
                    q_header_tuple[8],  # customer_name_at_quote
                    q_header_tuple[9],  # project_name_at_quote
                    total_amount_display, # total_amount_inclusive_tax (桁区切り)
                    q_header_tuple[11], # status
                    q_header_tuple[7] or ""  # staff_name (Noneの場合は空文字)
                )
                # Treeviewにアイテムを挿入 (iid に quotation_id を設定)
                self.headers_tree.insert("", tk.END, values=display_values, iid=q_header_tuple[0])
        # else:
            # messagebox.showinfo("情報", "登録されている見積情報はありません。") # 必要に応じて
    def on_header_tree_select(self, event):
        if getattr(self, '_preparing_new_quotation_flag', False):
            self._preparing_new_quotation_flag = False
            return 

        # ★ ヘッダー編集中だった場合は、編集モードを解除する (選択変更によるキャンセル扱い)
        if getattr(self, '_is_editing_header', False):
            self._is_editing_header = False
            # 保存ボタンなどを元に戻す処理もここで行うか、
            # フォーム読み込み後に状態設定する部分でまとめて行う。
            # ここではフラグのリセットのみに留め、後続の処理でフォームはreadonlyになる。
            if hasattr(self, 'save_quotation_button'):
                self.save_quotation_button.config(state="disabled")
            if hasattr(self, 'new_quotation_button'):
                 self.new_quotation_button.config(state="normal")


        selected_items = self.headers_tree.selection()

        if not selected_items:
            self.selected_quotation_id = None
            for key in self.detail_vars:
                self.detail_vars[key].set("")
            
            if hasattr(self, 'items_tree') and self.items_tree: 
                self.load_selected_quotation_items(None)
            
            if hasattr(self, 'save_quotation_button'): 
                self.save_quotation_button.config(state=tk.DISABLED)
            if hasattr(self, 'add_item_button'):
                self.add_item_button.config(state=tk.DISABLED)
            if hasattr(self, 'edit_item_button'):
                self.edit_item_button.config(state=tk.DISABLED)
            if hasattr(self, 'delete_item_button'):
                self.delete_item_button.config(state=tk.DISABLED)
            if hasattr(self, 'start_edit_header_button'): # ★追加
                self.start_edit_header_button.config(state=tk.DISABLED)
            return
        
        selected_iid = selected_items[0] 
        self.selected_quotation_id = selected_iid
        
        header_data = self.db_ops.get_quotation_by_id(self.selected_quotation_id)
 
        if header_data:
            # フォームのStringVarに値をセット
            self.detail_vars["quotation_code"].set(header_data[5] or "")
            self.detail_vars["quotation_date"].set(header_data[6] or "")
            self.detail_vars["customer_name_at_quote"].set(header_data[7] or "")
            self.detail_vars["project_name_at_quote"].set(header_data[8] or "")
            self.detail_vars["site_address_at_quote"].set(header_data[9] or "")
            self.detail_vars["construction_period_notes"].set(header_data[10] or "")
            self.detail_vars["total_amount_exclusive_tax"].set(f"{header_data[11]:,}" if header_data[11] is not None else "")
            self.detail_vars["tax_rate"].set(f"{header_data[12]*100:.0f}" if header_data[12] is not None else "") # %なしで表示し入力可能に
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

            # フォームエントリーを読み取り専用に設定 (編集モードへの移行は別途ボタンで行う想定)
            for key, entry_widget in self.header_form_entries.items():
                entry_widget.config(state="readonly") # 基本的に全てreadonly
            
            # 明細一覧を読み込む
            self.load_selected_quotation_items(self.selected_quotation_id)
            
            # ボタンの状態更新
            if hasattr(self, 'save_quotation_button'): 
                if not getattr(self, '_is_editing_header', False):
                    self.save_quotation_button.config(state=tk.DISABLED)
            if hasattr(self, 'add_item_button'): 
                self.add_item_button.config(state=tk.NORMAL) # 見積ヘッダー選択時は明細追加を可能に
            if hasattr(self, 'start_edit_header_button'): # ★追加
                self.start_edit_header_button.config(state=tk.NORMAL) # ヘッダー選択時は編集開始ボタンを有効化
            if hasattr(self, 'delete_quotation_button'): self.delete_quotation_button.config(state=tk.NORMAL) # ★追加: 選択時は有効
            # edit_item_button, delete_item_button は on_item_tree_select で制御


            # TODO: 「ヘッダー編集開始」ボタンなどを有効化
            # TODO: 「ヘッダー削除」ボタンなども有効化
            
        else: # header_data が None の場合 (DBからの取得失敗など)
            messagebox.showwarning("データ取得エラー", f"見積ID {self.selected_quotation_id} のヘッダー情報取得に失敗しました。", parent=self)
            for key in self.detail_vars:
                self.detail_vars[key].set("") # 空にする
            for entry_widget in self.header_form_entries.values():
                entry_widget.config(state="normal")
                entry_widget.delete(0, tk.END) 
                entry_widget.config(state="disabled")
            self.load_selected_quotation_items(None)
            # ボタンの状態更新
            if hasattr(self, 'save_quotation_button'): self.save_quotation_button.config(state=tk.DISABLED)
            if hasattr(self, 'add_item_button'): self.add_item_button.config(state=tk.DISABLED)
            if hasattr(self, 'start_edit_header_button'): self.start_edit_header_button.config(state=tk.DISABLED)
            if hasattr(self, 'delete_quotation_button'): self.delete_quotation_button.config(state=tk.DISABLED) # ★追加



    def _create_items_treeview(self, parent_frame):
        # ### 変更点: 表示カラムの変更 ###
        columns = (
            "no", "name", "specification", "quantity", # item_id, display_order を削除し、no を追加
            "unit", "unit_price", "amount", "remarks"
        )
        self.items_tree = ttk.Treeview(parent_frame, columns=columns, show="headings", height=10)

        # 各列のヘッダーテキストと幅などを設定
        # self.items_tree.heading("item_id", text="明細ID") # 削除
        # self.items_tree.column("item_id", width=50, anchor=tk.CENTER) # 削除

        self.items_tree.heading("no", text="No.") # ### 追加 ###
        self.items_tree.column("no", width=40, anchor=tk.CENTER) # ### 追加 ###
        
        # self.items_tree.heading("display_order", text="順") # 削除
        # self.items_tree.column("display_order", width=40, anchor=tk.CENTER) # 削除

        self.items_tree.heading("name", text="名称")
        # ... (以降のカラム設定は変更なし、ただしインデックスは変わらないので注意) ...
        self.items_tree.column("name", width=200)
        self.items_tree.heading("specification", text="仕様")
        self.items_tree.column("specification", width=200)
        self.items_tree.heading("quantity", text="数量")
        self.items_tree.column("quantity", width=60, anchor=tk.E)
        self.items_tree.heading("unit", text="単位")
        self.items_tree.column("unit", width=60, anchor=tk.CENTER)
        self.items_tree.heading("unit_price", text="単価")
        self.items_tree.column("unit_price", width=90, anchor=tk.E)
        self.items_tree.heading("amount", text="金額")
        self.items_tree.column("amount", width=90, anchor=tk.E)
        self.items_tree.heading("remarks", text="備考")
        self.items_tree.column("remarks", width=150)
        # スクロールバーの作成
        scrollbar_y = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        scrollbar_x = ttk.Scrollbar(parent_frame, orient=tk.HORIZONTAL, command=self.items_tree.xview)
        self.items_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # --- pack を使った配置に修正 ---
        # 縦スクロールバーを右側に配置
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        # 横スクロールバーを下部に配置
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        # Treeviewを残りスペース全体に配置
        self.items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 明細Treeview選択時のイベント設定
        self.items_tree.bind("<<TreeviewSelect>>", self.on_item_tree_select)

# quotation_management_window.py の load_selected_quotation_items メソッドを修正
    def load_selected_quotation_items(self, quotation_id):
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)

        if quotation_id is None:
            return

        items_data = self.db_ops.get_items_for_quotation(quotation_id) # DBからは display_order も取得されるが使わない
        
        if items_data:
            for index, item_tuple in enumerate(items_data): # ### enumerate でインデックスを取得 ###
                # get_items_for_quotation が返すタプルのインデックス:
                # (0:item_id, 1:quotation_id, 2:display_order, 3:name, 4:specification, 
                #  5:quantity, 6:unit, 7:unit_price, 8:amount, 9:remarks, ...)

                quantity_display = f"{item_tuple[5]:.2f}" if item_tuple[5] is not None else ""
                unit_price_display = f"{item_tuple[7]:,}" if item_tuple[7] is not None else ""
                amount_display = f"{item_tuple[8]:,}" if item_tuple[8] is not None else ""

                display_values = (
                    index + 1,            # ### No. (1から始まる連番) ###
                    item_tuple[3],        # name
                    item_tuple[4] or "",  # specification
                    quantity_display,     # quantity
                    item_tuple[6] or "",  # unit
                    unit_price_display,   # unit_price
                    amount_display,       # amount
                    item_tuple[9] or ""   # remarks
                )
                # iid は item_id (DBの主キー) を使うことで、後で選択行の特定に利用
                self.items_tree.insert("", tk.END, values=display_values, iid=item_tuple[0]) 
    def on_item_tree_select(self, event):
        # 現時点では具体的な処理は未実装でも、メソッドが存在することが重要
        # ここで選択された明細アイテムを取得し、
        # それに応じて「明細編集」「明細削除」ボタンの状態を更新するロジックを将来的に追加します。
        selected_items = self.items_tree.selection()
        if selected_items:
            # item_id = selected_items[0] # 選択されたアイテムのID (iid)
            # ここで edit_item_button や delete_item_button の state を tk.NORMAL にするなど
            print(f"Item selected: {selected_items[0]}") # デバッグ用に選択されたアイテムを表示
            if hasattr(self, 'edit_item_button'):
                 self.edit_item_button.config(state=tk.NORMAL)
            if hasattr(self, 'delete_item_button'):
                 self.delete_item_button.config(state=tk.NORMAL)
        else:
            if hasattr(self, 'edit_item_button'):
                 self.edit_item_button.config(state=tk.DISABLED)
            if hasattr(self, 'delete_item_button'):
                 self.delete_item_button.config(state=tk.DISABLED)
        pass # pass は処理がないことを示す仮の記述です。必要に応じて処理を記述します。

    def open_add_item_dialog(self):
        if self.selected_quotation_id is None:
            messagebox.showwarning("未選択", "明細を追加する見積ヘッダーが選択されていません。", parent=self)
            return
        
        dialog = QuotationItemDialog(self, title="見積明細 - 新規追加", quotation_id=self.selected_quotation_id)
        
        if dialog.result: # ダイアログで「保存」が押され、データが入力された場合
            item_data = dialog.result
            # データベースに新しい明細を追加
            new_item_id_or_error = self.db_ops.add_quotation_item(
                quotation_id=item_data["quotation_id"], # dialogから渡されたquotation_id
                name=item_data["name"],
                specification=item_data["specification"],
                quantity=item_data["quantity"],
                unit=item_data["unit"],
                unit_price=item_data["unit_price"],
                amount=item_data["amount"], # 計算済み
                remarks=item_data["remarks"]
            )

            if isinstance(new_item_id_or_error, int):
                messagebox.showinfo("成功", "見積明細を追加しました。", parent=self)
                self.load_selected_quotation_items(self.selected_quotation_id) # 明細一覧を更新
                self.recalculate_and_update_quotation_totals(self.selected_quotation_id) # ### この行のメソッド名を確認 ###
            else:
                messagebox.showerror("エラー", f"明細の追加に失敗しました: {new_item_id_or_error}", parent=self)
        self.lift()

    def recalculate_and_update_quotation_totals(self, quotation_id):
        print(f"### DEBUG: recalculate_totals CALLED for quotation_id: {quotation_id}")
        if quotation_id is None:
            # フォームの合計金額関連をクリアまたはデフォルト（例: 0）に設定
            self.detail_vars["total_amount_exclusive_tax"].set("0")
            self.detail_vars["tax_amount"].set("0")
            self.detail_vars["total_amount_inclusive_tax"].set("0")
            self.detail_vars["tax_rate"].set("0%") # または ""
            print("### DEBUG: quotation_id is None, totals cleared on form.")
            return

        items = self.db_ops.get_items_for_quotation(quotation_id)
        print(f"### DEBUG: Fetched items for total calculation: {items}")
        
        total_exclusive = 0
        if items:
            for item_tuple in items:
                # amount はインデックス 8 
                # (item_id, q_id, disp_order, name, spec, qty, unit, unit_price, amount, rem, cr_at, up_at)
                item_amount = item_tuple[8] if item_tuple[8] is not None else 0
                total_exclusive += item_amount
                print(f"### DEBUG: item_amount: {item_amount}, current total_exclusive: {total_exclusive}")
        
        print(f"### DEBUG: Final total_exclusive calculated: {total_exclusive}")
        
        # DBから最新の見積ヘッダー情報を取得して、そこから税率を使用
        current_header_data_for_tax_info = self.db_ops.get_quotation_by_id(quotation_id)
        if not current_header_data_for_tax_info:
            messagebox.showerror("エラー", "合計計算のための見積ヘッダー情報取得に失敗しました。", parent=self)
            return

        # get_quotation_by_id が返すタプルのインデックス (再確認):
        # (..., 12:q.tax_rate, ...)
        db_tax_rate_value = current_header_data_for_tax_info[12] if current_header_data_for_tax_info[12] is not None else 0.0
        
        current_tax_rate_for_calc = db_tax_rate_value # DBの税率で計算

        tax_amount = int(total_exclusive * current_tax_rate_for_calc) # ### 消費税の小数点以下は切り捨て ###
        total_inclusive = total_exclusive + tax_amount
        print(f"### DEBUG: tax_rate: {current_tax_rate_for_calc}, tax_amount: {tax_amount}, total_inclusive: {total_inclusive}")

        # フォームのStringVarを更新
        self.detail_vars["total_amount_exclusive_tax"].set(f"{total_exclusive:,}")
        self.detail_vars["tax_rate"].set(f"{current_tax_rate_for_calc*100:.0f}%") # DBの税率を再表示
        self.detail_vars["tax_amount"].set(f"{tax_amount:,}")
        self.detail_vars["total_amount_inclusive_tax"].set(f"{total_inclusive:,}")
        print("### DEBUG: Form totals updated.")

        # データベースのquotationsテーブルも更新
        # current_header_data_for_tax_info を使って他のフィールドも埋める
        if current_header_data_for_tax_info: # 変数名を修正
            update_result = self.db_ops.update_quotation(
                quotation_id=quotation_id,
                project_id=current_header_data_for_tax_info[1],
                quotation_staff_id=current_header_data_for_tax_info[3],
                quotation_code=current_header_data_for_tax_info[5],
                quotation_date=current_header_data_for_tax_info[6],
                customer_name_at_quote=current_header_data_for_tax_info[7],
                project_name_at_quote=current_header_data_for_tax_info[8],
                site_address_at_quote=current_header_data_for_tax_info[9],
                construction_period_notes=current_header_data_for_tax_info[10],
                total_amount_exclusive_tax=total_exclusive,       # 更新
                tax_rate=current_tax_rate_for_calc,               # 更新
                tax_amount=tax_amount,                            # 更新
                total_amount_inclusive_tax=total_inclusive,       # 更新
                validity_period_notes=current_header_data_for_tax_info[15],
                payment_terms_notes=current_header_data_for_tax_info[16],
                status=current_header_data_for_tax_info[17], 
                remarks=current_header_data_for_tax_info[18]
            )
            if update_result is True:
                print(f"### DEBUG: Quotation ID {quotation_id} totals updated in DB.")
                # self.load_quotation_headers_to_treeview() # ← この行をコメントアウトまたは削除

                # headers_tree の該当行の表示を更新する
                if hasattr(self, 'headers_tree') and self.selected_quotation_id:
                    try:
                        # 現在のTreeviewの行から表示されている値を取得
                        current_values = list(self.headers_tree.item(self.selected_quotation_id, 'values'))
                        # 更新された合計金額(税込)を取得 (フォームのStringVarから)
                        new_total_inclusive_tax_str = self.detail_vars["total_amount_inclusive_tax"].get()
                        
                        # headers_treeのカラム定義を確認し、"total_amount_inclusive_tax" が何番目のカラムか特定
                        # columns = ("quotation_id", "quotation_code", "quotation_date", "customer_name_at_quote", 
                        #            "project_name_at_quote", "total_amount_inclusive_tax", "status", "staff_name")
                        # 上記定義だと、"total_amount_inclusive_tax" は 5番目 (0から数えて) のカラム
                        total_amount_column_index = 5 # このインデックスは実際のカラム定義に合わせてください

                        if len(current_values) > total_amount_column_index:
                            current_values[total_amount_column_index] = new_total_inclusive_tax_str
                            self.headers_tree.item(self.selected_quotation_id, values=tuple(current_values))
                            print(f"### DEBUG: Updated headers_tree row for ID {self.selected_quotation_id} with new total.")
                        else:
                            print(f"### WARNING: Could not update headers_tree row. Index out of bounds or values issue.")
                    except Exception as e:
                        print(f"### ERROR: Failed to update headers_tree row: {e}")
                # 他に一覧表示されていて更新が必要な項目があれば同様に更新
            else:
                messagebox.showerror("エラー", f"見積合計金額のDB更新に失敗しました: {update_result}", parent=self)
                print(f"### DEBUG: DB update failed for totals: {update_result}")

    def open_edit_item_dialog(self):
        selected_item_refs = self.items_tree.selection()
        if not selected_item_refs:
            messagebox.showwarning("未選択", "編集する明細が選択されていません。", parent=self)
            self.lift() # ダイアログが他のウィンドウの後ろに隠れるのを防ぐ
            return

        selected_item_id = selected_item_refs[0] # iid が item_id になっているはず

        # データベースから選択された明細の現在のデータを取得
        item_to_edit = self.db_ops.get_quotation_item_by_id(selected_item_id)

        if not item_to_edit:
            messagebox.showerror("エラー", f"選択された明細 (ID: {selected_item_id}) のデータ取得に失敗しました。", parent=self)
            self.lift()
            return

        # QuotationItemDialog を編集モードで開く
        # item_data に取得した明細データを渡し、quotation_id も渡す
        dialog = QuotationItemDialog(
            self, 
            title="見積明細 - 編集", 
            item_data=item_to_edit, 
            quotation_id=self.selected_quotation_id # 現在のヘッダーのID
        )

        if dialog.result: # ダイアログで「保存」が押された場合
            edited_item_data = dialog.result 
            # dialog.result には item_id も含まれているはず (QuotationItemDialog の on_save で設定)
            
            # display_order はダイアログで編集していないので、元の値をそのまま使う
            # item_to_edit 辞書から display_order を取得
            current_display_order = item_to_edit.get("display_order") 
            # もし display_order も編集可能にするなら、dialog.result に含める必要がある

            update_success_or_error = self.db_ops.update_quotation_item(
                item_id=edited_item_data["item_id"], # dialog.result から item_id を取得
                display_order=current_display_order, # 元の display_order を使用
                name=edited_item_data["name"],
                specification=edited_item_data["specification"],
                quantity=edited_item_data["quantity"],
                unit=edited_item_data["unit"],
                unit_price=edited_item_data["unit_price"],
                amount=edited_item_data["amount"], # dialog.result で計算済み
                remarks=edited_item_data["remarks"]
            )

            if update_success_or_error is True:
                messagebox.showinfo("成功", "見積明細を更新しました。", parent=self)
                self.load_selected_quotation_items(self.selected_quotation_id) # 明細一覧を再読み込み
                self.recalculate_and_update_quotation_totals(self.selected_quotation_id) # 合計金額を再計算・更新
            else:
                messagebox.showerror("エラー", f"明細の更新に失敗しました: {update_success_or_error}", parent=self)
        
        self.lift() # メインウィンドウを前面に表示し直す


    def delete_selected_item(self):
        selected_item_refs = self.items_tree.selection() # items_tree から選択中のアイテムを取得
        if not selected_item_refs:
            messagebox.showwarning("未選択", "削除する明細が選択されていません。", parent=self)
            self.lift()
            return

        selected_item_id = selected_item_refs[0] # iid が item_id になっているはず

        # ユーザーに削除確認
        # 選択されたアイテムの情報を少し表示して確認を促すとより親切です。
        # 例えば、item_id から名称などを取得してメッセージに含めるなど。
        # ここでは item_id のみで確認します。
        item_values = self.items_tree.item(selected_item_id, 'values')
        item_name_to_confirm = item_values[1] if len(item_values) > 1 else f"ID {selected_item_id}" # "name" カラムが2番目(インデックス1)と想定

        confirm_message = f"明細「{item_name_to_confirm}」(ID: {selected_item_id}) を本当に削除しますか？"
        if not messagebox.askyesno("削除確認", confirm_message, parent=self):
            self.lift()
            return

        # データベースから明細を削除
        delete_result = self.db_ops.delete_quotation_item(selected_item_id)

        if delete_result is True:
            messagebox.showinfo("成功", f"明細 (ID: {selected_item_id}) を削除しました。", parent=self)
            # 明細一覧を再読み込みして表示を更新
            self.load_selected_quotation_items(self.selected_quotation_id)
            # 見積もり全体の合計金額を再計算・DB更新・フォーム表示更新
            self.recalculate_and_update_quotation_totals(self.selected_quotation_id)
            
            # 削除後、明細編集・削除ボタンを非アクティブにする
            # (load_selected_quotation_items の後、選択がクリアされるか、
            #  on_item_tree_select が適切に呼ばれていれば自動的に更新されるはずですが、念のため)
            if hasattr(self, 'edit_item_button'):
                self.edit_item_button.config(state=tk.DISABLED)
            if hasattr(self, 'delete_item_button'):
                self.delete_item_button.config(state=tk.DISABLED)
        elif delete_result == "NOT_FOUND":
            messagebox.showerror("エラー", f"削除対象の明細 (ID: {selected_item_id}) が見つかりませんでした。", parent=self)
        else: # CONNECTION_ERROR や OTHER_DB_ERROR など
            messagebox.showerror("エラー", f"明細の削除に失敗しました: {delete_result}", parent=self)
        
        self.lift()

    def on_close(self):
        self.destroy()
# quotation_management_window.py の末尾など、クラスの外に新しいクラスとして定義

class QuotationItemDialog(tk.Toplevel):
    def __init__(self, parent, title="見積明細入力", item_data=None, quotation_id=None): # item_data は編集時に使用
        super().__init__(parent)
        self.transient(parent) 
        self.title(title)
        self.parent = parent 
        self.result = None   
        self.item_data = item_data 
        self.quotation_id = quotation_id 
        self._preparing_new_quotation_flag = False # 新規見積準備中フラグを追加

        self.resizable(False, False)

        # --- 入力フィールドフレーム ---
        form_frame = ttk.Frame(self, padding="10")
        form_frame.pack(expand=True, fill=tk.BOTH)

        # --- 入力フィールド定義 ---
        # (表示順, 名称, 仕様, 数量, 単位, 単価, 備考)
        fields = {
            # "display_order": {"label": "表示順:", "row": 0, "col": 0, "width": 10, "type": "entry"}, # ### 削除 ###
            "name": {"label": "名称 (必須):", "row": 0, "col": 0, "width": 40, "type": "entry"}, # rowを0に変更
            "specification": {"label": "仕様:", "row": 1, "col": 0, "width": 40, "type": "text", "height": 3}, # rowを1に変更
            "quantity": {"label": "数量:", "row": 2, "col": 0, "width": 10, "type": "entry"}, # rowを2に変更
            "unit": {"label": "単位:", "row": 2, "col": 2, "width": 10, "type": "entry"}, # rowを2に変更
            "unit_price": {"label": "単価:", "row": 3, "col": 0, "width": 15, "type": "entry"}, # rowを3に変更
            "remarks": {"label": "備考:", "row": 4, "col": 0, "width": 40, "type": "text", "height": 3} # rowを4に変更
        }

        self.entries = {} # 入力ウィジェットを保持する辞書
        self.string_vars = {} # StringVarを保持する辞書 (Entry用)

        for key, field_info in fields.items():
            ttk.Label(form_frame, text=field_info["label"]).grid(
                row=field_info["row"], column=field_info["col"], padx=5, pady=3, sticky=tk.NW if field_info["type"] == "text" else tk.W
            )
            if field_info["type"] == "entry":
                self.string_vars[key] = tk.StringVar()
                entry = ttk.Entry(form_frame, textvariable=self.string_vars[key], width=field_info["width"])
                entry.grid(row=field_info["row"], column=field_info["col"] + 1, padx=5, pady=3, sticky=tk.EW, 
                           columnspan=3 if field_info["col"] == 0 and field_info.get("type") != "text" and key not in ["display_order", "quantity", "unit_price"] else 1) # 名称などは幅広に
                self.entries[key] = entry
            elif field_info["type"] == "text":
                text_widget = tk.Text(form_frame, width=field_info["width"], height=field_info["height"])
                text_widget.grid(row=field_info["row"], column=field_info["col"] + 1, padx=5, pady=3, sticky=tk.NSEW, columnspan=3)
                self.entries[key] = text_widget
        
        form_frame.columnconfigure(1, weight=1) # Entry/Textがある列を広げる
        form_frame.columnconfigure(3, weight=1) # 右側のEntryがある列も広げる (単位用など)


        # --- ボタンフレーム ---
        button_frame = ttk.Frame(self, padding=(10, 5, 10, 10)) # 上のpaddingを少し調整
        button_frame.pack(fill=tk.X, side=tk.BOTTOM) # 下に配置

        ttk.Button(button_frame, text="キャンセル", command=self.on_cancel).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="保存", command=self.on_save).pack(side=tk.RIGHT, padx=5)
        
        # 編集モードなら既存データをフォームにセット (今回は新規追加なのでこの部分はまだ使わない)
        # 編集モードなら既存データをフォームにセット
        if self.item_data:
            # self.item_data は get_quotation_item_by_id から返された辞書を想定
            self.title(title if title else "見積明細 - 編集") # 編集時はタイトルも変更 (任意)

            # 各StringVarに値をセット
            if "name" in self.string_vars and "name" in self.item_data:
                self.string_vars["name"].set(self.item_data.get("name", ""))
            
            # quantity, unit, unit_price は数値かもしれないので文字列に変換してセット
            if "quantity" in self.string_vars and "quantity" in self.item_data:
                self.string_vars["quantity"].set(str(self.item_data.get("quantity", "")))
            
            if "unit" in self.string_vars and "unit" in self.item_data:
                self.string_vars["unit"].set(self.item_data.get("unit", ""))

            if "unit_price" in self.string_vars and "unit_price" in self.item_data:
                self.string_vars["unit_price"].set(str(self.item_data.get("unit_price", "")))

            # Textウィジェットに値をセット
            if "specification" in self.entries and "specification" in self.item_data:
                self.entries["specification"].delete("1.0", tk.END) # 既存の内容をクリア
                self.entries["specification"].insert("1.0", self.item_data.get("specification", ""))
            
            if "remarks" in self.entries and "remarks" in self.item_data:
                self.entries["remarks"].delete("1.0", tk.END) # 既存の内容をクリア
                self.entries["remarks"].insert("1.0", self.item_data.get("remarks", ""))
            
            # display_order はダイアログで編集しないので、ここではセット不要
            # self.string_vars["display_order"].set(self.item_data.get("display_order", "")) # ← この行は不要

        self.entries["name"].focus_set() # 初期フォーカスを名称に
        
        self.geometry("") 
        self.update_idletasks() # ウィジェット配置後のサイズを計算させる
        # 親ウィンドウの中央付近に表示 (少しオフセット)
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
            messagebox.showerror("入力エラー", "表示順、数量、単価には有効な数値を入力してください。", parent=self)
            return

        amount = int(quantity * unit_price) # 金額を計算 (整数に丸め)

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
        
        if self.item_data and "item_id" in self.item_data: # 編集モードの場合
            self.result["item_id"] = self.item_data["item_id"]
            
        self.destroy()

    def on_cancel(self):
        self.destroy()

# このファイル単体でテスト実行するためのコード
if __name__ == '__main__':
    root = tk.Tk()
    root.title("メインウィンドウ (テスト用)")
    
    def open_quotation_window():
        if not hasattr(root, 'db_ops'): 
            root.db_ops = db_ops 
        quotation_win = QuotationManagementWindow(root)
        quotation_win.grab_set() 
    
    open_button = ttk.Button(root, text="見積管理を開く", command=open_quotation_window)
    open_button.pack(padx=20, pady=20)
    
    root.mainloop()