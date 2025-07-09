#!/bin/bash

PROJECT_ID="cloudmile-referral-report"
JOB_NAME="referral-reporter"
REGION="asia-east1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${JOB_NAME}"
SERVICE_ACCOUNT="auto-reporter@${PROJECT_ID}.iam.gserviceaccount.com"

echo "部署開始..."

# 1. 設定 quota project
echo "修正 quota project..."
gcloud auth application-default set-quota-project $PROJECT_ID

# 2. 設定專案
echo "📋 設定專案..."
gcloud config set project $PROJECT_ID

# 3. 檢查 Docker
echo "檢查 Docker..."
if ! docker ps > /dev/null 2>&1; then
    echo "Docker 沒有運行，請先啟動 Docker Desktop"
    exit 1
fi
echo "Docker 運行正常"

# 4. 建立映像
echo "建立 Docker 映像..."
docker build -t $IMAGE_NAME .

# 5. 推送映像
echo "推送映像..."
docker push $IMAGE_NAME

# 6. 刪除舊的 Job (如果存在)
echo "清理舊的 Job..."
gcloud run jobs delete $JOB_NAME --region $REGION --quiet 2>/dev/null || true

# 7. 建立新的 Job (修正參數)
echo "建立 Cloud Run Job..."
gcloud run jobs create $JOB_NAME \
  --image $IMAGE_NAME \
  --region $REGION \
  --memory 4Gi \
  --cpu 2 \
  --max-retries 2 \
  --parallelism 1 \
  --task-timeout 3600 \
  --service-account $SERVICE_ACCOUNT \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID

if [ $? -eq 0 ]; then
    echo "✅ Cloud Run Job 建立成功！"
    echo ""
    echo "🎉 部署完成！"
    echo "===================="
    echo "Job Name: $JOB_NAME"
    echo "Region: $REGION"
    echo "Service Account: $SERVICE_ACCOUNT"
else
    echo "Cloud Run Job 建立失敗"
    exit 1
fi