from typing import List

from src.core.domain.detection import Detection


def format_cards_simple(cards: List[Detection]) -> str:
    """
    Format a list of ReadedCard objects as simple concatenated template names

    Args:
        cards: List of ReadedCard objects

    Returns:
        Formatted string like "4S6DJH" (just template names concatenated)
    """
    if not cards:
        return ""
    return ''.join(card.template_name for card in cards if card.template_name)