import os

class Config:
    # GCP 專案
    PROJECT_ID = "cloudmile-referral-report"
    DATASET_ID = "referral_service"
    
    # BigQuery 表
    BILLING_DATA_TABLE = "billing_data"
    CUSTOMER_PROFILE_TABLE = "customer_profile"
    
    # Google Sheets 
    SHEETS_FILE_ID = "1Ha6wnvhm4M9fV1B0Z3mYHMFt5t8IefFw24z06ga2us4"
    DRIVE_FOLDER_ID = "16UH39yl2WaawLRadUB1CMnz72jjWjhBG"
    
    # NetSuite API 
    NETSUITE_BASE_URL = "https://7005542.restlets.api.netsuite.com/app/site/hosting/restlet.nl"
    NETSUITE_SCRIPT_ID = "customscript_cm_rl_referral_inv_status"
    NETSUITE_DEPLOY_ID = "customdeploy_cm_rl_referral_inv_status"
    
    # OAuth 1.0 
    NETSUITE_REALM = "7005542"
    NETSUITE_CONSUMER_KEY = "fc09b5d0517a0b0f091b024cbade261e4a8af7ed13eea9a8bdc9ec1d03b8531f"
    NETSUITE_CONSUMER_SECRET = "d62b480bc9a8d58cc64d724f03cfbdc607c0d37d6b2db71f62fc5a64a34308d5"
    NETSUITE_TOKEN = "2b8cb395fd02616c3a932f1c7702554e27b36806cb74b817bf4b3a17f5307c87"
    NETSUITE_TOKEN_SECRET = "8f875e0a91b49d40297bbb99534ba4e4bed11aac3d688b159bc23f2f533e1f94"
    
    # 服務帳號
    SERVICE_ACCOUNT_FILE = "service-account.json"
    
    # 業務邏輯
    SHEET_NAME_FORMAT = "Report_{year}"
    REPORT_FILE_NAME_FORMAT = "IMPOSSIBLE auto report_{month}"
    
    # 欄位對應
    PAYMENT_STATUS_MAPPING = {
        "Open": "waiting",
        "Paid In Full": "Clear"
    }
    
    # 輸出表欄位
    OUTPUT_COLUMNS = [
        "Month",
        "Billing Account Name", 
        "Currency",
        "Spending $$",
        "Referral share rate",
        "Profit $$",
        "Referral Company",  
        "Customer<>CM",
        "Sales",
        "EDP status"
    ]
    
    # 錯誤訊息
    ERROR_MESSAGES = {
        "API_ERROR": "API Error",
        "INVOICE_NOT_FOUND": "Invoice Not Found",
        "NOT_FOUND_BILLING": "not found in billing_data",
        "NOT_FOUND_CUSTOMER": "not found in customer_profile",
        "NULL_VALUE": "not found"
    }