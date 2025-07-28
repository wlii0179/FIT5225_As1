# Kubernetes集群设置指南

## 前提条件
- 两个OCI实例（4GB内存，2 OCPUs）
- 两个实例都在香港节点
- 实例1作为Master节点，实例2作为Worker节点

## 第一步：在两个实例上安装Docker

### 在Master和Worker节点都执行以下命令：

```bash
# 更新系统
sudo apt-get update

# 安装必要的包
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

# 添加Docker官方GPG密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加Docker仓库
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 将当前用户添加到docker组（避免每次都要sudo）
sudo usermod -aG docker $USER

# 验证Docker安装
docker --version
```

**注意**：添加用户到docker组后需要重新登录才能生效。

## 第二步：在Master节点上安装Kubernetes

### 1. 禁用swap
```bash
sudo swapoff -a
sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
```

### 2. 加载必要的内核模块
```bash
sudo modprobe overlay
sudo modprobe br_netfilter
```

### 3. 设置网络参数
```bash
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

sudo sysctl --system
```

### 4. 安装containerd
```bash
# 配置containerd
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml

# 修改containerd配置以使用systemd cgroup驱动
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml

# 重启containerd
sudo systemctl restart containerd
sudo systemctl enable containerd
```

### 5. 安装Kubernetes组件
```bash
# 添加Kubernetes GPG密钥
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -

# 添加Kubernetes仓库
echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list

# 安装Kubernetes组件
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl

# 固定版本（避免自动升级）
sudo apt-mark hold kubelet kubeadm kubectl
```

### 6. 初始化Kubernetes集群
```bash
# 初始化集群（使用flannel网络插件）
sudo kubeadm init --pod-network-cidr=10.244.0.0/16 --apiserver-advertise-address=<MASTER_PRIVATE_IP>

# 设置kubectl配置
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

### 7. 安装网络插件（Flannel）
```bash
kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml
```

### 8. 获取join命令
```bash
sudo kubeadm token create --print-join-command
```

**保存这个join命令，稍后在Worker节点上使用。**

## 第三步：在Worker节点上安装Kubernetes

### 1. 执行与Master节点相同的步骤1-5（禁用swap、安装containerd、安装Kubernetes组件）

### 2. 加入集群
```bash
# 使用Master节点提供的join命令
sudo kubeadm join <MASTER_PRIVATE_IP>:6443 --token <TOKEN> --discovery-token-ca-cert-hash <HASH>
```

## 第四步：验证集群

### 在Master节点上执行：
```bash
# 查看节点状态
kubectl get nodes

# 查看所有pods
kubectl get pods --all-namespaces

# 查看集群信息
kubectl cluster-info
```

## 第五步：构建和部署Docker镜像

### 1. 在Master节点上构建Docker镜像
```bash
# 进入web_service目录
cd /path/to/FIT5225_As1/web_service

# 构建镜像
docker build -f Dockerfile.minimal -t cloudpose:latest .

# 验证镜像
docker images | grep cloudpose
```

### 2. 创建Kubernetes部署文件
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cloudpose-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cloudpose
  template:
    metadata:
      labels:
        app: cloudpose
    spec:
      containers:
      - name: cloudpose
        image: cloudpose:latest
        ports:
        - containerPort: 60000
        resources:
          requests:
            cpu: "0.5"
            memory: "512Mi"
          limits:
            cpu: "0.5"
            memory: "512Mi"
```

### 3. 创建Service
```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: cloudpose-service
spec:
  type: NodePort
  selector:
    app: cloudpose
  ports:
  - port: 60000
    targetPort: 60000
    nodePort: 30000
```

### 4. 部署应用
```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# 查看部署状态
kubectl get deployments
kubectl get services
kubectl get pods
```

## 第六步：配置OCI安全组

确保在OCI控制台中为Master节点配置以下入站规则：
- 端口22 (SSH)
- 端口6443 (Kubernetes API)
- 端口30000 (NodePort服务)
- 端口10250 (Kubelet)

## 故障排除

### 常见问题：
1. **节点NotReady**：检查网络插件是否正确安装
2. **Pod无法启动**：检查镜像是否存在，资源限制是否合理
3. **服务无法访问**：检查安全组配置和NodePort设置

### 有用的命令：
```bash
# 查看pod日志
kubectl logs <pod-name>

# 查看pod详细信息
kubectl describe pod <pod-name>

# 进入pod
kubectl exec -it <pod-name> -- /bin/bash

# 查看服务端点
kubectl get endpoints
``` 