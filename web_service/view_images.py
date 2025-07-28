#!/usr/bin/env python3
"""
查看标注图像脚本
"""

import os
import base64
import requests
import cv2
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

def encode_image(image_path):
    """将图像编码为base64"""
    with open(image_path, 'rb') as f:
        image_data = f.read()
        return base64.b64encode(image_data).decode('utf-8')

def decode_base64_image(base64_string):
    """将base64字符串解码为图像"""
    image_data = base64.b64decode(base64_string)
    nparr = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

def test_and_save_image(image_path, server_url="http://localhost:60000"):
    """测试图像API并保存结果"""
    print(f"处理图像: {os.path.basename(image_path)}")
    
    try:
        # 编码图像
        image_base64 = encode_image(image_path)
        
        # 发送请求
        response = requests.post(
            f"{server_url}/api/pose_image",
            json={
                "id": "test-view",
                "image": image_base64
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # 解码标注图像
            annotated_image = decode_base64_image(result['annotated_image'])
            
            # 保存图像
            output_path = f"annotated_{os.path.basename(image_path)}"
            cv2.imwrite(output_path, cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
            
            print(f"标注图像已保存: {output_path}")
            return annotated_image, output_path
        else:
            print(f"请求失败: {response.status_code}")
            return None, None
            
    except Exception as e:
        print(f"处理失败: {e}")
        return None, None

def display_images(original_path, annotated_image, output_path):
    """显示原图和标注图的对比"""
    try:
        # 读取原图
        original = cv2.imread(original_path)
        original_rgb = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
        
        # 创建对比图
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
        
        # 显示原图
        ax1.imshow(original_rgb)
        ax1.set_title('原图')
        ax1.axis('off')
        
        # 显示标注图
        ax2.imshow(annotated_image)
        ax2.set_title('姿态检测结果')
        ax2.axis('off')
        
        plt.tight_layout()
        plt.savefig(f'comparison_{os.path.basename(original_path)}', dpi=150, bbox_inches='tight')
        print(f"对比图已保存: comparison_{os.path.basename(original_path)}")
        
        # 显示图像
        plt.show()
        
    except Exception as e:
        print(f"显示图像失败: {e}")

def main():
    print("=== 图像查看工具 ===")
    
    # 测试图像列表
    test_images = [
        "../model3-yolol/test.jpg",
        "../model3-yolol/bus.jpg"
    ]
    
    # 检查服务器是否运行
    try:
        response = requests.get("http://localhost:60000/health", timeout=5)
        if response.status_code != 200:
            print("服务器未运行，请先启动Web服务")
            return
    except:
        print("无法连接到服务器，请先启动Web服务")
        return
    
    print("服务器连接正常\n")
    
    # 处理每个图像
    for image_path in test_images:
        if os.path.exists(image_path):
            print(f"\n--- 处理 {os.path.basename(image_path)} ---")
            
            # 测试并保存图像
            annotated_image, output_path = test_and_save_image(image_path)
            
            if annotated_image is not None:
                # 显示对比图
                display_images(image_path, annotated_image, output_path)
        else:
            print(f"图像不存在: {image_path}")
    
    print("\n=== 处理完成 ===")
    print("生成的图像文件:")
    for file in os.listdir('.'):
        if file.startswith('annotated_') or file.startswith('comparison_'):
            print(f"  - {file}")

if __name__ == "__main__":
    main() 