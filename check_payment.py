#!/usr/bin/env python3
"""
檢查過去月份的 Customer<>CM 欄位，更新 "waiting" 狀態的記錄
"""

from services.sheets_service import SheetsService
from services.netsuite_service import NetSuiteService
from config import Config
from collections import defaultdict

def check_and_update_payment_status(year: int):
    """
    檢查並更新指定年份的歷史付款狀態
        year: 要檢查的年份
    """
    print(f"Starting payment status check for {year}...")
    
    # 初始化服務
    sheets_service = SheetsService()
    netsuite_service = NetSuiteService()
    
    # 1. 取得所有 "waiting" 狀態的記錄
    waiting_records = sheets_service.get_waiting_records(year)
    
    if not waiting_records:
        print("No waiting records found")
        return
    
    print(f"Found {len(waiting_records)} waiting records")
    
    # 2. 按月分組，批次查詢
    records_by_month = defaultdict(list)
    for record in waiting_records:
        month = record['month']
        if month:  
            records_by_month[month].append(record)
    
    print(f"Grouped into {len(records_by_month)} months")
    
    # 3. 批次查詢每個月份的付款狀態
    all_updates = []
    
    for month, records in records_by_month.items():
        print(f"\nProcessing month {month} ({len(records)} records)...")
        
        try:
            # 該月份需要查詢的資料
            month_updates = process_month_records(netsuite_service, month, records)
            all_updates.extend(month_updates)
            
        except Exception as e:
            print(f"Error processing month {month}: {e}")
            continue
    
    # 4. 批次更新 Google Sheets
    if all_updates:
        print(f"\nUpdating {len(all_updates)} records in Google Sheets...")
        sheets_service.update_payment_status(year, all_updates)
        print("Payment status update completed")
    else:
        print("No updates needed")

def process_month_records(netsuite_service: NetSuiteService, month: str, records: list) -> list:
    """
    處理單一月份的記錄  
    Returns:
        list: 需要更新的記錄清單
    """
    updates = []
    # 透過 billing_account_name 查詢，取得對應關係
    
    unique_names = list(set(record['billing_account_name'] for record in records))
    print(f"  Unique billing account names: {len(unique_names)}")
    
    # 查詢每個 billing_account_name 的付款狀態
    for billing_account_name in unique_names:
        try:
            new_status = netsuite_service.get_payment_status_by_name(
                month, billing_account_name
            )
            
            # 檢查是否需要更新
            if should_update_status(new_status):
                # 找到所有需要更新的記錄
                for record in records:
                    if record['billing_account_name'] == billing_account_name:
                        updates.append({
                            'row_number': record['row_number'],
                            'new_status': new_status
                        })
                        print(f"    {billing_account_name}: waiting -> {new_status}")
            
        except Exception as e:
            print(f"  Error querying {billing_account_name}: {e}")
            continue
    
    return updates

def should_update_status(new_status: str) -> bool:
    """
    判斷是否需要更新狀態
        new_status: 新的付款狀態 
    Returns:
        bool: 是否需要更新
    """
    # 只有在狀態改變且不是錯誤狀態時才更新
    if new_status == "waiting":
        return False  # 狀態沒變，不需更新
    
    if new_status in [Config.ERROR_MESSAGES["API_ERROR"], 
                     Config.ERROR_MESSAGES["INVOICE_NOT_FOUND"]]:
        return False  # 錯誤狀態，不更新
    
    return True  # 其他情況都更新

if __name__ == "__main__":
    # 測試用 - 檢查當前年份
    from datetime import datetime
    current_year = datetime.now().year
    check_and_update_payment_status(current_year)