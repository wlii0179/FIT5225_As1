#!/usr/bin/env python3
"""
CloudPose Web Service 启动脚本
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def check_dependencies():
    """检查依赖包是否已安装"""
    required_packages = [
        'fastapi', 'uvicorn', 'ultralytics', 'opencv-python', 
        'torch', 'torchvision', 'numpy', 'Pillow', 'pydantic'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"[OK] {package} 已安装")
        except ImportError:
            missing_packages.append(package)
            print(f"[ERROR] {package} 未安装")
    
    if missing_packages:
        print(f"缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("所有依赖包已安装")
    return True

def check_model_file():
    """检查模型文件是否存在"""
    model_path = Path("yolo11l-pose.pt")
    if not model_path.exists():
        print("模型文件不存在: yolo11l-pose.pt")
        print("请确保模型文件在项目根目录下")
        return False
    
    print(f"模型文件存在: {model_path}")
    return True

def check_port_available(port):
    """检查端口是否可用"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False

def wait_for_server(url, timeout=30):
    """等待服务器启动"""
    print(f"等待服务器启动: {url}")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print("服务器启动成功!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(1)
        print(".", end="", flush=True)
    
    print("\n服务器启动超时")
    return False

def main():
    print("=== CloudPose Web Service 启动脚本 ===")
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 检查模型文件
    if not check_model_file():
        sys.exit(1)
    
    # 设置端口
    port = 60000
    
    # 检查端口是否可用
    if not check_port_available(port):
        print(f"端口 {port} 已被占用")
        print("请关闭占用该端口的程序或修改端口号")
        sys.exit(1)
    
    print(f"端口 {port} 可用")
    
    # 启动服务器
    print(f"\n启动服务器 (端口: {port})...")
    print("按 Ctrl+C 停止服务器")
    
    try:
        # 使用uvicorn启动服务器
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", str(port),
            "--reload"
        ]
        
        # 启动服务器进程
        process = subprocess.Popen(cmd)
        
        # 等待服务器启动
        server_url = f"http://localhost:{port}"
        if wait_for_server(server_url):
            print(f"\nAPI文档: {server_url}/docs")
            print(f"健康检查: {server_url}/health")
            print(f"JSON API: {server_url}/api/pose")
            print(f"图像API: {server_url}/api/pose_image")
        
        # 等待进程结束
        process.wait()
        
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
    except Exception as e:
        print(f"\n启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 