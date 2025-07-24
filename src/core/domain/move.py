from dataclasses import dataclass

from src.core.domain.action_type import ActionType
from src.core.domain.street import Street


@dataclass
class Move:
    player_number: int  # 1-6
    action_type: ActionType
    amount: float  # Amount added this action
    street: Street
    total_pot_contribution: float  # Total contribution this street
