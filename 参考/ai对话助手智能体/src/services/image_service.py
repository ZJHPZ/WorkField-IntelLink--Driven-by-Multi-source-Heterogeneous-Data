"""
图片处理服务模块
功能：图片上传、存储、URL生成
"""
import base64
import hashlib
import io
import os
import uuid
from typing import Optional, List
from PIL import Image
import logging

from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context

logger = logging.getLogger(__name__)


class ImageUploadService:
    """图片上传服务"""

    # 支持的图片格式
    SUPPORTED_FORMATS = {
        'jpeg': 'image/jpeg',
        'jpg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'bmp': 'image/bmp'
    }

    # 图片大小限制 (字节)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    # 最大分辨率
    MAX_DIMENSION = 4096

    def __init__(self):
        self.storage_base_path = os.getenv('IMAGE_STORAGE_PATH', '/tmp/uploads/images')
        os.makedirs(self.storage_base_path, exist_ok=True)

    def validate_image(self, file_content: bytes, filename: str = "") -> dict:
        """
        验证图片格式和大小

        Args:
            file_content: 图片二进制内容
            filename: 文件名（用于检测格式）

        Returns:
            dict: 验证结果 {"valid": bool, "error": str, "format": str}
        """
        # 检查文件大小
        if len(file_content) > self.MAX_FILE_SIZE:
            return {
                "valid": False,
                "error": f"图片大小超过限制 ({self.MAX_FILE_SIZE // (1024*1024)}MB)",
                "format": None
            }

        # 从文件头检测真实格式
        detected_format = self._detect_format(file_content)
        if not detected_format:
            return {
                "valid": False,
                "error": "无法识别图片格式",
                "format": None
            }

        # 从文件名检测格式（作为备用）
        if filename:
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            if ext in self.SUPPORTED_FORMATS:
                detected_format = ext

        # 尝试打开图片验证完整性
        try:
            img = Image.open(io.BytesIO(file_content))
            img.verify()

            # 检查分辨率
            width, height = img.size
            if width > self.MAX_DIMENSION or height > self.MAX_DIMENSION:
                return {
                    "valid": False,
                    "error": f"图片分辨率超过限制 ({self.MAX_DIMENSION}x{self.MAX_DIMENSION})",
                    "format": detected_format
                }

            return {
                "valid": True,
                "error": None,
                "format": detected_format,
                "width": width,
                "height": height
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"图片文件损坏: {str(e)}",
                "format": None
            }

    def _detect_format(self, content: bytes) -> Optional[str]:
        """从文件头检测图片格式"""
        # PNG
        if content[:8] == b'\x89PNG\r\n\x1a\n':
            return 'png'
        # JPEG
        if content[:2] == b'\xff\xd8':
            return 'jpg'
        # GIF
        if content[:6] in (b'GIF87a', b'GIF89a'):
            return 'gif'
        # WebP
        if content[:4] == b'RIFF' and content[8:12] == b'WEBP':
            return 'webp'
        # BMP
        if content[:2] == b'BM':
            return 'bmp'
        return None

    def upload_from_base64(self, base64_data: str, user_id: str = "anonymous") -> dict:
        """
        从Base64上传图片

        Args:
            base64_data: Base64编码的图片数据（不包含前缀如 data:image/png;base64,）
            user_id: 用户ID

        Returns:
            dict: 上传结果 {"success": bool, "url": str, "error": str}
        """
        ctx = request_context.get() or new_context(method="image_upload_base64")

        try:
            # 解码Base64
            try:
                # 处理可能带有前缀的Base64
                if ',' in base64_data:
                    base64_data = base64_data.split(',', 1)[1]
                file_content = base64.b64decode(base64_data)
            except Exception as e:
                return {
                    "success": False,
                    "url": None,
                    "error": f"Base64解码失败: {str(e)}",
                    "error_code": "INVALID_BASE64"
                }

            # 验证图片
            validation = self.validate_image(file_content)
            if not validation["valid"]:
                return {
                    "success": False,
                    "url": None,
                    "error": validation["error"],
                    "error_code": "INVALID_IMAGE"
                }

            # 生成文件名
            file_id = str(uuid.uuid4())
            ext = validation["format"]
            filename = f"{file_id}.{ext}"
            filepath = os.path.join(self.storage_base_path, filename)

            # 保存文件
            with open(filepath, 'wb') as f:
                f.write(file_content)

            # 生成URL（这里使用本地路径，生产环境需要配置CDN或S3）
            image_url = f"/api/v1/images/{filename}"

            logger.info(f"[ImageUpload] Image uploaded: {image_url}, user={user_id}, size={len(file_content)}")

            return {
                "success": True,
                "url": image_url,
                "filename": filename,
                "format": ext,
                "size": len(file_content),
                "width": validation.get("width"),
                "height": validation.get("height"),
                "error": None
            }

        except Exception as e:
            logger.error(f"[ImageUpload] Upload failed: {str(e)}")
            return {
                "success": False,
                "url": None,
                "error": f"上传失败: {str(e)}",
                "error_code": "UPLOAD_FAILED"
            }

    def upload_from_url(self, image_url: str, user_id: str = "anonymous") -> dict:
        """
        从URL下载并存储图片

        Args:
            image_url: 外部图片URL
            user_id: 用户ID

        Returns:
            dict: 上传结果 {"success": bool, "url": str, "error": str}
        """
        ctx = request_context.get() or new_context(method="image_upload_url")

        try:
            import requests

            # 下载图片
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            file_content = response.content

            # 验证图片
            validation = self.validate_image(file_content)
            if not validation["valid"]:
                return {
                    "success": False,
                    "url": None,
                    "error": validation["error"],
                    "error_code": "INVALID_IMAGE"
                }

            # 生成文件名
            file_id = str(uuid.uuid4())
            ext = validation["format"]
            filename = f"{file_id}.{ext}"
            filepath = os.path.join(self.storage_base_path, filename)

            # 保存文件
            with open(filepath, 'wb') as f:
                f.write(file_content)

            # 返回本地URL
            local_url = f"/api/v1/images/{filename}"

            logger.info(f"[ImageUpload] Image downloaded and stored: {local_url}, source={image_url}")

            return {
                "success": True,
                "url": local_url,
                "source_url": image_url,
                "filename": filename,
                "format": ext,
                "size": len(file_content),
                "width": validation.get("width"),
                "height": validation.get("height"),
                "error": None
            }

        except Exception as e:
            logger.error(f"[ImageUpload] Download failed: {str(e)}")
            return {
                "success": False,
                "url": None,
                "error": f"下载失败: {str(e)}",
                "error_code": "DOWNLOAD_FAILED"
            }

    def get_image_path(self, filename: str) -> Optional[str]:
        """获取图片文件路径"""
        filepath = os.path.join(self.storage_base_path, filename)
        if os.path.exists(filepath):
            return filepath
        return None


# 全局服务实例
_image_upload_service = None


def get_image_upload_service() -> ImageUploadService:
    """获取图片上传服务实例"""
    global _image_upload_service
    if _image_upload_service is None:
        _image_upload_service = ImageUploadService()
    return _image_upload_service
