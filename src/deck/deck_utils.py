from typing import List


def format_card_with_unicode(card_name: str) -> str:
    """
    Convert card name to include Unicode suit symbols

    Args:
        card_name: Card name like "4S", "JH", "AC", "10D"

    Returns:
        Formatted string like "4S(♤)", "JH(♡)", "AC(♧)", "10D(♢)"
    """
    if not card_name or len(card_name) < 2:
        return card_name

    # Unicode suit symbols mapping
    suit_unicode = {
        'S': '♤',  # Spades (black spade suit)
        'H': '♡',  # Hearts (white heart suit)
        'D': '♢',  # Diamonds (white diamond suit)
        'C': '♧'  # Clubs (white club suit)
    }

    # Get the last character as suit
    suit = card_name[-1].upper()

    if suit in suit_unicode:
        return f"{card_name}({suit_unicode[suit]})"
    else:
        return card_name


def format_cards_with_unicode(cards: List[str]) -> str:
    """
    Format a list of cards with Unicode suit symbols

    Args:
        cards: List of card names like ["4S", "6D", "JH", "AC"]

    Returns:
        Formatted string like "4S(♤)6D(♢)JH(♡)AC(♧)"
    """
    return ''.join([format_card_with_unicode(card) for card in cards])