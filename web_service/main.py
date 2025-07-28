from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import base64
import cv2
import numpy as np
import time
import logging
import threading
from pose_detector import PoseDetector
import io
from PIL import Image

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CloudPose API", description="Pose Detection Web Service")

# 全局姿态检测器实例
detector = None

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化模型"""
    global detector
    try:
        logger.info("正在加载YOLO姿态检测模型...")
        detector = PoseDetector()
        logger.info("模型加载完成")
    except Exception as e:
        logger.error(f"模型加载失败: {e}")
        raise e

class ImageRequest(BaseModel):
    id: str
    image: str

def base64_to_cv2(base64_string: str) -> np.ndarray:
    """将base64字符串转换为OpenCV图像格式"""
    try:
        # 解码base64
        image_data = base64.b64decode(base64_string)
        # 转换为numpy数组
        nparr = np.frombuffer(image_data, np.uint8)
        # 解码为OpenCV图像
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("无法解码图像")
        return image
    except Exception as e:
        logger.error(f"图像解码失败: {e}")
        raise HTTPException(status_code=400, detail=f"图像解码失败: {str(e)}")

def cv2_to_base64(image: np.ndarray) -> str:
    """将OpenCV图像转换为base64字符串"""
    try:
        # 编码为JPEG格式
        _, buffer = cv2.imencode('.jpg', image)
        # 转换为base64
        base64_string = base64.b64encode(buffer).decode('utf-8')
        return base64_string
    except Exception as e:
        logger.error(f"图像编码失败: {e}")
        raise HTTPException(status_code=500, detail=f"图像编码失败: {str(e)}")

@app.post("/api/pose")
async def detect_pose_json(request: ImageRequest):
    """
    姿态检测JSON API端点
    接收base64编码的图像，返回检测到的关键点数据
    """
    try:
        logger.info(f"收到姿态检测请求，ID: {request.id}")
        
        # 解码图像
        start_time = time.time()
        image = base64_to_cv2(request.image)
        decode_time = time.time() - start_time
        
        # 执行姿态检测
        start_detection = time.time()
        results, preprocess_time, inference_time, postprocess_time = detector.detect(image)
        detection_time = time.time() - start_detection
        
        # 解析结果
        response_data = detector.parse_results(results, request.id)
        response_data.update({
            "speed_preprocess": round(preprocess_time * 1000, 2),  # 转换为毫秒
            "speed_inference": round(inference_time * 1000, 2),
            "speed_postprocess": round(postprocess_time * 1000, 2),
            "speed_decode": round(decode_time * 1000, 2),
            "speed_total": round((decode_time + detection_time) * 1000, 2)
        })
        
        logger.info(f"姿态检测完成，ID: {request.id}, 检测到 {response_data['count']} 人")
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"姿态检测失败，ID: {request.id}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"姿态检测失败: {str(e)}")

@app.post("/api/pose_image")
async def detect_pose_image(request: ImageRequest):
    """
    姿态检测图像API端点
    接收base64编码的图像，返回标注后的图像
    """
    try:
        logger.info(f"收到图像标注请求，ID: {request.id}")
        
        # 解码图像
        image = base64_to_cv2(request.image)
        
        # 执行姿态检测并生成标注图像
        annotated_image = detector.detect_and_annotate(image)
        
        # 编码标注图像为base64
        annotated_base64 = cv2_to_base64(annotated_image)
        
        response_data = {
            "id": request.id,
            "annotated_image": annotated_base64
        }
        
        logger.info(f"图像标注完成，ID: {request.id}")
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"图像标注失败，ID: {request.id}, 错误: {e}")
        raise HTTPException(status_code=500, detail=f"图像标注失败: {str(e)}")

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "model_loaded": detector is not None}

@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "CloudPose API",
        "endpoints": {
            "pose_json": "/api/pose",
            "pose_image": "/api/pose_image",
            "health": "/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=60000) 