from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from config import Config
import time

class BigQueryService:
    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(
            Config.SERVICE_ACCOUNT_FILE
        )
        self.client = bigquery.Client(
            credentials=credentials,
            project=Config.PROJECT_ID
        )
    
    def get_latest_month_data(self):
        """
        自動取得最新月份的資料 Returns: (billing_data_df, customer_profile_df, target_month)
        """
        # 查詢最新的月份
        latest_month = self._get_latest_month()
        
        if latest_month is None:
            print("Warning: No data found in tables")
            return pd.DataFrame(), pd.DataFrame(), None
        
        print(f"Latest month found: {latest_month}")
        
        # 檢查資料量
        billing_count = self._get_month_record_count('billing_data', latest_month)
        customer_count = self._get_month_record_count('customer_profile', latest_month)
        
        print(f"Expected records - Billing: {billing_count:,}, Customer: {customer_count:,}")
        
        # 取得該月份的資料
        billing_data = self.get_billing_data_optimized(latest_month)
        customer_profile = self.get_customer_profile(latest_month)
        
        return billing_data, customer_profile, latest_month
    
    def _get_month_record_count(self, table_name: str, month: int) -> int:
        """
        取得指定月份的記錄數量
        """
        query = f"""
        SELECT COUNT(*) as count
        FROM `{Config.PROJECT_ID}.{Config.DATASET_ID}.{table_name}`
        WHERE month = {month}
        """
        
        try:
            result = self.client.query(query).result(timeout=30)
            for row in result:
                return row.count
        except Exception as e:
            print(f"Error counting records: {e}")
            return 0
    
    def get_billing_data_optimized(self, month: int) -> pd.DataFrame:
        """
        只查詢必要欄位，加入聚合
        month: "XXXXXX"
        Returns: 聚合後的 billing_data 資料
        """
        # 在 BigQuery 端先聚合，處理 credits 
        query = f"""
        SELECT 
            billing_account_id,
            currency,
            SUM(cost) as total_cost,
            SUM(
                CASE 
                    WHEN credits IS NOT NULL AND ARRAY_LENGTH(credits) > 0
                    THEN (
                        SELECT SUM(CAST(credit.amount AS FLOAT64)) 
                        FROM UNNEST(credits) AS credit 
                        WHERE credit.amount IS NOT NULL
                    )
                    ELSE 0 
                END
            ) as total_credits,
            month,
            COUNT(*) as record_count
        FROM `{Config.PROJECT_ID}.{Config.DATASET_ID}.{Config.BILLING_DATA_TABLE}`
        WHERE month = {month}
        GROUP BY billing_account_id, currency, month
        """
        
        try:
            print(f"Querying aggregated billing_data for month {month}...")
            start_time = time.time()
            
            # 設定查詢工作
            job_config = bigquery.QueryJobConfig()
            job_config.use_query_cache = True
            job_config.use_legacy_sql = False
            
            query_job = self.client.query(query, job_config=job_config)
            print("Query submitted, waiting for results...")
            
            # 監控查詢進度
            while query_job.state != 'DONE':
                print(f"Query status: {query_job.state}")
                time.sleep(2)
                query_job.reload()
            
            result = query_job.result(timeout=180)  # 3分鐘超時
            
            print("Converting to DataFrame...")
            df = result.to_dataframe()
            
            elapsed_time = time.time() - start_time
            print(f"Retrieved {len(df)} aggregated billing records in {elapsed_time:.2f} seconds")
            
            # 計算 Spending = cost + credits，處理 NaN 值
            df['total_cost'] = df['total_cost'].fillna(0)
            df['total_credits'] = df['total_credits'].fillna(0)
            df['spending'] = df['total_cost'] + df['total_credits']
            
            return df
            
        except Exception as e:
            print(f"Error querying billing_data: {e}")
            return pd.DataFrame()
    
    def _get_latest_month(self) -> int:
        """
        取得資料表中最新的月份
        """
        queries = [
            f"""
            SELECT MAX(month) as latest_month 
            FROM `{Config.PROJECT_ID}.{Config.DATASET_ID}.{Config.BILLING_DATA_TABLE}`
            """,
            f"""
            SELECT MAX(month) as latest_month 
            FROM `{Config.PROJECT_ID}.{Config.DATASET_ID}.{Config.CUSTOMER_PROFILE_TABLE}`
            """
        ]
        
        latest_months = []
        
        for query in queries:
            try:
                job_config = bigquery.QueryJobConfig()
                query_job = self.client.query(query, job_config=job_config)
                result = query_job.result(timeout=30)
                df = result.to_dataframe()
                
                if not df.empty and not pd.isna(df.iloc[0]['latest_month']):
                    latest_months.append(int(df.iloc[0]['latest_month']))
                    
            except Exception as e:
                print(f"Error querying latest month: {e}")
                continue
        
        if not latest_months:
            return None
        
        return min(latest_months)
    
    def get_customer_profile(self, month: int) -> pd.DataFrame:
        """
        取得指定月份的 customer_profile
        """
        query = f"""
        SELECT 
            customer,
            service_set,
            salesrep,
            commission,
            billing_account_id,
            billing_account_name,
            referral_company,
            referral_share_rate,
            month,
            edp_type
        FROM `{Config.PROJECT_ID}.{Config.DATASET_ID}.{Config.CUSTOMER_PROFILE_TABLE}`
        WHERE month = {month}
        """
        
        try:
            print(f"Querying customer_profile for month {month}...")
            start_time = time.time()
            
            job_config = bigquery.QueryJobConfig()
            job_config.use_query_cache = True
            
            query_job = self.client.query(query, job_config=job_config)
            result = query_job.result(timeout=60)
            df = result.to_dataframe()
            
            elapsed_time = time.time() - start_time
            print(f"Retrieved {len(df)} customer_profile records in {elapsed_time:.2f} seconds")
            return df
            
        except Exception as e:
            print(f"Error querying customer_profile: {e}")
            return pd.DataFrame()
    
    def get_billing_account_ids(self, month: int) -> list:
        
        # 從已查詢的資料中取得 billing_account_ids
        customer_profile = self.get_customer_profile(month)
        
        if customer_profile.empty:
            return []
        
        return customer_profile['billing_account_id'].unique().tolist()
    
    def test_connection(self):
        
        # 測試 BigQuery 連線
        try:
            query = f"""
            SELECT COUNT(*) as row_count 
            FROM `{Config.PROJECT_ID}.{Config.DATASET_ID}.{Config.BILLING_DATA_TABLE}`
            LIMIT 1
            """
            result = self.client.query(query).result(timeout=30)
            for row in result:
                print(f"BigQuery connection successful. Total rows in billing_data: {row.row_count:,}")
            return True
        except Exception as e:
            print(f"BigQuery connection failed: {e}")
            return False