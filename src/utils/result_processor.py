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
        **kwargs: Additional arguments (image, detector for table cards, original_image, result_image for player cards)
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


def _process_player_results(readed_cards: List[ReadedCard], debug=True, original_image=None, result_image=None):
    """Process player card results with enhanced visualization"""

    if not debug or not readed_cards:
        return

    print(f"Found {len(readed_cards)} player cards")

    # Save cards
    if readed_cards:
        from src.utils.save_utils import save_readed_player_cards
        save_readed_player_cards(readed_cards)

    # Display if possible
    if MATPLOTLIB_AVAILABLE:
        _display_player_results_enhanced(readed_cards, original_image, result_image)


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


def _display_player_results_enhanced(readed_cards: List[ReadedCard], original_image=None, result_image=None):
    """Display enhanced player card detection results with original and highlighted images"""
    try:
        if not readed_cards:
            print("No cards to display")
            return

        # Calculate grid layout based on available images and cards
        has_original = original_image is not None
        has_result = result_image is not None
        num_cards = min(len(readed_cards), 6)  # Show max 6 individual cards

        # Calculate subplot layout
        if has_original and has_result:
            # 2 overview images + individual cards
            total_plots = 2 + num_cards
            if total_plots <= 4:
                rows, cols = 2, 2
            elif total_plots <= 6:
                rows, cols = 2, 3
            else:
                rows, cols = 3, 3
        elif has_original or has_result:
            # 1 overview image + individual cards
            total_plots = 1 + num_cards
            if total_plots <= 4:
                rows, cols = 2, 2
            elif total_plots <= 6:
                rows, cols = 2, 3
            else:
                rows, cols = 3, 3
        else:
            # Only individual cards
            if num_cards <= 4:
                rows, cols = 2, 2
            elif num_cards <= 6:
                rows, cols = 2, 3
            else:
                rows, cols = 3, 3

        plt.figure(figsize=(15, 10))

        subplot_idx = 1

        # Display original image if available
        if has_original:
            plt.subplot(rows, cols, subplot_idx)
            plt.imshow(cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB))
            plt.title('Original Image')
            plt.axis('off')
            subplot_idx += 1

        # Display result image with detections if available
        if has_result:
            plt.subplot(rows, cols, subplot_idx)
            plt.imshow(cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB))
            plt.title(f'Detected Cards ({len(readed_cards)} found)')
            plt.axis('off')
            subplot_idx += 1

        # Display individual card regions
        for i in range(num_cards):
            if subplot_idx > rows * cols:
                break

            plt.subplot(rows, cols, subplot_idx)
            card = readed_cards[i]
            plt.imshow(cv2.cvtColor(card.card_region, cv2.COLOR_BGR2RGB))
            plt.title(f"{card.template_name}\n({card.match_score:.2f}, scale:{card.scale:.1f})")
            plt.axis('off')
            subplot_idx += 1

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Display not available: {e}")


def _display_player_results(readed_cards: List[ReadedCard]):
    """Original display player card detection results (for backward compatibility)"""
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