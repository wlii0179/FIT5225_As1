from ultralytics import YOLO
import cv2
import numpy as np
import time
import logging

logger = logging.getLogger(__name__)

class PoseDetector:
    def __init__(self, model_path='./yolo11l-pose.pt'):
        """
        初始化姿态检测器
        Args:
            model_path: YOLO模型文件路径
        """
        try:
            logger.info(f"正在加载模型: {model_path}")
            self.model = YOLO(model_path)
            logger.info("模型加载成功")
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise e
        
        # COCO关键点连接定义 (17个关键点)
        self.keypoint_connections = [
            [0, 1],   # 鼻子到左眼
            [0, 2],   # 鼻子到右眼
            [1, 3],   # 左眼到左耳
            [2, 4],   # 右眼到右耳
            [5, 6],   # 左肩到右肩
            [5, 7],   # 左肩到左肘
            [7, 9],   # 左肘到左手腕
            [6, 8],   # 右肩到右肘
            [8, 10],  # 右肘到右手腕
            [5, 11],  # 左肩到左臀
            [6, 12],  # 右肩到右臀
            [11, 12], # 左臀到右臀
            [11, 13], # 左臀到左膝
            [13, 15], # 左膝到左脚踝
            [12, 14], # 右臀到右膝
            [14, 16]  # 右膝到右脚踝
        ]
        
        # COCO关键点名称
        self.keypoint_names = [
            "nose", "left_eye", "right_eye", "left_ear", "right_ear",
            "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
            "left_wrist", "right_wrist", "left_hip", "right_hip",
            "left_knee", "right_knee", "left_ankle", "right_ankle"
        ]

    def detect(self, image):
        """
        执行姿态检测
        Args:
            image: OpenCV格式的图像
        Returns:
            results: YOLO检测结果
            preprocess_time: 预处理时间
            inference_time: 推理时间
            postprocess_time: 后处理时间
        """
        try:
            # 预处理
            start_preprocess = time.time()
            # 确保图像格式正确
            if len(image.shape) == 3:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image
            preprocess_time = time.time() - start_preprocess
            
            # 推理
            start_inference = time.time()
            results = self.model(image_rgb)
            inference_time = time.time() - start_inference
            
            # 后处理
            start_postprocess = time.time()
            # 这里可以添加额外的后处理逻辑
            postprocess_time = time.time() - start_postprocess
            
            return results, preprocess_time, inference_time, postprocess_time
            
        except Exception as e:
            logger.error(f"姿态检测失败: {e}")
            raise e

    def parse_results(self, results, request_id):
        """
        解析YOLO检测结果
        Args:
            results: YOLO检测结果
            request_id: 请求ID
        Returns:
            dict: 解析后的结果数据
        """
        try:
            boxes = []
            keypoints_list = []
            count = 0
            
            for result in results:
                if result.keypoints is not None and len(result.keypoints.xy) > 0:
                    # 获取边界框
                    if result.boxes is not None and len(result.boxes.xyxy) > 0:
                        for i, box in enumerate(result.boxes.xyxy):
                            x1, y1, x2, y2 = box.cpu().numpy()
                            conf = result.boxes.conf[i].cpu().numpy()
                            
                            boxes.append({
                                "id": request_id,
                                "x": float(x1),
                                "y": float(y1),
                                "width": float(x2 - x1),
                                "height": float(y2 - y1),
                                "probability": float(conf)
                            })
                    
                    # 获取关键点
                    keypoints_xy = result.keypoints.xy.cpu().numpy()  # (num_people, num_keypoints, 2)
                    keypoints_conf = result.keypoints.conf.cpu().numpy()  # (num_people, num_keypoints)
                    
                    for person_idx in range(len(keypoints_xy)):
                        person_keypoints = []
                        for kp_idx in range(len(keypoints_xy[person_idx])):
                            x, y = keypoints_xy[person_idx][kp_idx]
                            conf = keypoints_conf[person_idx][kp_idx]
                            person_keypoints.append([float(x), float(y), float(conf)])
                        keypoints_list.append(person_keypoints)
                        count += 1
            
            return {
                "count": count,
                "boxes": boxes,
                "keypoints": keypoints_list
            }
            
        except Exception as e:
            logger.error(f"结果解析失败: {e}")
            return {
                "count": 0,
                "boxes": [],
                "keypoints": []
            }

    def detect_and_annotate(self, image):
        """
        执行姿态检测并生成标注图像
        Args:
            image: OpenCV格式的图像
        Returns:
            annotated_image: 标注后的图像
        """
        try:
            # 复制原图像用于标注
            annotated_image = image.copy()
            
            # 执行检测
            results, _, _, _ = self.detect(image)
            
            # 绘制检测结果
            for result in results:
                if result.keypoints is not None and len(result.keypoints.xy) > 0:
                    keypoints_xy = result.keypoints.xy.cpu().numpy()
                    keypoints_conf = result.keypoints.conf.cpu().numpy()
                    
                    # 绘制每个检测到的人
                    for person_idx in range(len(keypoints_xy)):
                        # 绘制关键点
                        for kp_idx, (x, y) in enumerate(keypoints_xy[person_idx]):
                            conf = keypoints_conf[person_idx][kp_idx]
                            if conf > 0.5:  # 只绘制置信度高的关键点
                                # 绘制关键点圆圈
                                cv2.circle(annotated_image, (int(x), int(y)), 5, (0, 255, 0), -1)
                                # 添加关键点标签
                                cv2.putText(annotated_image, str(kp_idx), 
                                          (int(x) + 5, int(y) - 5), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                        
                        # 绘制关键点连接线
                        for connection in self.keypoint_connections:
                            kp1_idx, kp2_idx = connection
                            if (kp1_idx < len(keypoints_xy[person_idx]) and 
                                kp2_idx < len(keypoints_xy[person_idx])):
                                
                                x1, y1 = keypoints_xy[person_idx][kp1_idx]
                                x2, y2 = keypoints_xy[person_idx][kp2_idx]
                                conf1 = keypoints_conf[person_idx][kp1_idx]
                                conf2 = keypoints_conf[person_idx][kp2_idx]
                                
                                # 只有当两个关键点都有足够高的置信度时才绘制连接线
                                if conf1 > 0.5 and conf2 > 0.5:
                                    cv2.line(annotated_image, 
                                           (int(x1), int(y1)), 
                                           (int(x2), int(y2)), 
                                           (0, 0, 255), 2)
            
            return annotated_image
            
        except Exception as e:
            logger.error(f"图像标注失败: {e}")
            return image  # 如果标注失败，返回原图像

    def get_model_info(self):
        """
        获取模型信息
        Returns:
            dict: 模型信息
        """
        return {
            "model_type": "YOLO11L-pose",
            "keypoints_count": 17,
            "keypoint_names": self.keypoint_names,
            "connections": self.keypoint_connections
        } 