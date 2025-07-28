#!/bin/bash

# CloudPose Kubernetes部署脚本
echo "开始部署CloudPose服务..."

# 1. 构建Docker镜像
echo "步骤1: 构建Docker镜像..."
docker build -f Dockerfile.minimal -t cloudpose:latest .

if [ $? -ne 0 ]; then
    echo "错误: Docker镜像构建失败"
    exit 1
fi

echo "Docker镜像构建成功"

# 2. 验证镜像
echo "步骤2: 验证镜像..."
docker images | grep cloudpose

# 3. 部署到Kubernetes
echo "步骤3: 部署到Kubernetes..."

# 应用部署配置
kubectl apply -f deployment.yaml
if [ $? -ne 0 ]; then
    echo "错误: 部署配置应用失败"
    exit 1
fi

# 应用服务配置
kubectl apply -f service.yaml
if [ $? -ne 0 ]; then
    echo "错误: 服务配置应用失败"
    exit 1
fi

# 4. 等待部署完成
echo "步骤4: 等待部署完成..."
kubectl rollout status deployment/cloudpose-deployment

# 5. 检查部署状态
echo "步骤5: 检查部署状态..."
echo "=== 部署状态 ==="
kubectl get deployments
echo ""
echo "=== 服务状态 ==="
kubectl get services
echo ""
echo "=== Pod状态 ==="
kubectl get pods -l app=cloudpose

# 6. 显示访问信息
echo ""
echo "=== 访问信息 ==="
echo "服务已部署在NodePort 30000"
echo "可以通过以下方式访问:"
echo "http://<MASTER_NODE_IP>:30000"
echo ""
echo "API端点:"
echo "- JSON API: http://<MASTER_NODE_IP>:30000/api/pose"
echo "- 图像API: http://<MASTER_NODE_IP>:30000/api/pose_image"
echo "- 健康检查: http://<MASTER_NODE_IP>:30000/health"

echo ""
echo "部署完成！" 