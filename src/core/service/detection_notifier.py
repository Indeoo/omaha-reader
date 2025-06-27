#!/usr/bin/env python3
"""
Detection notifier that manages observer pattern for detection updates.
Extracted from DetectionService for better separation of concerns.
"""
from typing import List, Callable


class DetectionNotifier:
    """
    Manages observer pattern for detection result notifications.
    Handles adding/removing observers and broadcasting updates.
    """

    def __init__(self):
        self._observers: List[Callable] = []

    def add_observer(self, callback: Callable[[dict], None]):
        """Add an observer that will be notified when detection results change"""
        self._observers.append(callback)

    def remove_observer(self, callback: Callable[[dict], None]):
        """Remove an observer"""
        if callback in self._observers:
            self._observers.remove(callback)

    def notify_observers(self, data: dict):
        """Notify all observers of detection changes"""
        for observer in self._observers:
            try:
                observer(data)
            except Exception as e:
                print(f"❌ Error notifying observer: {str(e)}")

    def get_observer_count(self) -> int:
        """Get the number of registered observers"""
        return len(self._observers)

    def clear_observers(self):
        """Remove all observers"""
        self._observers.clear()