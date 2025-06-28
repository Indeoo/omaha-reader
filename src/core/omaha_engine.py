#!/usr/bin/env python3

import os
from typing import List, Dict, Optional

from src.core.domain.detection_result import DetectionResult
from src.core.service.detection_notifier import DetectionNotifier
from src.core.service.game_state_manager import GameStateManager
from src.core.service.image_capture_service import ImageCaptureService
from src.core.service.move_reconstructor import MoveReconstructor
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

        self.move_reconstructor = MoveReconstructor()

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
            self._process_windows(changed_images)
            self._notify_observers()

    def force_detect(self):
        timestamp_folder = create_timestamp_folder(self.debug_mode)
        captured_windows = self.image_capture_service.capture_windows(timestamp_folder)

        if captured_windows:
            print(f"🔍 Force processing {len(captured_windows)} images")
            self._process_windows(captured_windows)
            self._notify_observers()
            print(f"🔄 Force detection completed - notified observers")

    def _process_windows(self, captured_windows):
        for i, captured_image in enumerate(captured_windows):
            try:
                print(f"\n📷 Processing image {i + 1}: {captured_image.window_name}")
                print("-" * 40)
                detection_result = self._process_window(captured_image)
                self.game_state_manager.manage(detection_result)

            except Exception as e:
                print(f"❌ Error processing {captured_image.window_name}: {str(e)}")

    def _process_window(self, captured_image: CapturedWindow) -> DetectionResult:
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

            bids_result = None
            if self._poker_game_processor.should_detect_bids(cards_result):
                print(f"💰 Detecting bids in {window_name}...")
                bids_result = self._poker_game_processor.detect_bids(captured_image)

            if self._poker_game_processor.is_player_move(cv2_image, window_name):
                print(f"🔄 Reconstructing moves for {window_name}...")
                self._reconstruct_moves(window_name, cards_result, positions_result, bids_result)

            result = self._poker_game_processor.combine_detection_results(
                captured_image, cards_result, positions_result, moves_result, bids_result
            )

            return result

        except Exception as e:
            raise Exception(f"❌ Error in detection for {window_name}: {str(e)}")

    def _reconstruct_moves(self, window_name: str, cards_result, positions_result, bids_result):
        current_game = self._build_game_state(window_name, cards_result, positions_result, bids_result)

        if not current_game:
            return

        previous_game_state = self.game_state_manager.get_previous_game_state(window_name)

        if previous_game_state and self._is_new_game(current_game, previous_game_state):
            print(f"    🆕 New game detected - resetting move history")
            current_game.reset_move_history()
            previous_game_state = None

        if previous_game_state and self._is_new_street(current_game, previous_game_state):
            print(f"    🔄 New street detected - resetting bids")
            current_game.reset_bids_for_new_street()
            if bids_result and bids_result.bids:
                current_game.current_bids = self._parse_bids(bids_result.bids)

        moves = self.move_reconstructor.reconstruct_moves(current_game)

        if moves:
            current_street = current_game.get_street()
            current_game.add_moves(moves, current_street)
            print(f"    📝 Reconstructed {len(moves)} moves for {current_street.value}:")
            for move in moves:
                action_desc = f"{move.action_type.value}"
                if move.amount > 0:
                    action_desc += f" ${move.amount:.2f}"
                player_label = "Main" if move.player_number == 1 else f"P{move.player_number}"
                print(f"        {player_label}: {action_desc}")

        self.game_state_manager.store_previous_game_state(window_name, current_game)

    def _build_game_state(self, window_name: str, cards_result, positions_result, bids_result) -> Optional[Game]:
        if not cards_result.has_cards:
            return None

        positions = {}
        if positions_result and positions_result.has_positions:
            positions = positions_result.player_positions

        current_bids = {}
        if bids_result and bids_result.bids:
            current_bids = self._parse_bids(bids_result.bids)

        previous_game = self.game_state_manager.get_previous_game_state(window_name)
        move_history = None
        if previous_game and not self._is_new_game_by_cards(cards_result, previous_game):
            move_history = previous_game.move_history

        return Game(
            window_name=window_name,
            player_cards=cards_result.player_cards,
            table_cards=cards_result.table_cards,
            positions=positions,
            current_bids=current_bids,
            move_history=move_history
        )

    def _parse_bids(self, bids_dict: Dict[str, str]) -> Dict[int, float]:
        position_to_player = {
            'POSITION1': 1,
            'POSITION2': 2,
            'POSITION3': 3,
            'POSITION4': 4,
            'POSITION5': 5,
            'POSITION6': 6
        }

        parsed_bids = {}
        for position_key, bid_str in bids_dict.items():
            if position_key in position_to_player and bid_str:
                try:
                    player_num = position_to_player[position_key]
                    bid_amount = float(bid_str)
                    parsed_bids[player_num] = bid_amount
                except ValueError:
                    print(f"    ⚠️ Could not parse bid '{bid_str}' for {position_key}")

        return parsed_bids

    def _is_new_game(self, current_game: Game, previous_game: Game) -> bool:
        return self._is_new_game_by_cards(current_game, previous_game)

    def _is_new_game_by_cards(self, current_game, previous_game) -> bool:
        current_player_cards = current_game.get_player_cards_string() if hasattr(current_game,
                                                                                 'get_player_cards_string') else ''.join(
            [c.template_name for c in current_game.player_cards if c.template_name])
        previous_player_cards = previous_game.get_player_cards_string()
        return current_player_cards != previous_player_cards

    def _is_new_street(self, current_game: Game, previous_game: Game) -> bool:
        current_street = current_game.get_street()
        previous_street = previous_game.get_street()
        return current_street != previous_street

    def _notify_observers(self):
        notification_data = self.game_state_manager.get_notification_data()
        self.notifier.notify_observers(notification_data)
        print(f"🔄 Detection changed - notified observers at {notification_data['last_update']}")