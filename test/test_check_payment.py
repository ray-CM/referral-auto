#!/usr/bin/env python3
"""
測試 check_payment 功能
"""

from services.sheets_service import SheetsService
from services.netsuite_service import NetSuiteService
import check_payment

def test_get_waiting_records():
    """
    測試 1: 檢查是否能讀取 waiting 記錄
    成本：幾乎為 0，只讀取 Google Sheets
    """
    print("=" * 50)
    print("測試 1: 讀取 waiting 記錄")
    print("=" * 50)
    
    try:
        sheets_service = SheetsService()
        waiting_records = sheets_service.get_waiting_records(2025)
        
        print(f"找到 {len(waiting_records)} 筆 waiting 記錄：")
        for i, record in enumerate(waiting_records, 1):
            print(f"  {i}. Row {record['row_number']}: {record['billing_account_name']} ({record['month']})")
        
        return waiting_records
        
    except Exception as e:
        print(f"錯誤: {e}")
        return []

def test_netsuite_single_query():
    """
    測試 2: 測試單筆 NetSuite API 查詢
    成本：1 次 API 呼叫
    """
    print("\n" + "=" * 50)
    print("測試 2: 單筆 NetSuite API 查詢")
    print("=" * 50)
    
    # 使用一個已知的 billing_account_name 進行測試
    test_billing_name = "CloudMile-Astar"  # 從您的資料中選一個
    test_month = "202506"
    
    try:
        netsuite_service = NetSuiteService()
        result = netsuite_service.get_payment_status_by_name(test_month, test_billing_name)
        
        print(f"測試帳戶: {test_billing_name}")
        print(f"查詢月份: {test_month}")
        print(f"付款狀態: {result}")
        
        return result
        
    except Exception as e:
        print(f"錯誤: {e}")
        return None

def test_manual_update():
    """
    測試 3: 手動更新一筆記錄（模擬）
    成本：0，只是模擬更新流程
    """
    print("\n" + "=" * 50)
    print("測試 3: 模擬更新流程")
    print("=" * 50)
    
    # 模擬更新資料
    mock_updates = [
        {'row_number': 2, 'new_status': 'Clear'},  # 假設第2行要更新
    ]
    
    print("模擬的更新資料:")
    for update in mock_updates:
        print(f"  Row {update['row_number']} → {update['new_status']}")
    
    # 實際要執行更新請取消下面的註解
    # try:
    #     sheets_service = SheetsService()
    #     sheets_service.update_payment_status(2025, mock_updates)
    #     print("更新成功！")
    # except Exception as e:
    #     print(f"更新失敗: {e}")
    
    print("(這是模擬，如需實際更新請取消程式中的註解)")

def test_check_payment_dry_run():
    """
    測試 4: check_payment 乾跑測試
    成本：讀取 + 少量 API 呼叫
    """
    print("\n" + "=" * 50)
    print("測試 4: check_payment 完整流程測試")
    print("=" * 50)
    
    print("這會執行完整的 check_payment 流程")
    print("包含真實的 NetSuite API 呼叫")
    
    proceed = input("確定要執行嗎？ (y/N): ").lower()
    
    if proceed == 'y':
        try:
            check_payment.check_and_update_payment_status(2025)
            print("check_payment 測試完成")
        except Exception as e:
            print(f"錯誤: {e}")
    else:
        print("已取消測試")

def main():
    """
    主測試流程
    """
    print("Check Payment 功能測試")
    print("建議順序執行，可隨時停止")
    
    # 測試 1: 讀取 waiting 記錄（成本最低）
    waiting_records = test_get_waiting_records()
    
    if not waiting_records:
        print("沒有 waiting 記錄，無法進行後續測試")
        return
    
    # 測試 2: 單筆 API 查詢
    input("\n按 Enter 繼續測試單筆 API 查詢...")
    test_netsuite_single_query()
    
    # 測試 3: 模擬更新
    input("\n按 Enter 繼續測試模擬更新...")
    test_manual_update()
    
    # 測試 4: 完整流程（可選）
    input("\n按 Enter 繼續完整流程測試（或 Ctrl+C 退出）...")
    test_check_payment_dry_run()

if __name__ == "__main__":
    main()