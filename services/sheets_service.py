import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from config import Config
from datetime import datetime

class SheetsService:
    def __init__(self):
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        credentials = Credentials.from_service_account_file(
            Config.SERVICE_ACCOUNT_FILE, 
            scopes=scope
        )
        
        self.gc = gspread.authorize(credentials)
        self.spreadsheet = self.gc.open_by_key(Config.SHEETS_FILE_ID)
    
    def get_or_create_worksheet(self, year: int) -> gspread.Worksheet:
        """
        取得或建立指定年份的工作表
            year: 年份 
            Returns: gspread.Worksheet: 工作表物件
        """
        sheet_name = Config.SHEET_NAME_FORMAT.format(year=year)
        
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            return worksheet
        except gspread.WorksheetNotFound:
            # 建立新工作表
            worksheet = self.spreadsheet.add_worksheet(
                title=sheet_name,
                rows=1000,
                cols=len(Config.OUTPUT_COLUMNS)
            )
            
            # 設定標題
            worksheet.insert_row(Config.OUTPUT_COLUMNS, 1)
            
            # 格式化標題列 - 藍色背景 #366092，白色粗體字，字體大小 11
            try:
                worksheet.format('A1:J1', {
                    'backgroundColor': {
                        'red': 54/255,    
                        'green': 96/255, 
                        'blue': 146/255
                    },
                    'textFormat': {
                        'bold': True,
                        'foregroundColor': {
                            'red': 1.0,     
                            'green': 1.0, 
                            'blue': 1.0
                        },
                        'fontSize': 11
                    }
                })
                print("Header formatting applied successfully")
            except Exception as e:
                print(f"Warning: Could not format header: {e}")
            
            try:
                worksheet.format('A:J', {
                    'textFormat': {
                        'fontSize': 11
                    }
                })
                print("Default font size set to 11")
            except Exception as e:
                print(f"Warning: Could not set default font size: {e}")
            
            return worksheet
    
    def write_monthly_data(self, data: pd.DataFrame, year: int, month: int):
        """
        寫入月份資料到工作表
            data: 要寫入的資料
            year: 年份
            month: 月份
        """
        worksheet = self.get_or_create_worksheet(year)
        
        # 檢查並更新表頭（確保欄位名稱正確）
        self._ensure_correct_headers(worksheet)
        
        # 檢查是否已存在該月份資料，如果有則先刪除
        self._remove_existing_month_data(worksheet, month)
        
        # 寫入資料
        if data.empty:
            return
        
        # 處理 NaN 值 - 轉換為空字串或適當的預設值
        data_clean = data.copy()
        
        # 將所有 NaN 替換為空字串，除了數值欄位
        for col in data_clean.columns:
            if col in ['Spending $$$', 'Referral share rate', 'Profit $$$']:
                data_clean[col] = data_clean[col].fillna('')
            else:
                data_clean[col] = data_clean[col].fillna('')
        
        # 找到最後一行
        last_row = len(worksheet.get_all_values())
        start_row = last_row + 1
        
        # 將 DataFrame 轉換為清單格式，確保所有值都是 JSON 可序列化的
        values = []
        for _, row in data_clean.iterrows():
            row_values = []
            for value in row:
                if pd.isna(value):
                    row_values.append('')
                elif isinstance(value, (int, float)):
                    if pd.isna(value) or value != value:  
                        row_values.append('')
                    else:
                        row_values.append(value)
                else:
                    row_values.append(str(value))
            values.append(row_values)
        
        # 批次寫入資料
        if values:
            end_row = start_row + len(values) - 1
            cell_range = f'A{start_row}:J{end_row}'
            
            try:
                worksheet.update(cell_range, values)
                print(f"Successfully wrote {len(values)} rows to Google Sheets")
                
                # 設定寫入字體大小為 11
                data_range = f'A{start_row}:J{end_row}'
                worksheet.format(data_range, {
                    'textFormat': {
                        'fontSize': 11
                    }
                })
                
                # 設定金錢格式 
                spending_range = f'D{start_row}:D{end_row}'  # Spending $$ 
                profit_range = f'F{start_row}:F{end_row}'    # Profit $$ 
                money_format = {
                    'numberFormat': {
                        'type': 'CURRENCY',
                        'pattern': '$#,##0.00'
                    }
                }
                
                worksheet.format(spending_range, money_format)
                worksheet.format(profit_range, money_format)
                print("Money format applied to Spending and Profit columns")
                
            except Exception as e:
                print(f"Error writing to Google Sheets: {e}")
                # 如果批次寫入失敗，嘗試逐行寫入
                self._write_row_by_row(worksheet, values, start_row)
            
            # 格式化 null 值的儲存格 (淺黃色背景)
            self._format_null_cells(worksheet, data_clean, start_row)
    
    def _ensure_correct_headers(self, worksheet: gspread.Worksheet):
        """
        確保表頭格式正確（不重寫表頭）
        """
        try:
            # 檢查第一行是否存在
            current_headers = worksheet.row_values(1)
            
            if not current_headers:
                # 當工作表完全沒有表頭時才寫入，若已存在，只確保格式正確，不重寫內容
                print("No headers found, adding headers...")
                worksheet.update('A1:J1', [Config.OUTPUT_COLUMNS])
            else:
                print("Headers already exist, ensuring format only...")
            
            # 不管內容如何，確保格式正確
            worksheet.format('A1:J1', {
                'backgroundColor': {
                    'red': 54/255,    
                    'green': 96/255, 
                    'blue': 146/255
                },
                'textFormat': {
                    'bold': True,
                    'foregroundColor': {
                        'red': 1.0,      
                        'green': 1.0, 
                        'blue': 1.0
                    },
                    'fontSize': 11
                }
            })
            print("Header formatting applied successfully")
            
        except Exception as e:
            print(f"Warning: Could not update headers: {e}")
    
    def update_spreadsheet_title(self, month: int):
        """
        更新 Google Sheets 檔案名稱
            month: 月份 (YYYYMM 格式)
        """
        try:
            new_title = Config.REPORT_FILE_NAME_FORMAT.format(month=month)
            self.spreadsheet.update_title(new_title)
            print(f"Spreadsheet title updated to: {new_title}")
        except Exception as e:
            print(f"Warning: Could not update spreadsheet title: {e}")
    
    def _write_row_by_row(self, worksheet: gspread.Worksheet, values: list, start_row: int):
        """
        逐行寫入資料（備用方法）
        """
        print("Attempting row-by-row write...")
        successful_rows = 0
        
        for i, row_data in enumerate(values):
            try:
                row_num = start_row + i
                cell_range = f'A{row_num}:J{row_num}'
                worksheet.update(cell_range, [row_data])
                successful_rows += 1
            except Exception as e:
                print(f"Error writing row {i+1}: {e}")
                continue
        
        print(f"Successfully wrote {successful_rows}/{len(values)} rows")
    
    def _remove_existing_month_data(self, worksheet: gspread.Worksheet, month: int):
        """
        移除已存在的月份資料
            worksheet: 工作表物件
            month: 月份
        """
        all_values = worksheet.get_all_values()
        
        if len(all_values) <= 1:  # 只有標題列
            return
        
        # 找到要刪除的行
        rows_to_delete = []
        for i, row in enumerate(all_values[1:], start=2):  
            if row and row[0] == str(month): 
                rows_to_delete.append(i)
        
        # 從後往前刪除，避免行號變動
        for row_num in reversed(rows_to_delete):
            worksheet.delete_rows(row_num)
    
    def _format_null_cells(self, worksheet: gspread.Worksheet, data: pd.DataFrame, start_row: int):
        """
        格式化包含 null 值的儲存格
            worksheet: 工作表物件
            data: 資料
            start_row: 開始行號
        """
        # 設 null 欄位底色
        null_format = {
            'backgroundColor': {
                'red': 1.0,           
                'green': 242/255, 
                'blue': 204/255
            },
            'textFormat': {
                'fontSize': 11
            }
        }
        
        for row_idx, (_, row) in enumerate(data.iterrows()):
            actual_row = start_row + row_idx
            
            for col_idx, value in enumerate(row):
                if (pd.isna(value) or 
                    value in [Config.ERROR_MESSAGES["NULL_VALUE"], 
                             Config.ERROR_MESSAGES["NOT_FOUND_BILLING"],
                             Config.ERROR_MESSAGES["NOT_FOUND_CUSTOMER"]]):
                    # 將欄位索引轉換為字母
                    col_letter = chr(65 + col_idx)  
                    cell_range = f'{col_letter}{actual_row}'
                    try:
                        worksheet.format(cell_range, null_format)
                    except Exception as e:
                        print(f"Warning: Could not format cell {cell_range}: {e}")
    
    def get_waiting_records(self, year: int) -> list:
        """
        取得所有狀態為 "waiting" 的記錄
        Returns: 包含 waiting 狀態記錄的清單
        """
        try:
            worksheet = self.get_or_create_worksheet(year)
            all_values = worksheet.get_all_values()
            
            if len(all_values) <= 1:  
                return []
            
            headers = all_values[0]
            waiting_records = []
            
            # 找到 Customer<>CM 欄位
            try:
                cm_col_idx = headers.index("Customer<>CM")
                month_col_idx = headers.index("Month")
                billing_name_col_idx = headers.index("Billing Account Name")
            except ValueError as e:
                print(f"Column not found: {e}")
                return []
            
            # 尋找 waiting 狀態的記錄
            for row_idx, row in enumerate(all_values[1:], start=2):
                if (len(row) > cm_col_idx and 
                    row[cm_col_idx] == "waiting"):
                    
                    waiting_records.append({
                        'row_number': row_idx,
                        'month': row[month_col_idx] if len(row) > month_col_idx else '',
                        'billing_account_name': row[billing_name_col_idx] if len(row) > billing_name_col_idx else '',
                        'current_status': row[cm_col_idx]
                    })
            
            return waiting_records
            
        except gspread.WorksheetNotFound:
            return []
    
    def update_payment_status(self, year: int, updates: list):
        """
        批次更新付款狀態
            year: 年份
            updates: 更新清單 [{'row_number': int, 'new_status': str}]
        """
        if not updates:
            return
        
        worksheet = self.get_or_create_worksheet(year)
        headers = worksheet.row_values(1)
        
        try:
            cm_col_idx = headers.index("Customer<>CM")
            col_letter = chr(65 + cm_col_idx)  # 轉換為字母
            
            # 批次更新
            batch_updates = []
            for update in updates:
                cell_range = f'{col_letter}{update["row_number"]}'
                batch_updates.append({
                    'range': cell_range,
                    'values': [[update['new_status']]]
                })
            
            if batch_updates:
                worksheet.batch_update(batch_updates)
                
        except ValueError as e:
            print(f"Error updating payment status: {e}")
        except Exception as e:
            print(f"Unexpected error updating payment status: {e}")