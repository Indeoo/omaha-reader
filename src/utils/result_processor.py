import cv2
from typing import List
from src.readed_card import ReadedCard

try:
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def process_results(readed_cards: List[ReadedCard], result_type="player", **kwargs):
    """
    Unified function to process both table and player card results

    Args:
        readed_cards: List of ReadedCard objects
        result_type: "player" or "table"
        **kwargs: Additional arguments (image, detector for table cards)
    """

    if result_type == "table":
        _process_table_results(readed_cards, **kwargs)
    elif result_type == "player":
        _process_player_results(readed_cards, **kwargs)


def _process_table_results(readed_cards: List[ReadedCard], image=None, detector=None, debug=True):
    """Process table card results"""

    if not debug:
        return

    print(f"Detected {len(readed_cards)} table cards")

    # Save cards
    if readed_cards:
        from src.utils.save_utils import save_detected_cards
        save_detected_cards(readed_cards)

    # Display if possible
    if MATPLOTLIB_AVAILABLE and image is not None and detector is not None:
        _display_table_results(readed_cards, image, detector)


def _process_player_results(readed_cards: List[ReadedCard], debug=True):
    """Process player card results"""

    if not debug or not readed_cards:
        return

    print(f"Found {len(readed_cards)} player cards")

    # Save cards
    if readed_cards:
        from src.utils.save_utils import save_readed_player_cards
        save_readed_player_cards(readed_cards)

    # Display if possible
    if MATPLOTLIB_AVAILABLE:
        _display_player_results(readed_cards)


def _display_table_results(readed_cards: List[ReadedCard], image, detector):
    """Display table card detection results"""
    try:
        result_image = detector.draw_detected_cards(image, readed_cards)
        processed = detector.image_preprocessor.preprocess_image(image)

        plt.figure(figsize=(15, 10))

        plt.subplot(2, 2, 1)
        plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        plt.title('Original Image')
        plt.axis('off')

        plt.subplot(2, 2, 2)
        plt.imshow(processed, cmap='gray')
        plt.title('Preprocessed')
        plt.axis('off')

        plt.subplot(2, 2, 3)
        plt.imshow(cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB))
        plt.title('Detected Cards')
        plt.axis('off')

        plt.subplot(2, 2, 4)
        if readed_cards:
            sample_card = readed_cards[0].card_region
            plt.imshow(cv2.cvtColor(sample_card, cv2.COLOR_BGR2RGB))
            plt.title('Sample Card')
        plt.axis('off')

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Display not available: {e}")


def _display_player_results(readed_cards: List[ReadedCard]):
    """Display player card detection results"""
    try:
        if not readed_cards:
            return

        plt.figure(figsize=(15, 8))

        # Display first few card regions as samples
        num_cards = min(len(readed_cards), 6)
        for i in range(num_cards):
            plt.subplot(2, 3, i + 1)
            card = readed_cards[i]
            plt.imshow(cv2.cvtColor(card.card_region, cv2.COLOR_BGR2RGB))
            plt.title(f"{card.template_name} ({card.match_score:.2f})")
            plt.axis('off')

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Display not available: {e}")