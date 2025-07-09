import pandas as pd
from config import Config

class DataProcessor:
    @staticmethod
    def integrate_data(billing_data: pd.DataFrame, customer_profile: pd.DataFrame, 
                      payment_status: dict) -> pd.DataFrame:
        """
        整合所有資料來源
        """
        # 合併 billing_data 和 customer_profile
        merged_data = DataProcessor._merge_billing_and_customer(
            billing_data, customer_profile
        )
        
        # 加入付款狀態資訊
        merged_data = DataProcessor._add_payment_status(merged_data, payment_status)
        
        # 產生最終輸出格式
        output_data = DataProcessor._format_output(merged_data)
        
        return output_data
    
    @staticmethod
    def _merge_billing_and_customer(billing_data: pd.DataFrame, 
                                   customer_profile: pd.DataFrame) -> pd.DataFrame:
        """
        合併 billing_data 和 customer_profile
        """
        # 檢查 billing_data 是否為聚合後的資料
        if not billing_data.empty:
            if 'total_cost' in billing_data.columns:
                # 已經是聚合後的資料，直接使用，若為原始資料，進行聚合處理
                billing_agg = billing_data.copy()
                # 重新命名欄位
                billing_agg = billing_agg.rename(columns={
                    'total_cost': 'cost',
                    'total_credits': 'credits_amount'
                })
            else:
                def extract_credits_amount(credits_data):
                    """提取 credits 的 amount 值"""
                    if pd.isna(credits_data) or credits_data is None:
                        return 0
                    
                    # 如果是字典格式
                    if isinstance(credits_data, dict):
                        return credits_data.get('amount', 0)
                    
                    # 如果是清單格式
                    if isinstance(credits_data, list):
                        total = 0
                        for credit in credits_data:
                            if isinstance(credit, dict):
                                total += credit.get('amount', 0)
                        return total
                    
                    # 如果是數值
                    try:
                        return float(credits_data)
                    except (ValueError, TypeError):
                        return 0
                
                # 聚合 billing_data ( billing_account_id )
                billing_agg = billing_data.groupby('billing_account_id').agg({
                    'cost': 'sum',
                    'currency': 'first', 
                    'month': 'first'
                }).reset_index()
                
                # 處理 credits 欄位
                billing_data['credits_amount'] = billing_data['credits'].apply(extract_credits_amount)
                credits_sum = billing_data.groupby('billing_account_id')['credits_amount'].sum()
                billing_agg['credits_amount'] = billing_agg['billing_account_id'].map(credits_sum).fillna(0)
            
            # 計算 Spending $$ = cost + credits.amount
            billing_agg['spending'] = billing_agg['cost'] + billing_agg['credits_amount']
        else:
            billing_agg = pd.DataFrame()
        
        # 執行合併
        if not billing_agg.empty and not customer_profile.empty:
            # 兩邊都有資料 - 外部合併
            merged = pd.merge(
                customer_profile, 
                billing_agg, 
                on='billing_account_id', 
                how='outer',
                suffixes=('_customer', '_billing')
            )
        elif not customer_profile.empty:
            # 只有 customer_profile
            merged = customer_profile.copy()
            merged['spending'] = None
            merged['currency'] = None
        elif not billing_agg.empty:
            # 只有 billing_data
            merged = billing_agg.copy()
            for col in ['billing_account_name', 'referral_share_rate', 
                       'referral_company', 'salesrep', 'edp_type']:
                merged[col] = None
        else:
            # 都沒有資料
            return pd.DataFrame()
        
        # 處理資料不一致情況
        merged = DataProcessor._handle_data_inconsistency(merged)
        
        return merged
    
    @staticmethod
    def _handle_data_inconsistency(merged_data: pd.DataFrame) -> pd.DataFrame:
        """
        處理資料不一致的情況
        """
        if merged_data.empty:
            return merged_data
        
        # 在 customer_profile 但不在 billing_data
        mask_customer_only = merged_data['spending'].isna()
        merged_data.loc[mask_customer_only, 'spending'] = Config.ERROR_MESSAGES["NOT_FOUND_BILLING"]
        merged_data.loc[mask_customer_only, 'currency'] = Config.ERROR_MESSAGES["NOT_FOUND_BILLING"]
        
        # 在 billing_data 但不在 customer_profile  
        mask_billing_only = merged_data['billing_account_name'].isna()
        for col in ['billing_account_name', 'referral_company', 'salesrep', 'edp_type']:
            merged_data.loc[mask_billing_only, col] = Config.ERROR_MESSAGES["NOT_FOUND_CUSTOMER"]
        
        # 如果在 billing_data 但不在 customer_profile，應該顯示錯誤訊息
        merged_data.loc[mask_billing_only, 'referral_share_rate'] = Config.ERROR_MESSAGES["NOT_FOUND_CUSTOMER"]
        
        return merged_data
    
    @staticmethod
    def _add_payment_status(merged_data: pd.DataFrame, payment_status: dict) -> pd.DataFrame:
        """
        加入付款狀態資訊
        """
        if merged_data.empty:
            return merged_data
        
        # 為每個 billing_account_id 加入付款狀態
        merged_data['payment_status'] = merged_data['billing_account_id'].map(
            lambda x: payment_status.get(x, Config.ERROR_MESSAGES["INVOICE_NOT_FOUND"])
        )
        
        return merged_data
    
    @staticmethod
    def _format_output(merged_data: pd.DataFrame) -> pd.DataFrame:
        """
        格式化最終輸出
        """
        if merged_data.empty:
            return pd.DataFrame(columns=Config.OUTPUT_COLUMNS)
        
        output = pd.DataFrame()
        
        # Month：使用 customer 的 month，如果沒有則用 billing 的
        if 'month_customer' in merged_data.columns:
            output['Month'] = merged_data['month_customer'].fillna(
                merged_data.get('month_billing', merged_data.get('month', ''))
            )
        else:
            output['Month'] = merged_data.get('month', '')
        
        # Billing Account Name
        output['Billing Account Name'] = merged_data['billing_account_name'].fillna(
            Config.ERROR_MESSAGES["NULL_VALUE"]
        )
        
        # Currency
        output['Currency'] = merged_data['currency'].fillna(
            Config.ERROR_MESSAGES["NULL_VALUE"]
        )
        
        # Spending $$$
        output['Spending $$$'] = merged_data['spending']
        
        # Referral share rate
        def format_referral_rate(rate):
            if pd.isna(rate):
                return Config.ERROR_MESSAGES["NULL_VALUE"]
            elif isinstance(rate, str) and rate in Config.ERROR_MESSAGES.values():
                return rate  
            else:
                return rate
        
        output['Referral share rate'] = merged_data['referral_share_rate'].apply(format_referral_rate)
        
        # Profit $$$ = Spending $$$ × Referral share rate
        output['Profit $$$'] = DataProcessor._calculate_profit(
            merged_data['spending'], 
            merged_data['referral_share_rate']
        )
        
        # Referral Company 
        output['Referral Company'] = merged_data['referral_company'].fillna(
            Config.ERROR_MESSAGES["NULL_VALUE"]
        )
        
        # Customer<>CM (付款狀態)
        output['Customer<>CM'] = merged_data['payment_status']
        
        # Sales
        output['Sales'] = merged_data['salesrep'].fillna(
            Config.ERROR_MESSAGES["NULL_VALUE"]
        )
        
        # EDP status (null 值為空白)
        output['EDP status'] = merged_data['edp_type'].fillna('')
        
        return output
    
    @staticmethod
    def _calculate_profit(spending_series: pd.Series, rate_series: pd.Series) -> pd.Series:
        """
        計算 Profit $$
        """
        def calculate_single_profit(spending, rate):
            # 處理 spending 的錯誤訊息
            if (isinstance(spending, str) and spending in Config.ERROR_MESSAGES.values()):
                return 0.00  
            
            # 處理 rate 的錯誤訊息
            if (isinstance(rate, str) and rate in Config.ERROR_MESSAGES.values()):
                return 0.00  
            
            # rate 為 null 時顯示 $0.00
                return 0.00
            
            # spending 為 null 時顯示 $0.0
            if pd.isna(spending):
                return 0.00
            
            try:
                spending_float = float(spending)
                rate_float = float(rate)
                return spending_float * rate_float
            except (ValueError, TypeError):
                return 0.00  # 轉換失敗時顯示 $0.00
        
        return pd.Series([
            calculate_single_profit(spending, rate) 
            for spending, rate in zip(spending_series, rate_series)
        ])