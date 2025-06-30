#!/usr/bin/env python3

import os

from src.core.domain.readed_card import ReadedCard
from src.core.service.detection_notifier import DetectionNotifier
from src.core.service.game_state_manager import GameStateManager
from src.core.service.image_capture_service import ImageCaptureService
from src.core.service.move_reconstructor import MoveReconstructor
from src.core.utils.fs_utils import create_timestamp_folder
from src.core.utils.poker_game_processor import PokerGameProcessor
from src.core.domain.captured_image import CapturedWindow


class OmahaEngine:
    def __init__(self, country="canada", debug_mode: bool = True):
        self.debug_mode = debug_mode

        self.image_capture_service = ImageCaptureService(debug_mode=debug_mode)
        self.notifier = DetectionNotifier()
        self.game_state_manager = GameStateManager()
        self.state_repository = self.game_state_manager.repository

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

        player_cards = self._poker_game_processor.detect_player_cards(cv2_image)
        is_new_game = self.game_state_manager.is_new_game(window_name, player_cards)
        table_cards = self._poker_game_processor.detect_table_cards(cv2_image)

        if is_new_game:
            positions_result = self._poker_game_processor.detect_positions(cv2_image)
            self.state_repository.new_game(window_name, player_cards, table_cards, positions_result.player_positions)
        else:
            previous_table_cards = self.state_repository.get_table_cards(window_name)
            is_new_street = ReadedCard.format_cards_simple(table_cards) != ReadedCard.format_cards_simple(
                previous_table_cards)

            if is_new_street:
                self.state_repository.update_table_cards(window_name, table_cards)

        is_player_move = self._poker_game_processor.is_player_move(cv2_image, window_name)

        if is_player_move:
            current_game = self.state_repository.get_by_window(window_name)
            bids_before_update = self.state_repository.get_by_window(window_name).current_bids

            bids_result = self._poker_game_processor.detect_bids(captured_image)
            bids_updated = self.state_repository.update_bids(window_name, bids_result.bids)

            if bids_updated:
                print(f"💰 Bids updated for {window_name} - reconstructing moves...")
                self._reconstruct_moves(current_game, bids_before_update, bids_result.bids)

    def _reconstruct_moves(self, current_game, previous_bids, current_bids):
        current_street = current_game.get_street()
        if not current_street:
            return

        moves = self.move_reconstructor.reconstruct_moves(
            current_bids=current_bids,
            previous_bids=previous_bids,
            current_street=current_street,
            positions=current_game.positions
        )

        if moves:
            current_game.add_moves(moves, current_street)
            print(f"    📝 Reconstructed {len(moves)} moves for {current_street.value}:")
            for move in moves:
                action_desc = f"{move.action_type.value}"
                if move.amount > 0:
                    action_desc += f" ${move.amount:.2f}"
                player_label = f"P{move.player_number}"
                print(f"        {player_label}: {action_desc}")

    def _notify_observers(self):
        notification_data = self.game_state_manager.get_notification_data()
        self.notifier.notify_observers(notification_data)
        print(f"🔄 Detection changed - notified observers at {notification_data['last_update']}")
