import cv2


def load_image(image_path: str):
    if image_path:
        # Load image from file
        image = cv2.imread(image_path)
        if image is None:
            print(f"Could not load image from {image_path}")
            return None, None
    else:
        raise Exception("No image provided")