from typing import List, Optional
from dataclasses import dataclass

from src.core.domain.game import Game


@dataclass
class GameChangeResult:
    has_changed: bool
    is_new_game: bool
    is_new_street: bool
    old_game: Optional[Game]
    new_game: Game
    change_type: str


class StateChangeDetector:

    def detect_single_game_change(self, new_game: Game, old_game: Optional[Game]) -> GameChangeResult:
        if old_game is None:
            return GameChangeResult(
                has_changed=True,
                is_new_game=True,
                is_new_street=False,
                old_game=None,
                new_game=new_game,
                change_type="new_table"
            )

        is_new_game = self._is_new_game(new_game, old_game)
        is_new_street = self._is_new_street(new_game, old_game)

        has_any_change = (
                new_game.get_player_cards_string() != old_game.get_player_cards_string() or
                new_game.get_table_cards_string() != old_game.get_table_cards_string() or
                new_game.get_positions_string() != old_game.get_positions_string()
        )

        change_type = self._determine_change_type(is_new_game, is_new_street, has_any_change)

        return GameChangeResult(
            has_changed=has_any_change,
            is_new_game=is_new_game,
            is_new_street=is_new_street,
            old_game=old_game,
            new_game=new_game,
            change_type=change_type
        )

    def detect_batch_changes(self, new_games: List[Game], old_games: List[Game]) -> bool:
        if len(new_games) != len(old_games):
            return True

        for new_game, old_game in zip(new_games, old_games):
            change_result = self.detect_single_game_change(new_game, old_game)
            if change_result.has_changed:
                return True

        return False

    def _is_new_game(self, new_game: Game, old_game: Game) -> bool:
        return new_game.get_player_cards_string() != old_game.get_player_cards_string()

    def _is_new_street(self, new_game: Game, old_game: Game) -> bool:
        old_table_cards = old_game.get_table_cards_string()
        new_table_cards = new_game.get_table_cards_string()

        return bool(old_table_cards) and (new_table_cards != old_table_cards)

    def _determine_change_type(self, is_new_game: bool, is_new_street: bool, has_any_change: bool) -> str:
        if not has_any_change:
            return "no_change"
        elif is_new_game:
            return "new_game"
        elif is_new_street:
            return "new_street"
        else:
            return "position_change"

    def log_change(self, change_result: GameChangeResult, window_name: str):
        if change_result.is_new_game:
            print(
                f"  🆕 NEW GAME detected at '{window_name}' - Player cards: {change_result.new_game.get_player_cards_string()}")

        if change_result.is_new_street and change_result.old_game:
            old_street = change_result.old_game.get_street()
            new_street = change_result.new_game.get_street()
            old_street_name = old_street.value if old_street else 'Unknown'
            new_street_name = new_street.value if new_street else 'Unknown'
            print(f"  🔄 NEW STREET at '{window_name}' - {old_street_name} → {new_street_name}")