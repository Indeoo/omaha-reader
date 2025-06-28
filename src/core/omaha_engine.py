#!/usr/bin/env python3

import os
from typing import Optional

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
                self._process_window(captured_image)

            except Exception as e:
                print(f"❌ Error processing {captured_image.window_name}: {str(e)}")

    def _process_window(self, captured_image: CapturedWindow):
        window_name = captured_image.window_name
        cv2_image = captured_image.get_cv2_image()

        print(f"🃏 Processing {window_name}...")
        player_cards = self._poker_game_processor.detect_player_cards(cv2_image)
        table_cards = self._poker_game_processor.detect_table_cards(cv2_image)
        player_count = len(player_cards)
        table_count = len(table_cards)
        print(f"    ✅ Found {player_count} player cards, {table_count} table cards")

        is_new_game = self.game_state_manager.is_new_game(window_name, player_cards)

        if is_new_game:
            positions_result = self._poker_game_processor.detect_positions(cv2_image)
            print(f"    ✅ Found positions:")
            for player_num, position in sorted(positions_result.player_positions.items()):
                position_type = "Main player" if player_num == 1 else f"Player {player_num}"
                print(f"        {position_type}: {position}")

        if self._poker_game_processor.is_player_move(cv2_image, window_name):
            actions_result = self._poker_game_processor.detect_actions(cv2_image, window_name)
            bids_result = None
            if self._poker_game_processor.should_detect_bids(player_cards):
                print(f"💰 Detecting bids in {window_name}...")
                bids_result = self._poker_game_processor.detect_bids(captured_image)

            print(f"🔄 Reconstructing moves for {window_name}...")
            new_game_state = self._build_game_state(window_name, player_cards, table_cards, positions_result, bids_result, is_new_game)
            moves = self._reconstruct_moves(window_name, new_game_state)

        result = self._poker_game_processor.combine_detection_results(
            captured_image, player_cards, table_cards, positions_result, actions_result, bids_result
        )

        self.game_state_manager.manage(result)

    def _reconstruct_moves(self, window_name: str, new_game_state):
        previous_game_state = self.game_state_manager.get_previous_game_state(window_name)

        if previous_game_state and self._is_new_street(new_game_state, previous_game_state):
            print(f"    🔄 New street detected - resetting bids")
            new_game_state.reset_bids_for_new_street()
            if new_game_state.bids_result and new_game_state.bids_result.bids:
                new_game_state.current_bids = new_game_state.bids_result.bids

        moves = self.move_reconstructor.reconstruct_moves(new_game_state)

        if moves:
            current_street = new_game_state.get_street()
            new_game_state.add_moves(moves, current_street)
            print(f"    📝 Reconstructed {len(moves)} moves for {current_street.value}:")
            for move in moves:
                action_desc = f"{move.action_type.value}"
                if move.amount > 0:
                    action_desc += f" ${move.amount:.2f}"
                player_label = "Main" if move.player_number == 1 else f"P{move.player_number}"
                print(f"        {player_label}: {action_desc}")

        self.game_state_manager.store_previous_game_state(window_name, new_game_state)

        return moves

    def _build_game_state(self, window_name: str, player_cards, table_cards, positions_result, bids_result, is_new_game) -> Optional[
        Game]:
        positions = {}
        if positions_result and positions_result.has_positions:
            positions = positions_result.player_positions

        current_bids = bids_result.bids

        previous_game = self.game_state_manager.get_previous_game_state(window_name)
        if previous_game and not is_new_game:
            move_history = previous_game.move_history
        else:
            move_history = []

        return Game(
            window_name=window_name,
            player_cards=player_cards,
            table_cards=table_cards,
            positions=positions,
            current_bids=current_bids,
            move_history=move_history
        )

    def _is_new_street(self, current_game: Game, previous_game: Game) -> bool:
        current_street = current_game.get_street()
        previous_street = previous_game.get_street()
        return current_street != previous_street

    def _notify_observers(self):
        notification_data = self.game_state_manager.get_notification_data()
        self.notifier.notify_observers(notification_data)
        print(f"🔄 Detection changed - notified observers at {notification_data['last_update']}")
