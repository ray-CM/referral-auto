#!/usr/bin/env python3
"""
Production API 測試工具
測試 API 連線和認證
"""

import requests
from requests_oauthlib import OAuth1
from config import Config
import json

def test_oauth_credentials():
    """
    測試 1: OAuth 認證設定是否正確
    成本: 0 (不發送請求)
    """
    print("=" * 50)
    print("測試 1: OAuth 認證設定檢查")
    print("=" * 50)
    
    print(f"Base URL: {Config.NETSUITE_BASE_URL}")
    print(f"Realm: {Config.NETSUITE_REALM}")
    print(f"Consumer Key: {Config.NETSUITE_CONSUMER_KEY[:8]}...{Config.NETSUITE_CONSUMER_KEY[-8:]}")
    print(f"Consumer Secret: {Config.NETSUITE_CONSUMER_SECRET[:8]}...{Config.NETSUITE_CONSUMER_SECRET[-8:]}")
    print(f"Token: {Config.NETSUITE_TOKEN[:8]}...{Config.NETSUITE_TOKEN[-8:]}")
    print(f"Token Secret: {Config.NETSUITE_TOKEN_SECRET[:8]}...{Config.NETSUITE_TOKEN_SECRET[-8:]}")
    
    # 檢查是否還有 Sandbox 設定殘留
    if "sb2" in Config.NETSUITE_BASE_URL.lower():
        print("⚠️  警告: URL 中仍包含 'sb2'，可能未正確更新")
        return False
    
    if "sb2" in Config.NETSUITE_REALM.lower():
        print("⚠️  警告: Realm 中仍包含 'SB2'，可能未正確更新")
        return False
    
    print("✅ OAuth 設定檢查通過")
    return True

def test_single_api_call():
    """
    測試 2: 單次 API 呼叫
    成本: 1 次 API 呼叫 (最小測試)
    """
    print("\n" + "=" * 50)
    print("測試 2: Production API 連線測試")
    print("=" * 50)
    
    # 使用最小的測試參數
    test_month = "202506"
    test_billing_id = "dummy-test-id"  # 使用假的 ID 進行連線測試
    
    # 設定 OAuth
    oauth = OAuth1(
        Config.NETSUITE_CONSUMER_KEY,
        client_secret=Config.NETSUITE_CONSUMER_SECRET,
        resource_owner_key=Config.NETSUITE_TOKEN,
        resource_owner_secret=Config.NETSUITE_TOKEN_SECRET,
        signature_method='HMAC-SHA256',
        realm=Config.NETSUITE_REALM
    )
    
    # 準備 API 參數
    params = {
        'script': Config.NETSUITE_SCRIPT_ID,
        'deploy': Config.NETSUITE_DEPLOY_ID,
        'month': test_month,
        'billing_account_ids': test_billing_id
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        print(f"發送請求到: {Config.NETSUITE_BASE_URL}")
        print(f"測試參數: month={test_month}, billing_account_ids={test_billing_id}")
        
        response = requests.get(
            Config.NETSUITE_BASE_URL,
            params=params,
            headers=headers,
            auth=oauth,
            timeout=10
        )
        
        print(f"HTTP 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API 連線成功！")
            try:
                data = response.json()
                print(f"回應格式: {type(data)}")
                if isinstance(data, dict) and 'data' in data:
                    print(f"資料結構: 包含 'data' 欄位")
                    print("✅ API 回應格式正確")
                else:
                    print(f"實際回應: {data}")
            except json.JSONDecodeError:
                print(f"回應內容 (非 JSON): {response.text[:200]}")
        
        elif response.status_code == 401:
            print("❌ 認證失敗 - 請檢查 OAuth 認證資訊")
            print(f"回應內容: {response.text}")
            return False
        
        elif response.status_code == 404:
            print("❌ API 端點不存在 - 請檢查 URL 設定")
            print(f"回應內容: {response.text}")
            return False
        
        else:
            print(f"⚠️  未預期的狀態碼: {response.status_code}")
            print(f"回應內容: {response.text[:200]}")
        
        return response.status_code == 200
        
    except requests.exceptions.Timeout:
        print("❌ 請求超時")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 連線錯誤")
        return False
    except Exception as e:
        print(f"❌ 未知錯誤: {e}")
        return False

def test_real_data_minimal():
    """
    測試 3: 使用真實資料的最小測試
    成本: 1 次 API 呼叫 (使用一個真實的 billing_account_id)
    """
    print("\n" + "=" * 50)
    print("測試 3: 真實資料最小測試")
    print("=" * 50)
    
    # 使用一個已知存在的 billing_account_id (從您的資料中)
    real_billing_id = "01AB50-D7F322-D81D48"  # 從 API 文件範例中取得
    test_month = "202506"
    
    oauth = OAuth1(
        Config.NETSUITE_CONSUMER_KEY,
        client_secret=Config.NETSUITE_CONSUMER_SECRET,
        resource_owner_key=Config.NETSUITE_TOKEN,
        resource_owner_secret=Config.NETSUITE_TOKEN_SECRET,
        signature_method='HMAC-SHA256',
        realm=Config.NETSUITE_REALM
    )
    
    params = {
        'script': Config.NETSUITE_SCRIPT_ID,
        'deploy': Config.NETSUITE_DEPLOY_ID,
        'month': test_month,
        'billing_account_ids': real_billing_id
    }
    
    try:
        print(f"測試真實 billing_account_id: {real_billing_id}")
        
        response = requests.get(
            Config.NETSUITE_BASE_URL,
            params=params,
            headers={'Content-Type': 'application/json'},
            auth=oauth,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 真實資料測試成功！")
            
            if 'data' in data and data['data']:
                print(f"找到 {len(data['data'])} 筆發票記錄")
                # 只顯示第一筆的基本資訊
                first_invoice = data['data'][0]
                print(f"範例發票: {first_invoice.get('invoice_number', 'N/A')}")
                print(f"付款狀態: {first_invoice.get('payment_status', 'N/A')}")
                print("✅ Production API 完全正常！")
            else:
                print("ℹ️  該 billing_account_id 在當月沒有發票記錄")
                print("✅ API 功能正常，但無資料")
            
            return True
        else:
            print(f"❌ 測試失敗: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 測試錯誤: {e}")
        return False

def main():
    """
    主測試流程 - 逐步測試，隨時可停止
    """
    print("Production API 最小成本測試工具")
    print("測試順序：設定檢查 → 連線測試 → 真實資料測試")
    
    # 測試 1: 設定檢查 (成本: 0)
    if not test_oauth_credentials():
        print("\n❌ 設定檢查失敗，請先修正 config.py")
        return
    
    # 測試 2: 基本連線 (成本: 1 API 呼叫)
    input("\n按 Enter 繼續連線測試 (1 次 API 呼叫)...")
    if not test_single_api_call():
        print("\n❌ API 連線失敗，請檢查認證設定")
        return
    
    # 測試 3: 真實資料 (成本: 1 API 呼叫)
    proceed = input("\n是否進行真實資料測試？(y/N): ").lower()
    if proceed == 'y':
        if test_real_data_minimal():
            print("\n🎉 所有測試通過！Production API 已就緒")
        else:
            print("\n⚠️  真實資料測試有問題，請進一步檢查")
    else:
        print("\n✅ 基本測試完成，可手動進行真實資料測試")

if __name__ == "__main__":
    main()