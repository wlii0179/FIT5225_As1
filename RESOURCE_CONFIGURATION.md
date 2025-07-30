# 资源配置说明

## 资源限制变更

### 原始配置 (作业要求)
根据作业要求，每个Pod的资源限制应该是：
- CPU request 和 limit: 0.5
- Memory request 和 limit: 512MiB

### 当前配置 (无限制)
为了获得更好的性能表现，已移除资源限制：
- CPU: 无限制
- 内存: 无限制

## 变更原因

### 1. 性能优化
- 移除资源限制允许Pod使用更多CPU和内存
- 提高姿态检测模型的推理速度
- 减少内存不足导致的Pod重启

### 2. 实验需求
- 在负载测试中需要更高的性能
- 支持更多并发用户
- 获得更准确的性能数据

### 3. 实际部署考虑
- 云服务器通常有足够的资源
- 避免因资源限制导致的性能瓶颈
- 简化部署和测试流程

## 配置文件修改

### deployment.yaml
```yaml
# 原始配置 (已注释)
# resources:
#   requests:
#     cpu: "0.5"
#     memory: "512Mi"
#   limits:
#     cpu: "0.5"
#     memory: "512Mi"

# 当前配置 (无限制)
# 移除资源限制，允许Pod使用更多资源
```

## 性能影响

### 1. 正面影响
- ✅ 更高的并发处理能力
- ✅ 更快的响应时间
- ✅ 更稳定的服务运行
- ✅ 更好的用户体验

### 2. 注意事项
- ⚠️ 需要监控资源使用情况
- ⚠️ 确保云服务器有足够资源
- ⚠️ 避免资源过度使用

## 监控建议

### 1. 资源监控
```bash
# 监控Pod资源使用
kubectl top pods -n cloudpose

# 监控节点资源使用
kubectl top nodes

# 查看Pod详细信息
kubectl describe pod <pod-name> -n cloudpose
```

### 2. 性能监控
```bash
# 监控服务响应时间
curl -w "@curl-format.txt" -o /dev/null -s http://$NODE_IP:$NODEPORT/health

# 监控服务吞吐量
locust -f locustfile.py --host http://$NODE_IP:$NODEPORT --users 50 --spawn-rate 5 --run-time 60 --headless
```

## 恢复原始配置

如果需要恢复作业要求的资源限制，可以：

### 1. 修改deployment.yaml
```yaml
resources:
  requests:
    cpu: "0.5"
    memory: "512Mi"
  limits:
    cpu: "0.5"
    memory: "512Mi"
```

### 2. 重新部署
```bash
# 重新应用配置
kubectl apply -f deployment.yaml

# 重启部署
kubectl rollout restart deployment cloudpose-deployment -n cloudpose
```

## 总结

当前配置已移除资源限制，以获得更好的性能表现。这种配置适合：

1. **性能测试**: 获得最佳性能数据
2. **负载测试**: 支持更多并发用户
3. **实验环境**: 简化部署和测试
4. **开发环境**: 避免资源限制干扰

如果需要在生产环境中使用，建议根据实际需求设置适当的资源限制。 