# CloudPose Web Service 使用说明

## 快速开始

### 1. 安装依赖
```bash
cd web_service
pip install -r requirements.txt
```

### 2. 启动服务
```bash
# 方法1: 使用启动脚本（推荐）
python start_server.py

# 方法2: 直接启动
python main.py

# 方法3: 使用uvicorn
uvicorn main:app --host 0.0.0.0 --port 60000 --reload
```

### 3. 测试服务
```bash
# 快速测试
python quick_test.py

# 详细测试
python test_client.py
```

## API使用示例

### 1. 健康检查
```bash
curl http://localhost:60000/health
```

### 2. JSON API测试
```python
import requests
import base64

# 编码图像
with open("test.jpg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

# 发送请求
response = requests.post(
    "http://localhost:60000/api/pose",
    json={
        "id": "test-123",
        "image": image_base64
    }
)

print(response.json())
```

### 3. 图像API测试
```python
import requests
import base64

# 编码图像
with open("test.jpg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

# 发送请求
response = requests.post(
    "http://localhost:60000/api/pose_image",
    json={
        "id": "test-456",
        "image": image_base64
    }
)

# 保存标注图像
result = response.json()
annotated_data = base64.b64decode(result['annotated_image'])
with open("annotated_test.jpg", "wb") as f:
    f.write(annotated_data)
```

## 使用作业提供的客户端

```bash
# 使用提供的客户端测试128张图像
python ../client/cloudpose_client.py ../client/inputfolder/ http://localhost:60000/api/pose 4
```

## 性能监控

服务会返回详细的性能指标：
- `speed_preprocess`: 预处理时间（毫秒）
- `speed_inference`: 推理时间（毫秒）
- `speed_postprocess`: 后处理时间（毫秒）
- `speed_decode`: 图像解码时间（毫秒）
- `speed_total`: 总处理时间（毫秒）

## 故障排除

### 常见问题

1. **模型加载失败**
   ```
   错误: 模型文件不存在
   解决: 确保 yolo11l-pose.pt 在项目根目录
   ```

2. **端口被占用**
   ```
   错误: 端口 60000 已被占用
   解决: 关闭占用端口的程序或修改端口号
   ```

3. **依赖包缺失**
   ```
   错误: ModuleNotFoundError
   解决: pip install -r requirements.txt
   ```

4. **内存不足**
   ```
   错误: CUDA out of memory
   解决: 减少并发请求数量或增加系统内存
   ```

### 日志查看

服务运行时会输出详细日志：
```
INFO: 正在加载YOLO姿态检测模型...
INFO: 模型加载完成
INFO: 收到姿态检测请求，ID: test-123
INFO: 姿态检测完成，ID: test-123, 检测到 1 人
```

## 开发调试

### 1. 启用调试模式
```bash
uvicorn main:app --host 0.0.0.0 --port 60000 --reload --log-level debug
```

### 2. 查看API文档
访问 http://localhost:60000/docs 查看交互式API文档

### 3. 测试单个端点
```bash
# 测试健康检查
curl http://localhost:60000/health

# 测试根端点
curl http://localhost:60000/
```

## 部署准备

### 1. 容器化准备
- 所有依赖已在 requirements.txt 中定义
- 模型文件已包含在项目中
- 服务配置为监听 0.0.0.0:60000

### 2. 生产环境配置
- 建议使用 gunicorn 或 uvicorn 作为WSGI服务器
- 配置反向代理（如nginx）
- 设置适当的资源限制
- 启用日志记录和监控

### 3. 负载测试
```bash
# 使用Locust进行负载测试
locust -f locustfile.py --host=http://localhost:60000
```

## 文件说明

- `main.py`: FastAPI主应用
- `pose_detector.py`: 姿态检测核心逻辑
- `requirements.txt`: Python依赖包
- `start_server.py`: 服务启动脚本
- `quick_test.py`: 快速测试脚本
- `test_client.py`: 详细测试客户端
- `README.md`: 项目说明文档
- `yolo11l-pose.pt`: YOLO11L姿态检测模型

## 技术栈

- **Web框架**: FastAPI
- **AI模型**: YOLO11L-pose
- **图像处理**: OpenCV
- **深度学习**: PyTorch
- **并发处理**: asyncio + threading
- **API文档**: 自动生成（Swagger UI）

## 性能优化建议

1. **模型优化**: 使用GPU加速推理
2. **并发处理**: 调整worker数量
3. **内存管理**: 及时释放图像数据
4. **缓存策略**: 缓存常用图像处理结果
5. **负载均衡**: 使用多个服务实例 