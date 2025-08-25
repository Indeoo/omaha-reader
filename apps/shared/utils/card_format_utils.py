from typing import List

from apps.shared.domain.detection import Detection


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


def format_card_with_unicode(card_name: str) -> str:
    """
    Format single card name with unicode suit symbols.
    
    Args:
        card_name: Card name like "AS", "KH", etc.
        
    Returns:
        Formatted card with unicode symbols like "A♠", "K♥"
    """
    if not card_name or len(card_name) < 2:
        return card_name or "UNKNOWN"

    # Get rank and suit for cards
    rank = card_name[:-1]
    suit = card_name[-1].upper()

    suit_unicode = {
        'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'
    }

    return f"{rank}{suit_unicode.get(suit, suit)}"