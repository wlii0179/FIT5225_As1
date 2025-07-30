# CloudPose 完整使用指南

## 概述

本指南提供CloudPose项目的完整部署和使用流程，包括Kubernetes集群安装、服务部署、负载测试和实验运行。

## 项目结构

```
FIT5225_As1/
├── kubernetes_setup.sh          # Kubernetes集群安装脚本
├── deployment.yaml              # Kubernetes部署配置
├── deploy_to_kubernetes.py      # 自动化部署脚本
├── locustfile.py               # Locust负载测试脚本
├── experiment_runner.py         # 实验自动化脚本
├── KUBERNETES_SETUP_GUIDE.md   # Kubernetes安装指南
├── USAGE.md                    # 本使用指南
├── web_service/                # Web服务代码
│   ├── main.py
│   ├── pose_detector.py
│   └── yolo11l-pose.pt
└── client/                     # 客户端代码
    ├── cloudpose_client.py
    └── inputfolder/
```

## 快速开始

### 1. 环境准备

#### 1.1 云服务器配置

在OCI或阿里云上创建2个VM实例：

**Master节点**:
- 实例名称: `cloudpose-master`
- 内存: 4GB
- CPU: 2 OCPUs
- 操作系统: Ubuntu 20.04 LTS
- 地域: 香港

**Worker节点**:
- 实例名称: `cloudpose-worker`
- 内存: 4GB
- CPU: 2 OCPUs
- 操作系统: Ubuntu 20.04 LTS
- 地域: 香港

#### 1.2 安全组配置

**Master节点开放端口**:
- 22 (SSH)
- 6443 (Kubernetes API)
- 2379-2380 (etcd)
- 10250 (Kubelet)
- 10251 (kube-scheduler)
- 10252 (kube-controller-manager)
- 30000-32767 (NodePort服务)

**Worker节点开放端口**:
- 22 (SSH)
- 10250 (Kubelet)
- 30000-32767 (NodePort服务)

### 2. Kubernetes集群安装

#### 2.1 在Master节点上执行

```bash
# 1. 连接到Master节点
ssh ubuntu@<master-ip>

# 2. 下载项目文件
git clone <your-repo-url>
cd FIT5225_As1

# 3. 运行Kubernetes安装脚本
chmod +x kubernetes_setup.sh
sudo ./kubernetes_setup.sh
# 选择: 1) Master节点

# 4. 记录join命令
kubeadm token create --print-join-command
```

#### 2.2 在Worker节点上执行

```bash
# 1. 连接到Worker节点
ssh ubuntu@<worker-ip>

# 2. 下载项目文件
git clone <your-repo-url>
cd FIT5225_As1

# 3. 运行Kubernetes安装脚本
chmod +x kubernetes_setup.sh
sudo ./kubernetes_setup.sh
# 选择: 2) Worker节点

# 4. 输入join命令 (从Master节点获取)
# 例如: kubeadm join 10.0.0.10:6443 --token abc123... --discovery-token-ca-cert-hash sha256:...
```

#### 2.3 验证集群状态

在Master节点上执行：

```bash
# 检查节点状态
kubectl get nodes -o wide

# 检查Pod状态
kubectl get pods --all-namespaces

# 检查集群信息
kubectl cluster-info
```

### 3. 部署CloudPose服务

#### 3.1 准备部署文件

确保以下文件在Master节点上：

```bash
# 检查必要文件
ls -la web_service/
ls -la deployment.yaml
ls -la deploy_to_kubernetes.py
```

#### 3.2 执行部署

```bash
# 1. 进入项目目录
cd FIT5225_As1

# 2. 运行部署脚本
python3 deploy_to_kubernetes.py deploy

# 3. 验证部署
kubectl get pods -n cloudpose
kubectl get services -n cloudpose
```

#### 3.3 测试服务

```bash
# 获取服务地址
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}')
NODEPORT=$(kubectl get service cloudpose-service -n cloudpose -o jsonpath='{.spec.ports[0].nodePort}')

# 测试健康检查
curl http://$NODE_IP:$NODEPORT/health

# 测试API文档
curl http://$NODE_IP:$NODEPORT/docs
```

### 4. 负载测试

#### 4.1 安装Locust

```bash
# 安装Locust
pip3 install locust pillow

# 验证安装
locust --version
```

#### 4.2 运行基本测试

```bash
# 运行基本功能测试
python3 locustfile.py --host http://$NODE_IP:$NODEPORT --test-type basic

# 运行性能测试
python3 locustfile.py --host http://$NODE_IP:$NODEPORT --users 10 --spawn-rate 1 --run-time 60
```

#### 4.3 运行完整测试

```bash
# 运行完整测试
python3 locustfile.py --host http://$NODE_IP:$NODEPORT --test-type both --users 20 --spawn-rate 2 --run-time 120
```

### 5. 实验运行

#### 5.1 扩展Pod数量

```bash
# 扩展到2个Pod
python3 deploy_to_kubernetes.py scale 2

# 扩展到3个Pod
python3 deploy_to_kubernetes.py scale 3

# 扩展到4个Pod
python3 deploy_to_kubernetes.py scale 4
```

#### 5.2 运行自动化实验

```bash
# 运行完整实验
python3 experiment_runner.py --master-ip $NODE_IP --nodeport $NODEPORT

# 运行特定位置测试
python3 experiment_runner.py --master-ip $NODE_IP --nodeport $NODEPORT --test-location master_node
```

## 详细操作指南

### 1. Kubernetes集群管理

#### 1.1 检查集群状态

```bash
# 检查节点
kubectl get nodes -o wide

# 检查命名空间
kubectl get namespaces

# 检查所有Pod
kubectl get pods --all-namespaces

# 检查服务
kubectl get services --all-namespaces
```

#### 1.2 查看日志

```bash
# 查看Pod日志
kubectl logs <pod-name> -n cloudpose

# 查看服务日志
python3 deploy_to_kubernetes.py logs

# 实时查看日志
kubectl logs -f <pod-name> -n cloudpose
```

#### 1.3 故障排除

```bash
# 检查Pod状态
kubectl describe pod <pod-name> -n cloudpose

# 检查服务状态
kubectl describe service cloudpose-service -n cloudpose

# 检查节点状态
kubectl describe node <node-name>
```

### 2. 服务管理

#### 2.1 扩展服务

```bash
# 手动扩展
kubectl scale deployment cloudpose-deployment --replicas=4 -n cloudpose

# 使用脚本扩展
python3 deploy_to_kubernetes.py scale 4
```

#### 2.2 更新服务

```bash
# 重新部署
kubectl rollout restart deployment cloudpose-deployment -n cloudpose

# 查看部署状态
kubectl rollout status deployment cloudpose-deployment -n cloudpose
```

#### 2.3 清理资源

```bash
# 清理所有资源
python3 deploy_to_kubernetes.py cleanup

# 手动清理
kubectl delete namespace cloudpose
```

### 3. 负载测试

#### 3.1 基本测试

```bash
# 测试健康检查
curl -f http://$NODE_IP:$NODEPORT/health

# 测试API文档
curl http://$NODE_IP:$NODEPORT/docs

# 测试JSON API
curl -X POST http://$NODE_IP:$NODEPORT/api/pose \
  -H "Content-Type: application/json" \
  -d '{"id":"test","image":"base64_data"}'
```

#### 3.2 性能测试

```bash
# 运行Locust测试
locust -f locustfile.py --host http://$NODE_IP:$NODEPORT --users 10 --spawn-rate 1 --run-time 60 --headless

# 生成报告
locust -f locustfile.py --host http://$NODE_IP:$NODEPORT --users 20 --spawn-rate 2 --run-time 120 --headless --html report.html --csv results
```

#### 3.3 监控测试

```bash
# 查看Pod资源使用
kubectl top pods -n cloudpose

# 查看节点资源使用
kubectl top nodes

# 查看服务指标
kubectl get endpoints cloudpose-service -n cloudpose
```

### 4. 实验管理

#### 4.1 运行单个实验

```bash
# 运行1个Pod的实验
python3 experiment_runner.py --master-ip $NODE_IP --nodeport $NODEPORT --test-location master_node

# 运行特定配置
python3 experiment_runner.py --master-ip $NODE_IP --nodeport $NODEPORT --test-location nectar_azure
```

#### 4.2 查看实验结果

```bash
# 查看生成的报告
ls -la experiment_report_*/

# 查看详细结果
cat experiment_report_*/detailed_results.json

# 查看表格数据
cat experiment_report_*/experiment_results.csv
```

#### 4.3 生成图表

```bash
# 安装matplotlib
pip3 install matplotlib

# 重新生成图表
python3 experiment_runner.py --master-ip $NODE_IP --nodeport $NODEPORT
```

## 故障排除

### 1. 常见问题

#### 1.1 Pod无法启动

```bash
# 检查Pod状态
kubectl describe pod <pod-name> -n cloudpose

# 查看Pod日志
kubectl logs <pod-name> -n cloudpose

# 检查资源限制
kubectl get pod <pod-name> -n cloudpose -o yaml
```

#### 1.2 服务无法访问

```bash
# 检查服务状态
kubectl get service cloudpose-service -n cloudpose

# 检查端口映射
kubectl get endpoints cloudpose-service -n cloudpose

# 测试端口连通性
telnet $NODE_IP $NODEPORT
```

#### 1.3 节点不可用

```bash
# 检查节点状态
kubectl describe node <node-name>

# 检查系统资源
kubectl top nodes

# 重启kubelet
sudo systemctl restart kubelet
```

### 2. 重置集群

```bash
# 在Master节点上
kubeadm reset

# 在Worker节点上
kubeadm reset

# 重新初始化Master节点
kubeadm init --pod-network-cidr=10.244.0.0/16
```

### 3. 清理资源

```bash
# 删除所有资源
kubectl delete namespace cloudpose

# 删除Docker镜像
docker rmi cloudpose:latest

# 清理磁盘空间
docker system prune -a
```

## 性能优化

### 1. 资源配置

已移除资源限制，允许Pod使用更多资源：
- CPU: 无限制
- 内存: 无限制

### 2. 网络优化

```bash
# 配置网络策略
kubectl apply -f network-policy.yaml

# 优化DNS设置
kubectl patch deployment cloudpose-deployment -n cloudpose -p '{"spec":{"template":{"spec":{"dnsPolicy":"ClusterFirst"}}}}'
```

### 3. 存储优化

```bash
# 使用本地存储
kubectl patch deployment cloudpose-deployment -n cloudpose -p '{"spec":{"template":{"spec":{"volumes":[{"name":"tmp","emptyDir":{}}]}}}}'
```

## 监控和维护

### 1. 系统监控

```bash
# 监控Pod状态
watch kubectl get pods -n cloudpose

# 监控资源使用
watch kubectl top pods -n cloudpose

# 监控服务状态
watch kubectl get services -n cloudpose
```

### 2. 日志管理

```bash
# 查看实时日志
kubectl logs -f deployment/cloudpose-deployment -n cloudpose

# 导出日志
kubectl logs deployment/cloudpose-deployment -n cloudpose > cloudpose.log

# 清理日志
kubectl logs deployment/cloudpose-deployment -n cloudpose --previous
```

### 3. 备份和恢复

```bash
# 备份配置
kubectl get all -n cloudpose -o yaml > cloudpose-backup.yaml

# 恢复配置
kubectl apply -f cloudpose-backup.yaml
```

## 总结

通过以上步骤，你已经成功：

1. ✅ 在云服务器上安装了Kubernetes集群
2. ✅ 部署了CloudPose Web服务
3. ✅ 配置了负载均衡和服务发现
4. ✅ 设置了资源限制和健康检查
5. ✅ 运行了负载测试和性能实验
6. ✅ 收集了实验数据和生成报告

下一步可以：
- 分析实验结果
- 编写实验报告
- 优化系统性能
- 准备视频演示

## 相关文档

- [Kubernetes官方文档](https://kubernetes.io/docs/)
- [Docker官方文档](https://docs.docker.com/)
- [FastAPI部署指南](https://fastapi.tiangolo.com/deployment/)
- [Locust负载测试指南](https://docs.locust.io/)
- [KUBERNETES_SETUP_GUIDE.md](KUBERNETES_SETUP_GUIDE.md) 