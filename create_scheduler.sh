#!/bin/bash

PROJECT_ID="cloudmile-referral-report"
JOB_NAME="referral-reporter"
SCHEDULER_NAME="referral-reporter-trigger"
REGION="asia-east1"
SERVICE_ACCOUNT="auto-reporter@${PROJECT_ID}.iam.gserviceaccount.com"

echo "🔧 重新建立 Scheduler 解決認證問題..."



# 2. 確認服務帳號權限
echo "確認服務帳號權限..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/run.invoker"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/run.developer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/iam.serviceAccountUser"

# 3. 等待權限傳播
echo "等待權限傳播 (30秒)..."
sleep 30

# 4. 重新建立 Scheduler
echo "重新建立 Scheduler..."
JOB_URL="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run"

gcloud scheduler jobs create http $SCHEDULER_NAME \
  --schedule="00 00 10 * *" \
  --time-zone="Asia/Taipei" \
  --uri="$JOB_URL" \
  --http-method=POST \
  --location=$REGION \
  --description="Monthly auto referral report " \
  --oidc-service-account-email=$SERVICE_ACCOUNT \
  --oidc-token-audience="$JOB_URL" \
  --headers="Content-Type=application/json"

if [ $? -eq 0 ]; then
    echo "Scheduler 重新建立成功！"
    
else
    echo "Scheduler 建立失敗"
    exit 1
fi