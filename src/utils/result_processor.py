import cv2

try:
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def process_results(results, result_type="player", **kwargs):
    """
    Unified function to process both table and player card results

    Args:
        results: Detection results
        result_type: "player" or "table"
        **kwargs: Additional arguments (image, detector for table cards)
    """

    if result_type == "table":
        _process_table_results(results, **kwargs)
    elif result_type == "player":
        _process_player_results(results, **kwargs)


def _process_table_results(detected_cards, image=None, detector=None, debug=True):
    """Process table card results"""

    if not debug:
        return

    print(f"Detected {len(detected_cards)} table cards")

    # Save cards
    if detected_cards:
        from src.utils.template_validator import extract_card
        from src.utils.save_utils import save_detected_cards

        extracted_cards = [extract_card(image, card) for card in detected_cards]
        save_detected_cards(extracted_cards)

    # Display if possible
    if MATPLOTLIB_AVAILABLE and image is not None and detector is not None:
        _display_table_results(detected_cards, image, detector)


def _process_player_results(results, debug=True):
    """Process player card results"""

    if not debug or not results:
        return

    summary = results.get('summary', {})
    print(f"Found {summary.get('total', 0)} player cards")

    # Save cards
    if results.get('detections'):
        from src.utils.save_utils import save_readed_player_cards
        save_readed_player_cards(results)

    # Display if possible
    if MATPLOTLIB_AVAILABLE:
        _display_player_results(results)


def _display_table_results(detected_cards, image, detector):
    """Display table card detection results"""
    try:
        result_image = detector.draw_detected_cards(image, detected_cards)
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
        if detected_cards:
            from src.utils.template_validator import extract_card
            sample_card = extract_card(image, detected_cards[0])
            plt.imshow(cv2.cvtColor(sample_card, cv2.COLOR_BGR2RGB))
            plt.title('Sample Card')
        plt.axis('off')

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Display not available: {e}")


def _display_player_results(results):
    """Display player card detection results"""
    try:
        original = results.get('original')
        result_image = results.get('result_image')
        summary = results.get('summary', {})

        if original is None or result_image is None:
            return

        plt.figure(figsize=(15, 8))

        plt.subplot(1, 2, 1)
        plt.imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
        plt.title('Original Image')
        plt.axis('off')

        plt.subplot(1, 2, 2)
        plt.imshow(cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB))
        plt.title(f"Detections ({summary.get('total', 0)} found)")
        plt.axis('off')

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Display not available: {e}")