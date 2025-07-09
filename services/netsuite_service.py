import requests
import json
from requests_oauthlib import OAuth1
from config import Config

class NetSuiteService:
    def __init__(self):
        self.oauth = OAuth1(
            Config.NETSUITE_CONSUMER_KEY,
            client_secret=Config.NETSUITE_CONSUMER_SECRET,
            resource_owner_key=Config.NETSUITE_TOKEN,
            resource_owner_secret=Config.NETSUITE_TOKEN_SECRET,
            signature_method='HMAC-SHA256',
            realm=Config.NETSUITE_REALM
        )
    
    def get_invoice_payment_status(self, month: str, billing_account_ids: list) -> dict:
        """
        查詢發票付款狀態
        Returns: {billing_account_id: payment_status}
        """
        if not billing_account_ids:
            return {}
        
        # 準備 API 參數
        params = {
            'script': Config.NETSUITE_SCRIPT_ID,
            'deploy': Config.NETSUITE_DEPLOY_ID,
            'month': month,
            'billing_account_ids': ','.join(billing_account_ids)
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                Config.NETSUITE_BASE_URL,
                params=params,
                headers=headers,
                auth=self.oauth,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_payment_status(data, billing_account_ids)
            else:
                print(f"NetSuite API Error: {response.status_code} - {response.text}")
                return {bid: Config.ERROR_MESSAGES["API_ERROR"] for bid in billing_account_ids}
                
        except requests.exceptions.RequestException as e:
            print(f"NetSuite API Request Error: {e}")
            return {bid: Config.ERROR_MESSAGES["API_ERROR"] for bid in billing_account_ids}
        except json.JSONDecodeError as e:
            print(f"NetSuite API JSON Parse Error: {e}")
            return {bid: Config.ERROR_MESSAGES["API_ERROR"] for bid in billing_account_ids}
    
    def _parse_payment_status(self, api_response: dict, requested_ids: list) -> dict:
        """
        api_response: NetSuite API 回應   
        Returns: {billing_account_id: payment_status}
        """
        result = {}
        
        # 建立從 API 回應中的對應表
        invoice_mapping = {}
        
        if 'data' in api_response and api_response['data']:
            for invoice in api_response['data']:
                payment_status = invoice.get('payment_status', '')
                items = invoice.get('items', [])
                
                # 對應 NetSuite 狀態到系統狀態
                mapped_status = Config.PAYMENT_STATUS_MAPPING.get(
                    payment_status, 
                    payment_status
                )
                
                for billing_account_id in items:
                    invoice_mapping[billing_account_id] = mapped_status
        
        # 為每個請求的 ID 建立結果
        for billing_account_id in requested_ids:
            if billing_account_id in invoice_mapping:
                result[billing_account_id] = invoice_mapping[billing_account_id]
            else:
                result[billing_account_id] = Config.ERROR_MESSAGES["INVOICE_NOT_FOUND"]
        
        return result
    
    def get_payment_status_by_name(self, month: str, billing_account_name: str) -> str:
        """
        透過 billing_account_name 查詢付款狀態 (check_payment.py) 
        Returns: 付款狀態
        """
        # 查詢該月份的 customer_profile，將 billing_account_name 轉為 billing_account_id，
        from services.bigquery_service import BigQueryService
        bq_service = BigQueryService()

        month_int = int(month)
        customer_profile = bq_service.get_customer_profile(month_int)
        
        if customer_profile.empty:
            return Config.ERROR_MESSAGES["API_ERROR"]
        
        # 找到對應的 billing_account_id
        matching_row = customer_profile[
            customer_profile['billing_account_name'] == billing_account_name
        ]
        
        if matching_row.empty:
            return Config.ERROR_MESSAGES["INVOICE_NOT_FOUND"]
        
        billing_account_id = matching_row.iloc[0]['billing_account_id']
        
        # 查詢付款狀態
        payment_status = self.get_invoice_payment_status(month, [billing_account_id])
        return payment_status.get(billing_account_id, Config.ERROR_MESSAGES["INVOICE_NOT_FOUND"])