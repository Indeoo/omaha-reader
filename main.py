#!/usr/bin/env python3
"""
Console-based version of the poker card detector using DetectionService.
Outputs detection results to console and saves files locally.
"""
import time
from detection_service import DetectionService


class ConsoleObserver:
    """Observer that prints detection results to console"""

    def __init__(self):
        self.last_games = []

    def on_detection_update(self, data: dict):
        """Handle detection updates from detection service"""
        try:
            games = data.get('detections', [])

            if not games:
                print("🃏 No poker tables detected")
                return

            # Check if results have changed
            if self._results_changed(games):
                print("\n" + "=" * 60)
                print(f"🎯 DETECTION UPDATE - {data.get('last_update', 'Unknown time')}")
                print("=" * 60)

                for game in games:
                    self._print_game_result(game)

                self.last_games = games
                print("=" * 60)
            else:
                print("📊 Detection results unchanged")

        except Exception as e:
            print(f"❌ Error processing detection update: {str(e)}")

    def _results_changed(self, new_games) -> bool:
        """Check if detection results have changed"""
        if len(new_games) != len(self.last_games):
            return True

        for new_game, old_game in zip(new_games, self.last_games):
            if (new_game.get('player_cards_string', '') != old_game.get('player_cards_string', '') or
                    new_game.get('table_cards_string', '') != old_game.get('table_cards_string', '')):
                return True

        return False

    def _print_game_result(self, game: dict):
        """Print a single game result with colored cards"""
        window_name = game.get('window_name', 'Unknown')
        player_cards = game.get('player_cards', [])
        table_cards = game.get('table_cards', [])
        player_cards_string = game.get('player_cards_string', '')
        table_cards_string = game.get('table_cards_string', '')

        print(f"\n🎰 Table: {window_name}")
        print("-" * 40)

        # Print player cards
        if player_cards:
            player_display = self._format_cards_for_console(player_cards)
            print(f"  👤 Player: {player_display} ({player_cards_string})")
        else:
            print("  👤 Player: No cards detected")

        # Print table cards
        if table_cards:
            table_display = self._format_cards_for_console(table_cards)
            print(f"  🃏 Table:  {table_display} ({table_cards_string})")
        else:
            print("  🃏 Table:  No cards detected")

    def _format_cards_for_console(self, cards) -> str:
        """Format cards with colors for console display"""
        if not cards:
            return "None"

        # ANSI color codes
        colors = {
            '♦': '\033[94m',  # Blue for Diamonds
            '♥': '\033[91m',  # Red for Hearts
            '♣': '\033[92m',  # Green for Clubs
            '♠': '\033[90m',  # Dark Gray for Spades
        }
        reset = '\033[0m'

        formatted_cards = []
        for card in cards:
            display = card.get('display', card.get('name', ''))
            if display:
                # Find suit and apply color
                for suit, color in colors.items():
                    if suit in display:
                        display = display.replace(suit, f"{color}{suit}{reset}")
                        break
                formatted_cards.append(display)

        return " ".join(formatted_cards)


def main():
    """Main function for console-based card detection"""
    print("🎯 Initializing Console Omaha Card Reader")
    print("------------------------------")

    # Configuration
    WAIT_TIME = 20  # Detection interval in seconds
    DEBUG_MODE = True  # Set to False for live capture

    try:
        # Create console observer
        console_observer = ConsoleObserver()

        # Initialize detection service
        detection_service = DetectionService(
            wait_time=WAIT_TIME,
            debug_mode=DEBUG_MODE
        )

        # Register the console observer
        detection_service.add_observer(console_observer.on_detection_update)

        print(f"✅ Detection service initialized")
        print(f"⏱️  Detection interval: {WAIT_TIME} seconds")
        print(f"🐛 Debug mode: {'ON' if DEBUG_MODE else 'OFF'}")

        if DEBUG_MODE:
            print("📁 Using debug images from: Dropbox/data_screenshots/_20250610_023049/_20250610_025342")
        else:
            print("📷 Live window capture mode")

        print("\nPress Ctrl+C to stop...\n")

        # Start detection service
        detection_service.start()

        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping detection service...")

    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        # Clean up
        if 'detection_service' in locals():
            detection_service.stop()
        print("✅ Console application stopped")


if __name__ == "__main__":
    main()