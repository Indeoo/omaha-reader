import unittest
import cv2
from pathlib import Path

from table_detector.services.game_snapshot_service import GameSnapshotService


class GameSnapshotServiceTest(unittest.TestCase):

    def load_image(self, image_name):
        test_dir = Path(__file__).parent.parent
        test_image_path = test_dir / "resources" / "service" / "game_snapshot_service" / "1" / image_name

        # Verify test image exists
        if not test_image_path.exists():
            self.fail(f"Test image not found: {test_image_path}")
        # Load test image
        cv2_image = cv2.imread(str(test_image_path))

        if cv2_image is None:
            self.fail(f"Failed to load test image: {test_image_path}")

        return cv2_image

    def test_create_game_snapshot_basic(self):
        """Test that create_game_snapshot returns a valid GameSnapshot object."""
        # Execute the method under test
        cv2_image = self.load_image("01__2_50__5_Pot_Limit_Omaha.png")

        game_snapshot = GameSnapshotService.create_game_snapshot(cv2_image)

        print(game_snapshot)
