# CloudPose Web Service

这是一个基于FastAPI的姿态检测Web服务，使用YOLO11L-pose模型进行人体姿态估计。

## 功能特性

- **JSON API**: 接收图像并返回检测到的关键点数据
- **图像API**: 接收图像并返回标注后的图像
- **并发处理**: 支持多客户端并发请求
- **性能监控**: 提供详细的处理时间统计
- **健康检查**: 提供服务状态监控

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行服务

### 1. 确保模型文件存在
将YOLO模型文件 `yolo11l-pose.pt` 放在项目根目录下。

### 2. 启动服务
```bash
# 方法1: 直接运行
python main.py

# 方法2: 使用uvicorn
uvicorn main:app --host 0.0.0.0 --port 60000 --reload
```

### 3. 访问API文档
启动服务后，访问 http://localhost:60000/docs 查看交互式API文档。

## API端点

### 1. 健康检查
```
GET /health
```
返回服务状态信息。

### 2. 姿态检测JSON API
```
POST /api/pose
```
**请求格式**:
```json
{
  "id": "unique-request-id",
  "image": "base64-encoded-image"
}
```

**响应格式**:
```json
{
  "count": 检测到的人数,
  "boxes": [
    {
      "id": "request-id",
      "x": x坐标,
      "y": y坐标,
      "width": 宽度,
      "height": 高度,
      "probability": 置信度
    }
  ],
  "keypoints": [
    [
      [x1, y1, confidence1],
      [x2, y2, confidence2],
      ...
      [x17, y17, confidence17]
    ]
  ],
  "speed_preprocess": 预处理时间(ms),
  "speed_inference": 推理时间(ms),
  "speed_postprocess": 后处理时间(ms)
}
```

### 3. 姿态检测图像API
```
POST /api/pose_image
```
**请求格式**: 与JSON API相同

**响应格式**:
```json
{
  "id": "request-id",
  "annotated_image": "base64-encoded-annotated-image"
}
```

## 测试服务

### 使用提供的测试客户端
```bash
python test_client.py
```

### 使用curl测试
```bash
# 健康检查
curl http://localhost:60000/health

# JSON API测试 (需要先准备base64编码的图像)
curl -X POST http://localhost:60000/api/pose \
  -H "Content-Type: application/json" \
  -d '{"id":"test-123","image":"base64-image-data"}'
```

### 使用提供的客户端脚本
```bash
# 使用作业提供的客户端测试
python ../client/cloudpose_client.py ../client/inputfolder/ http://localhost:60000/api/pose 4
```

## 项目结构

```
web_service/
├── main.py              # FastAPI主应用
├── pose_detector.py     # 姿态检测逻辑
├── test_client.py       # 测试客户端
├── requirements.txt     # 依赖包
├── README.md           # 说明文档
└── yolo11l-pose.pt     # YOLO模型文件
```

## 性能优化建议

1. **模型预热**: 服务启动时会自动加载模型
2. **并发处理**: 每个请求在独立线程中处理
3. **内存管理**: 及时释放不需要的图像数据
4. **错误处理**: 完善的异常处理机制

## 故障排除

### 常见问题

1. **模型加载失败**
   - 检查模型文件路径是否正确
   - 确保有足够的内存加载模型

2. **图像解码失败**
   - 检查base64编码是否正确
   - 确保图像格式支持

3. **服务启动失败**
   - 检查端口是否被占用
   - 确保所有依赖包已安装

### 日志查看
服务运行时会输出详细的日志信息，包括：
- 模型加载状态
- 请求处理过程
- 错误信息

## 部署说明

这个Web服务设计用于在Kubernetes集群中部署，支持：
- 容器化部署
- 负载均衡
- 自动扩缩容
- 健康检查

详细的部署配置请参考Kubernetes相关文档。 