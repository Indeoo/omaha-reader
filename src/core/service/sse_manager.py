import threading
import uuid
from queue import Queue
from typing import Dict


class SSEManager:
    """Manages Server-Sent Events clients and message broadcasting"""

    def __init__(self):
        self._clients: Dict[str, Queue] = {}
        self._lock = threading.Lock()

    def add_client(self) -> tuple[str, Queue]:
        """Add a new SSE client and return client ID and queue"""
        client_id = str(uuid.uuid4())
        client_queue = Queue()

        with self._lock:
            self._clients[client_id] = client_queue

        print(f"🔌 New SSE client connected: {client_id[:8]}")
        return client_id, client_queue

    def remove_client(self, client_id: str):
        """Remove an SSE client"""
        with self._lock:
            if client_id in self._clients:
                del self._clients[client_id]
        print(f"🔌 SSE client {client_id[:8]} disconnected")

    def broadcast(self, data: dict):
        """Broadcast data to all connected SSE clients"""
        message = f"data: {json.dumps(data)}\n\n"

        with self._lock:
            # Remove disconnected clients
            disconnected_clients = []

            for client_id, queue in self._clients.items():
                try:
                    queue.put(message, block=False)
                except:
                    disconnected_clients.append(client_id)

            # Clean up disconnected clients
            for client_id in disconnected_clients:
                del self._clients[client_id]

        if self._clients:
            print(f"📡 Broadcasted to {len(self._clients)} SSE clients")

    def get_client_count(self) -> int:
        """Get the number of connected SSE clients"""
        with self._lock:
            return len(self._clients)