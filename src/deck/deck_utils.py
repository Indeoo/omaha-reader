from typing import List
from src.readed_card import ReadedCard


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
