#!/usr/bin/env python3
"""
测试客户端 - 用于测试CloudPose Web服务
"""

import requests
import base64
import json
import time
import os

def test_pose_json_api(base_url, image_path):
    """测试姿态检测JSON API"""
    print(f"测试JSON API: {image_path}")
    
    try:
        # 读取并编码图像
        with open(image_path, 'rb') as f:
            image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # 准备请求数据
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
            print(f"  检测到人数: {result['count']}")
            print(f"  响应时间: {(end_time - start_time)*1000:.2f}ms")
            print(f"  预处理时间: {result.get('speed_preprocess', 0)}ms")
            print(f"  推理时间: {result.get('speed_inference', 0)}ms")
            print(f"  后处理时间: {result.get('speed_postprocess', 0)}ms")
            
            # 显示关键点信息
            if result['keypoints']:
                print(f"  关键点数量: {len(result['keypoints'][0])}")
                print("  前3个关键点:")
                for i, kp in enumerate(result['keypoints'][0][:3]):
                    print(f"    {i}: x={kp[0]:.1f}, y={kp[1]:.1f}, conf={kp[2]:.3f}")
            
            return True
        else:
            print(f"JSON API测试失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"JSON API测试异常: {e}")
        return False

def test_pose_image_api(base_url, image_path):
    """测试姿态检测图像API"""
    print(f"测试图像API: {image_path}")
    
    try:
        # 读取并编码图像
        with open(image_path, 'rb') as f:
            image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # 准备请求数据
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
            print(f"  响应时间: {(end_time - start_time)*1000:.2f}ms")
            
            # 保存标注图像
            if 'annotated_image' in result:
                import cv2
                import numpy as np
                
                # 解码base64图像
                image_data = base64.b64decode(result['annotated_image'])
                nparr = np.frombuffer(image_data, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                # 保存图像
                output_path = f"annotated_{os.path.basename(image_path)}"
                cv2.imwrite(output_path, image)
                print(f"  标注图像已保存: {output_path}")
            
            return True
        else:
            print(f"图像API测试失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"图像API测试异常: {e}")
        return False

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

def main():
    print("=== CloudPose Web Service 测试客户端 ===")
    
    # 服务器地址
    base_url = "http://localhost:60000"
    
    # 测试图像
    test_image = "../model3-yolol/test.jpg"
    
    # 检查图像文件是否存在
    if not os.path.exists(test_image):
        print(f"测试图像不存在: {test_image}")
        return
    
    # 测试健康检查
    if not test_health_check(base_url):
        print("健康检查失败，停止测试")
        return
    
    print()
    
    # 测试JSON API
    test_pose_json_api(base_url, test_image)
    print()
    
    # 测试图像API
    test_pose_image_api(base_url, test_image)
    
    print("\n测试完成!")

if __name__ == "__main__":
    main() 