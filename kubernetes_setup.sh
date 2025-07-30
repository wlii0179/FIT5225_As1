#!/bin/bash

# Kubernetes集群安装脚本
# 适用于Oracle Cloud Infrastructure (OCI) 或 阿里云
# 作者: FIT5225 Assignment 1
# 版本: 1.0

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        exit 1
    fi
}

# 检查操作系统
check_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        log_error "无法检测操作系统"
        exit 1
    fi
    
    log_info "检测到操作系统: $OS $VER"
}

# 禁用swap
disable_swap() {
    log_info "禁用swap..."
    swapoff -a
    sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
    log_success "swap已禁用"
}

# 加载内核模块
load_kernel_modules() {
    log_info "加载必要的内核模块..."
    cat <<EOF | tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

    modprobe overlay
    modprobe br_netfilter
    log_success "内核模块已加载"
}

# 配置内核参数
configure_kernel_params() {
    log_info "配置内核参数..."
    cat <<EOF | tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

    sysctl --system
    log_success "内核参数已配置"
}

# 安装Docker (如果未安装)
install_docker() {
    if command -v docker &> /dev/null; then
        log_info "Docker已安装，版本: $(docker --version)"
        return
    fi
    
    log_info "安装Docker..."
    
    # 卸载旧版本
    apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # 安装依赖
    apt-get update
    apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # 添加Docker官方GPG密钥
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # 添加Docker仓库
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 安装Docker
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # 配置Docker使用systemd
    cat > /etc/docker/daemon.json <<EOF
{
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m"
  },
  "storage-driver": "overlay2"
}
EOF
    
    # 启动Docker
    systemctl enable docker
    systemctl start docker
    
    log_success "Docker安装完成"
}

# 安装Kubernetes组件
install_kubernetes() {
    log_info "安装Kubernetes组件..."
    
    # 添加Kubernetes GPG密钥
    curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/kubernetes-archive-keyring.gpg
    
    # 添加Kubernetes仓库
    echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | tee /etc/apt/sources.list.d/kubernetes.list
    
    # 安装Kubernetes组件
    apt-get update
    apt-get install -y kubelet kubeadm kubectl
    apt-mark hold kubelet kubeadm kubectl
    
    log_success "Kubernetes组件安装完成"
}

# 配置containerd
configure_containerd() {
    log_info "配置containerd..."
    
    mkdir -p /etc/containerd
    containerd config default | tee /etc/containerd/config.toml
    
    # 修改sandbox_image
    sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
    
    # 重启containerd
    systemctl restart containerd
    systemctl enable containerd
    
    log_success "containerd配置完成"
}

# 初始化Master节点
init_master() {
    log_info "初始化Kubernetes Master节点..."
    
    # 获取本机IP
    MASTER_IP=$(hostname -I | awk '{print $1}')
    
    # 初始化集群
    kubeadm init \
        --pod-network-cidr=10.244.0.0/16 \
        --apiserver-advertise-address=$MASTER_IP \
        --kubernetes-version=v1.28.0
    
    # 创建kubeconfig目录
    mkdir -p $HOME/.kube
    cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
    chown $(id -u):$(id -g) $HOME/.kube/config
    
    # 安装Flannel网络插件
    kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml
    
    log_success "Master节点初始化完成"
    
    # 显示join命令
    log_info "Worker节点加入命令:"
    kubeadm token create --print-join-command
}

# 配置Worker节点
configure_worker() {
    log_info "配置Worker节点..."
    
    # 等待用户输入join命令
    echo "请在Master节点运行 'kubeadm token create --print-join-command' 获取join命令"
    echo "然后在此节点运行该命令"
    
    read -p "请输入join命令: " JOIN_CMD
    
    if [[ -n "$JOIN_CMD" ]]; then
        eval $JOIN_CMD
        log_success "Worker节点加入集群完成"
    else
        log_warning "未提供join命令，请手动运行"
    fi
}

# 验证集群状态
verify_cluster() {
    log_info "验证集群状态..."
    
    # 等待节点就绪
    sleep 30
    
    # 检查节点状态
    kubectl get nodes -o wide
    
    # 检查pod状态
    kubectl get pods --all-namespaces
    
    log_success "集群验证完成"
}

# 安装网络插件
install_network_plugin() {
    log_info "安装网络插件 (Flannel)..."
    
    kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml
    
    # 等待网络插件就绪
    kubectl wait --for=condition=ready pod -l app=flannel -n kube-flannel --timeout=300s
    
    log_success "网络插件安装完成"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."
    
    # 开放Kubernetes端口
    ufw allow 6443/tcp  # Kubernetes API server
    ufw allow 2379:2380/tcp  # etcd server client API
    ufw allow 10250/tcp  # Kubelet API
    ufw allow 10251/tcp  # kube-scheduler
    ufw allow 10252/tcp  # kube-controller-manager
    ufw allow 10255/tcp  # Read-only Kubelet API
    ufw allow 179/tcp  # Calico BGP
    ufw allow 4789/udp  # Calico VXLAN
    ufw allow 5473/tcp  # Calico Typha
    ufw allow 9099/tcp  # Calico Felix
    
    log_success "防火墙配置完成"
}

# 主函数
main() {
    echo "=== Kubernetes集群安装脚本 ==="
    echo "适用于: Oracle Cloud Infrastructure (OCI) 或 阿里云"
    echo "节点类型: Master + Worker"
    echo "=================================="
    
    # 检查root权限
    check_root
    
    # 检查操作系统
    check_os
    
    # 询问节点类型
    echo ""
    echo "请选择节点类型:"
    echo "1) Master节点"
    echo "2) Worker节点"
    read -p "请输入选择 (1 或 2): " NODE_TYPE
    
    case $NODE_TYPE in
        1)
            log_info "开始配置Master节点..."
            disable_swap
            load_kernel_modules
            configure_kernel_params
            install_docker
            install_kubernetes
            configure_containerd
            configure_firewall
            init_master
            install_network_plugin
            verify_cluster
            ;;
        2)
            log_info "开始配置Worker节点..."
            disable_swap
            load_kernel_modules
            configure_kernel_params
            install_docker
            install_kubernetes
            configure_containerd
            configure_firewall
            configure_worker
            ;;
        *)
            log_error "无效选择"
            exit 1
            ;;
    esac
    
    log_success "Kubernetes集群安装完成!"
    echo ""
    echo "下一步操作:"
    echo "1. 在Master节点运行: kubectl get nodes"
    echo "2. 部署CloudPose服务"
    echo "3. 配置负载均衡"
}

# 运行主函数
main "$@" 