启动脚本之后，按以下步骤操作：

## 1. 启动监控脚本（Controller节点）
```bash
# 后台运行监控
nohup ./monitor_cluster.sh > cluster_monitor.log 2>&1 &

# 查看监控日志
tail -f cluster_monitor.log
```

## 2. 等待API服务器恢复
监控脚本会每30秒检查一次API服务器状态。当看到：
```
API服务器: 正常
```
时，立即进行下一步。

## 3. 立即生成join命令（Controller节点）
```bash
ww
```
**重要**：API服务器恢复后要立即执行，因为它可能很快又断联！

## 4. Worker节点执行join
复制生成的命令到Worker节点执行：
```bash
sudo kubeadm join 172.20.196.39:6443 --token [token] --discovery-token-ca-cert-hash sha256:[hash] --ignore-preflight-errors=all
```

## 5. 验证Worker是否成功加入
在Controller节点检查：
```bash
kubectl get nodes
```
应该看到两个节点：
- `izj6cfsmp2yjtsi0yzts15z` (Controller)
- `izj6c7kz0ay0sdwtab8pbyZ` (Worker)

## 6. 如果API又断联了
```bash
# 运行快速重启
./quick_restart.sh
```
然后重复步骤2-5。

## 关键策略：
- **抓住时机**：API服务器恢复的窗口期很短
- **快速操作**：准备好所有命令，一旦恢复立即执行
- **持续监控**：保持监控脚本运行，及时发现问题

准备好开始不停的尝试吧！

