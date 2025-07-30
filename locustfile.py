#!/usr/bin/env python3
"""
Locust负载测试脚本
用于测试CloudPose服务的性能
"""

import time
import json
import base64
import os
import random
from locust import HttpUser, task, between
from PIL import Image
import io

class CloudPoseUser(HttpUser):
    """CloudPose负载测试用户类"""
    
    wait_time = between(1, 3)  # 用户等待时间1-3秒
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.images = []
        self.load_test_images()
    
    def load_test_images(self):
        """加载测试图像"""
        # 图像文件夹路径
        image_folder = "../client/inputfolder"
        
        if os.path.exists(image_folder):
            # 获取所有图像文件
            image_files = [f for f in os.listdir(image_folder) 
                         if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            
            for image_file in image_files[:20]:  # 限制加载20张图像
                image_path = os.path.join(image_folder, image_file)
                try:
                    # 读取图像并转换为base64
                    with open(image_path, "rb") as f:
                        image_data = f.read()
                    
                    # 压缩图像以减少传输大小
                    img = Image.open(io.BytesIO(image_data))
                    img = img.resize((640, 480))  # 调整大小
                    
                    # 转换为JPEG格式
                    buffer = io.BytesIO()
                    img.save(buffer, format='JPEG', quality=85)
                    compressed_data = buffer.getvalue()
                    
                    # 转换为base64
                    base64_image = base64.b64encode(compressed_data).decode('utf-8')
                    
                    self.images.append({
                        'id': f"test_{image_file}",
                        'image': base64_image
                    })
                    
                except Exception as e:
                    print(f"加载图像失败 {image_file}: {e}")
        
        # 如果没有找到图像，创建测试数据
        if not self.images:
            self.create_test_data()
    
    def create_test_data(self):
        """创建测试数据"""
        # 创建一个简单的测试图像
        img = Image.new('RGB', (640, 480), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        test_image_data = buffer.getvalue()
        base64_image = base64.b64encode(test_image_data).decode('utf-8')
        
        self.images.append({
            'id': 'test_image_1',
            'image': base64_image
        })
    
    @task(3)
    def test_pose_detection_json(self):
        """测试姿态检测JSON API"""
        if not self.images:
            return
        
        # 随机选择一张图像
        test_data = random.choice(self.images)
        
        # 准备请求数据
        payload = {
            "id": test_data['id'],
            "image": test_data['image']
        }
        
        # 发送请求
        with self.client.post(
            "/api/pose",
            json=payload,
            headers={"Content-Type": "application/json"},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    # 验证响应格式
                    if 'count' in result and 'keypoints' in result:
                        response.success()
                    else:
                        response.failure("响应格式不正确")
                except json.JSONDecodeError:
                    response.failure("响应不是有效的JSON")
            else:
                response.failure(f"HTTP错误: {response.status_code}")
    
    @task(1)
    def test_pose_detection_image(self):
        """测试姿态检测图像API"""
        if not self.images:
            return
        
        # 随机选择一张图像
        test_data = random.choice(self.images)
        
        # 准备请求数据
        payload = {
            "id": test_data['id'],
            "image": test_data['image']
        }
        
        # 发送请求
        with self.client.post(
            "/api/pose_image",
            json=payload,
            headers={"Content-Type": "application/json"},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    # 验证响应格式
                    if 'id' in result and 'image' in result:
                        response.success()
                    else:
                        response.failure("响应格式不正确")
                except json.JSONDecodeError:
                    response.failure("响应不是有效的JSON")
            else:
                response.failure(f"HTTP错误: {response.status_code}")
    
    @task(1)
    def test_health_check(self):
        """测试健康检查"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"健康检查失败: {response.status_code}")
    
    @task(1)
    def test_docs(self):
        """测试API文档"""
        with self.client.get("/docs", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"文档访问失败: {response.status_code}")

class CloudPoseLoadTest:
    """CloudPose负载测试类"""
    
    def __init__(self, host_url):
        self.host_url = host_url
        self.results = []
    
    def run_basic_test(self):
        """运行基本功能测试"""
        import requests
        
        print("=== 基本功能测试 ===")
        
        # 测试健康检查
        try:
            response = requests.get(f"{self.host_url}/health", timeout=10)
            print(f"健康检查: {response.status_code}")
        except Exception as e:
            print(f"健康检查失败: {e}")
        
        # 测试API文档
        try:
            response = requests.get(f"{self.host_url}/docs", timeout=10)
            print(f"API文档: {response.status_code}")
        except Exception as e:
            print(f"API文档访问失败: {e}")
    
    def run_performance_test(self, num_users=10, spawn_rate=1, run_time=60):
        """运行性能测试"""
        import subprocess
        
        print(f"=== 性能测试 ===")
        print(f"用户数: {num_users}")
        print(f"生成速率: {spawn_rate} 用户/秒")
        print(f"运行时间: {run_time} 秒")
        
        # 构建Locust命令
        cmd = [
            "locust",
            "-f", "locustfile.py",
            "--host", self.host_url,
            "--users", str(num_users),
            "--spawn-rate", str(spawn_rate),
            "--run-time", f"{run_time}s",
            "--headless",  # 无界面模式
            "--html", "report.html",  # 生成HTML报告
            "--csv", "results"  # 生成CSV报告
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            print("性能测试完成")
            print(f"退出码: {result.returncode}")
            if result.stdout:
                print("输出:", result.stdout)
            if result.stderr:
                print("错误:", result.stderr)
        except Exception as e:
            print(f"性能测试失败: {e}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CloudPose负载测试")
    parser.add_argument("--host", required=True, help="服务主机地址")
    parser.add_argument("--users", type=int, default=10, help="并发用户数")
    parser.add_argument("--spawn-rate", type=int, default=1, help="用户生成速率")
    parser.add_argument("--run-time", type=int, default=60, help="运行时间(秒)")
    parser.add_argument("--test-type", choices=["basic", "performance", "both"], 
                       default="both", help="测试类型")
    
    args = parser.parse_args()
    
    # 创建测试实例
    tester = CloudPoseLoadTest(args.host)
    
    if args.test_type in ["basic", "both"]:
        tester.run_basic_test()
    
    if args.test_type in ["performance", "both"]:
        tester.run_performance_test(args.users, args.spawn_rate, args.run_time)

if __name__ == "__main__":
    main() 