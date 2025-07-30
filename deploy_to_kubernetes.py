#!/usr/bin/env python3
"""
Kubernetes部署脚本
用于自动化部署CloudPose服务到Kubernetes集群
"""

import subprocess
import sys
import time
import json
import base64
import os
from pathlib import Path

class KubernetesDeployer:
    def __init__(self):
        self.namespace = "cloudpose"
        self.deployment_name = "cloudpose-deployment"
        self.service_name = "cloudpose-service"
        self.image_name = "cloudpose:latest"
        
    def run_command(self, command, description=""):
        """运行命令并处理错误"""
        print(f"🔄 {description}")
        try:
            result = subprocess.run(command, shell=True, check=True, 
                                 capture_output=True, text=True)
            print(f"✅ {description} - 成功")
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"❌ {description} - 失败")
            print(f"错误: {e.stderr}")
            return None
    
    def check_kubernetes_cluster(self):
        """检查Kubernetes集群状态"""
        print("=== 检查Kubernetes集群状态 ===")
        
        # 检查集群连接
        if not self.run_command("kubectl cluster-info", "检查集群连接"):
            print("❌ 无法连接到Kubernetes集群")
            return False
        
        # 检查节点状态
        nodes = self.run_command("kubectl get nodes -o wide", "检查节点状态")
        if nodes:
            print(nodes)
        
        # 检查命名空间
        namespaces = self.run_command("kubectl get namespaces", "检查命名空间")
        if namespaces:
            print(namespaces)
        
        return True
    
    def create_namespace(self):
        """创建命名空间"""
        print("=== 创建命名空间 ===")
        
        namespace_yaml = f"""
apiVersion: v1
kind: Namespace
metadata:
  name: {self.namespace}
  labels:
    name: {self.namespace}
"""
        
        # 创建临时文件
        with open("namespace.yaml", "w") as f:
            f.write(namespace_yaml)
        
        # 应用命名空间
        if self.run_command(f"kubectl apply -f namespace.yaml", "创建命名空间"):
            os.remove("namespace.yaml")
            return True
        else:
            return False
    
    def build_and_push_image(self):
        """构建并推送Docker镜像"""
        print("=== 构建Docker镜像 ===")
        
        # 检查Dockerfile是否存在
        if not os.path.exists("Dockerfile"):
            print("❌ Dockerfile不存在")
            return False
        
        # 构建镜像
        if not self.run_command(f"docker build -t {self.image_name} .", "构建Docker镜像"):
            return False
        
        # 检查镜像是否构建成功
        if not self.run_command(f"docker images {self.image_name}", "检查镜像"):
            return False
        
        return True
    
    def create_model_configmap(self):
        """创建模型ConfigMap"""
        print("=== 创建模型ConfigMap ===")
        
        model_path = "yolo11l-pose.pt"
        if not os.path.exists(model_path):
            print(f"❌ 模型文件不存在: {model_path}")
            return False
        
        # 将模型文件转换为base64
        with open(model_path, "rb") as f:
            model_data = base64.b64encode(f.read()).decode()
        
        # 创建ConfigMap YAML
        configmap_yaml = f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: cloudpose-model
  namespace: {self.namespace}
data:
  yolo11l-pose.pt: |
    {model_data}
"""
        
        with open("model-configmap.yaml", "w") as f:
            f.write(configmap_yaml)
        
        # 应用ConfigMap
        if self.run_command(f"kubectl apply -f model-configmap.yaml", "创建模型ConfigMap"):
            os.remove("model-configmap.yaml")
            return True
        else:
            return False
    
    def deploy_application(self):
        """部署应用程序"""
        print("=== 部署应用程序 ===")
        
        # 应用部署配置
        if not self.run_command(f"kubectl apply -f deployment.yaml", "部署应用程序"):
            return False
        
        # 等待部署完成
        print("⏳ 等待部署完成...")
        time.sleep(30)
        
        # 检查部署状态
        deployment_status = self.run_command(
            f"kubectl get deployment {self.deployment_name} -n {self.namespace}",
            "检查部署状态"
        )
        if deployment_status:
            print(deployment_status)
        
        # 检查Pod状态
        pod_status = self.run_command(
            f"kubectl get pods -n {self.namespace}",
            "检查Pod状态"
        )
        if pod_status:
            print(pod_status)
        
        return True
    
    def verify_service(self):
        """验证服务状态"""
        print("=== 验证服务状态 ===")
        
        # 检查服务状态
        service_status = self.run_command(
            f"kubectl get service {self.service_name} -n {self.namespace}",
            "检查服务状态"
        )
        if service_status:
            print(service_status)
        
        # 获取NodePort
        nodeport = self.run_command(
            f"kubectl get service {self.service_name} -n {self.namespace} -o jsonpath='{{.spec.ports[0].nodePort}}'",
            "获取NodePort"
        )
        if nodeport:
            print(f"🌐 服务NodePort: {nodeport}")
        
        # 获取节点IP
        node_ip = self.run_command(
            "kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type==\"ExternalIP\")].address}'",
            "获取节点IP"
        )
        if not node_ip:
            node_ip = self.run_command(
                "kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type==\"InternalIP\")].address}'",
                "获取内部IP"
            )
        
        if node_ip and nodeport:
            print(f"🎯 服务访问地址: http://{node_ip.strip()}:{nodeport.strip()}")
        
        return True
    
    def scale_deployment(self, replicas):
        """扩展部署"""
        print(f"=== 扩展部署到 {replicas} 个副本 ===")
        
        if self.run_command(f"kubectl scale deployment {self.deployment_name} --replicas={replicas} -n {self.namespace}", 
                          f"扩展到 {replicas} 个副本"):
            
            # 等待扩展完成
            print("⏳ 等待扩展完成...")
            time.sleep(30)
            
            # 检查Pod状态
            pod_status = self.run_command(
                f"kubectl get pods -n {self.namespace}",
                "检查Pod状态"
            )
            if pod_status:
                print(pod_status)
            
            return True
        else:
            return False
    
    def test_service(self):
        """测试服务功能"""
        print("=== 测试服务功能 ===")
        
        # 获取服务地址
        node_ip = self.run_command(
            "kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type==\"ExternalIP\")].address}'",
            "获取节点IP"
        )
        if not node_ip:
            node_ip = self.run_command(
                "kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type==\"InternalIP\")].address}'",
                "获取内部IP"
            )
        
        nodeport = self.run_command(
            f"kubectl get service {self.service_name} -n {self.namespace} -o jsonpath='{{.spec.ports[0].nodePort}}'",
            "获取NodePort"
        )
        
        if node_ip and nodeport:
            service_url = f"http://{node_ip.strip()}:{nodeport.strip()}"
            
            # 测试健康检查
            health_test = self.run_command(
                f"curl -f {service_url}/health",
                "测试健康检查"
            )
            
            if health_test:
                print("✅ 健康检查通过")
            else:
                print("❌ 健康检查失败")
        
        return True
    
    def show_logs(self):
        """显示Pod日志"""
        print("=== 显示Pod日志 ===")
        
        # 获取Pod名称
        pod_name = self.run_command(
            f"kubectl get pods -n {self.namespace} -o jsonpath='{{.items[0].metadata.name}}'",
            "获取Pod名称"
        )
        
        if pod_name:
            logs = self.run_command(
                f"kubectl logs {pod_name.strip()} -n {self.namespace} --tail=20",
                "显示Pod日志"
            )
            if logs:
                print(logs)
    
    def cleanup(self):
        """清理资源"""
        print("=== 清理资源 ===")
        
        # 删除部署
        self.run_command(f"kubectl delete deployment {self.deployment_name} -n {self.namespace}", "删除部署")
        
        # 删除服务
        self.run_command(f"kubectl delete service {self.service_name} -n {self.namespace}", "删除服务")
        
        # 删除ConfigMap
        self.run_command(f"kubectl delete configmap cloudpose-model -n {self.namespace}", "删除ConfigMap")
        
        # 删除命名空间
        self.run_command(f"kubectl delete namespace {self.namespace}", "删除命名空间")
        
        print("✅ 清理完成")
    
    def deploy(self):
        """执行完整部署流程"""
        print("🚀 开始Kubernetes部署流程")
        print("=" * 50)
        
        # 1. 检查集群状态
        if not self.check_kubernetes_cluster():
            return False
        
        # 2. 创建命名空间
        if not self.create_namespace():
            return False
        
        # 3. 构建镜像
        if not self.build_and_push_image():
            return False
        
        # 4. 创建模型ConfigMap
        if not self.create_model_configmap():
            return False
        
        # 5. 部署应用程序
        if not self.deploy_application():
            return False
        
        # 6. 验证服务
        if not self.verify_service():
            return False
        
        # 7. 测试服务
        if not self.test_service():
            return False
        
        # 8. 显示日志
        self.show_logs()
        
        print("=" * 50)
        print("🎉 Kubernetes部署完成!")
        print("📖 下一步:")
        print("1. 运行负载测试")
        print("2. 扩展Pod数量进行性能测试")
        print("3. 监控服务性能")
        
        return True

def main():
    """主函数"""
    deployer = KubernetesDeployer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "deploy":
            deployer.deploy()
        elif command == "scale":
            if len(sys.argv) > 2:
                replicas = int(sys.argv[2])
                deployer.scale_deployment(replicas)
            else:
                print("用法: python deploy_to_kubernetes.py scale <replicas>")
        elif command == "test":
            deployer.test_service()
        elif command == "logs":
            deployer.show_logs()
        elif command == "cleanup":
            deployer.cleanup()
        else:
            print("未知命令")
    else:
        # 默认执行完整部署
        deployer.deploy()

if __name__ == "__main__":
    main() 