import cv2
from typing import List, Optional, Any
from src.readed_card import ReadedCard

try:
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def process_results(
        readed_cards: List[ReadedCard],
        original_image: Optional[Any] = None,
        result_image: Optional[Any] = None,
        detector: Optional[Any] = None,
        debug: bool = True,
        save_cards: bool = True,
        card_type: str = "cards"  # "table" or "player" or "cards" (generic)
):
    """
    Unified function to process both table and player card results

    Args:
        readed_cards: List of ReadedCard objects
        original_image: Original input image (numpy array)
        result_image: Image with detection overlays (numpy array)
        detector: Detector instance (for table cards, can generate result_image)
        debug: Whether to show debug output and visualizations
        save_cards: Whether to save detected card regions to disk
        card_type: Type of cards for logging ("table", "player", or "cards")
    """

    if not debug:
        return

    # Print detection summary
    print(f"🎯 Detected {len(readed_cards)} {card_type}")

    if not readed_cards:
        print(f"   No {card_type} found")
        return

    # Print individual card details
    for i, card in enumerate(readed_cards):
        print(f"   {card_type.capitalize()} {i + 1}: {card.get_summary()}")

    # Save cards if requested
    if save_cards:
        _save_detected_cards(readed_cards, card_type)

    # Generate result image if we have detector but no result image
    if result_image is None and detector is not None and original_image is not None:
        if hasattr(detector, 'draw_detected_cards'):
            result_image = detector.draw_detected_cards(original_image, readed_cards)

    # Display visualization if matplotlib is available
    if MATPLOTLIB_AVAILABLE:
        _display_unified_results(
            readed_cards,
            original_image,
            result_image,
            detector,
            card_type
        )


def _save_detected_cards(readed_cards: List[ReadedCard], card_type: str):
    """Save detected cards using appropriate save function"""
    try:
        if card_type == "player":
            from src.utils.save_utils import save_readed_player_cards
            save_readed_player_cards(readed_cards)
        else:  # table or generic
            from src.utils.save_utils import save_detected_cards
            save_detected_cards(readed_cards)

        print(f"   💾 Saved {len(readed_cards)} {card_type} to disk")

    except Exception as e:
        print(f"   ❌ Error saving {card_type}: {e}")


def _display_unified_results(
        readed_cards: List[ReadedCard],
        original_image: Optional[Any],
        result_image: Optional[Any],
        detector: Optional[Any],
        card_type: str
):
    """Display unified visualization for any card type"""
    try:
        # Calculate subplot layout
        has_original = original_image is not None
        has_result = result_image is not None
        has_processed = (detector is not None and
                         hasattr(detector, 'image_preprocessor') and
                         original_image is not None)

        num_cards_to_show = min(len(readed_cards), 6)  # Show max 6 individual cards

        # Count available overview images
        overview_images = sum([has_original, has_result, has_processed])
        total_plots = overview_images + num_cards_to_show

        # Determine grid layout
        if total_plots <= 4:
            rows, cols = 2, 2
        elif total_plots <= 6:
            rows, cols = 2, 3
        elif total_plots <= 9:
            rows, cols = 3, 3
        else:
            rows, cols = 4, 3

        plt.figure(figsize=(15, 10))
        subplot_idx = 1

        # Show original image
        if has_original:
            plt.subplot(rows, cols, subplot_idx)
            if len(original_image.shape) == 3:  # Color image
                plt.imshow(cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB))
            else:  # Grayscale
                plt.imshow(original_image, cmap='gray')
            plt.title('Original Image')
            plt.axis('off')
            subplot_idx += 1

        # Show processed image (for table cards)
        if has_processed:
            processed = detector.image_preprocessor.preprocess_image(original_image)
            plt.subplot(rows, cols, subplot_idx)
            plt.imshow(processed, cmap='gray')
            plt.title('Preprocessed Image')
            plt.axis('off')
            subplot_idx += 1

        # Show result image with detections
        if has_result:
            plt.subplot(rows, cols, subplot_idx)
            if len(result_image.shape) == 3:  # Color image
                plt.imshow(cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB))
            else:  # Grayscale
                plt.imshow(result_image, cmap='gray')
            plt.title(f'Detected {card_type.capitalize()} ({len(readed_cards)} found)')
            plt.axis('off')
            subplot_idx += 1

        # Show individual card regions
        for i in range(num_cards_to_show):
            if subplot_idx > rows * cols:
                break

            plt.subplot(rows, cols, subplot_idx)
            card = readed_cards[i]

            if len(card.card_region.shape) == 3:  # Color image
                plt.imshow(cv2.cvtColor(card.card_region, cv2.COLOR_BGR2RGB))
            else:  # Grayscale
                plt.imshow(card.card_region, cmap='gray')

            # Create title with available information
            title_parts = []
            if card.template_name:
                title_parts.append(card.template_name)
            if card.match_score is not None:
                title_parts.append(f"conf:{card.match_score:.2f}")
            if card.scale is not None:
                title_parts.append(f"scale:{card.scale:.1f}")

            title = '\n'.join(title_parts) if title_parts else f"Card {i + 1}"
            plt.title(title)
            plt.axis('off')
            subplot_idx += 1

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"   ⚠️  Visualization not available: {e}")


# Convenience functions for backward compatibility
def process_table_results(readed_cards: List[ReadedCard], image=None, detector=None, debug=True):
    """Backward compatible function for table cards"""
    process_results(
        readed_cards=readed_cards,
        original_image=image,
        detector=detector,
        debug=debug,
        card_type="table"
    )


def process_player_results(readed_cards: List[ReadedCard], debug=True,
                           original_image=None, result_image=None):
    """Backward compatible function for player cards"""
    process_results(
        readed_cards=readed_cards,
        original_image=original_image,
        result_image=result_image,
        debug=debug,
        card_type="player"
    )