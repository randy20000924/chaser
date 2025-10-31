"""系統硬體檢測器 - 檢測 CPU、GPU、記憶體、硬碟並推薦適合的 Qwen 模型."""

import psutil
import platform
import subprocess
import json
from typing import Dict, Any, Optional
from loguru import logger

class SystemDetector:
    """系統硬體檢測器."""
    
    def __init__(self):
        self.system_info = {}
        self.recommended_model = None
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """獲取 CPU 資訊."""
        try:
            cpu_info = {
                "name": platform.processor(),
                "physical_cores": psutil.cpu_count(logical=False),
                "total_cores": psutil.cpu_count(logical=True),
                "max_frequency": psutil.cpu_freq().max if psutil.cpu_freq() else None,
                "architecture": platform.machine(),
                "system": platform.system()
            }
            
            # 嘗試獲取更詳細的 CPU 資訊
            try:
                if platform.system() == "Darwin":  # macOS
                    result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        cpu_info["name"] = result.stdout.strip()
                elif platform.system() == "Linux":
                    with open('/proc/cpuinfo', 'r') as f:
                        for line in f:
                            if line.startswith('model name'):
                                cpu_info["name"] = line.split(':')[1].strip()
                                break
            except Exception as e:
                logger.warning(f"Could not get detailed CPU info: {e}")
            
            return cpu_info
        except Exception as e:
            logger.error(f"Error getting CPU info: {e}")
            return {"error": str(e)}
    
    def get_memory_info(self) -> Dict[str, Any]:
        """獲取記憶體資訊."""
        try:
            svmem = psutil.virtual_memory()
            return {
                "total_gb": round(svmem.total / (1024**3), 2),
                "available_gb": round(svmem.available / (1024**3), 2),
                "used_gb": round(svmem.used / (1024**3), 2),
                "percentage": svmem.percent
            }
        except Exception as e:
            logger.error(f"Error getting memory info: {e}")
            return {"error": str(e)}
    
    def get_disk_info(self) -> Dict[str, Any]:
        """獲取硬碟資訊."""
        try:
            disk_usage = psutil.disk_usage('/')
            return {
                "total_gb": round(disk_usage.total / (1024**3), 2),
                "used_gb": round(disk_usage.used / (1024**3), 2),
                "free_gb": round(disk_usage.free / (1024**3), 2),
                "percentage": round((disk_usage.used / disk_usage.total) * 100, 2)
            }
        except Exception as e:
            logger.error(f"Error getting disk info: {e}")
            return {"error": str(e)}
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """獲取 GPU 資訊."""
        gpu_info = {"gpus": [], "total_vram_gb": 0}
        
        try:
            # 嘗試使用 nvidia-ml-py
            try:
                import pynvml
                pynvml.nvmlInit()
                device_count = pynvml.nvmlDeviceGetCount()
                
                for i in range(device_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                    memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    
                    gpu = {
                        "name": name,
                        "memory_total_mb": memory_info.total,
                        "memory_total_gb": round(memory_info.total / (1024**2), 2),
                        "memory_free_gb": round(memory_info.free / (1024**2), 2),
                        "memory_used_gb": round(memory_info.used / (1024**2), 2)
                    }
                    gpu_info["gpus"].append(gpu)
                    gpu_info["total_vram_gb"] += gpu["memory_total_gb"]
                
                pynvml.nvmlShutdown()
                
            except ImportError:
                logger.warning("pynvml not available, trying alternative methods")
                # 嘗試使用 nvidia-smi
                try:
                    result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', 
                                          '--format=csv,noheader,nounits'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        for line in lines:
                            parts = line.split(', ')
                            if len(parts) >= 2:
                                gpu = {
                                    "name": parts[0],
                                    "memory_total_gb": int(parts[1]) / 1024
                                }
                                gpu_info["gpus"].append(gpu)
                                gpu_info["total_vram_gb"] += gpu["memory_total_gb"]
                except Exception as e:
                    logger.warning(f"Could not get GPU info via nvidia-smi: {e}")
            
            except Exception as e:
                logger.warning(f"Could not get GPU info: {e}")
                
        except Exception as e:
            logger.error(f"Error getting GPU info: {e}")
        
        return gpu_info
    
    def detect_system(self) -> Dict[str, Any]:
        """檢測完整系統資訊."""
        logger.info("Detecting system hardware...")
        
        self.system_info = {
            "cpu": self.get_cpu_info(),
            "memory": self.get_memory_info(),
            "disk": self.get_disk_info(),
            "gpu": self.get_gpu_info()
        }
        
        # 推薦適合的 Qwen 模型
        self.recommended_model = self.recommend_qwen_model()
        self.system_info["recommended_model"] = self.recommended_model
        
        logger.info(f"System detection completed. Recommended model: {self.recommended_model}")
        return self.system_info
    
    def recommend_qwen_model(self) -> str:
        """根據系統硬體推薦適合的 Qwen 模型."""
        try:
            total_memory = self.system_info["memory"]["total_gb"]
            total_disk = self.system_info["disk"]["total_gb"]
            total_vram = self.system_info["gpu"]["total_vram_gb"]
            cpu_cores = self.system_info["cpu"]["total_cores"]
            
            logger.info(f"System specs - Memory: {total_memory}GB, Disk: {total_disk}GB, "
                       f"VRAM: {total_vram}GB, CPU cores: {cpu_cores}")
            
            # Qwen 模型推薦邏輯
            if total_vram >= 80 and total_memory >= 64 and total_disk >= 80:
                return "Qwen2.5:14B"
            elif total_vram >= 40 and total_memory >= 48 and total_disk >= 60:
                return "Qwen2.5:8B"
            elif total_vram >= 24 and total_memory >= 24 and total_disk >= 40:
                return "Qwen2.5:4B"
            elif total_vram >= 12 and total_memory >= 16 and total_disk >= 30:
                return "Qwen2.5:1.5B"
            elif total_vram >= 8 and total_memory >= 8 and total_disk >= 20:
                return "Qwen2.5:0.5B"
            elif total_memory >= 32 and total_disk >= 40:  # 無 GPU 但記憶體充足
                return "Qwen2.5:4B"
            elif total_memory >= 16 and total_disk >= 30:
                return "Qwen2.5:1.5B"
            elif total_memory >= 8 and total_disk >= 20:
                return "qwen2.5:0.5b-instruct"
            else:
                # 超低配預設：使用 instruct 變體（更省記憶體）
                return "qwen2.5:0.5b-instruct"
                
        except Exception as e:
            logger.error(f"Error recommending model: {e}")
            return "qwen2.5:0.5b-instruct"
    
    def get_model_requirements(self, model_name: str) -> Dict[str, Any]:
        """獲取指定模型的硬體需求."""
        requirements = {
            "Qwen2.5:0.5B": {
                "min_memory_gb": 4,
                "min_disk_gb": 2,
                "min_vram_gb": 2,
                "recommended_memory_gb": 8,
                "recommended_vram_gb": 4
            },
            "Qwen2.5:1.5B": {
                "min_memory_gb": 8,
                "min_disk_gb": 4,
                "min_vram_gb": 4,
                "recommended_memory_gb": 16,
                "recommended_vram_gb": 8
            },
            "Qwen2.5:4B": {
                "min_memory_gb": 16,
                "min_disk_gb": 8,
                "min_vram_gb": 8,
                "recommended_memory_gb": 24,
                "recommended_vram_gb": 16
            },
            "Qwen2.5:8B": {
                "min_memory_gb": 32,
                "min_disk_gb": 16,
                "min_vram_gb": 16,
                "recommended_memory_gb": 48,
                "recommended_vram_gb": 24
            },
            "Qwen2.5:14B": {
                "min_memory_gb": 48,
                "min_disk_gb": 28,
                "min_vram_gb": 24,
                "recommended_memory_gb": 64,
                "recommended_vram_gb": 40
            }
        }
        
        return requirements.get(model_name, requirements["Qwen2.5:0.5B"])

# 創建全局實例
system_detector = SystemDetector()
