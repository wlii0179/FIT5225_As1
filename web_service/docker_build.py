#!/usr/bin/env python3
"""
Docker构建和测试脚本
"""

import subprocess
import sys
import time
import requests
import os

def run_command(command, description):
    """运行命令并处理错误"""
    print(f"[RUN] {description}...")
    print(f"   执行命令: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"[OK] {description} 成功")
        if result.stdout:
            print(f"   输出: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} 失败")
        print(f"   错误: {e.stderr}")
        return False

def check_docker_installed():
    """检查Docker是否已安装"""
    return run_command("docker --version", "检查Docker安装")

def build_docker_image():
    """构建Docker镜像"""
    image_name = "cloudpose:latest"
    return run_command(f"docker build -t {image_name} .", f"构建Docker镜像 {image_name}")

def run_docker_container():
    """运行Docker容器"""
    container_name = "cloudpose-test"
    image_name = "cloudpose:latest"
    
    # 停止并删除已存在的容器
    run_command(f"docker stop {container_name} 2>/dev/null || true", "停止旧容器")
    run_command(f"docker rm {container_name} 2>/dev/null || true", "删除旧容器")
    
    # 运行新容器
    command = f"docker run -d --name {container_name} -p 60000:60000 {image_name}"
    return run_command(command, f"运行容器 {container_name}")

def wait_for_container_ready():
    """等待容器启动完成"""
    print("等待容器启动...")
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get("http://localhost:60000/health", timeout=5)
            if response.status_code == 200:
                print("容器启动成功!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        attempt += 1
        time.sleep(2)
        print(f"   尝试 {attempt}/{max_attempts}...")
    
    print("容器启动超时")
    return False

def test_container():
    """测试容器功能"""
    print("测试容器功能...")
    
    # 测试健康检查
    try:
        response = requests.get("http://localhost:60000/health", timeout=10)
        if response.status_code == 200:
            print("健康检查通过")
        else:
            print("健康检查失败")
            return False
    except Exception as e:
        print(f"健康检查异常: {e}")
        return False
    
    # 测试根端点
    try:
        response = requests.get("http://localhost:60000/", timeout=10)
        if response.status_code == 200:
            print("根端点测试通过")
        else:
            print("根端点测试失败")
            return False
    except Exception as e:
        print(f"根端点测试异常: {e}")
        return False
    
    return True

def show_container_info():
    """显示容器信息"""
    print("\n容器信息:")
    run_command("docker ps", "查看运行中的容器")
    run_command("docker images cloudpose", "查看镜像信息")
    run_command("docker logs cloudpose-test --tail 20", "查看容器日志")

def cleanup():
    """清理资源"""
    print("\n清理资源...")
    run_command("docker stop cloudpose-test", "停止测试容器")
    run_command("docker rm cloudpose-test", "删除测试容器")

def main():
    print("=== Docker构建和测试脚本 ===\n")
    
    # 检查Docker安装
    if not check_docker_installed():
        print("Docker未安装，请先安装Docker")
        sys.exit(1)
    
    # 构建镜像
    if not build_docker_image():
        print("Docker镜像构建失败")
        sys.exit(1)
    
    # 运行容器
    if not run_docker_container():
        print("Docker容器启动失败")
        sys.exit(1)
    
    # 等待容器就绪
    if not wait_for_container_ready():
        print("容器启动超时")
        cleanup()
        sys.exit(1)
    
    # 测试容器功能
    if not test_container():
        print("容器功能测试失败")
        cleanup()
        sys.exit(1)
    
    # 显示容器信息
    show_container_info()
    
    print("\nDocker构建和测试完成!")
    print("API文档: http://localhost:60000/docs")
    print("健康检查: http://localhost:60000/health")
    print("JSON API: http://localhost:60000/api/pose")
    print("图像API: http://localhost:60000/api/pose_image")
    
    # 询问是否清理
    try:
        choice = input("\n是否清理测试容器? (y/n): ").lower()
        if choice == 'y':
            cleanup()
            print("清理完成")
    except KeyboardInterrupt:
        print("\n\n用户中断")
        cleanup()

if __name__ == "__main__":
    main() 