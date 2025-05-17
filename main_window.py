import tkinter as tk
from tkinter import ttk # themed Tkinter widgets for a more modern look

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("木村塗装工業 業務管理システム")
        self.geometry("800x600") # ウィンドウサイズを適宜調整してください

        self._create_widgets()

    def _create_widgets(self):
        # --- ヘッダーフレーム ---
        header_frame = ttk.Frame(self, padding="10")
        header_frame.grid(row=0, column=0, columnspan=3, sticky="ew") # カラムスパンを3に変更

        # システムタイトル
        system_title_label = ttk.Label(header_frame, text="木村塗装工業 業務管理システム", font=("Arial", 16, "bold"))
        system_title_label.pack(side="left")

        # ログインユーザー名
        login_user_label = ttk.Label(header_frame, text="ログイン: 佐藤勝義", font=("Arial", 10))
        login_user_label.pack(side="right", padx=10) # 右側に配置

        # --- 通知エリア ---
        notification_frame = ttk.LabelFrame(self, text="通知", padding="10")
        # columnspanを2、stickyを"ewns"に変更。配置の調整のためrowspanも設定
        notification_frame.grid(row=1, column=0, columnspan=2, rowspan=2, padx=10, pady=10, sticky="ewns")

        # 仮の通知メッセージ
        notification_message = tk.Message(notification_frame, text="新しい見積依頼があります。\n〇〇様邸 外壁塗装工事の件、詳細確認をお願いします。", width=280, font=("Arial", 10))
        notification_message.pack(pady=5, fill="x", expand=True)
        # さらに通知を追加する場合
        # notification_message2 = tk.Message(notification_frame, text="資材Aの在庫が少なくなっています。", width=280, font=("Arial", 10))
        # notification_message2.pack(pady=5, fill="x", expand=True)


        # --- 機能ボタンフレーム ---
        button_frame = ttk.Frame(self, padding="10")
        button_frame.grid(row=1, column=2, padx=10, pady=10, sticky="n") # 通知エリアの右に配置

        # ボタンのスタイルを統一
        button_style = {"width": 15, "padding": 10}

        # 見積管理ボタン
        quote_button = ttk.Button(button_frame, text="見積管理", command=self.open_quote_management, **button_style)
        quote_button.pack(pady=5)

        # 工事管理ボタン
        construction_button = ttk.Button(button_frame, text="工事管理", command=self.open_construction_management, **button_style)
        construction_button.pack(pady=5)

        # 資材管理ボタン
        material_button = ttk.Button(button_frame, text="資材管理", command=self.open_material_management, **button_style)
        material_button.pack(pady=5)

        # 人員管理ボタン
        personnel_button = ttk.Button(button_frame, text="人員管理", command=self.open_personnel_management, **button_style)
        personnel_button.pack(pady=5)


        # --- カレンダーエリア ---
        calendar_frame = ttk.LabelFrame(self, text="カレンダー", padding="10")
        # columnspanを3に変更し、stickyを"ewns"に設定
        calendar_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="ewns")

        # カレンダー表示エリア（仮のラベル）
        # 実際のカレンダーウィジェットは後で導入します
        calendar_label = ttk.Label(calendar_frame, text="（ここにカレンダーが表示されます）", font=("Arial", 14), anchor="center")
        calendar_label.pack(expand=True, fill="both")

        # --- 行と列の伸縮設定 ---
        # ウィンドウリサイズ時にカレンダーエリアが広がるように設定
        self.grid_rowconfigure(3, weight=1) # カレンダーのある行
        self.grid_columnconfigure(0, weight=1) # 通知エリアのある列 (左側)
        self.grid_columnconfigure(1, weight=1) # 通知エリアを広げるため (左側)
        self.grid_columnconfigure(2, weight=0) # ボタンエリアのある列 (右側、固定幅)


    # --- ボタンが押されたときの処理（ダミー）---
    # これらは後で実際の機能に置き換えます
    def open_quote_management(self):
        print("見積管理画面を開きます (未実装)")

    def open_construction_management(self):
        print("工事管理画面を開きます (未実装)")

    def open_material_management(self):
        print("資材管理画面を開きます (未実装)")

    def open_personnel_management(self):
        print("人員管理画面を開きます (未実装)")


if __name__ == "__main__":
    app = Application()
    app.mainloop()