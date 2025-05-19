graph TD
    A["QuotationManagementWindow 起動"] --> B["初期化処理 (init)"]
    B --> C["ウィンドウ設定 (タイトル, サイズ)"]
    B --> D["DatabaseOperations インスタンス生成"]
    B --> E["UI部品作成 (create_widgets)"]
    E --> E1["案件名ドロップダウン作成"]
    E --> E2["顧客名ドロップダウン作成"]
    E --> E3["金額入力欄など作成"]
    E --> E4["追加/更新/削除/クリアボタン作成"]
    E --> E5["見積もり一覧リストボックス作成"]
    E --> E6["見積もり詳細表示エリア作成"]
    B --> F["初期データ読み込み"]
    F --> G["案件情報読み込み (load_projects)"]
    G --> G1["DBから案件取得"]
    G1 --> G2["案件ドロップダウンに設定"]
    F --> H["顧客情報読み込み (load_customers)"]
    H --> H1["DBから顧客取得"]
    H1 --> H2["顧客ドロップダウンに設定"]
    F --> I["見積もり一覧読み込み (load_quotations)"]
    I --> I1["DBから見積もり取得"]
    I1 --> I2["見積もり一覧リストボックスに表示"]
    I2 --> J["ユーザー操作待機"]

    J --> K["操作: 見積もり追加ボタン クリック"]
    K -- はい --> L["入力値取得 (add_quotation)"]
    L --> M["DBに見積もり情報保存"]
    M --> I

    J --> N["操作: 見積もり更新ボタン クリック"]
    N -- はい --> O["選択見積もりIDと入力値取得 (update_quotation)"]
    O --> P["DBの見積もり情報更新"]
    P --> I

    J --> Q["操作: 見積もり削除ボタン クリック"]
    Q -- はい --> R["選択見積もりID取得 (delete_quotation)"]
    R --> S["DBから見積もり情報削除"]
    S --> I

    J --> T["操作: クリアボタン クリック"]
    T -- はい --> U["入力欄クリア (clear_entries)"]
    U --> U1["詳細表示エリアクリア"]
    U1 --> J

    J --> V["操作: 一覧から見積もり選択"]
    V -- はい --> W["選択見積もり情報取得 (on_quotation_select)"]
    W --> X["入力欄に情報表示"]
    W --> Y["詳細表示エリアに情報表示 (show_quotation_details)"]
    Y --> J

    subgraph DB ["データベース (SQLite)"]
        direction LR
        DB_Projects["案件テーブル"]
        DB_Customers["顧客テーブル"]
        DB_Quotations["見積もりテーブル"]
    end

    G1 --> DB_Projects
    H1 --> DB_Customers
    I1 --> DB_Quotations
    M --> DB_Quotations
    P --> DB_Quotations
    S --> DB_Quotations
    Y --> DB_Quotations

    classDef default fill:#f9f,stroke:#333,stroke-width:2px
    classDef process fill:#ccf,stroke:#333,stroke-width:2px
    classDef db fill:#cfc,stroke:#333,stroke-width:2px
    classDef io fill:#fcc,stroke:#333,stroke-width:2px

    class A,B,C,D,E,F,J process
    class E1,E2,E3,E4,E5,E6 process
    class G,H,I process
    class G1,G2,H1,H2,I1,I2 process
    class K,N,Q,T,V io
    class L,M,O,P,R,S,U,U1,W,X,Y process
    class DB_Projects,DB_Customers,DB_Quotations db