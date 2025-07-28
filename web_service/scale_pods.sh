#!/bin/bash

# Pod扩展脚本
# 用法: ./scale_pods.sh <number_of_pods>

if [ $# -eq 0 ]; then
    echo "用法: $0 <number_of_pods>"
    echo "例如: $0 2"
    exit 1
fi

POD_COUNT=$1

echo "扩展pods到 $POD_COUNT 个..."

# 更新部署配置中的副本数
kubectl scale deployment cloudpose-deployment --replicas=$POD_COUNT

if [ $? -eq 0 ]; then
    echo "成功扩展到 $POD_COUNT 个pods"
    
    # 等待所有pods就绪
    echo "等待pods就绪..."
    kubectl rollout status deployment/cloudpose-deployment
    
    # 显示当前状态
    echo ""
    echo "=== 当前部署状态 ==="
    kubectl get deployments
    echo ""
    echo "=== 当前Pod状态 ==="
    kubectl get pods -l app=cloudpose
    echo ""
    echo "=== 服务状态 ==="
    kubectl get services
    
    echo ""
    echo "扩展完成！现在有 $POD_COUNT 个pods在运行。"
else
    echo "错误: 扩展失败"
    exit 1
fi 