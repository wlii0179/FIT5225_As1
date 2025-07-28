# CloudPose Docker 部署指南

## 概述

本指南介绍如何将CloudPose Web服务容器化，包括Docker镜像构建、容器运行和测试。

## 文件说明

- `Dockerfile`: Docker镜像构建文件
- `requirements-docker.txt`: Docker环境依赖包
- `.dockerignore`: Docker构建忽略文件
- `docker_build.py`: 自动化构建和测试脚本

## 快速开始

### 1. 检查Docker安装

```bash
docker --version
```

如果未安装，请参考 [Docker官方安装指南](https://docs.docker.com/get-docker/)。

### 2. 构建Docker镜像

```bash
# 使用自动化脚本
python docker_build.py

# 或手动构建
docker build -t cloudpose:latest .
```

### 3. 运行容器

```bash
# 使用自动化脚本（包含在docker_build.py中）
python docker_build.py

# 或手动运行
docker run -d --name cloudpose -p 60000:60000 cloudpose:latest
```

### 4. 测试服务

```bash
# 健康检查
curl http://localhost:60000/health

# 查看API文档
# 浏览器访问: http://localhost:60000/docs
```

## Dockerfile 详解

### 基础镜像
```dockerfile
FROM python:3.10-slim
```
- 使用Python 3.10官方精简镜像
- 减小镜像体积，提高安全性

### 系统依赖
```dockerfile
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0
```
- 安装OpenCV所需的系统库
- 支持图像处理和显示功能

### 安全配置
```dockerfile
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
```
- 创建非root用户
- 提高容器安全性

### 健康检查
```dockerfile
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:60000/health || exit 1
```
- 定期检查服务健康状态
- 自动重启不健康的容器

## 镜像优化

### 1. 多阶段构建（可选）

```dockerfile
# 构建阶段
FROM python:3.10-slim as builder
WORKDIR /app
COPY requirements-docker.txt .
RUN pip install --user -r requirements-docker.txt

# 运行阶段
FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
```

### 2. 缓存优化

```dockerfile
# 先复制requirements，利用Docker缓存
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# 再复制应用代码
COPY . .
```

## 容器管理

### 查看容器状态
```bash
# 查看运行中的容器
docker ps

# 查看所有容器
docker ps -a

# 查看容器日志
docker logs cloudpose-test

# 查看容器资源使用
docker stats cloudpose-test
```

### 容器操作
```bash
# 停止容器
docker stop cloudpose-test

# 启动容器
docker start cloudpose-test

# 重启容器
docker restart cloudpose-test

# 删除容器
docker rm cloudpose-test

# 删除镜像
docker rmi cloudpose:latest
```

## 生产环境部署

### 1. 资源限制
```bash
docker run -d \
  --name cloudpose \
  --memory=2g \
  --cpus=1.0 \
  -p 60000:60000 \
  cloudpose:latest
```

### 2. 环境变量
```bash
docker run -d \
  --name cloudpose \
  -e PYTHONUNBUFFERED=1 \
  -e LOG_LEVEL=INFO \
  -p 60000:60000 \
  cloudpose:latest
```

### 3. 数据卷挂载
```bash
docker run -d \
  --name cloudpose \
  -v /host/path/logs:/app/logs \
  -v /host/path/models:/app/models \
  -p 60000:60000 \
  cloudpose:latest
```

## 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 检查端口使用
   netstat -tulpn | grep 60000
   
   # 使用不同端口
   docker run -p 60001:60000 cloudpose:latest
   ```

2. **内存不足**
   ```bash
   # 增加内存限制
   docker run --memory=4g cloudpose:latest
   ```

3. **模型加载失败**
   ```bash
   # 检查模型文件
   docker exec cloudpose-test ls -la yolo11l-pose.pt
   
   # 查看容器日志
   docker logs cloudpose-test
   ```

### 调试模式
```bash
# 交互式运行
docker run -it --rm cloudpose:latest /bin/bash

# 查看容器内部
docker exec -it cloudpose-test /bin/bash
```

## 性能优化

### 1. 镜像大小优化
- 使用多阶段构建
- 清理不必要的文件
- 使用.dockerignore排除文件

### 2. 启动时间优化
- 预加载模型
- 使用健康检查
- 优化依赖安装

### 3. 运行时优化
- 设置资源限制
- 使用数据卷
- 配置日志轮转

## 下一步

容器化完成后，可以：
1. 推送到Docker Hub
2. 部署到Kubernetes集群
3. 配置CI/CD流水线
4. 进行负载测试

## 相关文档

- [Docker官方文档](https://docs.docker.com/)
- [FastAPI部署指南](https://fastapi.tiangolo.com/deployment/)
- [Kubernetes部署指南](kubernetes-deployment.md) 