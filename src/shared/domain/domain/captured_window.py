from typing import Optional
from PIL import Image
import hashlib
import numpy as np
from loguru import logger

from src.client.services.opencv_utils import pil_to_cv2


class CapturedWindow:
    def __init__(
            self,
            image: Image.Image,
            filename: str,
            window_name: str,
            description: str = ""
    ):
        self.image = image
        self.filename = filename
        self.window_name = window_name
        self.description = description
        self._image_hash: Optional[str] = None

    def get_cv2_image(self) -> np.ndarray:
        try:
            return pil_to_cv2(self.image)
        except Exception as e:
            raise Exception(f"❌ Error converting image {self.window_name}: {str(e)}")

    def calculate_hash(self) -> str:
        if self._image_hash is None:
            try:
                resized_image = self.image.resize((100, 100))
                image_bytes = resized_image.tobytes()
                self._image_hash = hashlib.sha256(image_bytes).hexdigest()[:16]
            except Exception as e:
                logger.error(f"❌ Error calculating image hash: {str(e)}")
                self._image_hash = ""

        return self._image_hash

    def get_size(self) -> tuple[int, int]:
        return self.image.size

    def save(self, filepath: str) -> bool:
        try:
            self.image.save(filepath)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save {self.filename}: {e}")
            return False

    def to_dict(self) -> dict:
        return {
            'image': self.image,
            'filename': self.filename,
            'window_name': self.window_name,
            'description': self.description
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CapturedWindow':
        return cls(
            image=data['image'],
            filename=data['filename'],
            window_name=data['window_name'],
            description=data.get('description', '')
        )

    def __str__(self) -> str:
        width, height = self.get_size()
        return f"CapturedImage(window='{self.window_name}', file='{self.filename}', size={width}x{height})"

    def __repr__(self) -> str:
        return f"CapturedImage(window_name='{self.window_name}', filename='{self.filename}', description='{self.description}')"