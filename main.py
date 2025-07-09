#!/usr/bin/env python3
"""
CloudMile Referral Auto Reporter Auto 每月10號自動執行
"""

import os
import sys
from datetime import datetime, timedelta
from services.bigquery_service import BigQueryService
from services.netsuite_service import NetSuiteService
from services.sheets_service import SheetsService
from utils.data_processor import DataProcessor
from config import Config
import check_payment

def get_api_month() -> str:
    """
    取得 NetSuite API 查詢當月份（當月開立上月發票)
    Returns:
        str: API 查詢月份 (YYYYMM)
    """
    current_date = datetime.now()
    return current_date.strftime('%Y%m')

def main():
    print("=" * 50)
    print("CloudMile Referral Report Generator Started")
    print(f"Execution Time: {datetime.now()}")
    print("=" * 50)
    
    try:
        # 1. 初始化服務
        bq_service = BigQueryService()
        
        # 2. 測試 BigQuery 連線
        print("\nTesting BigQuery connection...")
        if not bq_service.test_connection():
            print("BigQuery connection failed. Please check permissions.")
            return
        
        netsuite_service = NetSuiteService()
        sheets_service = SheetsService()
        
        # 3. 取得最新月份的資料
        print(f"\nFetching latest month data from BigQuery...")
        billing_data, customer_profile, data_month = bq_service.get_latest_month_data()
        
        if data_month is None:
            print("No data found in BigQuery tables")
            return
        
        year = data_month // 100
        api_month = get_api_month()
        
        print(f"Processing data for month: {data_month}")
        print(f"NetSuite API query month: {api_month}")
        print(f"Target year: {year}")
        print(f"Billing data records: {len(billing_data)}")
        print(f"Customer profile records: {len(customer_profile)}")
        
        if billing_data.empty and customer_profile.empty:
            print("Warning: No data found in BigQuery for the specified month")
            return
        
        # 4. 取得所有需要查詢的 billing_account_ids
        billing_account_ids = bq_service.get_billing_account_ids(data_month)
        print(f"Total billing account IDs: {len(billing_account_ids)}")
        
        if not billing_account_ids:
            print("Warning: No billing account IDs found")
            return
        
        # 5. 查詢 NetSuite 發票付款狀態
        print(f"\nQuerying NetSuite API for payment status...")
        payment_status = netsuite_service.get_invoice_payment_status(
            api_month, billing_account_ids
        )
        print(f"Payment status results: {len(payment_status)}")
        
        # 6. 整合資料
        integrated_data = DataProcessor.integrate_data(
            billing_data, customer_profile, payment_status
        )
        print(f"Integrated data records: {len(integrated_data)}")
        
        if integrated_data.empty:
            print("Warning: No data to write after integration")
            return
        
        # 7. 寫入 Google Sheets
        print(f"\nWriting data to Google Sheets...")
        sheets_service.write_monthly_data(integrated_data, year, data_month)
        print("Data written successfully")
        
        # 8. 更新檔案名稱
        print(f"\nUpdating spreadsheet title...")
        sheets_service.update_spreadsheet_title(data_month)
        
        # 9. 檢查歷史資料付款狀態
        print(f"\nChecking historical payment status...")
        check_payment.check_and_update_payment_status(year)
        print("All payment status check completed")
        
        print("\n" + "=" * 50)
        print("Process completed successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        print("Process failed!")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()