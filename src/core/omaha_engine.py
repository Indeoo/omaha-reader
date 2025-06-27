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
from src.core.domain.captured_image import CapturedImage


class OmahaGameReader:
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

    def remove_observer(self, callback):
        self.notifier.remove_observer(callback)

    def get_latest_results(self) -> dict:
        return self.game_state_manager.get_latest_results()

    def detect_and_notify(self) -> List[Game]:
        return self._execute_detection(use_change_detection=True, always_notify=False)

    def force_detect(self) -> List[Game]:
        return self._execute_detection(use_change_detection=False, always_notify=True)

    def _execute_detection(self, use_change_detection: bool, always_notify: bool) -> List[Game]:
        try:
            timestamp_folder = create_timestamp_folder(self.debug_mode)

            images_to_process = self._get_images_to_process(timestamp_folder, use_change_detection)

            if not images_to_process:
                if use_change_detection:
                    print("🚫 No poker tables detected or no changes")
                else:
                    print("🚫 No poker tables detected")
                return self._get_current_games()

            all_games = []

            for i, captured_image in enumerate(images_to_process):
                try:
                    detection_result = self._process_single_image(captured_image, i)

                    should_notify = self._update_state_and_check_notification(
                        detection_result, timestamp_folder, use_change_detection, always_notify
                    )

                    if should_notify:
                        self._notify_observers(use_change_detection)

                    game = self.game_state_manager._convert_result_to_game(detection_result)
                    if game:
                        all_games.append(game)

                except Exception as e:
                    print(f"❌ Error processing {captured_image.window_name}: {str(e)}")

            return all_games

        except Exception as e:
            print(f"❌ Error in detection: {str(e)}")
            return []

    def _get_images_to_process(self, timestamp_folder: str, use_change_detection: bool) -> List[CapturedImage]:
        if use_change_detection:
            return self.image_capture_service.get_images_to_process(timestamp_folder)
        else:
            captured_windows = self.image_capture_service.capture_windows(timestamp_folder)
            if captured_windows:
                print(f"🔍 Force processing {len(captured_windows)} images")
            return captured_windows

    def _process_single_image(self, captured_image: CapturedImage, index: int) -> DetectionResult:
        window_name = captured_image.window_name

        print(f"\n📷 Processing image {index + 1}: {window_name}")
        print("-" * 40)

        try:
            cv2_image = captured_image.get_cv2_image()
        except Exception as e:
            raise Exception(f"❌ Error converting image {window_name}: {str(e)}")

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

    def _update_state_and_check_notification(self,
                                             detection_result: DetectionResult,
                                             timestamp_folder: str,
                                             use_change_detection: bool,
                                             always_notify: bool) -> bool:
        if not use_change_detection:
            self.game_state_manager.update_state(detection_result, timestamp_folder)
            return always_notify
        else:
            has_changed = self.game_state_manager.update_state(detection_result, timestamp_folder)
            return has_changed or always_notify

    def _notify_observers(self, use_change_detection: bool):
        notification_data = self.game_state_manager.get_notification_data()
        self.notifier.notify_observers(notification_data)

        if not use_change_detection:
            print(f"🔄 Force detection completed - notified observers")
        else:
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

    def get_window_hash_stats(self) -> dict:
        return self.image_capture_service.get_window_hash_stats()