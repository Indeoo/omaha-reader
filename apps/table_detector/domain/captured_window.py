import hashlib
from typing import Optional

import numpy as np
from PIL import Image
from loguru import logger

from table_detector.utils.opencv_utils import pil_to_cv2


class CapturedWindow:
    def __init__(
            self,
            image: Image.Image,
            filename: str,
            window_name: str,
            description: str = 'test',
    ):
        self.image = image
        self.filename = filename
        self.window_name = window_name
        self.description = None
        self._image_hash: Optional[str] = None
        self._is_closed = False

    def get_cv2_image(self) -> np.ndarray:
        if self._is_closed:
            raise Exception(f"❌ Cannot convert closed image {self.window_name}")
        try:
            return pil_to_cv2(self.image)
        except Exception as e:
            raise Exception(f"❌ Error converting image {self.window_name}: {str(e)}")

    def calculate_hash(self) -> str:
        if self._is_closed:
            return self._image_hash or ""
            
        if self._image_hash is None:
            try:
                resized_image = self.image.resize((100, 100))
                image_bytes = resized_image.tobytes()
                self._image_hash = hashlib.sha256(image_bytes).hexdigest()[:16]
                # Clean up the resized image immediately
                resized_image.close()
            except Exception as e:
                logger.error(f"❌ Error calculating image hash: {str(e)}")
                self._image_hash = ""

        return self._image_hash

    def get_size(self) -> tuple[int, int]:
        if self._is_closed:
            raise Exception(f"❌ Cannot get size of closed image {self.window_name}")
        return self.image.size

    def save(self, filepath: str) -> bool:
        if self._is_closed:
            logger.error(f"❌ Cannot save closed image {self.filename}")
            return False
        try:
            self.image.save(filepath)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save {self.filename}: {e}")
            return False

    def close(self):
        """Explicitly release the PIL Image memory."""
        if not self._is_closed and self.image:
            try:
                self.image.close()
                self._is_closed = True
                logger.debug(f"🧹 Closed image: {self.window_name}")
            except Exception as e:
                logger.error(f"❌ Error closing image {self.window_name}: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically clean up."""
        self.close()

    def __del__(self):
        """Destructor - ensure cleanup happens."""
        if not self._is_closed:
            self.close()

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