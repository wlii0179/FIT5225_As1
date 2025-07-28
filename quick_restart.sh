#!/bin/bash
echo "=== 快速重启Kubernetes集群 ==="

# 1. 重启containerd
echo "重启containerd..."
sudo systemctl restart containerd
sleep 5

# 2. 重启kubelet
echo "重启kubelet..."
sudo systemctl restart kubelet
sleep 10

# 3. 等待API服务器启动
echo "等待API服务器启动..."
for i in {1..30}; do
    if curl -k https://172.20.196.39:6443/healthz 2>/dev/null; then
        echo "API服务器已启动！"
        break
    fi
    echo "等待中... ($i/30)"
    sleep 2
done

# 4. 检查集群状态
echo "检查集群状态..."
kubectl get nodes
kubectl get pods --all-namespaces

echo "重启完成！" 