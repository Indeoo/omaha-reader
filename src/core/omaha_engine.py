#!/usr/bin/env python3

import os
from typing import List

from src.core.domain.detection_result import DetectionResult
from src.core.service.detection_notifier import DetectionNotifier
from src.core.service.game_state_manager import GameStateManager
from src.core.service.image_capture_service import ImageCaptureService
from src.core.utils.fs_utils import create_timestamp_folder
from src.core.utils.poker_game_processor import PokerGameProcessor
from src.core.domain.game import Game
from src.core.domain.captured_image import CapturedWindow


class OmahaEngine:
    def __init__(self, country="canada", debug_mode: bool = True):
        self.debug_mode = debug_mode

        self.image_capture_service = ImageCaptureService(debug_mode=debug_mode)
        self.notifier = DetectionNotifier()
        self.game_state_manager = GameStateManager()

        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

        self._poker_game_processor = PokerGameProcessor(
            country=country,
            project_root=project_root,
            save_result_images=False,
            write_detection_files=False
        )

    def add_observer(self, callback):
        self.notifier.add_observer(callback)

    def get_latest_results(self) -> dict:
        return self.game_state_manager.get_latest_results()

    def detect_and_notify(self):
        timestamp_folder = create_timestamp_folder(self.debug_mode)
        changed_images = self.image_capture_service.get_changed_images(timestamp_folder)

        if changed_images:
            self.process_windows(changed_images)
            self._notify_observers()

    def force_detect(self):
        timestamp_folder = create_timestamp_folder(self.debug_mode)
        captured_windows = self.image_capture_service.capture_windows(timestamp_folder)

        if captured_windows:
            print(f"🔍 Force processing {len(captured_windows)} images")
            self.process_windows(captured_windows)
            self._notify_observers()
            print(f"🔄 Force detection completed - notified observers")

    def process_windows(self, captured_windows):
        for i, captured_image in enumerate(captured_windows):
            try:
                print(f"\n📷 Processing image {i + 1}: {captured_image.window_name}")
                print("-" * 40)
                detection_result = self._process_single_image(captured_image)
                self.game_state_manager.manage(detection_result)

            except Exception as e:
                print(f"❌ Error processing {captured_image.window_name}: {str(e)}")

    def _process_single_image(self, captured_image: CapturedWindow) -> DetectionResult:
        window_name = captured_image.window_name
        cv2_image = captured_image.get_cv2_image()

        try:
            print(f"🃏 Detecting cards in {window_name}...")
            cards_result = self._poker_game_processor.detect_cards(cv2_image)

            if cards_result.has_cards:
                player_count = len(cards_result.player_cards)
                table_count = len(cards_result.table_cards)
                print(f"    ✅ Found {player_count} player cards, {table_count} table cards")
            else:
                print(f"    ℹ️  No cards detected")

            positions_result = None
            if self._poker_game_processor.should_detect_positions(cards_result):
                print(f"👤 Detecting positions in {window_name}...")
                positions_result = self._poker_game_processor.detect_positions(cv2_image)

                if positions_result.has_positions:
                    print(f"    ✅ Found positions:")
                    for player_num, position in sorted(positions_result.player_positions.items()):
                        position_type = "Main player" if player_num == 1 else f"Player {player_num}"
                        print(f"        {position_type}: {position}")
                else:
                    print(f"    ℹ️  No positions detected")

            moves_result = None
            if self._poker_game_processor.should_detect_moves(cards_result):
                print(f"🎯 Detecting moves in {window_name}...")
                moves_result = self._poker_game_processor.detect_moves(cv2_image, window_name)

            stakes_result = None
            if self._poker_game_processor.should_detect_stakes(cards_result):
                print(f"💰 Detecting stakes in {window_name}...")
                stakes_result = self._poker_game_processor.detect_stakes(captured_image)

            result = self._poker_game_processor.combine_detection_results(
                captured_image, cards_result, positions_result, moves_result, stakes_result
            )

            return result

        except Exception as e:
            raise Exception(f"❌ Error in detection for {window_name}: {str(e)}")

    def _notify_observers(self):
        notification_data = self.game_state_manager.get_notification_data()
        self.notifier.notify_observers(notification_data)
        print(f"🔄 Detection changed - notified observers at {notification_data['last_update']}")

    def _get_current_games(self) -> List[Game]:
        latest_results = self.game_state_manager.get_latest_results()

        games = []
        for game_dict in latest_results.get('detections', []):
            game = Game(
                window_name=game_dict['window_name'],
                player_cards=[],
                table_cards=[]
            )
            games.append(game)

        return games
