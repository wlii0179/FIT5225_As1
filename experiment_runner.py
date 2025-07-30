#!/usr/bin/env python3
"""
实验自动化脚本
用于运行CloudPose服务的性能测试实验
"""

import subprocess
import time
import json
import csv
import os
import sys
from datetime import datetime
import requests

class ExperimentRunner:
    def __init__(self, master_ip, nodeport):
        self.master_ip = master_ip
        self.nodeport = nodeport
        self.service_url = f"http://{master_ip}:{nodeport}"
        self.results = []
        self.experiment_data = {
            "master_node": {},
            "nectar_azure": {}
        }
    
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
    
    def scale_deployment(self, replicas):
        """扩展部署到指定数量的Pod"""
        print(f"=== 扩展部署到 {replicas} 个Pod ===")
        
        # 扩展部署
        if not self.run_command(
            f"kubectl scale deployment cloudpose-deployment --replicas={replicas} -n cloudpose",
            f"扩展到 {replicas} 个Pod"
        ):
            return False
        
        # 等待Pod就绪
        print("⏳ 等待Pod就绪...")
        time.sleep(60)
        
        # 检查Pod状态
        pod_status = self.run_command(
            f"kubectl get pods -n cloudpose",
            "检查Pod状态"
        )
        if pod_status:
            print(pod_status)
        
        return True
    
    def test_service_health(self):
        """测试服务健康状态"""
        print("=== 测试服务健康状态 ===")
        
        try:
            response = requests.get(f"{self.service_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ 服务健康检查通过")
                return True
            else:
                print(f"❌ 服务健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 服务健康检查异常: {e}")
            return False
    
    def run_locust_test(self, num_users, spawn_rate, run_time, test_location):
        """运行Locust负载测试"""
        print(f"=== 运行Locust测试 ({test_location}) ===")
        print(f"用户数: {num_users}")
        print(f"生成速率: {spawn_rate} 用户/秒")
        print(f"运行时间: {run_time} 秒")
        
        # 构建Locust命令
        cmd = [
            "locust",
            "-f", "locustfile.py",
            "--host", self.service_url,
            "--users", str(num_users),
            "--spawn-rate", str(spawn_rate),
            "--run-time", f"{run_time}s",
            "--headless",
            "--html", f"report_{test_location}_{num_users}users.html",
            "--csv", f"results_{test_location}_{num_users}users"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            print("✅ Locust测试完成")
            
            # 解析结果
            return self.parse_locust_results(f"results_{test_location}_{num_users}users_stats.csv")
        except Exception as e:
            print(f"❌ Locust测试失败: {e}")
            return None
    
    def parse_locust_results(self, csv_file):
        """解析Locust测试结果"""
        if not os.path.exists(csv_file):
            print(f"❌ 结果文件不存在: {csv_file}")
            return None
        
        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Name'] == 'Aggregated':
                        return {
                            'avg_response_time': float(row['Average Response Time']),
                            'median_response_time': float(row['Median Response Time']),
                            'p95_response_time': float(row['95% Response Time']),
                            'p99_response_time': float(row['99% Response Time']),
                            'requests_per_sec': float(row['Requests/sec']),
                            'total_requests': int(row['Number of Requests']),
                            'failed_requests': int(row['Number of Failures'])
                        }
        except Exception as e:
            print(f"❌ 解析结果失败: {e}")
            return None
    
    def find_max_users(self, test_location, max_pods):
        """找到最大并发用户数"""
        print(f"=== 寻找最大并发用户数 ({test_location}, {max_pods} Pods) ===")
        
        # 测试不同的用户数
        user_counts = [1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        max_users = 0
        avg_response_time = 0
        
        for users in user_counts:
            print(f"测试 {users} 个并发用户...")
            
            # 运行测试
            result = self.run_locust_test(users, 1, 60, test_location)
            
            if result:
                # 检查是否有失败
                if result['failed_requests'] == 0:
                    max_users = users
                    avg_response_time = result['avg_response_time']
                    print(f"✅ {users} 个用户测试成功")
                else:
                    print(f"❌ {users} 个用户测试失败")
                    break
            else:
                print(f"❌ {users} 个用户测试异常")
                break
        
        return max_users, avg_response_time
    
    def run_experiment(self, pod_count, test_location):
        """运行单个实验"""
        print(f"=== 运行实验: {pod_count} Pods, {test_location} ===")
        
        # 1. 扩展部署 (无资源限制)
        if not self.scale_deployment(pod_count):
            return None
        
        # 2. 测试服务健康
        if not self.test_service_health():
            return None
        
        # 3. 寻找最大用户数
        max_users, avg_response_time = self.find_max_users(test_location, pod_count)
        
        return {
            'pod_count': pod_count,
            'test_location': test_location,
            'max_users': max_users,
            'avg_response_time': avg_response_time
        }
    
    def run_all_experiments(self):
        """运行所有实验"""
        print("🚀 开始运行所有实验")
        print("=" * 50)
        
        # Pod数量配置
        pod_counts = [1, 2, 3, 4]
        
        # 测试位置
        test_locations = ["master_node", "nectar_azure"]
        
        for pod_count in pod_counts:
            for test_location in test_locations:
                print(f"\n--- 实验 {pod_count} Pods, {test_location} ---")
                
                result = self.run_experiment(pod_count, test_location)
                
                if result:
                    self.results.append(result)
                    
                    # 保存到实验数据
                    if test_location not in self.experiment_data:
                        self.experiment_data[test_location] = {}
                    
                    self.experiment_data[test_location][pod_count] = {
                        'max_users': result['max_users'],
                        'avg_response_time': result['avg_response_time']
                    }
                
                # 等待一段时间再进行下一个实验
                time.sleep(30)
        
        # 生成报告
        self.generate_report()
    
    def generate_report(self):
        """生成实验报告"""
        print("=== 生成实验报告 ===")
        
        # 创建报告目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = f"experiment_report_{timestamp}"
        os.makedirs(report_dir, exist_ok=True)
        
        # 保存详细结果
        with open(f"{report_dir}/detailed_results.json", 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # 生成表格数据
        self.generate_table_data(report_dir)
        
        # 生成图表
        self.generate_charts(report_dir)
        
        print(f"✅ 报告已生成到: {report_dir}")
    
    def generate_table_data(self, report_dir):
        """生成表格数据"""
        print("生成表格数据...")
        
        # 创建CSV文件
        csv_file = f"{report_dir}/experiment_results.csv"
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['# of Pods', 'Nectar/Azure', '', '', 'Master', '', ''])
            writer.writerow(['', 'Max Users', 'Avg. Response Time (ms)', '', 'Max Users', 'Avg. Response Time (ms)', ''])
            
            for pod_count in [1, 2, 3, 4]:
                row = [pod_count]
                
                # Nectar/Azure数据
                if pod_count in self.experiment_data.get("nectar_azure", {}):
                    nectar_data = self.experiment_data["nectar_azure"][pod_count]
                    row.extend([nectar_data['max_users'], nectar_data['avg_response_time'], ''])
                else:
                    row.extend(['', '', ''])
                
                # Master数据
                if pod_count in self.experiment_data.get("master_node", {}):
                    master_data = self.experiment_data["master_node"][pod_count]
                    row.extend([master_data['max_users'], master_data['avg_response_time'], ''])
                else:
                    row.extend(['', '', ''])
                
                writer.writerow(row)
        
        print(f"✅ 表格数据已保存到: {csv_file}")
    
    def generate_charts(self, report_dir):
        """生成图表"""
        print("生成图表...")
        
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            # 创建图表
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            pod_counts = [1, 2, 3, 4]
            
            # 最大用户数图表
            master_users = [self.experiment_data.get("master_node", {}).get(pod, {}).get('max_users', 0) for pod in pod_counts]
            nectar_users = [self.experiment_data.get("nectar_azure", {}).get(pod, {}).get('max_users', 0) for pod in pod_counts]
            
            ax1.plot(pod_counts, master_users, 'o-', label='Master Node', linewidth=2, markersize=8)
            ax1.plot(pod_counts, nectar_users, 's-', label='Nectar/Azure', linewidth=2, markersize=8)
            ax1.set_xlabel('Number of Pods')
            ax1.set_ylabel('Max Concurrent Users')
            ax1.set_title('Maximum Concurrent Users vs Number of Pods')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 平均响应时间图表
            master_response = [self.experiment_data.get("master_node", {}).get(pod, {}).get('avg_response_time', 0) for pod in pod_counts]
            nectar_response = [self.experiment_data.get("nectar_azure", {}).get(pod, {}).get('avg_response_time', 0) for pod in pod_counts]
            
            ax2.plot(pod_counts, master_response, 'o-', label='Master Node', linewidth=2, markersize=8)
            ax2.plot(pod_counts, nectar_response, 's-', label='Nectar/Azure', linewidth=2, markersize=8)
            ax2.set_xlabel('Number of Pods')
            ax2.set_ylabel('Average Response Time (ms)')
            ax2.set_title('Average Response Time vs Number of Pods')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(f"{report_dir}/experiment_charts.png", dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ 图表已保存到: {report_dir}/experiment_charts.png")
            
        except ImportError:
            print("⚠️ matplotlib未安装，跳过图表生成")
        except Exception as e:
            print(f"❌ 图表生成失败: {e}")
    
    def show_summary(self):
        """显示实验摘要"""
        print("\n" + "=" * 50)
        print("📊 实验摘要")
        print("=" * 50)
        
        print("\n| # of Pods | Nectar/Azure |                         | Master    |                         |")
        print("| --------- | ------------ | ----------------------- | --------- | ----------------------- |")
        print("|           | Max Users    | Avg. Response Time (ms) | Max Users | Avg. Response Time (ms) |")
        
        for pod_count in [1, 2, 3, 4]:
            nectar_data = self.experiment_data.get("nectar_azure", {}).get(pod_count, {})
            master_data = self.experiment_data.get("master_node", {}).get(pod_count, {})
            
            nectar_users = nectar_data.get('max_users', '')
            nectar_response = nectar_data.get('avg_response_time', '')
            master_users = master_data.get('max_users', '')
            master_response = master_data.get('avg_response_time', '')
            
            print(f"| {pod_count}         | {nectar_users:<11} | {nectar_response:<24} | {master_users:<9} | {master_response:<24} |")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CloudPose实验运行器")
    parser.add_argument("--master-ip", required=True, help="Master节点IP地址")
    parser.add_argument("--nodeport", type=int, default=30000, help="NodePort端口")
    parser.add_argument("--test-location", choices=["master_node", "nectar_azure", "both"], 
                       default="both", help="测试位置")
    
    args = parser.parse_args()
    
    # 创建实验运行器
    runner = ExperimentRunner(args.master_ip, args.nodeport)
    
    # 运行实验
    runner.run_all_experiments()
    
    # 显示摘要
    runner.show_summary()

if __name__ == "__main__":
    main() 