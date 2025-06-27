from typing import Optional
from PIL import Image
import hashlib


class CapturedImage:
    """
    Represents a captured window/image with metadata.
    Replaces the dictionary format used in capture_and_save_windows.
    """

    def __init__(
            self,
            image: Image.Image,
            filename: str,
            window_name: str,
            description: str = ""
    ):
        """
        Initialize a captured image object.

        Args:
            image: PIL Image object
            filename: Name of the file (e.g., "01_poker_table.png")
            window_name: Name of the window/table
            description: Optional description of the capture method
        """
        self.image = image
        self.filename = filename
        self.window_name = window_name
        self.description = description
        self._image_hash: Optional[str] = None

    def calculate_hash(self) -> str:
        """
        Calculate a hash of the image content for change detection.
        Cached after first calculation.

        Returns:
            String hash of the image content
        """
        if self._image_hash is None:
            try:
                # Use a smaller image for faster hashing while maintaining uniqueness
                resized_image = self.image.resize((100, 100))
                image_bytes = resized_image.tobytes()
                self._image_hash = hashlib.sha256(image_bytes).hexdigest()[:16]
            except Exception as e:
                print(f"❌ Error calculating image hash: {str(e)}")
                self._image_hash = ""

        return self._image_hash

    def get_size(self) -> tuple[int, int]:
        """Get image size as (width, height)"""
        return self.image.size

    def save(self, filepath: str) -> bool:
        """
        Save the image to the specified file path.

        Args:
            filepath: Full path where to save the image

        Returns:
            True if successful, False otherwise
        """
        try:
            self.image.save(filepath)
            return True
        except Exception as e:
            print(f"❌ Failed to save {self.filename}: {e}")
            return False

    def to_dict(self) -> dict:
        """
        Convert to dictionary format for backward compatibility.

        Returns:
            Dictionary representation matching the old format
        """
        return {
            'image': self.image,
            'filename': self.filename,
            'window_name': self.window_name,
            'description': self.description
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'CapturedImage':
        """
        Create CapturedImage from dictionary format.

        Args:
            data: Dictionary containing image data

        Returns:
            CapturedImage instance
        """
        return cls(
            image=data['image'],
            filename=data['filename'],
            window_name=data['window_name'],
            description=data.get('description', '')
        )

    def __str__(self) -> str:
        """String representation"""
        width, height = self.get_size()
        return f"CapturedImage(window='{self.window_name}', file='{self.filename}', size={width}x{height})"

    def __repr__(self) -> str:
        """Detailed representation for debugging"""
        return f"CapturedImage(window_name='{self.window_name}', filename='{self.filename}', description='{self.description}')"