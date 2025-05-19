import tkinter as tk
from tkinter import ttk # themed Tkinter widgets for a more modern look
from tkinter import messagebox # ★★★ この行を追加 ★★★
# ★★★ QuotationListWindow と db_ops をインポート ★★★
from quotation_management_window import QuotationListWindow 
import database_operations as db_ops # データベース操作モジュールをインポート

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("木村塗装工業 業務管理システム")
        self.geometry("800x600")

        # ★★★ db_ops インスタンスを保持 ★★★
        # (実際のアプリケーションでは、ここでdb_opsを初期化するか、
        #  適切な場所でインスタンス化されたものを参照します)
        #  ここでは、直接インポートした db_ops モジュールそのものを属性として保持します。
        #  もし db_ops がクラスベースでインスタンスが必要な場合は、
        #  self.db_ops = db_ops.DatabaseOperations() のようにインスタンス化してください。
        #  現在の db_ops.py は関数ベースなので、モジュール自体を渡せばOKです。
        self.db_ops = db_ops

        self._create_widgets()

    def _create_widgets(self):
        # --- ヘッダーフレーム ---
        header_frame = ttk.Frame(self, padding="10")
        header_frame.grid(row=0, column=0, columnspan=3, sticky="ew")

        system_title_label = ttk.Label(header_frame, text="木村塗装工業 業務管理システム", font=("Arial", 16, "bold"))
        system_title_label.pack(side="left")

        login_user_label = ttk.Label(header_frame, text="ログイン: 佐藤勝義", font=("Arial", 10))
        login_user_label.pack(side="right", padx=10)

        # --- 通知エリア ---
        notification_frame = ttk.LabelFrame(self, text="通知", padding="10")
        notification_frame.grid(row=1, column=0, columnspan=2, rowspan=2, padx=10, pady=10, sticky="ewns")

        notification_message = tk.Message(notification_frame, text="新しい見積依頼があります。\n〇〇様邸 外壁塗装工事の件、詳細確認をお願いします。", width=280, font=("Arial", 10))
        notification_message.pack(pady=5, fill="x", expand=True)

        # --- 機能ボタンフレーム ---
        button_frame = ttk.Frame(self, padding="10")
        button_frame.grid(row=1, column=2, padx=10, pady=10, sticky="n")

        button_style = {"width": 15, "padding": 10}

        # 見積管理ボタンのコマンドを変更
        quote_button = ttk.Button(button_frame, text="見積管理", command=self.open_quotation_list_window, **button_style) # ★コマンド変更
        quote_button.pack(pady=5)

        construction_button = ttk.Button(button_frame, text="工事管理", command=self.open_construction_management, **button_style)
        construction_button.pack(pady=5)

        material_button = ttk.Button(button_frame, text="資材管理", command=self.open_material_management, **button_style)
        material_button.pack(pady=5)

        personnel_button = ttk.Button(button_frame, text="人員管理", command=self.open_personnel_management, **button_style)
        personnel_button.pack(pady=5)

        # --- カレンダーエリア ---
        calendar_frame = ttk.LabelFrame(self, text="カレンダー", padding="10")
        calendar_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="ewns")

        calendar_label = ttk.Label(calendar_frame, text="（ここにカレンダーが表示されます）", font=("Arial", 14), anchor="center")
        calendar_label.pack(expand=True, fill="both")

        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)

    # open_quote_management メソッドを open_quotation_list_window に変更し、実装
    def open_quotation_list_window(self): # ★メソッド名変更と実装
        # master として self (Application インスタンス) を渡す
        # QuotationListWindow の __init__ で master.db_ops を参照するため、
        # Application インスタンスが db_ops 属性を持っている必要がある。
        if not hasattr(self, 'db_ops'):
             messagebox.showerror("エラー", "データベース操作モジュールが初期化されていません。")
             return
        
        quotation_list_win = QuotationListWindow(self)
        # quotation_list_win.grab_set() # 必要に応じてモーダルにする（今回は不要かもしれません）

    def open_construction_management(self):
        print("工事管理画面を開きます (未実装)") #

    def open_material_management(self):
        print("資材管理画面を開きます (未実装)") #

    def open_personnel_management(self):
        print("人員管理画面を開きます (未実装)") #

if __name__ == "__main__":
    app = Application()
    app.mainloop()