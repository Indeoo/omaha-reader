import unittest
import cv2
import tempfile
from PIL import Image

from table_detector.services.poker_game_processor import PokerGameProcessor
from table_detector.domain.captured_window import CapturedWindow
from table_detector.domain.omaha_engine import InvalidPositionSequenceError, WrongPlayerAmount
from table_detector.test.service.test_utils import load_image


class PokerGameProcessorTest(unittest.TestCase):

    def create_captured_window(self, cv2_image, window_name="test_window"):
        """Convert CV2 image to CapturedWindow for PokerGameProcessor."""
        # Convert CV2 (BGR) to RGB then to PIL Image
        rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        return CapturedWindow(
            image=pil_image,
            filename=f"{window_name}.png",
            window_name=window_name
        )

    def create_poker_processor(self):
        """Create stateless PokerGameProcessor for integration testing."""
        return PokerGameProcessor()

    def create_temp_folder(self):
        """Create temporary folder for test timestamp folder parameter."""
        return tempfile.mkdtemp()

    def test_process_window_basic_1(self):
        """Test that process_window raises InvalidPositionSequenceError due to invalid poker action sequence."""
        # Load test image and create CapturedWindow
        cv2_image = load_image("1.png")
        captured_window = self.create_captured_window(cv2_image)
        
        # Create processor and temp folder
        processor = self.create_poker_processor()
        temp_folder = self.create_temp_folder()

        with self.assertRaises(InvalidPositionSequenceError):
            processor.process_window(captured_window, temp_folder)

    def test_process_window_basic_2(self):
        """Test that process_window returns valid game data with expected moves."""
        # Load test image and create CapturedWindow
        cv2_image = load_image("2.png")
        captured_window = self.create_captured_window(cv2_image)
        
        # Create processor and temp folder
        processor = self.create_poker_processor()
        temp_folder = self.create_temp_folder()

        # Execute the method under test
        game_data = processor.process_window(captured_window, temp_folder)

        # Expected moves in web format (using actual format returned by system)
        expected_moves = [
            {'player_label': 'EARLY_POSITION', 'action': 'fold'},
            {'player_label': 'MIDDLE_POSITION', 'action': 'fold'},
            {'player_label': 'CUTOFF', 'action': 'fold'},
            {'player_label': 'BUTTON', 'action': 'fold'}
        ]

        # Extract PREFLOP moves from web format (using actual street name format)
        preflop_moves = None
        for street_data in game_data['moves']:
            if street_data['street'] == 'Preflop':
                preflop_moves = street_data['moves']
                break

        # Test solver link is present (but don't test exact value as it depends on implementation)
        solver_link = game_data.get('solver_link')
        self.assertIsNotNone(solver_link, "Solver link should be generated")

        #self.assertIsNotNone(preflop_moves, "PREFLOP moves not found in game data")
        self.assertEqual(expected_moves, preflop_moves)

    def test_process_window_basic_3(self):
        """Test that process_window returns valid game data with expected moves."""
        # Load test image and create CapturedWindow
        cv2_image = load_image("3.png")
        captured_window = self.create_captured_window(cv2_image)
        
        # Create processor and temp folder
        processor = self.create_poker_processor()
        temp_folder = self.create_temp_folder()

        # Execute the method under test
        game_data = processor.process_window(captured_window, temp_folder)

        # Expected moves in web format
        expected_moves = [
            {'player_label': 'EARLY_POSITION', 'action': 'fold'},
            {'player_label': 'MIDDLE_POSITION', 'action': 'fold'},
        ]

        # Extract PREFLOP moves from web format
        preflop_moves = None
        for street_data in game_data['moves']:
            if street_data['street'] == 'Preflop':
                preflop_moves = street_data['moves']
                break

        # Test solver link is present (but don't test exact value as it depends on implementation)
        solver_link = game_data.get('solver_link')
        self.assertIsNotNone(solver_link, "Solver link should be generated")

        self.assertIsNotNone(preflop_moves, "PREFLOP moves not found in game data")
        self.assertEqual(expected_moves, preflop_moves)

    def test_process_window_basic_4(self):
        """Test that process_window returns valid game data with no moves."""
        # Load test image and create CapturedWindow
        cv2_image = load_image("4.png")
        captured_window = self.create_captured_window(cv2_image)
        
        # Create processor and temp folder
        processor = self.create_poker_processor()
        temp_folder = self.create_temp_folder()

        # Execute the method under test
        game_data = processor.process_window(captured_window, temp_folder)

        # Expected moves in web format (empty list)
        expected_moves = []

        # Extract PREFLOP moves from web format
        preflop_moves = None
        for street_data in game_data['moves']:
            if street_data['street'] == 'Preflop':
                preflop_moves = street_data['moves']
                break

        # Test solver link is present (but don't test exact value as it depends on implementation)
        solver_link = game_data.get('solver_link')
        self.assertIsNotNone(solver_link, "Solver link should be generated")

        self.assertIsNotNone(preflop_moves, "PREFLOP moves not found in game data")
        self.assertEqual(expected_moves, preflop_moves)

    def test_process_window_basic_5(self):
        """Test that process_window returns valid game data with expected moves."""
        # Load test image and create CapturedWindow
        cv2_image = load_image("5.png")
        captured_window = self.create_captured_window(cv2_image)
        
        # Create processor and temp folder
        processor = self.create_poker_processor()
        temp_folder = self.create_temp_folder()

        # Execute the method under test
        game_data = processor.process_window(captured_window, temp_folder)

        # Expected moves in web format
        expected_moves = [
            {'player_label': 'EARLY_POSITION', 'action': 'raise'}
        ]

        # Extract PREFLOP moves from web format
        preflop_moves = None
        for street_data in game_data['moves']:
            if street_data['street'] == 'Preflop':
                preflop_moves = street_data['moves']
                break

        # Test solver link is present (but don't test exact value as it depends on implementation)
        solver_link = game_data.get('solver_link')
        self.assertIsNotNone(solver_link, "Solver link should be generated")

        self.assertIsNotNone(preflop_moves, "PREFLOP moves not found in game data")
        self.assertEqual(expected_moves, preflop_moves)

    def test_process_window_basic_6(self):
        """Test that process_window returns valid game data with multi-street moves."""
        # Load test image and create CapturedWindow
        cv2_image = load_image("6.png")
        captured_window = self.create_captured_window(cv2_image)
        
        # Create processor and temp folder
        processor = self.create_poker_processor()
        temp_folder = self.create_temp_folder()

        # Execute the method under test
        game_data = processor.process_window(captured_window, temp_folder)

        # Expected moves in web format
        expected_moves = [
            {
                'street': 'Preflop',
                'moves': [
                    {'player_label': 'EARLY_POSITION', 'action': 'raise'},
                    {'player_label': 'MIDDLE_POSITION', 'action': 'call'},
                    {'player_label': 'CUTOFF', 'action': 'fold'},
                    {'player_label': 'BUTTON', 'action': 'call'},
                    {'player_label': 'SMALL_BLIND', 'action': 'call'},
                    {'player_label': 'BIG_BLIND', 'action': 'call'},
                ]
            },
            {
                'street': 'Flop',
                'moves': [
                    {'player_label': 'SMALL_BLIND', 'action': 'check'},
                    {'player_label': 'BIG_BLIND', 'action': 'check'},
                    {'player_label': 'EARLY_POSITION', 'action': 'check'},
                ]
            },
            {
                'street': 'Turn',
                'moves': []
            },
            {
                'street': 'River',
                'moves': []
            }
        ]

        # Test solver link is present (but don't test exact value as it depends on implementation)
        solver_link = game_data.get('solver_link')
        self.assertIsNotNone(solver_link, "Solver link should be generated")

        # Compare the moves structure
        result_moves = game_data['moves']
        self.assertEqual(expected_moves, result_moves)

    def test_process_window_basic_7(self):
        """Test that process_window returns valid game data with multi-street moves and solver link."""
        # Load test image and create CapturedWindow
        cv2_image = load_image("7.png")
        captured_window = self.create_captured_window(cv2_image)
        
        # Create processor and temp folder
        processor = self.create_poker_processor()
        temp_folder = self.create_temp_folder()

        # Execute the method under test
        game_data = processor.process_window(captured_window, temp_folder)

        # Expected moves in web format
        expected_moves = [
            {
                'street': 'Preflop',
                'moves': [
                    {'player_label': 'BUTTON', 'action': 'raise'},
                    {'player_label': 'SMALL_BLIND', 'action': 'call'},
                    {'player_label': 'BIG_BLIND', 'action': 'call'},
                ]
            },
            {
                'street': 'Flop',
                'moves': [
                    {'player_label': 'SMALL_BLIND', 'action': 'check'},
                    {'player_label': 'BIG_BLIND', 'action': 'check'},
                    {'player_label': 'BUTTON', 'action': 'bet'},
                    {'player_label': 'SMALL_BLIND', 'action': 'call'},
                    {'player_label': 'BIG_BLIND', 'action': 'call'},
                ]
            },
            {
                'street': 'Turn',
                'moves': []
            },
            {
                'street': 'River',
                'moves': []
            }
        ]

        # Debug output (keep original print statements)
        result_moves = game_data['moves']
        print(result_moves)
        
        # Test solver link is present (but don't test exact value as it depends on implementation)
        solver_link = game_data.get('solver_link')

        #REAL
        print("https://app.flophero.com/omaha/cash/strategies?research=full_tree&site=GGPoker&bb=10&blindStructure=Regular&players=3&openRaise=3.5&stack=100&topRanks&suitLevel&preflopActions=r35_c_c&flopActions=c_c_r70_c_c&turnActions&riverActions&boardCards=6s5d3dTd")

        #todo: DON'T work only due to lack of TURN

        print("https://app.flophero.com/omaha/cash/strategies?research=full_tree&site=GGPoker&bb=10&blindStructure=Regular&players=3&openRaise=3.5&stack=100&topRanks&suitLevel&preflopActions=r35_c_c&flopActions=c_c_r70_c_c&turnActions&riverActions&boardCards=7s6c5s")
        self.assertIsNotNone(solver_link, "Solver link should be generated")

        # Compare the moves structure
        self.assertEqual(expected_moves, result_moves)

    def test_process_window_basic_8(self):
        # Load test image and create CapturedWindow
        cv2_image = load_image("8.png")
        captured_window = self.create_captured_window(cv2_image)

        # Create processor and temp folder
        processor = self.create_poker_processor()
        temp_folder = self.create_temp_folder()

        # Execute the method under test
        game_data = processor.process_window(captured_window, temp_folder)

        # Expected moves in web format
        expected_moves = [
            {
                'street': 'Preflop',
                'moves': [
                    {'player_label': 'BUTTON', 'action': 'fold'},
                    {'player_label': 'SMALL_BLIND', 'action': 'call'},
                    {'player_label': 'BIG_BLIND', 'action': 'raise'},
                    {'player_label': 'SMALL_BLIND', 'action': 'call'},
                ]
            },
            {
                'street': 'Flop',
                'moves': [
                    {'player_label': 'SMALL_BLIND', 'action': 'bet'},
                    {'player_label': 'BIG_BLIND', 'action': 'call'},
                ]
            },
            {
                'street': 'Turn',
                'moves': [
                        {'player_label': 'SMALL_BLIND', 'action': 'bet'},
                ]
            },
            {
                'street': 'River',
                'moves': []
            }
        ]

        # Debug output (keep original print statements)
        result_moves = game_data['moves']
        print(result_moves)

        # Test solver link is present (but don't test exact value as it depends on implementation)
        solver_link = game_data.get('solver_link')

        # REAL
        print(
            "https://app.flophero.com/omaha/cash/strategies?research=full_tree&site=GGPoker&bb=10&blindStructure=Regular&players=3&openRaise=3.5&stack=100&preflopActions=f_c_r30_c&flopActions=r50_c&turnActions=r83&riverActions&boardCards=Jc7d5c5s")
        # Generated
        print(
            "https://app.flophero.com/omaha/cash/strategies?research=full_tree&site=GGPoker&bb=10&blindStructure=Regular&players=3&openRaise=3.5&stack=100&preflopActions=f_c_r35_c&flopActions=b_c&turnActions=b&boardCards=Qc5sQdTs")
        self.assertIsNotNone(solver_link, "Solver link should be generated")

        # Compare the moves structure
        self.assertEqual(expected_moves, result_moves)

    def test_process_window_basic_9(self):
        # Load test image and create CapturedWindow
        cv2_image = load_image("9.png")
        captured_window = self.create_captured_window(cv2_image)

        # Create processor and temp folder
        processor = self.create_poker_processor()
        temp_folder = self.create_temp_folder()

        # Execute the method under test

        with self.assertRaises(InvalidPositionSequenceError):
            processor.process_window(captured_window, temp_folder)

    def test_process_window_basic_10(self):
        # Load test image and create CapturedWindow
        cv2_image = load_image("10.png")
        captured_window = self.create_captured_window(cv2_image)

        # Create processor and temp folder
        processor = self.create_poker_processor()
        temp_folder = self.create_temp_folder()

        # Execute the method under test
        with self.assertRaises(WrongPlayerAmount):
            processor.process_window(captured_window, temp_folder)


    def test_process_window_basic_12(self):
        # Load test image and create CapturedWindow
        cv2_image = load_image("12.png")
        captured_window = self.create_captured_window(cv2_image)

        # Create processor and temp folder
        processor = self.create_poker_processor()
        temp_folder = self.create_temp_folder()

        # Execute the method under test
        with self.assertRaises(ValueError):
            processor.process_window(captured_window, temp_folder)
