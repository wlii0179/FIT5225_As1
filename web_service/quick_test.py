#!/usr/bin/env python3
"""
快速测试脚本 - 验证CloudPose Web服务功能
"""

import requests
import base64
import json
import time
import os
from pathlib import Path

def test_health_check(base_url):
    """测试健康检查端点"""
    print("测试健康检查...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"健康检查成功: {result}")
            return True
        else:
            print(f"健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"健康检查异常: {e}")
        return False

def test_pose_json_api(base_url, image_path):
    """测试姿态检测JSON API"""
    print(f"测试JSON API (图像: {os.path.basename(image_path)})...")
    
    try:
        # 编码图像
        with open(image_path, 'rb') as f:
            image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # 准备请求
        request_data = {
            "id": "test-123",
            "image": image_base64
        }
        
        # 发送请求
        start_time = time.time()
        response = requests.post(
            f"{base_url}/api/pose",
            json=request_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            print(f"JSON API测试成功")
            print(f"   检测到人数: {result['count']}")
            print(f"   响应时间: {(end_time - start_time)*1000:.2f}ms")
            print(f"   预处理时间: {result.get('speed_preprocess', 0)}ms")
            print(f"   推理时间: {result.get('speed_inference', 0)}ms")
            print(f"   后处理时间: {result.get('speed_postprocess', 0)}ms")
            
            # 显示关键点信息
            if result['keypoints']:
                print(f"   关键点数量: {len(result['keypoints'][0])}")
                print("   前3个关键点:")
                for i, kp in enumerate(result['keypoints'][0][:3]):
                    print(f"     {i}: x={kp[0]:.1f}, y={kp[1]:.1f}, conf={kp[2]:.3f}")
            
            return True
        else:
            print(f"JSON API测试失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"JSON API测试异常: {e}")
        return False

def test_pose_image_api(base_url, image_path):
    """测试姿态检测图像API"""
    print(f"测试图像API (图像: {os.path.basename(image_path)})...")
    
    try:
        # 编码图像
        with open(image_path, 'rb') as f:
            image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # 准备请求
        request_data = {
            "id": "test-456",
            "image": image_base64
        }
        
        # 发送请求
        start_time = time.time()
        response = requests.post(
            f"{base_url}/api/pose_image",
            json=request_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            print(f"图像API测试成功")
            print(f"   响应时间: {(end_time - start_time)*1000:.2f}ms")
            
            # 保存标注图像
            if 'annotated_image' in result:
                annotated_data = base64.b64decode(result['annotated_image'])
                output_path = f"test_annotated_{os.path.basename(image_path)}"
                with open(output_path, 'wb') as f:
                    f.write(annotated_data)
                print(f"   标注图像已保存: {output_path}")
            
            return True
        else:
            print(f"图像API测试失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"图像API测试异常: {e}")
        return False

def main():
    print("=== CloudPose Web Service 快速测试 ===\n")
    
    # 服务器地址
    base_url = "http://localhost:60000"
    
    # 测试图像路径
    test_images = [
        "../model3-yolol/test.jpg",
        "../model3-yolol/bus.jpg"
    ]
    
    # 检查服务器是否运行
    print("检查服务器连接...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code != 200:
            print(f"服务器未响应: {response.status_code}")
            print("请确保服务器正在运行: python start_server.py")
            return
    except requests.exceptions.ConnectionError:
        print("无法连接到服务器")
        print("请确保服务器正在运行: python start_server.py")
        return
    
    print("服务器连接正常\n")
    
    # 测试健康检查
    if not test_health_check(base_url):
        print("健康检查失败，停止测试")
        return
    
    print()
    
    # 测试JSON API
    success_count = 0
    for image_path in test_images:
        if os.path.exists(image_path):
            if test_pose_json_api(base_url, image_path):
                success_count += 1
            print()
        else:
            print(f"测试图像不存在: {image_path}")
    
    # 测试图像API
    for image_path in test_images:
        if os.path.exists(image_path):
            if test_pose_image_api(base_url, image_path):
                success_count += 1
            print()
        else:
            print(f"测试图像不存在: {image_path}")
    
    # 测试总结
    print("=== 测试总结 ===")
    total_tests = len(test_images) * 2  # JSON API + 图像API
    print(f"总测试数: {total_tests}")
    print(f"成功测试数: {success_count}")
    print(f"成功率: {success_count/total_tests*100:.1f}%")
    
    if success_count == total_tests:
        print("所有测试通过！Web服务运行正常。")
    else:
        print("部分测试失败，请检查服务配置。")

if __name__ == "__main__":
    main() 