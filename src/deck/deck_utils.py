from typing import List
from src.readed_card import ReadedCard


# def format_cards_with_unicode(cards: List[ReadedCard]) -> str:
#     """
#     Format a list of ReadedCard objects with Unicode suit symbols
#
#     Args:
#         cards: List of ReadedCard objects
#
#     Returns:
#         Formatted string like "4S(♤)6D(♢)JH(♡)AC(♧)"
#     """
#     if not cards:
#         return ""
#
#     # Extract template names from ReadedCard objects
#     card_names = [card.template_name for card in cards if card.template_name]
#     return ''.join([format_card_with_unicode(card) for card in card_names])


def format_cards(cards: List[ReadedCard], show_probabilities: bool = True) -> str:
    """
    Format a list of ReadedCard objects with Unicode suit symbols and optionally include probabilities

    Args:
        cards: List of ReadedCard objects
        show_probabilities: Whether to include match scores/probabilities in the output

    Returns:
        Formatted string like "4S(♤)[0.85]6D(♢)[0.92]JH(♡)[0.78]AC(♧)[0.95]"
        or just "4S(♤)6D(♢)JH(♡)AC(♧)" if show_probabilities is False
    """
    if not cards:
        return ""

    formatted_cards = []
    for card in cards:
        if card.template_name:
            formatted_card = card.format_single_card(show_probabilities)
            formatted_cards.append(formatted_card)

    res = ''.join(card.template_name for card in cards)

    #return res + " " + ' '.join(formatted_cards)
    return res


# def print_cards_with_probabilities(cards: List[ReadedCard], window_name: str = "Window") -> None:
#     """
#     Print cards with detailed probability information
#
#     Args:
#         cards: List of ReadedCard objects
#         window_name: Name of the window/source for context
#     """
#     if not cards:
#         print(f"    ⚪ {window_name}: No cards detected")
#         return
#
#     # Format cards with unicode symbols and probabilities
#     cards_display = format_cards_with_unicode_and_probability(cards, show_probabilities=True)
#
#     # Calculate average confidence
#     valid_scores = [card.match_score for card in cards if card.match_score is not None]
#     avg_confidence = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
#
#     # Find lowest confidence card
#     min_confidence = min(valid_scores) if valid_scores else 0.0
#     min_card = min(cards, key=lambda c: c.match_score or 0.0) if valid_scores else None
#
#     print(f"    ✅ {window_name}: {cards_display}")
#     print(
#         f"        📊 Avg confidence: {avg_confidence:.3f}, Min: {min_confidence:.3f} ({min_card.template_name if min_card else 'N/A'})")


def get_cards_summary(cards: List[ReadedCard]) -> dict:
    """
    Get summary statistics for a list of detected cards

    Args:
        cards: List of ReadedCard objects

    Returns:
        Dictionary with summary statistics
    """
    if not cards:
        return {
            'count': 0,
            'avg_confidence': 0.0,
            'min_confidence': 0.0,
            'max_confidence': 0.0,
            'card_names': []
        }

    valid_scores = [card.match_score for card in cards if card.match_score is not None]
    card_names = [card.template_name for card in cards if card.template_name]

    return {
        'count': len(cards),
        'avg_confidence': sum(valid_scores) / len(valid_scores) if valid_scores else 0.0,
        'min_confidence': min(valid_scores) if valid_scores else 0.0,
        'max_confidence': max(valid_scores) if valid_scores else 0.0,
        'card_names': card_names
    }