# test_data_loader.py (エラー修正版2)

import database_operations as db_ops
from datetime import datetime, timedelta
import random

def load_test_data():
    print("テストデータのロードを開始します...")
    print("注意: 実行前に komuten_kanri.db を削除し、database_setup.py を実行してください。")

    def random_date(start_year=2023, end_year=2025, can_be_none=False, none_probability=0.2):
        if can_be_none and random.random() < none_probability:
            return None
        year = random.randint(start_year, end_year)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        return datetime(year, month, day).strftime("%Y-%m-%d")

    # --- 1. 顧客データの追加 ---
    # (変更なし)
    customers_to_add = [
        {"customer_name": "株式会社 東京ホームズ", "contact_person_name": "渡辺 健一", "phone_number": "03-1234-5678", "email": "watanabe@tokyo-homes.com", "address": "東京都千代田区丸の内1-1-1", "notes": "大手不動産"},
        {"customer_name": "神奈川リフォームサービス", "contact_person_name": "鈴木 良治", "phone_number": "045-987-6543", "email": "suzuki@kanagawa-reform.jp", "address": "神奈川県横浜市西区みなとみらい2-2-1", "notes": "リピーター"},
        {"customer_name": "埼玉ハウジング株式会社", "contact_person_name": "高橋 学", "phone_number": "048-888-1111", "email": "takahashi@saitama-housing.com", "address": "埼玉県さいたま市浦和区高砂3-1-4", "notes": "公共事業案件あり"},
        {"customer_name": "千葉建設工業", "contact_person_name": "伊藤 純", "phone_number": "043-222-3333", "email": "ito@chiba-kensetsu.co.jp", "address": "千葉県千葉市美浜区豊砂1-1", "notes": "地域密着型"},
        {"customer_name": "山田太郎様邸", "contact_person_name": "山田 太郎", "phone_number": "090-1111-0001", "email": "yamada.taro@personal.example.com", "address": "東京都世田谷区桜3-10-5", "notes": "個人顧客、外壁塗装希望"},
        {"customer_name": "佐藤邸", "contact_person_name": "佐藤 花子", "phone_number": "080-2222-0002", "email": "sato.hanako@personal.example.com", "address": "神奈川県川崎市多摩区宿河原7-2-8", "notes": "個人顧客、屋根修繕"},
        {"customer_name": "株式会社 未来オフィス", "contact_person_name": "中村 信二", "phone_number": "03-5555-7777", "email": "nakamura@mirai-office.com", "address": "東京都港区台場1-7-1", "notes": "オフィス内装"},
    ]
    customer_ids = {}
    print("\n--- 顧客データの追加 ---")
    for cust_data in customers_to_add:
        try:
            c_id = db_ops.add_customer(**cust_data)
            if isinstance(c_id, int):
                customer_ids[cust_data["customer_name"]] = c_id
                print(f"顧客「{cust_data['customer_name']}」を追加 (ID: {c_id})")
            else:
                print(f"顧客「{cust_data['customer_name']}」追加失敗: {c_id}")
                if c_id == "DUPLICATE_NAME":
                    all_cust = db_ops.get_all_customers()
                    for ac in all_cust:
                        if ac[1] == cust_data["customer_name"]:
                            customer_ids[cust_data["customer_name"]] = ac[0]
                            print(f"  (既存ID: {ac[0]} を使用)")
                            break
        except Exception as e: print(f"顧客「{cust_data['customer_name']}」追加中にエラー: {e}")

    # --- 2. 社員データの追加 ---
    # (変更なし)
    employees_to_add = [
        {"employee_code": "S001", "full_name": "木村 正義", "name_kana": "キムラ マサヨシ", "ccus_id": "10000000000001",
         "date_of_birth": "1970-01-15", "gender": "男性", "position": "社長", "address": "東京都本社1-1", "phone_number": "090-0001-0001",
         "job_title": "代表取締役", "employment_date": "2005-04-01", "experience_years_trade": 25.0,
         "emergency_contact_name": "木村 花", "emergency_contact_phone": "080-0001-0002", "emergency_contact_relationship": "妻",
         "last_health_check_date": random_date(2024,2025), "blood_type": "A型",
         "social_insurance_status_notes": "健康保険、厚生年金、雇用保険加入", "retirement_allowance_notes": "中小企業退職金共済加入",
         "qualifications_notes": "一級建築施工管理技士", "paid_leave_days_notes": "年間20日", "is_active": True, "remarks": "経営・最終確認"},
        {"employee_code": "S002", "full_name": "田中 恵子", "name_kana": "タナカ ケイコ", "ccus_id": "10000000000002",
         "date_of_birth": "1985-05-20", "gender": "女性", "position": "課長", "address": "神奈川県営業所2-2", "phone_number": "090-0002-0001",
         "job_title": "営業担当", "employment_date": "2010-05-10", "experience_years_trade": 10.5,
         "emergency_contact_name": "田中 一郎", "emergency_contact_phone": "080-0002-0002", "emergency_contact_relationship": "夫",
         "last_health_check_date": random_date(2024,2025), "blood_type": "O型",
         "social_insurance_status_notes": "フル加入", "retirement_allowance_notes": "確定拠出年金",
         "qualifications_notes": "宅地建物取引士", "paid_leave_days_notes": "残り15日", "is_active": True, "remarks": "見積作成、顧客対応"},
        {"employee_code": "S003", "full_name": "鈴木 浩二", "name_kana": "スズキ コウジ", "ccus_id": "10000000000003",
         "date_of_birth": "1978-11-03", "gender": "男性", "position": "部長", "address": "埼玉県工事部3-3", "phone_number": "090-0003-0001",
         "job_title": "工事部長", "employment_date": "2008-08-01", "experience_years_trade": 18.0,
         "emergency_contact_name": "鈴木 良子", "emergency_contact_phone": "080-0003-0002", "emergency_contact_relationship": "妻",
         "last_health_check_date": random_date(2024,2025), "blood_type": "B型",
         "social_insurance_status_notes": "完備", "retirement_allowance_notes": "あり",
         "qualifications_notes": "一級塗装技能士, 有機溶剤作業主任者", "paid_leave_days_notes": "年間18日", "is_active": True, "remarks": "現場総括、品質管理"},
        {"employee_code": "S004", "full_name": "佐藤 明", "name_kana": "サトウ アキラ", "ccus_id": "10000000000004",
         "date_of_birth": "1990-07-25", "gender": "男性", "position": "主任", "address": "千葉県事務センター4-4", "phone_number": "090-0004-0001",
         "job_title": "事務・経理", "employment_date": "2015-11-15", "experience_years_trade": 0,
         "emergency_contact_name": "佐藤 光", "emergency_contact_phone": "080-0004-0002", "emergency_contact_relationship": "兄",
         "last_health_check_date": random_date(2024,2025), "blood_type": "AB型",
         "social_insurance_status_notes": "加入", "retirement_allowance_notes": "検討中",
         "qualifications_notes": "日商簿記2級", "paid_leave_days_notes": "残り10日", "is_active": True, "remarks": "書類作成、請求処理"},
        {"employee_code": "S005", "full_name": "高橋 直樹（退職）", "name_kana": "タカハシ ナオキ", "ccus_id": "10000000000005",
         "date_of_birth": "1988-03-10", "gender": "男性", "position": "一般", "address": "退職者住所情報なし", "phone_number": "連絡不可",
         "job_title": "元・営業担当", "employment_date": "2018-04-01", "experience_years_trade": 5.0,
         "emergency_contact_name": "", "emergency_contact_phone": "", "emergency_contact_relationship": "",
         "last_health_check_date": "2023-10-01", "blood_type": "不明",
         "social_insurance_status_notes": "資格喪失済", "retirement_allowance_notes": "支払済",
         "qualifications_notes": "", "paid_leave_days_notes": "なし", "is_active": False, "remarks": "2024年3月末退職"},
    ]
    employee_ids = {}
    print("\n--- 社員データの追加 ---")
    for emp_data_item in employees_to_add:
        try:
            e_id = db_ops.add_employee(**emp_data_item)
            if isinstance(e_id, int):
                employee_ids[emp_data_item["full_name"]] = e_id
                print(f"社員「{emp_data_item['full_name']}」を追加 (ID: {e_id})")
            else:
                print(f"社員「{emp_data_item['full_name']}」追加失敗: {e_id}")
                if e_id in ["DUPLICATE_EMP_CODE", "DUPLICATE_CCUS_ID"]:
                    all_emp = db_ops.get_all_employees()
                    for ae in all_emp:
                        if ae[2] == emp_data_item["full_name"]:
                            employee_ids[emp_data_item["full_name"]] = ae[0]
                            print(f"  (既存ID: {ae[0]} を使用)")
                            break
        except Exception as e: print(f"社員「{emp_data_item['full_name']}」追加中にエラー: {e}")


    # --- 3. 案件データの追加 (親子関係も含む) ---
    # (変更なし)
    project_ids = {}
    project_data_map = {}
    print("\n--- 案件データの追加 ---")

    parent_projects_def = [
        {"project_code": "P2024-SK001", "project_name": "渋谷区オフィスビル改修プロジェクト", "customer_name": "株式会社 東京ホームズ",
         "responsible_staff_name": "鈴木 浩二", "status": "計画中", "reception_date": random_date(2024,2024),
         "start_date_scheduled": random_date(2024,2024, can_be_none=True), "completion_date_scheduled": random_date(2024,2025, can_be_none=True),
         "actual_completion_date": None, "estimated_amount": 25000000, "site_address": "東京都渋谷区道玄坂1-2-3", "remarks": "全体統括案件"},
        {"project_code": "P2025-MJ001", "project_name": "南青山マンション大規模修繕", "customer_name": "株式会社 未来オフィス",
         "responsible_staff_name": "鈴木 浩二", "status": "見積依頼", "reception_date": random_date(2025,2025),
         "start_date_scheduled": None, "completion_date_scheduled": None,
         "actual_completion_date": None, "estimated_amount": 75000000, "site_address": "東京都港区南青山3-5-7", "remarks": "長期計画"},
    ]
    for proj_def in parent_projects_def:
        cust_id = customer_ids.get(proj_def["customer_name"])
        if cust_id is None: continue
        data_for_db = {k:v for k,v in proj_def.items() if k != "customer_name"}
        data_for_db["customer_id"] = cust_id
        data_for_db["parent_project_id"] = None
        try:
            p_id = db_ops.add_project(**data_for_db)
            if isinstance(p_id, int):
                project_ids[proj_def["project_code"]] = p_id
                project_data_map[proj_def["project_code"]] = {**data_for_db, "project_id": p_id}
                print(f"親案件「{proj_def['project_name']}」を追加 (ID: {p_id})")
            else:
                print(f"親案件「{proj_def['project_name']}」追加失敗: {p_id}")
                if p_id == "DUPLICATE_CODE":
                    all_proj = db_ops.get_all_projects()
                    for ap in all_proj:
                        if ap[1] == proj_def["project_code"]:
                            project_ids[proj_def["project_code"]] = ap[0]
                            print(f"  (既存ID: {ap[0]} を使用)")
                            break
        except Exception as e: print(f"親案件「{proj_def['project_name']}」追加中にエラー: {e}")

    projects_to_add = [
        {"project_code": "P2024-SK001-01", "project_name": "渋谷区オフィスビル改修(外壁塗装)", "customer_name": "株式会社 東京ホームズ", "parent_project_code": "P2024-SK001",
         "responsible_staff_name": "鈴木 浩二", "status": "見積提出済", "reception_date": random_date(2024,2024),
         "start_date_scheduled": random_date(2024,2024), "completion_date_scheduled": random_date(2024,2024), "actual_completion_date": None,
         "estimated_amount": 8000000, "site_address": "東京都渋谷区道玄坂1-2-3 (外壁)", "remarks": "フッ素塗料指定"},
        {"project_code": "P2024-SK001-02", "project_name": "渋谷区オフィスビル改修(内装A工事)", "customer_name": "株式会社 東京ホームズ", "parent_project_code": "P2024-SK001",
         "responsible_staff_name": "田中 恵子", "status": "見積中", "reception_date": random_date(2024,2024),
         "start_date_scheduled": None, "completion_date_scheduled": None, "actual_completion_date": None,
         "estimated_amount": 12000000, "site_address": "東京都渋谷区道玄坂1-2-3 (内装A)", "remarks": "デザイン案3パターン"},
        {"project_code": "P2024-YR001", "project_name": "横浜工場屋根防水工事", "customer_name": "神奈川リフォームサービス",
         "responsible_staff_name": "鈴木 浩二", "status": "施工中", "reception_date": random_date(2024,2024),
         "start_date_scheduled": (datetime.strptime(random_date(2024,2024), "%Y-%m-%d") - timedelta(days=15)).strftime("%Y-%m-%d"),
         "completion_date_scheduled": (datetime.strptime(random_date(2024,2024), "%Y-%m-%d") + timedelta(days=60)).strftime("%Y-%m-%d"),
         "actual_completion_date": None, "estimated_amount": 9500000, "site_address": "神奈川県横浜市金沢区福浦1-5-2", "remarks": "梅雨時期注意"},
        {"project_code": "P2023-ST001", "project_name": "さいたま市公共施設塗装(完了)", "customer_name": "埼玉ハウジング株式会社",
         "responsible_staff_name": "鈴木 浩二", "status": "入金済", "reception_date": random_date(2023,2023),
         "start_date_scheduled": random_date(2023,2023), "completion_date_scheduled": random_date(2023,2023),
         "actual_completion_date": (datetime.strptime(random_date(2023,2023), "%Y-%m-%d") + timedelta(days=45)).strftime("%Y-%m-%d"),
         "estimated_amount": 15000000, "site_address": "埼玉県さいたま市中央区新都心10", "remarks": "検査合格済"},
        {"project_code": "P2025-CB001", "project_name": "千葉新港倉庫 新築塗装工事", "customer_name": "千葉建設工業",
         "responsible_staff_name": "鈴木 浩二", "status": "受注", "reception_date": random_date(2025,2025),
         "start_date_scheduled": (datetime.strptime(random_date(2025,2025), "%Y-%m-%d") + timedelta(days=30)).strftime("%Y-%m-%d"),
         "completion_date_scheduled": (datetime.strptime(random_date(2025,2025), "%Y-%m-%d") + timedelta(days=120)).strftime("%Y-%m-%d"),
         "actual_completion_date": None, "estimated_amount": 18000000, "site_address": "千葉県千葉市中央区千葉港7-1", "remarks": "大型クレーン使用"},
        {"project_code": "P2024-YM001", "project_name": "山田太郎様邸 全面リフォーム(塗装)", "customer_name": "山田太郎様邸",
         "responsible_staff_name": "田中 恵子", "status": "完了", "reception_date": random_date(2024,2024),
         "start_date_scheduled": random_date(2024,2024), "completion_date_scheduled": random_date(2024,2024), "actual_completion_date": random_date(2024,2024),
         "estimated_amount": 2800000, "site_address": "東京都世田谷区桜3-10-5", "remarks": "施主様こだわり強し"},
        {"project_code": "P2025-ST001", "project_name": "佐藤邸 屋根・外壁補修", "customer_name": "佐藤邸",
         "responsible_staff_name": "田中 恵子", "status": "見積依頼", "reception_date": random_date(2025,2025),
         "start_date_scheduled": None, "completion_date_scheduled": None, "actual_completion_date": None,
         "estimated_amount": 1900000, "site_address": "神奈川県川崎市多摩区宿河原7-2-8", "remarks": "雨漏り調査含む"},
        {"project_code": "P2023-MO001", "project_name": "未来オフィス内装デザイン塗装(失注)", "customer_name": "株式会社 未来オフィス",
         "responsible_staff_name": "田中 恵子", "status": "失注", "reception_date": random_date(2023,2023),
         "start_date_scheduled": None, "completion_date_scheduled": None, "actual_completion_date": None,
         "estimated_amount": 4500000, "site_address": "東京都港区台場1-7-1 アクアシティ5F", "remarks": "競合負け"},
        {"project_code": "P2024-TH002", "project_name": "東京ホームズ様管理物件 緊急補修", "customer_name": "株式会社 東京ホームズ",
         "responsible_staff_name": "鈴木 浩二", "status": "請求済", "reception_date": random_date(2024,2024),
         "start_date_scheduled": random_date(2024,2024), "completion_date_scheduled": random_date(2024,2024), "actual_completion_date": random_date(2024,2024),
         "estimated_amount": 750000, "site_address": "東京都渋谷区恵比寿南1-20-5", "remarks": "台風被害"},
        {"project_code": "P2025-KR001", "project_name": "神奈川リフォーム様からの紹介案件", "customer_name": "神奈川リフォームサービス",
         "responsible_staff_name": "田中 恵子", "status": "見積中", "reception_date": random_date(2025,2025),
         "start_date_scheduled": None, "completion_date_scheduled": None, "actual_completion_date": None,
         "estimated_amount": 3200000, "site_address": "神奈川県相模原市緑区橋本3-28-1", "remarks": "顧客紹介、価格重視"},
        {"project_code": "P2024-CNCL01", "project_name": "キャンセル案件テスト", "customer_name": "千葉建設工業",
         "responsible_staff_name": "田中 恵子", "status": "キャンセル", "reception_date": "2024-03-01",
         "start_date_scheduled": "2024-04-01", "completion_date_scheduled": "2024-05-01", "actual_completion_date": None,
         "estimated_amount": 2000000, "site_address": "千葉県船橋市市場2-3-4", "remarks": "顧客都合によりキャンセル"},
        {"project_code": "P2025-MJ001-01", "project_name": "南青山マンション大規模修繕(外壁調査)", "customer_name": "株式会社 未来オフィス", "parent_project_code": "P2025-MJ001",
         "responsible_staff_name": "鈴木 浩二", "status": "見積提出済", "reception_date": random_date(2025,2025),
         "start_date_scheduled": random_date(2025,2025), "completion_date_scheduled": random_date(2025,2025), "actual_completion_date": None,
         "estimated_amount": 1500000, "site_address": "東京都港区南青山3-5-7 (調査)", "remarks": "ドローン使用予定"},
    ]
    for proj_def in projects_to_add:
        cust_id = customer_ids.get(proj_def["customer_name"])
        parent_p_id = None
        if proj_def.get("parent_project_code"):
            parent_p_id = project_ids.get(proj_def["parent_project_code"])
            if parent_p_id is None:
                print(f"警告: 子案件「{proj_def['project_name']}」の親案件コード「{proj_def['parent_project_code']}」に対応するIDが見つかりません。親子関係なしで登録試行。")
        if cust_id is None:
            print(f"警告: 案件「{proj_def['project_name']}」の顧客「{proj_def['customer_name']}」が見つかりません。スキップ。")
            continue
        data_for_db = {k:v for k,v in proj_def.items() if k not in ["customer_name", "parent_project_code"]}
        data_for_db["customer_id"] = cust_id
        data_for_db["parent_project_id"] = parent_p_id
        try:
            p_id = db_ops.add_project(**data_for_db)
            if isinstance(p_id, int):
                project_ids[proj_def["project_code"]] = p_id
                project_data_map[proj_def["project_code"]] = {**data_for_db, "project_id": p_id}
                print(f"案件「{proj_def['project_name']}」を追加 (ID: {p_id})")
            else:
                print(f"案件「{proj_def['project_name']}」追加失敗: {p_id}")
                if p_id == "DUPLICATE_CODE":
                    all_proj = db_ops.get_all_projects()
                    for ap in all_proj:
                        if ap[1] == proj_def["project_code"]:
                            project_ids[proj_def["project_code"]] = ap[0]
                            print(f"  (既存ID: {ap[0]} を使用)")
                            break
        except Exception as e: print(f"案件「{proj_def['project_name']}」追加中にエラー: {e}")

    # --- 4. 見積ヘッダーデータの追加 ---
    # (変更なし)
    quotation_ids = {}
    print("\n--- 見積ヘッダーデータの追加 ---")
    quotations_to_add = [
        {"quotation_code": "Q24S01-01A", "project_code": "P2024-SK001-01", "staff_name": "田中 恵子", "quotation_date": random_date(2024,2024), "status": "提出済", "total_amount_exclusive_tax": 7800000, "tax_rate": 0.10, "validity_period_notes": "見積提出後1ヶ月"},
        {"quotation_code": "Q24S01-01B", "project_code": "P2024-SK001-01", "staff_name": "田中 恵子", "quotation_date": random_date(2024,2024), "status": "改訂中", "total_amount_exclusive_tax": 7500000, "tax_rate": 0.10, "remarks":"顧客要望により一部仕様変更"},
        {"quotation_code": "Q24S01-02A", "project_code": "P2024-SK001-02", "staff_name": "田中 恵子", "quotation_date": random_date(2024,2024), "status": "見積中", "total_amount_exclusive_tax": 11500000, "tax_rate": 0.10},
        {"quotation_code": "Q24YF01-01", "project_code": "P2024-YR001", "staff_name": "木村 正義", "quotation_date": random_date(2024,2024), "status": "受注", "total_amount_exclusive_tax": 9200000, "tax_rate": 0.10},
        {"quotation_code": "Q23STP1-01", "project_code": "P2023-ST001", "staff_name": "田中 恵子", "quotation_date": random_date(2023,2023), "status": "完了", "total_amount_exclusive_tax": 14800000, "tax_rate": 0.10},
        {"quotation_code": "Q25CBW1-01", "project_code": "P2025-CB001", "staff_name": "田中 恵子", "quotation_date": random_date(2025,2025), "status": "受注", "total_amount_exclusive_tax": 17500000, "tax_rate": 0.10},
        {"quotation_code": "Q24YM001-A", "project_code": "P2024-YM001", "staff_name": "田中 恵子", "quotation_date": random_date(2024,2024), "status": "完了", "total_amount_exclusive_tax": 2700000, "tax_rate": 0.10},
        {"quotation_code": "Q24YM001-B", "project_code": "P2024-YM001", "staff_name": "田中 恵子", "quotation_date": random_date(2024,2024), "status": "キャンセル", "total_amount_exclusive_tax": 500000, "tax_rate": 0.10, "remarks":"追加工事分キャンセル"},
        {"quotation_code": "Q25SAT01-01", "project_code": "P2025-ST001", "staff_name": "田中 恵子", "quotation_date": random_date(2025,2025), "status": "見積依頼", "total_amount_exclusive_tax": 0, "tax_rate": 0.10},
        {"quotation_code": "Q23MOF1-01", "project_code": "P2023-MO001", "staff_name": "田中 恵子", "quotation_date": random_date(2023,2023), "status": "失注", "total_amount_exclusive_tax": 4300000, "tax_rate": 0.10},
        {"quotation_code": "Q24THK2-01", "project_code": "P2024-TH002", "staff_name": "木村 正義", "quotation_date": random_date(2024,2024), "status": "請求済", "total_amount_exclusive_tax": 700000, "tax_rate": 0.10},
        {"quotation_code": "Q25KRS1-01", "project_code": "P2025-KR001", "staff_name": "田中 恵子", "quotation_date": random_date(2025,2025), "status": "見積中", "total_amount_exclusive_tax": 3000000, "tax_rate": 0.10},
        {"quotation_code": "Q25MA01-01", "project_code": "P2025-MJ001", "staff_name": "木村 正義", "quotation_date": random_date(2025,2025), "status": "見積依頼", "total_amount_exclusive_tax": 0, "tax_rate": 0.10},
        {"quotation_code": "Q25MA01-02", "project_code": "P2025-MJ001", "staff_name": "木村 正義", "quotation_date": random_date(2025,2025), "status": "作成中", "total_amount_exclusive_tax": 72000000, "tax_rate": 0.10, "remarks": "一次見積"},
        {"quotation_code": "Q24EXTR-01", "project_code": "P2024-YR001", "staff_name": "田中 恵子", "quotation_date": random_date(2024,2024), "status": "見積提出済", "total_amount_exclusive_tax": 150000, "tax_rate": 0.10, "remarks":"追加オプション分"},
        {"quotation_code": "Q23PAST-01", "project_code": "P2023-ST001", "staff_name": "高橋 直樹（退職）", "quotation_date": random_date(2023,2023), "status": "完了", "total_amount_exclusive_tax": 200000, "tax_rate": 0.10, "remarks":"過去の軽微な修正"},
        {"quotation_code": "Q25FUTR-01", "project_code": "P2025-CB001", "staff_name": "田中 恵子", "quotation_date": random_date(2025,2025), "status": "見積中", "total_amount_exclusive_tax": 500000, "tax_rate": 0.10, "remarks":"将来の拡張工事分"},
        {"quotation_code": "Q24CNCL-01", "project_code": "P2024-YM001", "staff_name": "田中 恵子", "quotation_date": random_date(2024,2024), "status": "キャンセル", "total_amount_exclusive_tax": 100000, "tax_rate": 0.10, "remarks":"一部キャンセル"},
    ]
    for quot_def in quotations_to_add:
        proj_id = project_ids.get(quot_def["project_code"])
        staff_id = employee_ids.get(quot_def["staff_name"])
        if proj_id is None:
            print(f"見積「{quot_def['quotation_code']}」の案件「{quot_def['project_code']}」が見つかりません。スキップ。")
            continue
        related_project_data = project_data_map.get(quot_def["project_code"])
        if related_project_data is None:
            print(f"見積「{quot_def['quotation_code']}」の関連案件データ「{quot_def['project_code']}」がproject_data_mapにありません。スキップ。")
            continue
        customer_info = None
        if related_project_data.get("customer_id"):
            all_customers_local = db_ops.get_all_customers() # get_all_customers() を呼び出し
            for c_local in all_customers_local: # cからc_localに変更
                if c_local[0] == related_project_data["customer_id"]:
                    customer_info = c_local
                    break
        customer_name_at_quote = quot_def.get("customer_name_at_quote", customer_info[1] if customer_info else "顧客名不明")
        project_name_at_quote = quot_def.get("project_name_at_quote", related_project_data.get("project_name", "案件名不明"))
        site_address_at_quote = quot_def.get("site_address_at_quote", related_project_data.get("site_address", ""))
        tax_amount = int(quot_def["total_amount_exclusive_tax"] * quot_def["tax_rate"])
        total_inclusive = quot_def["total_amount_exclusive_tax"] + tax_amount
        full_quot_data = {
            "project_id": proj_id, "quotation_staff_id": staff_id,
            "quotation_code": quot_def["quotation_code"], "quotation_date": quot_def["quotation_date"],
            "customer_name_at_quote": customer_name_at_quote,
            "project_name_at_quote": project_name_at_quote,
            "site_address_at_quote": site_address_at_quote,
            "construction_period_notes": quot_def.get("construction_period_notes", "別途協議"),
            "total_amount_exclusive_tax": quot_def["total_amount_exclusive_tax"],
            "tax_rate": quot_def["tax_rate"], "tax_amount": tax_amount,
            "total_amount_inclusive_tax": total_inclusive,
            "validity_period_notes": quot_def.get("validity_period_notes", "発行後1ヶ月"),
            "payment_terms_notes": quot_def.get("payment_terms_notes", "納品検収後月末締め翌月末払い"),
            "status": quot_def["status"], "remarks": quot_def.get("remarks", "")
        }
        try:
            q_id = db_ops.add_quotation(**full_quot_data)
            if isinstance(q_id, int):
                quotation_ids[quot_def["quotation_code"]] = q_id
                print(f"見積「{quot_def['quotation_code']}」を追加 (ID: {q_id})")
            else:
                print(f"見積「{quot_def['quotation_code']}」追加失敗: {q_id}")
        except Exception as e: print(f"見積「{quot_def['quotation_code']}」追加中にエラー: {e}")


    # --- 5. 見積明細データの追加 ---
    print("\n--- 見積明細データの追加 ---")
    # ★★★ 'remarks' を全ての明細アイテムに追加 ★★★
    quotation_items_def = {
        "Q24S01-01A": [
            {"name": "外壁高圧ジェット洗浄", "specification": "トルネードノズル使用、バイオ洗浄剤含む", "quantity": 500, "unit": "m2", "unit_price": 220, "remarks":"藻・カビ除去"},
            {"name": "シーリング打替え工事（高耐久）", "specification": "オートンイクシード使用", "quantity": 300, "unit": "m", "unit_price": 1200, "remarks":""},
            {"name": "外壁無機フッ素塗装（4回塗）", "specification": "プレマテックス タテイルα + 専用プライマー", "quantity": 500, "unit": "m2", "unit_price": 5200, "remarks":"超高耐久仕様"},
            {"name": "バルコニー防水工事（FRP）", "specification": "FRP防水トップコート仕上げ（グレー）", "quantity": 50, "unit": "m2", "unit_price": 6000, "remarks":""},
            {"name": "仮設足場設置・解体・養生", "specification": "全面メッシュシート、安全通路確保", "quantity": 1, "unit": "式", "unit_price": 1350000, "remarks":""},
            {"name": "現場管理費・諸経費", "specification": "工事金額の10%", "quantity": 1, "unit": "式", "unit_price": 0, "remarks":"自動計算対象"},
        ],
        "Q24YF01-01": [
            {"name": "屋根ケレン・清掃（動力工具使用）", "specification": "既存塗膜・錆除去", "quantity": 1200, "unit": "m2", "unit_price": 350, "remarks":""},
            {"name": "屋根遮熱断熱塗装（GAINA）", "specification": "ガイナ（GAINA）中塗り・上塗り 各2回", "quantity": 1200, "unit": "m2", "unit_price": 6000, "remarks":"夏季の室温低減効果大"},
            {"name": "雨樋交換工事（ステンレス製）", "specification": "高耐久ステンレス角樋", "quantity": 150, "unit": "m", "unit_price": 7500, "remarks":""},
            {"name": "産業廃棄物処理費", "specification": "旧屋根材・塗料缶等", "quantity": 1, "unit": "式", "unit_price": 150000, "remarks":""},
            {"name": "安全対策費（高所作業車含む）", "specification": "警備員配置・安全設備・高所作業車リース", "quantity": 1, "unit": "式", "unit_price": 450000, "remarks":""},
        ],
        "Q23STP1-01": [
            {"name": "外壁タイル面薬品洗浄（特殊対応）", "specification": "環境配慮型特殊薬品使用", "quantity": 800, "unit": "m2", "unit_price": 1800, "remarks":""},
            {"name": "タイル剥落防止ネット設置（高強度）", "specification": "高強度透明ネット、ステンレスアンカー", "quantity": 800, "unit": "m2", "unit_price": 3500, "remarks":""},
            {"name": "エントランス特殊吹付塗装", "specification": "多意匠装飾仕上げ（耐候性シリコン）", "quantity": 120, "unit": "m2", "unit_price": 7500, "remarks":"特注色、サンプル作成費含む"},
            {"name": "夜間・休日作業割増", "specification": "公共施設稼働時間外作業", "quantity": 1, "unit": "式", "unit_price": 700000, "remarks":""},
            {"name": "申請書類作成費", "specification": "行政提出用各種書類", "quantity": 1, "unit": "式", "unit_price": 120000, "remarks":""},
        ],
        "Q25CBW1-01": [
            {"name": "鉄骨ブラスト処理＋重防食塗装", "specification": "ISO12944 C5-M準拠", "quantity": 25000, "unit": "kg", "unit_price": 45, "remarks":"重量(kg)あたり単価"},
            {"name": "折板屋根遮熱フッ素塗装（高耐久）", "specification": "AGCルミフロンベースフッ素塗料", "quantity": 3000, "unit": "m2", "unit_price": 4200, "remarks":""},
            {"name": "外壁金属サイディングクリヤー塗装", "specification": "UVカット高耐候クリヤー", "quantity": 1500, "unit": "m2", "unit_price": 3800, "remarks":""},
            {"name": "床重量物対応防塵塗装", "specification": "厚膜型エポキシ樹脂系塗料", "quantity": 2800, "unit": "m2", "unit_price": 3000, "remarks":"フォークリフト走行対応"},
            {"name": "大型車両搬入路整備費", "specification": "仮設鉄板敷設等", "quantity": 1, "unit": "式", "unit_price": 800000, "remarks":""},
        ],
        "Q24YM001-A": [
            {"name": "外壁バイオ高圧洗浄", "specification": "専用バイオ洗浄剤使用、カビ・藻の根元から除去", "quantity": 180, "unit": "m2", "unit_price": 400, "remarks":""},
            {"name": "屋根塗装（無機ハイブリッド）", "specification": "KFワールドセラルーフ（超高耐候）", "quantity": 90, "unit": "m2", "unit_price": 4500, "remarks":"期待耐用年数20年以上"},
            {"name": "付帯部塗装（破風・軒天・雨樋・水切り）", "specification": "4フッ化フッ素塗料使用", "quantity": 1, "unit": "式", "unit_price": 350000, "remarks":""},
            {"name": "ベランダ防水（FRP防水改修）", "specification": "FRP防水積層・トップコート", "quantity": 15, "unit": "m2", "unit_price": 7000, "remarks":""},
            {"name": "近隣挨拶・粗品代", "specification": "工事前後の挨拶回り", "quantity": 1, "unit": "式", "unit_price": 30000, "remarks":""},
        ],
         "Q25MA01-02": [
            {"name": "共通仮設工事（大規模修繕用）", "specification": "居住者導線確保、防犯カメラ設置含む", "quantity": 1, "unit": "式", "unit_price": 6500000, "remarks":""},
            {"name": "外壁タイル補修・超低汚染塗装", "specification": "タイル浮き注入、プレマテックス グラステージ（4回塗）", "quantity": 3500, "unit": "m2", "unit_price": 13500, "remarks":"美観維持20年保証"},
            {"name": "屋上シート防水改修工事（機械固定）", "specification": "塩ビ系シート防水 機械固定工法", "quantity": 800, "unit": "m2", "unit_price": 12000, "remarks":""},
            {"name": "鉄部塗装工事（フッ素樹脂）", "specification": "階段・手摺・PS扉等 全面ケレン・フッ素塗装", "quantity": 1, "unit": "式", "unit_price": 9500000, "remarks":""},
            {"name": "共用廊下・階段 防滑性長尺シート張替", "specification": "タキステップMW 高耐久仕様", "quantity": 1200, "unit": "m2", "unit_price": 8800, "remarks":""},
            {"name": "駐車場ライン引き直し・車止め交換", "specification": "全区画対応", "quantity": 1, "unit": "式", "unit_price": 1200000, "remarks":""},
        ]
    }

    for q_code, items in quotation_items_def.items():
        q_id = quotation_ids.get(q_code)
        if q_id is None:
            print(f"明細追加のための見積「{q_code}」が見つかりません。スキップ。")
            continue

        print(f"見積「{q_code}」(ID: {q_id}) の明細を追加中...")
        current_total_exclusive = 0
        for item_data_item in items: # 変数名を item_data から item_data_item に変更
            # ★★★ remarks が存在しない場合に備えて .get() を使用 ★★★
            remarks_value = item_data_item.get("remarks", "") # remarks がなければ空文字

            if item_data_item["name"] == "現場管理費・諸経費" and item_data_item.get("unit_price", 0) == 0 :
                 item_data_item["unit_price"] = int(current_total_exclusive * 0.10)

            amount = int(item_data_item["quantity"] * item_data_item["unit_price"])
            # ★★★ full_item_data に remarks を含める ★★★
            full_item_data = {
                "quotation_id": q_id,
                "name": item_data_item["name"],
                "specification": item_data_item.get("specification"),
                "quantity": item_data_item["quantity"],
                "unit": item_data_item.get("unit"),
                "unit_price": item_data_item["unit_price"],
                "amount": amount,
                "remarks": remarks_value # 修正：remarks_value を使用
            }
            try:
                item_id = db_ops.add_quotation_item(**full_item_data)
                if isinstance(item_id, int):
                    print(f"  明細「{item_data_item['name']}」を追加 (Item ID: {item_id})")
                    current_total_exclusive += amount
                else:
                    print(f"  明細「{item_data_item['name']}」追加失敗: {item_id}")
            except Exception as e: print(f"  明細「{item_data_item['name']}」追加中にエラー: {e}")

        # ★★★ 'self' を参照している部分を削除 ★★★
        # 諸経費の再計算と更新は、このローダースクリプトの範囲外とするか、
        # DBから明細を再取得して行う必要があるため、一旦コメントアウト/削除します。
        # recalculated_total_for_sundry = current_total_exclusive
        # for item in self.items_tree.get_children(q_id): # これはGUIのTreeviewなので、DBから再取得が良い
        #     item_values = self.items_tree.item(item, 'values')
        #     if item_values and item_values[1] == "現場管理費・諸経費": # name列
        #         pass

        header_for_update = db_ops.get_quotation_by_id(q_id)
        if header_for_update:
            tax_rate = header_for_update[12] if header_for_update[12] is not None else 0.10
            new_tax_amount = int(current_total_exclusive * tax_rate)
            new_total_inclusive = current_total_exclusive + new_tax_amount
            update_q_res = db_ops.update_quotation(
                quotation_id=q_id, project_id=header_for_update[1],
                quotation_staff_id=header_for_update[3], quotation_code=header_for_update[5],
                quotation_date=header_for_update[6], customer_name_at_quote=header_for_update[7],
                project_name_at_quote=header_for_update[8], site_address_at_quote=header_for_update[9],
                construction_period_notes=header_for_update[10],
                total_amount_exclusive_tax=current_total_exclusive, tax_rate=tax_rate,
                tax_amount=new_tax_amount, total_amount_inclusive_tax=new_total_inclusive,
                validity_period_notes=header_for_update[15], payment_terms_notes=header_for_update[16],
                status=header_for_update[17], remarks=header_for_update[18]
            )
            if update_q_res is True:
                print(f"  見積「{q_code}」の合計金額を更新。税抜: {current_total_exclusive:,}円")
            else:
                print(f"  見積「{q_code}」の合計金額更新失敗: {update_q_res}")
        else:
            print(f"  見積「{q_code}」のヘッダー情報が見つからず、合計金額を更新できませんでした。")

    print("\nテストデータのロードが完了しました。")

if __name__ == '__main__':
    load_test_data()