#!/bin/bash
while true; do
    echo "=== $(date) ==="
    
    # 检查API服务器
    if curl -k https://172.20.196.39:6443/healthz 2>/dev/null; then
        echo "API服务器: 正常"
        
        # 检查节点
        kubectl get nodes 2>/dev/null || echo "无法获取节点信息"
        
        # 检查pods
        kubectl get pods --all-namespaces 2>/dev/null || echo "无法获取pods信息"
    else
        echo "API服务器: 断联"
    fi
    
    echo "等待30秒..."
    sleep 30
done 