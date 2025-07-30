# Kubernetes集群安装和部署指南

## 概述

本指南介绍如何在Oracle Cloud Infrastructure (OCI) 或阿里云上安装和配置Kubernetes集群，并部署CloudPose服务。

## 系统要求

### 硬件要求
- **内存**: 4GB (每个节点)
- **CPU**: 2 OCPUs (每个节点)
- **存储**: 至少20GB可用空间
- **网络**: 稳定的网络连接

### 软件要求
- **操作系统**: Ubuntu 20.04 LTS 或更高版本
- **Docker**: 20.10 或更高版本
- **Kubernetes**: 1.28.0 或更高版本

## 步骤1: 准备云服务器

### 1.1 创建VM实例

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

### 1.2 配置安全组

开放以下端口：

**Master节点**:
- 22 (SSH)
- 6443 (Kubernetes API)
- 2379-2380 (etcd)
- 10250 (Kubelet)
- 10251 (kube-scheduler)
- 10252 (kube-controller-manager)
- 30000-32767 (NodePort服务)

**Worker节点**:
- 22 (SSH)
- 10250 (Kubelet)
- 30000-32767 (NodePort服务)

## 步骤2: 安装Kubernetes集群

### 2.1 在Master节点上执行

```bash
# 1. 连接到Master节点
ssh ubuntu@<master-ip>

# 2. 下载安装脚本
wget https://raw.githubusercontent.com/your-repo/kubernetes_setup.sh
chmod +x kubernetes_setup.sh

# 3. 运行安装脚本 (选择Master节点)
sudo ./kubernetes_setup.sh
# 选择: 1) Master节点

# 4. 记录join命令
kubeadm token create --print-join-command
```

### 2.2 在Worker节点上执行

```bash
# 1. 连接到Worker节点
ssh ubuntu@<worker-ip>

# 2. 下载安装脚本
wget https://raw.githubusercontent.com/your-repo/kubernetes_setup.sh
chmod +x kubernetes_setup.sh

# 3. 运行安装脚本 (选择Worker节点)
sudo ./kubernetes_setup.sh
# 选择: 2) Worker节点

# 4. 输入join命令 (从Master节点获取)
# 例如: kubeadm join 10.0.0.10:6443 --token abc123... --discovery-token-ca-cert-hash sha256:...
```

### 2.3 验证集群状态

在Master节点上执行：

```bash
# 检查节点状态
kubectl get nodes -o wide

# 检查Pod状态
kubectl get pods --all-namespaces

# 检查集群信息
kubectl cluster-info
```

## 步骤3: 部署CloudPose服务

### 3.1 准备部署文件

确保以下文件在Master节点上：

```
FIT5225_As1/
├── deployment.yaml          # Kubernetes部署配置
├── deploy_to_kubernetes.py  # 自动化部署脚本
├── Dockerfile              # Docker镜像构建文件
├── main.py                 # Web服务代码
├── pose_detector.py        # 姿态检测代码
└── yolo11l-pose.pt        # 模型文件
```

### 3.2 执行部署

```bash
# 1. 进入项目目录
cd FIT5225_As1

# 2. 运行部署脚本
python3 deploy_to_kubernetes.py deploy

# 3. 验证部署
kubectl get pods -n cloudpose
kubectl get services -n cloudpose
```

### 3.3 测试服务

```bash
# 获取服务地址
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}')
NODEPORT=$(kubectl get service cloudpose-service -n cloudpose -o jsonpath='{.spec.ports[0].nodePort}')

# 测试健康检查
curl http://$NODE_IP:$NODEPORT/health

# 测试API文档
curl http://$NODE_IP:$NODEPORT/docs
```

## 步骤4: 扩展和测试

### 4.1 扩展Pod数量

```bash
# 扩展到2个Pod
python3 deploy_to_kubernetes.py scale 2

# 扩展到3个Pod
python3 deploy_to_kubernetes.py scale 3

# 扩展到4个Pod
python3 deploy_to_kubernetes.py scale 4
```

### 4.2 监控服务

```bash
# 查看Pod状态
kubectl get pods -n cloudpose

# 查看服务日志
python3 deploy_to_kubernetes.py logs

# 查看资源使用情况
kubectl top pods -n cloudpose
```

## 步骤5: 负载测试

### 5.1 在Master节点上运行Locust

```bash
# 安装Locust
pip3 install locust

# 运行负载测试
locust -f locustfile.py --host=http://$NODE_IP:$NODEPORT
```

### 5.2 在另一个VM上运行Locust

```bash
# 连接到测试VM
ssh ubuntu@<test-vm-ip>

# 安装Locust
pip3 install locust

# 运行负载测试
locust -f locustfile.py --host=http://$MASTER_IP:$NODEPORT
```

## 故障排除

### 常见问题

#### 1. Pod无法启动
```bash
# 检查Pod状态
kubectl describe pod <pod-name> -n cloudpose

# 查看Pod日志
kubectl logs <pod-name> -n cloudpose
```

#### 2. 服务无法访问
```bash
# 检查服务状态
kubectl get service cloudpose-service -n cloudpose

# 检查端口映射
kubectl get endpoints cloudpose-service -n cloudpose
```

#### 3. 节点不可用
```bash
# 检查节点状态
kubectl describe node <node-name>

# 检查系统资源
kubectl top nodes
```

### 重置集群

```bash
# 在Master节点上
kubeadm reset

# 在Worker节点上
kubeadm reset

# 重新初始化Master节点
kubeadm init --pod-network-cidr=10.244.0.0/16
```

## 性能优化

### 1. 资源配置

确保每个Pod的资源限制符合要求：
- CPU: 0.5 (请求和限制)
- 内存: 512MiB (请求和限制)

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

## 安全配置

### 1. RBAC配置

```bash
# 创建ServiceAccount
kubectl create serviceaccount cloudpose-sa -n cloudpose

# 创建Role和RoleBinding
kubectl apply -f rbac.yaml
```

### 2. 网络安全

```bash
# 配置网络策略
kubectl apply -f network-policy.yaml

# 启用Pod安全策略
kubectl apply -f pod-security-policy.yaml
```

## 监控和日志

### 1. 安装监控工具

```bash
# 安装Prometheus
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/kube-prometheus/main/manifests/setup/0-namespace.yaml
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/kube-prometheus/main/manifests/setup/
```

### 2. 配置日志收集

```bash
# 安装Fluentd
kubectl apply -f https://raw.githubusercontent.com/fluent/fluentd-kubernetes-daemonset/master/fluentd-daemonset.yaml
```

## 备份和恢复

### 1. 备份配置

```bash
# 备份Kubernetes配置
kubectl get all -n cloudpose -o yaml > cloudpose-backup.yaml

# 备份持久化数据
kubectl get pvc -n cloudpose -o yaml > pvc-backup.yaml
```

### 2. 恢复配置

```bash
# 恢复Kubernetes配置
kubectl apply -f cloudpose-backup.yaml

# 恢复持久化数据
kubectl apply -f pvc-backup.yaml
```

## 总结

通过以上步骤，你已经成功：

1. ✅ 在云服务器上安装了Kubernetes集群
2. ✅ 部署了CloudPose Web服务
3. ✅ 配置了负载均衡和服务发现
4. ✅ 设置了资源限制和健康检查
5. ✅ 准备了负载测试环境

下一步可以：
- 运行Locust负载测试
- 收集性能数据
- 编写实验报告

## 相关文档

- [Kubernetes官方文档](https://kubernetes.io/docs/)
- [Docker官方文档](https://docs.docker.com/)
- [FastAPI部署指南](https://fastapi.tiangolo.com/deployment/)
- [Locust负载测试指南](https://docs.locust.io/) 